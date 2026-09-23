# Agent messaging verification

Date: 2026-09-23, 13:54 Asia/Ho_Chi_Minh.

Source destination: `/Users/huutri/code/agent-messaging`.
Verified build: `/private/tmp/agent-messaging-build-f7_3t2rx/agent-messaging`.
Runtime: Python 3.14.4 on macOS; standard-library implementation.

## Final checks

| Check | Result |
| --- | --- |
| `python3 -m unittest discover -s tests -v` | 30 tests pass, 3.990 seconds |
| `ruff check .` | Pass |
| `ruff format --check .` | Pass |
| `mypy --strict skills/agent-messaging/scripts` | Pass, 9 source files |
| Codex `validate_plugin.py .` | Pass |
| Skill `quick_validate.py skills/agent-messaging` | Pass |
| `claude plugin validate . --strict` | Pass |
| `claude plugin validate skills --strict` | Pass |
| Python file line count | Maximum 119 lines |

Socket tests needed approved execution outside the workspace sandbox because
its local `bind()` calls are denied. No test sent messages to live agents.

## Coverage and observed development failures

Identity and role tests were written before the entrypoint existed: all 16
failed, then passed after implementation. Transport tests failed while
`send` was unimplemented, then passed after adding both transports. A new
regression exposed sending after the current Codex profile changed; it now
requires rejoining before sending.

The matrix covers Claude to Claude, Claude to Codex, Codex to Claude, and
Codex to Codex. Tests use real temporary Unix sockets and a controlled queue
executable. They check destination identity/profile/working directory,
Unicode and multiline text, safe argument handling, reply correlation, and
transport receipt wording. This is not four live-model round trips.

Further tests cover concurrent role claims, explicit replacement, private
state permissions, malformed or unsupported registry data, missing session
identity, inherited environment ambiguity, stale Claude registration,
symlinked/missing sockets, empty/oversized messages, self-send, missing roles,
invalid reply IDs, and queue failure without retries.

Before plugin implementation, a native Codex-to-Claude smoke test reached
the user-designated `test-codex` session on Claude 2.1.280 and produced
`ACK CODEX-PING-dc3c451a`. The user also delivered a Claude-to-Codex greeting.
These validate the underlying local transports separately from the finished
plugin integration tests. Installed Codex 0.156.1 exposes `codex queue`.

## Skill usability and review

A baseline agent understood sender identity and ACK semantics without the
new reference; no discipline failure was claimed. A guided evaluation with
the actual skill correctly selected Claude despite inherited Codex variables,
registered a worker, preserved an existing planner registration, and used
the reply metadata. It rejected peer claims as proof of user authorization.

The evaluation suggested an example metadata envelope, a clearer scope for
role questions, and explicit wording about claimed user approval. All three
documentation improvements were applied.

A separate fresh-context reviewer inspected routing, concurrency, role
replacement, profile selection, native Claude message handling, permission
boundaries, packaging, and documentation. No important correctness issue was
found. Its independent restricted run passed 24 cases and hit sandbox
`EPERM` in six socket fixtures; the approved final run passed all 30.

## Operating limits

This version connects existing sessions on the same machine under one OS
user. It does not create terminal panels. Registry entries are not live
presence checks; use `leave` or explicit replacement for closed sessions.
Claude's internal inbox format is version-sensitive. `submitted` or `queued`
is transport acceptance; recipient acknowledgment remains separate.

## Local installation

The complete 25-file build was synchronized to the source destination and
compared byte-for-byte. The original CDM repository remained clean.

Using the plugin-creator helper, created the `agent-messaging` entry in
`/Users/huutri/.agents/plugins/marketplace.json` and a symlink from
`/Users/huutri/plugins/agent-messaging` to the source. Installed with
`codex plugin add agent-messaging@personal --json` into
`/Users/huutri/.codex-cli/plugins/cache/personal/agent-messaging/0.1.0`.
`codex plugin list --marketplace personal --json` confirms installed and
enabled. The cached manifest, skill, and runtime match the source; the cached
CLI's `--help` succeeds. A new Codex conversation is needed to load the skill.

Claude uses `claude --plugin-dir /Users/huutri/code/agent-messaging`.
Its manifest and bundled skill passed the installed Claude validators;
no additional live Claude session was started during installation.
