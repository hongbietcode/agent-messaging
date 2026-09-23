# Agent messaging plugin implementation plan

> Execute inline with `superpowers:executing-plans`; use a fresh final reviewer.

**Goal:** installable Claude/Codex plugin supporting all four routing directions
and a planner/worker pair per team.

**Architecture:** shared reference skill invokes a standard-library Python CLI.
A private registry maps session identities to team roles and destination
transports. Claude uses its native inbox; Codex uses its existing queue CLI.

**Spec:** [design.md](design.md)

**Tech stack:** Python 3.14 for development; stdlib runtime; unittest; Ruff; mypy.

## Global constraints

- Work only at `/Users/huutri/code/agent-messaging` and this plan/report.
- Developer-tooling scope extension explicitly requested by the user.
- macOS/Linux, same OS user, same machine; existing sessions.
- No more than 200 lines per Python file; absolute imports at the top.
- No inline code comments; no `print()`; no shell interpolation of messages.
- No permission bypasses, config rewrites, or credential extraction.
- Preserve all existing source and plan history.

## Review focus

1. A second panel cannot silently take a role already occupied by another panel.
2. Stale routing metadata must not send to a reused Claude socket.
3. Inherited environment variables cannot silently change sender provider.
4. Queue acceptance must not be reported as recipient acknowledgment.
5. Concurrent joins must not lose records or allocate one role twice.

## Task 1: Panel identity and team registry

Files: `skills/agent-messaging/scripts/agent_messaging/{models,identity,registry}.py`
and corresponding `tests/test_identity.py`, `tests/test_registry.py`.

Interfaces: typed Peer records; resolve_identity(provider, environment);
Registry.join(peer, team, role, replace), list(), leave(address), get(address).

- [x] Write and run failing tests for identity resolution and role allocation.
- [x] Implement private state storage, locking, and atomic updates.
- [x] Run registry and identity tests; confirm collision/replacement semantics.

```bash
python3 -m unittest discover -s tests -v
```

Expected: identity and registry cases pass; no real messages sent.

## Task 2: Message delivery and command interface

Files: `{claude_delivery,codex_delivery,messaging,cli}.py`, `run.py`, and
`tests/{test_delivery,test_cli,test_role_workflow}.py`.

Interfaces: send(current_identity, target, text, in_reply_to) returns a receipt
with message_id, sender, recipient and submitted/queued status. CLI commands
join/leave/list/whoami/send emit JSON; user errors return nonzero exit codes.

- [x] Write failing socket and queue integration tests for all four directions.
- [x] Implement exact-target delivery and explicit reply correlation.
- [x] Write failing CLI tests for registration, role lookup, and errors.
- [x] Implement CLI and run the entire plugin suite.

```bash
python3 skills/agent-messaging/scripts/run.py --help
python3 -m unittest discover -s tests -v
```

Expected: documented commands available; all four matrix cases pass.

## Task 3: Plugin packaging, role guidance, and evidence

Files: `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`,
`skills/agent-messaging/SKILL.md`, `README.md`, `pyproject.toml`.

- [x] Scaffold and validate Codex metadata; add Claude manifest.
- [x] Write concise invocation and planner/worker guidance.
- [x] Test skill usage in a fresh agent context and record real limitations.
- [x] Validate manifests; run full tests, lint, strict types, and LOC checks.
- [x] Perform a fresh final review; fix material findings with regression tests.
- [x] Record verification in phase file and provide install/use commands.

```bash
claude plugin validate . --strict
python3 /Users/huutri/.codex-cli/skills/.system/plugin-creator/scripts/validate_plugin.py .
ruff check .
mypy --strict skills/agent-messaging/scripts
```

Expected: validators, lint and types pass.

## Decisions

| Decision | Reason |
| --- | --- |
| Skill + CLI instead of MCP | Current shell session metadata reliably identifies each panel. |
| Explicit provider on each command | A Claude process can inherit Codex variables when launched from Codex. |
| Registered peers only | Avoid guessing the destination from unrelated saved conversations. |
| Work in the current checkout | New self-contained plugin files do not overlap product work; no branch operation is needed. |


Location update: the user explicitly requested moving this work outside CDM to `~/code`. The standalone source is `/Users/huutri/code/agent-messaging`.

Implementation update (2026-09-23): the current-checkout decision above is
superseded by the user's location request. Development uses a temporary
staging copy because the original workspace sandbox cannot directly write
`~/code`; approved synchronization updates the standalone source. CDM has no
remaining changes. Tests were organized as `test_panel_identity.py`,
`test_panel_roles.py`, `test_delivery_matrix.py`, and `test_delivery_errors.py`.

Verification: [report](../reports/verification-260923-1354-agent-messaging.md).
