---
name: lmstudio-admin
description: Manage a local or remote LM Studio instance through its REST API and `lms` CLI. Use when Codex or Claude Code needs to inspect available or loaded models, load or unload models, download models, start or stop the LM Studio server, estimate memory fit, normalize LM Studio base URLs, or troubleshoot LM Studio connectivity on Windows, macOS, or Linux. Prefer this skill for repeatable LM Studio admin tasks instead of ad hoc curl commands; it keeps token usage low by using bundled scripts first and loading reference docs only when needed.
---

# LM Studio Admin

# Quick Start

Default to the bundled script instead of re-reading docs or hand-writing HTTP requests. This keeps token usage low and makes behavior consistent across Codex and Claude Code.

Run the script with the platform's Python launcher:

- macOS/Linux: `python3 scripts/lmstudio_admin.py --help`
- Windows: `python scripts/lmstudio_admin.py --help`

Common first commands:

- `python3 scripts/lmstudio_admin.py doctor`
- `python3 scripts/lmstudio_admin.py server-status`
- `python3 scripts/lmstudio_admin.py models --loaded-only`
- `python3 scripts/lmstudio_admin.py variants google/gemma-4-e4b`
- `python3 scripts/lmstudio_admin.py estimate qwen/qwen3-14b --context-length 32768 --gpu max`
- `python3 scripts/lmstudio_admin.py load qwen/qwen3-14b --context-length 32768`
- `python3 scripts/lmstudio_admin.py unload qwen/qwen3-14b`

## Workflow

1. Start with `doctor` to discover:
   - normalized base URL
   - whether the REST API responds
   - whether `lms` is available
   - whether an API token is configured
2. Prefer the bundled script for normal operations:
   - `models`
   - `variants`
   - `estimate`
   - `load`
   - `unload`
   - `download`
   - `server-start`, `server-stop`, `server-status`
3. Read reference files only when the task needs nuance:
   - API behavior, request fields, and endpoint semantics: [references/lmstudio-api.md](references/lmstudio-api.md)
   - skill design and compatibility notes for Codex and Claude Code: [references/skill-design.md](references/skill-design.md)
4. If `lms` is missing, use REST-only features where possible and report the bootstrap hint from the script output rather than inventing installation steps.

## Rules

- Prefer script execution over inline `curl`.
- Prefer REST for model inventory and load or unload operations.
- Prefer `lms` for server lifecycle operations, variant inspection, and memory estimation.
- Keep outputs compact. Ask for `--json` only when a downstream tool or parser needs machine-readable output.
- Do not dump full reference files into context. Search or open only the relevant section.
- When a model has multiple downloaded quantizations, inspect variants first. In practice LM Studio often loads the current `selectedVariant`, not an explicit `@q8_0` model key.
- For Claude Code work, assume full agent mode can inject a very large prompt. Validate fit before changing models just because the raw GGUF file fits on disk.
- On Codex, this skill may live in `.agents/skills/lmstudio-admin`, `$HOME/.agents/skills/lmstudio-admin`, or legacy/user-specific skill folders depending on installation style.
- On Claude Code, this skill should be cloned into `~/.claude/skills/lmstudio-admin`.

## Variant Workflow

Use this flow when the user cares about a specific quantization such as `Q6_K` vs `Q8_0`:

1. Run `doctor`.
2. Run `python3 scripts/lmstudio_admin.py variants <model-key>`.
3. Read `selectedVariant`, per-variant `sizeBytes`, `vision`, `trainedForToolUse`, and `maxContextLength`.
4. Estimate memory fit with `estimate`. Treat the output as a practical fit check, not a guarantee for Claude Code.
5. If the user wants the non-default quantization, confirm LM Studio has that variant selected before loading by plain model key.

Useful examples:

- `python3 scripts/lmstudio_admin.py variants google/gemma-4-e4b`
- `python3 scripts/lmstudio_admin.py variants qwen/qwen3.5-9b`

## Claude Code Notes

For local Claude Code tests against LM Studio, prefer one-shot environment prefixes so rollback is trivial:

- Smoke test: `ANTHROPIC_BASE_URL=http://127.0.0.1:1234 ANTHROPIC_AUTH_TOKEN=lmstudio claude --bare --model <model>`
- Full session: `ANTHROPIC_BASE_URL=http://127.0.0.1:1234 ANTHROPIC_AUTH_TOKEN=lmstudio claude --model <model> --effort <level>`

Observed practical rules:

- `ANTHROPIC_BASE_URL` should point at the LM Studio host root such as `http://127.0.0.1:1234`, not `/v1`.
- `--bare` is useful for smoke tests, but it skips normal auto-discovery. Skills still resolve only when called explicitly as `/skill-name`.
- Full Claude Code sessions can send very large prompts because tools, skills, and system instructions are expanded before the first generation step.
- `--effort high` increases this pressure further. A model that fits at `128k` on paper can still be a bad fit for real tool-heavy sessions.
- For one interactive Claude Code session, `parallel=1` is usually the best LM Studio setting. Higher `parallel` helps throughput, not single-session latency.

## References

Use these references sparingly:

- `references/lmstudio-api.md`
  Read when you need exact request fields, endpoint capabilities, variant inspection details, or the rationale for choosing REST vs `lms`.
- `references/skill-design.md`
  Read when you are editing or redistributing this skill and need to preserve Codex and Claude Code compatibility.

## Troubleshooting

- If the script says the server is unreachable, run `server-start` or check the LM Studio Developer tab.
- If `lms` is unavailable, use the bootstrap hint emitted by `doctor`.
- If authentication fails, set `LMSTUDIO_API_TOKEN` or `LM_API_TOKEN`.
- If the user provides an OpenAI-compatible base URL ending in `/v1`, keep using this skill; the script automatically normalizes it for LM Studio REST endpoints.
- If the user asks for a specific quantization and `load` keeps pulling the wrong one, inspect `variants` first. LM Studio may still be pointed at a different `selectedVariant`.
- If Claude Code hangs on a local model, do not assume the model is broken. Check context pressure, `parallel`, and whether a full skill-heavy prompt is larger than the model's effective working window.
- If the task requires a feature not yet covered by the script, extend the script first instead of embedding fragile one-off shell snippets in the prompt.

## Files

- `scripts/lmstudio_admin.py`: cross-platform LM Studio admin helper using only the Python standard library
- `references/lmstudio-api.md`: concise LM Studio REST and CLI notes, including variant inspection guidance
- `references/skill-design.md`: source notes for Codex and Claude Code skill compatibility
