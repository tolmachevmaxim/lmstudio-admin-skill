# LM Studio API Notes

Use this file only when the bundled script does not already cover the task. The goal is retrieval-first operation with minimal prompt bloat.

## Sources

- OpenAI Codex skills docs: <https://developers.openai.com/codex/skills>
- Codex open-source docs shim: <https://github.com/openai/codex/blob/main/docs/skills.md>
- OpenAI skills catalog: <https://github.com/openai/skills>
- Anthropic skills guidance: <https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md>
- LM Studio REST API overview: <https://lmstudio.ai/docs/developer/rest>
- LM Studio REST list models: <https://lmstudio.ai/docs/developer/rest/list>
- LM Studio REST load model: <https://lmstudio.ai/docs/developer/rest/load>
- LM Studio REST unload model: <https://lmstudio.ai/docs/developer/rest/unload>
- LM Studio REST download model: <https://lmstudio.ai/docs/developer/rest/download>
- LM Studio CLI `lms load`: <https://lmstudio.ai/docs/cli/local-models/load>
- LM Studio CLI `lms server start`: <https://lmstudio.ai/docs/cli/serve/server-start>
- LM Studio CLI `lms server status`: <https://lmstudio.ai/docs/cli/serve/server-status>
- LM Studio server overview: <https://lmstudio.ai/docs/developer/core/server>

## Search Patterns

Use these narrow search terms before opening more of this file:

- `GET /api/v1/models`
- `POST /api/v1/models/load`
- `POST /api/v1/models/unload`
- `POST /api/v1/models/download`
- `lms load`
- `lms server start`
- `lms server status`

## REST Endpoints

Base rule:

- LM Studio native REST lives under `/api/v1/*`
- OpenAI-compatible endpoints live under `/v1/*`
- If a user gives a base URL ending in `/v1`, normalize it back to the host root before calling native REST endpoints

### `GET /api/v1/models`

Purpose:

- list locally available models
- inspect `loaded_instances`
- read display name, key, quantization, capabilities, max context

Useful fields from the response:

- `models[].key`
- `models[].display_name`
- `models[].loaded_instances[].id`
- `models[].loaded_instances[].config.context_length`
- `models[].max_context_length`
- `models[].capabilities.trained_for_tool_use`

### `POST /api/v1/models/load`

Purpose:

- load a model with explicit runtime configuration

Supported request fields from current docs:

- `model`
- `context_length`
- `eval_batch_size`
- `flash_attention`
- `num_experts`
- `offload_kv_cache_to_gpu`

### `POST /api/v1/models/unload`

Purpose:

- unload a model instance by `instance_id`

Required field:

- `instance_id`

### `POST /api/v1/models/download`

Purpose:

- trigger model download by catalog id or exact Hugging Face link

Useful fields:

- `model`
- `quantization`

### `GET /api/v1/models/download/status`

Purpose:

- inspect async download jobs by `job_id`

## CLI Notes

Use `lms` when the task is about:

- server lifecycle: `server start`, `server stop`, `server status`
- optional model estimation with `lms load --estimate-only`

Important `lms load` flags from current docs:

- `--context-length`
- `--gpu`
- `--ttl`
- `--identifier`
- `--estimate-only`

Important server commands:

- `lms server start`
- `lms server stop`
- `lms server status --json --quiet`

Bootstrap notes from current CLI docs:

- macOS/Linux: `~/.lmstudio/bin/lms bootstrap`
- Windows: `cmd /c %USERPROFILE%/.lmstudio/bin/lms.exe bootstrap`

## Practical Guidance

- Prefer REST for model inventory and load or unload because it is easier to parse and more stable for automation.
- Prefer `lms server status --json --quiet` for machine-readable server checks.
- If auth is enabled, send `Authorization: Bearer <token>`.
- Environment names commonly used by wrappers are `LMSTUDIO_BASE_URL`, `LMSTUDIO_API_TOKEN`, and `LM_API_TOKEN`.
