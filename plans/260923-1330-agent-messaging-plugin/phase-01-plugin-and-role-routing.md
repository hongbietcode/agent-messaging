# Phase 01 — shared messaging plugin and panel roles

Status: completed (2026-09-23).

Scope extension: explicitly requested developer tooling, outside the CDM PRD.
The user requests Claude/Claude, Codex/Codex, Claude/Codex, Codex/Claude
messaging, with one planner panel and one worker panel.

- [x] Resolve current Claude/Codex identities.
- [x] Register a planner/worker pair per team with collision handling.
- [x] Send and explicitly reply over both destination transports.
- [x] Validate the four provider combinations.
- [x] Package for Claude Code and Codex.
- [x] Verify the reference skill and document installation.

## Risks and validation record

- Claude socket frame is confirmed against local Claude Code 2.1.280; future
  versions may require an adapter update.
- Codex requires a version exposing `codex queue` (verified locally on 0.156.1).
- Sandboxes may require permission for local socket access.
- Submitted/queued means transport acceptance; ACK is separate.
- No implementation files existed when this phase was created.


Location update: the user explicitly requested moving this work outside CDM to `~/code`. The standalone source is `/Users/huutri/code/agent-messaging`.

Completion evidence: 30 tests pass; Ruff lint and format, strict mypy, both
plugin manifests, and skill validation pass. A fresh reviewer found no
important correctness issue. All Python files are at most 119 lines.
See the [verification report](../reports/verification-260923-1354-agent-messaging.md)
for the boundary between controlled integration tests and live-session evidence.
