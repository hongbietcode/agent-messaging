---
title: Spawn gate and team-scoped workers
status: completed
mode: fast
created: 2026-10-24
---

# Spawn gate and team-scoped workers

**Outcome:** the planner spawns workers only when there is a reason, splits work
by context, and accepts results on real evidence (diff, tests). `ls`/`wait`
only see the team's own workers.

**Evidence:** a dry-run evaluation (2 runs per variant, 8 golden scenarios)
scored the current skill 7/8 and this variant 8/8; the only delta was the
coupled API + form scenario. The verification wording showed no measured gain
but is kept as cheap and harmless. Source: Anthropic, "Building agents: when to
fold subagents into your main agent loop".

## Constraints

- Keep one skill plus one shell script; no new runtime or dependency.
- Do not change the `herdr-team.sh` CLI.
- SKILL.md stays English, README stays Vietnamese.

## Non-goals

- Eval harness, the `AM_MAX_WORKERS` spawn cap, changes to default models.

## Phases

| # | Phase | Status |
|---|---|---|
| 1 | [Spawn gate docs and team-scoped `workers`](phase-01-spawn-gate-and-team-scoped-workers.md) | completed |

## Acceptance criteria

- SKILL.md has a "When to spawn" section and the revised Planner loop steps 1–3.
- README example matches the rules: package-parallel audit plus an independent
  Codex reviewer; no single worker building the coupled login feature, no
  changelog-only worker.
- `workers` matches only agents in the `team:<team>` workspace: team `demo`
  does not list a `demo-x` worker. Proven by a stub-`herdr` test, `sh -n`,
  and a negative control against the old helper.
