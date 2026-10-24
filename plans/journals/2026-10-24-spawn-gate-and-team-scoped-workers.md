---
title: Spawn gate and team-scoped workers
date: 2026-10-24
summary: Planner spawns only with a reason; workers() no longer leaks across teams sharing a name prefix
---

# Spawn gate and team-scoped workers

## What happened
A dry-run evaluation compared the current agent-messaging skill against two variants on 8 golden scenarios, with 2 runs each. The current skill scored 7/8 and variant A (docs-only spawn gate) scored 8/8. The only difference was the coupled API-plus-form scenario, which the current skill split into backend and frontend workers. The "verify with diff/tests" wording showed no measured gain because the current skill already scored 5/5 there. Variant B's `AM_MAX_WORKERS` cap passed a stub test but no run ever exceeded 4 workers, so it was not adopted.

## Changes
- `skills/agent-messaging/SKILL.md`: new "When to spawn" section; Planner loop steps 1-3 now split by context, merge coupled tasks, and check real evidence.
- `README.md`: the example became a package-parallel audit plus an independent Codex reviewer, and a paragraph restates the rule.
- `herdr-team.sh` `workers()`: filters on the `team:<team>` workspace so team `demo` no longer lists `demo-x-be`. It falls back to the name prefix when the team has no such workspace, because live Herdr showed `samx-harness` workers in a differently labelled workspace.

## Evidence
A stub-herdr test passes 5/5 on the new script and fails 2 checks on the old one. A live read-only `ls samx-harness` still lists its 3 workers.

## Follow-up fix
`team_panes` parsed the opaque pane id suffix with `tonumber`, which fails on ids such as `w4:pN` (Herdr 0.9.5 documents IDs as opaque). The jq error was silent: `spawn` still exited 0 but opened a new tab every time, so the 2x2 grid was never filled and free shells were never reused. No caller needs creation order, so the sort was removed. A stub test passes 4/4 on the new script and fails 2 checks on the old one.
