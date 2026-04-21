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
- Prefer `lms` for server lifecycle operations.
- Keep outputs compact. Ask for `--json` only when a downstream tool or parser needs machine-readable output.
- Do not dump full reference files into context. Search or open only the relevant section.
- On Codex, this skill may live in `.agents/skills/lmstudio-admin`, `$HOME/.agents/skills/lmstudio-admin`, or legacy/user-specific skill folders depending on installation style.
- On Claude Code, this skill should be cloned into `~/.claude/skills/lmstudio-admin`.

## References

Use these references sparingly:

- `references/lmstudio-api.md`
  Read when you need exact request fields, endpoint capabilities, or the rationale for choosing REST vs `lms`.
- `references/skill-design.md`
  Read when you are editing or redistributing this skill and need to preserve Codex and Claude Code compatibility.

## Troubleshooting

- If the script says the server is unreachable, run `server-start` or check the LM Studio Developer tab.
- If `lms` is unavailable, use the bootstrap hint emitted by `doctor`.
- If authentication fails, set `LMSTUDIO_API_TOKEN` or `LM_API_TOKEN`.
- If the user provides an OpenAI-compatible base URL ending in `/v1`, keep using this skill; the script automatically normalizes it for LM Studio REST endpoints.
- If the task requires a feature not yet covered by the script, extend the script first instead of embedding fragile one-off shell snippets in the prompt.

## Files

- `scripts/lmstudio_admin.py`: cross-platform LM Studio admin helper using only the Python standard library
- `references/lmstudio-api.md`: concise LM Studio REST and CLI notes
- `references/skill-design.md`: source notes for Codex and Claude Code skill compatibility
