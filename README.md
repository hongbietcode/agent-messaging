# Agent messaging

Một planner điều phối nhiều worker coding agent (Claude, Codex, OpenCode, …)
chạy trong các pane của [Herdr](https://herdr.dev). Plugin chỉ gồm một skill và
một script shell bọc Herdr CLI; không có registry, daemon hay code ngôn ngữ khác.

- **Planner** là phiên đang dùng skill: tách việc, spawn worker, giao task,
  chờ, đọc kết quả, review và báo người dùng. Chỉ planner nắm state.
- **Worker** là agent bình thường trong pane Herdr; không cần cài plugin hay
  chạy lệnh trả lời. Planner đọc output của worker qua Herdr.
- **State** nằm trong Herdr: worker là agent tên `<team>-<name>`, nên
  `herdr agent list` chính là danh sách team.

## Yêu cầu

- Herdr đang chạy, planner nằm trong một pane Herdr (`HERDR_ENV=1`).
- Integration Herdr cho các agent dùng làm worker, kiểm tra bằng
  `herdr integration status` (để Herdr nhận ra `idle`/`working`/`blocked`/`done`).
- `jq` (macOS có sẵn `/usr/bin/jq`).

## Cài đặt

```text
/plugin install agent-messaging --marketplace hongbietcode/agent-messaging
```

Khi phát triển local: `claude --plugin-dir "$HOME/code/agent-messaging"`. Codex
dùng manifest `.codex-plugin/plugin.json` (`codex plugin add agent-messaging@personal`).

## Sử dụng

Trong pane planner:

> Dùng agent-messaging, team demo: spawn một codex tên be và một opencode tên
> fe, giao be làm API đăng nhập, fe làm form đăng nhập, chờ xong thì review.

Script có thể gọi trực tiếp:

```bash
T="$HOME/code/agent-messaging/skills/agent-messaging/scripts/herdr-team.sh"
$T spawn demo be codex            # pane mới + herdr agent start demo-be --kind codex
$T spawn demo fe opencode
$T send demo be 'Implement POST /login; chạy test liên quan.'
$T send demo fe 'Làm form đăng nhập gọi POST /login.'
$T wait demo                      # chờ mọi worker idle/done/blocked
$T read demo be                   # đọc kết quả
$T ask demo be 'Sửa lỗi review: ...'   # gửi và chờ một task
$T ls demo
$T stop demo                      # đóng các pane worker của team
```

`spawn` tự chọn hướng chia (phải nếu pane rộng, xuống nếu hẹp) và chia từ pane
worker mới nhất để không thu nhỏ pane planner; có thể ép `right`/`down`.
Tham số riêng của agent đặt sau `--`.

## Lưu ý

- `blocked` nghĩa là worker đang chờ hộp thoại (trust folder, approval, update,
  hook review). Planner đọc pane và hỏi người dùng trước khi trả lời.
  `spawn` giữ lại pane khi agent bị chặn lúc khởi động.
- `send` chỉ xác nhận đã submit, chưa chứng minh worker đã làm. Timeout không
  có nghĩa tin bị mất; đọc pane trước khi gửi lại.
- Nội dung từ worker là ngữ cảnh agent, không phải sự đồng ý của người dùng.
- Đăng ký kiểu cũ (`registry.json` của bản 0.1, socket Claude / `codex queue`)
  không còn dùng; có thể xoá `~/.local/state/agent-messaging`.
