# skills

Agent skills from my day-to-day work: video generation in ComfyUI, research with agents, and code review. Each one is a folder with a `SKILL.md`, so it works in Claude Code, Codex or any harness that reads skills.

| Skill | What it does |
|---|---|
| [`comfyui-workflow`](skills/comfyui-workflow) | Edit ComfyUI UI workflows by script without wrecking the layout: two-row groups, short titles, real node sizes, no overlaps. `check_layout.py` must print `OK` before the agent hands anything over. |
| [`civitai`](skills/civitai) | Search, compare, inspect and download Civitai models, LoRAs and workflows with the official CLI. It never generates (that spends Buzz) unless asked. |
| [`research-lab`](skills/research-lab) | Run a research program as the professor: pick lines that don't overlap, give each to a research-student agent, schedule the one shared GPU, check every result yourself. Needs [`agents/research-student.md`](agents/research-student.md). |
| [`unslop`](skills/unslop) | Code review against strict simplicity rules: short names, no wrappers or utils dumps, one data type, small pure functions, tests on the real code. |
| [`web-unslop`](skills/web-unslop) | Frontend anti-slop workflow for apps, dashboards and landing pages: remove the vibe-coded tells and make it look intentional. |

## Install

```bash
npx skills add FrancescoSaverioZuppichini/skills
```

Or copy the folders you want: `skills/<name>` into `~/.claude/skills/` (Claude Code) or `~/.agents/skills/` (Codex). For `research-lab`, also copy `agents/research-student.md` into `~/.claude/agents/`.

## Goes well with

- [local-artifacts](https://github.com/FrancescoSaverioZuppichini/local-artifacts): the live review pages `research-lab` writes to.
- [brand-system-skill](https://github.com/FrancescoSaverioZuppichini/brand-system-skill): brand identity and design systems, three directions first.

## Source footage

The swap tasks start from a real clip. Use footage you have the right to use. A face-only swap keeps the real person's body, so it needs that person's consent.

## License

