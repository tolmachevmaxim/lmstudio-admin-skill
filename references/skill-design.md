# Skill Design Notes

Use this file when editing or publishing the skill, not during normal LM Studio operations.

## Codex Guidance

The official Codex skills docs and the `openai/skills` catalog emphasize:

- skills trigger primarily from `name` and especially `description`
- keep `SKILL.md` concise
- use bundled scripts for deterministic work
- use references for progressive disclosure
- install locally for Codex with user or repo skill folders

Relevant sources:

- <https://developers.openai.com/codex/skills>
- <https://github.com/openai/codex/blob/main/docs/skills.md>
- <https://github.com/openai/skills>
- <https://github.com/openai/skills/blob/main/skills/.system/skill-creator/SKILL.md>

Specific takeaways used here:

- description must include what the skill does and when to use it
- skill changes are auto-detected, but restart may still help if the skill is not picked up
- repository or user skill locations vary by Codex version, so keep the repo cloneable and path-agnostic

## Claude Code Guidance

Anthropic's skill guidance stresses:

- progressive disclosure
- compact `SKILL.md`
- references loaded only when needed
- descriptions should be explicit enough to overcome under-triggering

Primary source:

- <https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md>

Specific takeaways used here:

- keep the core workflow in `SKILL.md`
- move API details into `references/`
- prefer deterministic scripts for repetitive or fragile tool usage

## Cross-Platform Portability

Design decisions for macOS, Windows, and Linux:

- Python standard library only; no pip install step required
- no shell-specific script required
- `lms` lookup checks both PATH and common LM Studio install locations
- path handling uses `pathlib`
- HTTP requests use `urllib`, so there is no `requests` dependency

## Publication Notes

If publishing this skill to a public repository:

- keep the skill folder self-contained
- avoid extra docs inside the skill folder unless they are true references used by the agent
- if a repo-level README is added, keep it outside the skill folder so the skill remains clean
