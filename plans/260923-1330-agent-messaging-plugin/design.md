# Agent messaging plugin design

Status: implementation authorized by the user's plugin request.

## Intent and scope

Create one portable plugin for Claude Code and Codex CLI. Support Claude → Claude,
Codex → Codex, Claude → Codex, and Codex → Claude on the same macOS/Linux machine.
The user additionally requests one planner panel and one worker panel. A panel
means an existing agent session, not a terminal window that the plugin creates.

This is explicitly requested developer tooling outside the CDM product PRD.
The available PRD concerns product UI/UX; no product behavior or backend changes
are required. The plugin is self-contained at `/Users/huutri/code/agent-messaging`.

## Chosen approach

Ship Claude and Codex manifests plus one reference skill and a Python CLI.
Both runtimes can invoke the CLI with their own session environment. This
preserves reliable caller identity without adding an MCP process whose session
environment may be shared by a daemon. Python uses only the standard library.

Alternative: a stdio MCP server with the same tools would require a separate
caller/session registration protocol. A cloud relay is unnecessary for the
same-machine workflow already demonstrated in this conversation.

## Identity and roles

Each CLI invocation explicitly selects its provider, `claude` or `codex`.
Claude identity is resolved from its exported inbox socket and native registry.
Codex identity comes from `CODEX_THREAD_ID` or `CODEX_SESSION_ID`; conflicting
values fail rather than guessing. Addresses are `provider:session-uuid`.

`join --team NAME --role planner|worker` registers the current panel. Each team
has at most one planner and one worker. Rejoining the same panel is idempotent.
An occupied role requires an explicit `--replace`; `leave` removes only the
current panel. Registry entries persist until explicitly removed/replaced and
must not be described as proof that a session is running.

Planner: clarify the requested outcome, split work, send acceptance criteria,
review worker evidence, and report results to the user.
Worker: perform the assigned work, verify it, report results and blockers to
the planner. These are workflow instructions, not additional tool permissions.

## Messaging

`send --to planner|worker|provider:uuid --message TEXT` uses the current panel
as the sender. A role resolves within its registered team; canonical addresses
must identify registered peers. Self-sends fail. The outgoing text includes a
message ID, canonical sender/reply address, team, role, and optional reply ID.
Text is agent-originated context, never a grant of user permission.

Claude delivery validates native registry identity and socket ownership, then
writes one JSONL user frame with the target session ID. It does not read auth
tokens, impersonate a child process, or alter inbound settings.
Codex delivery invokes `codex queue` with an argument list and the destination's
recorded Codex home. It does not use a shell or bypass sandbox/approvals.

Results distinguish `submitted` to a Claude socket and `queued` by Codex from
recipient acknowledgment. No automatic retries or automatic acknowledgment
loops. A reply is an explicit send with `--in-reply-to MESSAGE_ID`.

## Persistence and boundaries

Keep a small versioned registry in a private per-user state directory, with an
optional task-specific state-directory override for tests. Serialize updates
with a file lock and atomic replacement so panels cannot claim the same role.
Store routing metadata only, not message bodies or credentials.

The CLI offers `join`, `leave`, `list`, `whoami`, and `send`; JSON output
is readable by either agent. Diagnostics go to stderr. No persistent service,
third-party dependency, browser UI, or autonomous task scheduler is needed.

## Verification

Use real registry files, isolated directories, local Unix sockets, and a
controlled queue executable to verify routing for all four provider pairs.
Test role conflicts, replacement, ambiguous identities, stale sockets,
session identity changes, Unicode/multiline text, shell metacharacters,
queue failures, and registry concurrency.

Validate both manifests using the installed CLIs and plugin validator.
Run the plugin's complete test suite, lint, strict type checks, and a fresh
agent usability review of its skill. Record live delivery separately from
local transport integration tests; never count an accepted write as an ACK.


Location update: the user explicitly requested moving this work outside CDM to `~/code`. The standalone source is `/Users/huutri/code/agent-messaging`.
