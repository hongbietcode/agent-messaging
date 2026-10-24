---
phase: 1
title: Spawn gate docs and team-scoped workers
status: completed
---

# Phase 1: Spawn gate docs and team-scoped workers

## Files

- `skills/agent-messaging/SKILL.md`
- `README.md`
- `skills/agent-messaging/scripts/herdr-team.sh`

## Steps

1. SKILL.md: add "When to spawn" before "Planner loop" (default inline; spawn
   for independent parallel work, context bloat, a different runtime/model such
   as an independent reviewer, or an explicit user request). Rewrite steps 1–3:
   split by context and merge coupled tasks; spawn what the task needs or the
   user asked for; check `git diff` and tests instead of trusting summaries.
2. README: replace the be/fe example with a package-parallel audit plus an
   independent Codex reviewer, using the same commands; add a short paragraph
   restating the spawn rule.
3. `herdr-team.sh`: `workers` keeps only agents whose `workspace_id` is the
   team workspace and whose name starts with `<team>-`. Today the name prefix
   alone lets team `demo` match `demo-x-be` from team `demo-x`. When the team
   has no `team:<team>` workspace, fall back to the name prefix: live Herdr
   showed a team (`samx-harness`) whose workers sit in a differently labelled
   workspace, and a strict filter would make its `wait` return at once.

## Validation

- `sh -n` on the script.
- Scratchpad stub-`herdr` test: team `demo` with workers in its own workspace
  plus `demo-x-*` agents in another workspace; `ls` lists only `demo` workers,
  `wait` waits only on them, a team without a workspace falls back to the
  prefix. The same test fails 2 checks against the old helper.
- Live read-only `ls samx-harness` still lists its three workers.

## Risk and rollback

Once a team has a `team:<team>` workspace, a worker started by hand outside it
is no longer listed; spawn always uses that workspace. Roll back
with `git revert`.
