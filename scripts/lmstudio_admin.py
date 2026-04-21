#!/usr/bin/env python3
"""Cross-platform LM Studio admin helper.

Uses LM Studio REST endpoints for model operations and the `lms` CLI for
server lifecycle operations when available.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional
from urllib import error, parse, request


DEFAULT_BASE_URL = "http://127.0.0.1:1234"
TIMEOUT_SECONDS = 20


class LMStudioError(RuntimeError):
    """Raised when LM Studio operations fail in an expected way."""


def normalize_base_url(raw_url: Optional[str]) -> str:
    url = (raw_url or os.environ.get("LMSTUDIO_BASE_URL") or DEFAULT_BASE_URL).strip()
    if not url:
        url = DEFAULT_BASE_URL
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    url = url.rstrip("/")
    if url.endswith("/v1"):
        url = url[:-3]
    if url.endswith("/api/v1"):
        url = url[:-7]
    return url


def build_rest_url(base_url: str, path: str) -> str:
    return base_url.rstrip("/") + "/api/v1/" + path.lstrip("/")


def api_token() -> Optional[str]:
    for key in ("LMSTUDIO_API_TOKEN", "LM_API_TOKEN"):
        value = os.environ.get(key)
        if value:
            return value.strip()
    return None


def http_request(
    method: str,
    url: str,
    payload: Optional[Dict[str, Any]] = None,
    timeout: int = TIMEOUT_SECONDS,
) -> Any:
    headers = {"Accept": "application/json"}
    token = api_token()
    data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = request.Request(url, data=data, headers=headers, method=method.upper())
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            if not body:
                return {}
            content_type = resp.headers.get("Content-Type", "")
            if "json" in content_type:
                return json.loads(body)
            return body
    except error.HTTPError as exc:
        try:
            body = exc.read().decode("utf-8")
        except Exception:
            body = exc.reason
        raise LMStudioError(f"HTTP {exc.code} for {url}: {body}") from exc
    except error.URLError as exc:
        raise LMStudioError(f"Failed to reach {url}: {exc.reason}") from exc


def which_lms() -> Optional[str]:
    direct = shutil.which("lms")
    if direct:
        return direct
    home = Path.home()
    candidates = []
    if os.name == "nt":
        candidates.extend(
            [
                home / ".lmstudio" / "bin" / "lms.exe",
                home / ".lmstudio" / "bin" / "lms.cmd",
            ]
        )
    else:
        candidates.append(home / ".lmstudio" / "bin" / "lms")
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def lms_bootstrap_hint() -> str:
    if os.name == "nt":
        return r"cmd /c %USERPROFILE%/.lmstudio/bin/lms.exe bootstrap"
    return "~/.lmstudio/bin/lms bootstrap"


def run_lms(args: list[str]) -> subprocess.CompletedProcess[str]:
    lms_bin = which_lms()
    if not lms_bin:
        raise LMStudioError(
            "Could not find `lms`. Bootstrap it first: " + lms_bootstrap_hint()
        )
    return subprocess.run(
        [lms_bin] + args,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def emit_process_output(proc: subprocess.CompletedProcess[str]) -> None:
    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()
    if stdout:
        print(stdout)
    if stderr and stderr != stdout:
        print(stderr)


def ping_models(base_url: str) -> Dict[str, Any]:
    return http_request("GET", build_rest_url(base_url, "models"))


def cmd_doctor(args: argparse.Namespace) -> int:
    base_url = normalize_base_url(args.base_url)
    report = {
        "base_url": base_url,
        "rest_url": build_rest_url(base_url, "models"),
        "api_token_configured": bool(api_token()),
        "lms_path": which_lms(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "python": sys.version.split()[0],
        },
    }
    try:
        models = ping_models(base_url)
        report["server_reachable"] = True
        report["model_count"] = len(models.get("models", []))
        report["loaded_instance_count"] = sum(
            len(model.get("loaded_instances", [])) for model in models.get("models", [])
        )
    except LMStudioError as exc:
        report["server_reachable"] = False
        report["error"] = str(exc)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=True))
        return 0
    print(f"Base URL: {report['base_url']}")
    print(f"REST URL: {report['rest_url']}")
    print(f"API token configured: {'yes' if report['api_token_configured'] else 'no'}")
    print(f"`lms` path: {report['lms_path'] or 'not found'}")
    print(
        "Platform: "
        f"{report['platform']['system']} {report['platform']['release']} "
        f"(Python {report['platform']['python']})"
    )
    print(f"Server reachable: {'yes' if report['server_reachable'] else 'no'}")
    if report.get("server_reachable"):
        print(f"Available models: {report['model_count']}")
        print(f"Loaded instances: {report['loaded_instance_count']}")
    else:
        print(f"Error: {report['error']}")
        if not report["lms_path"]:
            print("Bootstrap hint: " + lms_bootstrap_hint())
    return 0


def collect_models(base_url: str, loaded_only: bool) -> Dict[str, Any]:
    payload = ping_models(base_url)
    models = payload.get("models", [])
    if loaded_only:
        models = [m for m in models if m.get("loaded_instances")]
    return {"models": models}


def cmd_models(args: argparse.Namespace) -> int:
    result = collect_models(normalize_base_url(args.base_url), args.loaded_only)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=True))
        return 0
    if not result["models"]:
        print("No models matched.")
        return 0
    for model in result["models"]:
        quant = model.get("quantization") or {}
        quant_name = quant.get("name") or "unknown"
        loaded = model.get("loaded_instances", [])
        print(
            f"{model.get('key')} | {model.get('display_name')} | "
            f"{model.get('type')} | {quant_name} | loaded={len(loaded)}"
        )
        for instance in loaded:
            cfg = instance.get("config", {})
            print(
                "  - "
                f"{instance.get('id')} "
                f"(ctx={cfg.get('context_length')}, "
                f"flash_attention={cfg.get('flash_attention')})"
            )
    return 0


def cmd_load(args: argparse.Namespace) -> int:
    payload: Dict[str, Any] = {"model": args.model}
    for field in (
        "context_length",
        "eval_batch_size",
        "flash_attention",
        "num_experts",
        "offload_kv_cache_to_gpu",
    ):
        value = getattr(args, field)
        if value is not None:
            payload[field] = value
    result = http_request(
        "POST",
        build_rest_url(normalize_base_url(args.base_url), "models/load"),
        payload=payload,
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


def cmd_estimate(args: argparse.Namespace) -> int:
    cmd = ["load", "--estimate-only", args.model]
    if args.context_length is not None:
        cmd.extend(["--context-length", str(args.context_length)])
    if args.gpu is not None:
        cmd.extend(["--gpu", args.gpu])
    proc = run_lms(cmd)
    emit_process_output(proc)
    if proc.returncode != 0:
        raise LMStudioError(proc.stderr.strip() or "Failed to estimate model fit")
    return 0


def cmd_unload(args: argparse.Namespace) -> int:
    result = http_request(
        "POST",
        build_rest_url(normalize_base_url(args.base_url), "models/unload"),
        payload={"instance_id": args.instance_id},
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


def cmd_download(args: argparse.Namespace) -> int:
    payload: Dict[str, Any] = {"model": args.model}
    if args.quantization:
        payload["quantization"] = args.quantization
    result = http_request(
        "POST",
        build_rest_url(normalize_base_url(args.base_url), "models/download"),
        payload=payload,
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


def cmd_download_status(args: argparse.Namespace) -> int:
    base_url = normalize_base_url(args.base_url)
    query = parse.urlencode({"job_id": args.job_id})
    result = http_request(
        "GET", build_rest_url(base_url, "models/download/status") + "?" + query
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


def cmd_server_status(args: argparse.Namespace) -> int:
    proc = run_lms(["server", "status", "--json", "--quiet"])
    if proc.returncode != 0:
        raise LMStudioError(proc.stderr.strip() or proc.stdout.strip() or "lms failed")
    text = proc.stdout.strip()
    if not text:
        raise LMStudioError("`lms server status` returned no output")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        payload = {"raw": text}
    print(json.dumps(payload, indent=2, ensure_ascii=True))
    return 0


def cmd_server_start(args: argparse.Namespace) -> int:
    cmd = ["server", "start"]
    if args.port is not None:
        cmd.extend(["--port", str(args.port)])
    if args.cors:
        cmd.append("--cors")
    proc = run_lms(cmd)
    emit_process_output(proc)
    if proc.returncode != 0:
        raise LMStudioError(proc.stderr.strip() or "Failed to start server")
    return 0


def cmd_server_stop(args: argparse.Namespace) -> int:
    proc = run_lms(["server", "stop"])
    emit_process_output(proc)
    if proc.returncode != 0:
        raise LMStudioError(proc.stderr.strip() or "Failed to stop server")
    return 0


def add_bool_argument(parser: argparse.ArgumentParser, name: str, help_text: str) -> None:
    parser.add_argument(
        f"--{name}",
        dest=name.replace("-", "_"),
        action=argparse.BooleanOptionalAction,
        default=None,
        help=help_text,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LM Studio admin helper")
    parser.add_argument(
        "--base-url",
        help="LM Studio base URL. Accepts forms like http://127.0.0.1:1234 or .../v1",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Inspect LM Studio connectivity")
    doctor.add_argument("--json", action="store_true", help="Emit JSON output")
    doctor.set_defaults(func=cmd_doctor)

    models = subparsers.add_parser("models", help="List available models")
    models.add_argument("--loaded-only", action="store_true", help="Only show loaded models")
    models.add_argument("--json", action="store_true", help="Emit JSON output")
    models.set_defaults(func=cmd_models)

    load = subparsers.add_parser("load", help="Load a model through the REST API")
    load.add_argument("model", help="Model key, for example qwen/qwen3-14b")
    load.add_argument("--context-length", type=int, dest="context_length")
    load.add_argument("--eval-batch-size", type=int, dest="eval_batch_size")
    load.add_argument("--num-experts", type=int, dest="num_experts")
    add_bool_argument(load, "flash-attention", "Enable or disable Flash Attention")
    add_bool_argument(
        load,
        "offload-kv-cache-to-gpu",
        "Enable or disable KV cache GPU offload",
    )
    load.set_defaults(func=cmd_load)

    estimate = subparsers.add_parser(
        "estimate", help="Estimate memory use through `lms load --estimate-only`"
    )
    estimate.add_argument("model", help="Model key, for example qwen/qwen3-14b")
    estimate.add_argument("--context-length", type=int, dest="context_length")
    estimate.add_argument(
        "--gpu",
        help="GPU offload mode for estimation, for example max, off, or 0.5",
    )
    estimate.set_defaults(func=cmd_estimate)

    unload = subparsers.add_parser("unload", help="Unload a model instance")
    unload.add_argument("instance_id", help="Loaded instance id")
    unload.set_defaults(func=cmd_unload)

    download = subparsers.add_parser("download", help="Download a model through the REST API")
    download.add_argument("model", help="Catalog id or exact Hugging Face link")
    download.add_argument("--quantization", help="Quantization level when supported")
    download.set_defaults(func=cmd_download)

    download_status = subparsers.add_parser(
        "download-status", help="Check a model download job"
    )
    download_status.add_argument("job_id", help="Download job id")
    download_status.set_defaults(func=cmd_download_status)

    server_status = subparsers.add_parser(
        "server-status", help="Check LM Studio server status via `lms`"
    )
    server_status.set_defaults(func=cmd_server_status)

    server_start = subparsers.add_parser(
        "server-start", help="Start LM Studio server via `lms`"
    )
    server_start.add_argument("--port", type=int, help="Server port override")
    server_start.add_argument("--cors", action="store_true", help="Enable CORS")
    server_start.set_defaults(func=cmd_server_start)

    server_stop = subparsers.add_parser(
        "server-stop", help="Stop LM Studio server via `lms`"
    )
    server_stop.set_defaults(func=cmd_server_stop)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except LMStudioError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
