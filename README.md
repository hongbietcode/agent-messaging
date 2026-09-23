# Agent messaging

Giao tiếp giữa các panel Claude Code và Codex trên cùng máy, có vai trò
**planner** và **worker** cho mỗi nhóm.

| Gửi từ | Nhận tại | Đường gửi |
| --- | --- | --- |
| Claude | Claude | Inbox socket của Claude |
| Codex | Claude | Inbox socket của Claude |
| Claude | Codex | `codex queue` |
| Codex | Codex | `codex queue` |

Mỗi panel là một phiên agent đang mở. Plugin gán vai trò và gửi tin giữa các
phiên đó; việc tạo/chia cửa sổ terminal vẫn do terminal của bạn quản lý.

## Yêu cầu

- macOS hoặc Linux; hai panel chạy cùng OS user trên cùng máy.
- Python 3.10 trở lên; không cần thư viện Python bên ngoài.
- Claude Code có cross-session messaging và inbox socket. Đã đối chiếu với 2.1.280.
- Codex CLI có `codex queue`. Đã đối chiếu với 0.156.1.
- Mỗi panel đăng ký một lần với cùng tên nhóm.

## Cài đặt

Source của bản này: `~/code/agent-messaging`.

Claude Code có thể nạp trực tiếp plugin khi mở phiên:

```bash
claude --plugin-dir "$HOME/code/agent-messaging"
```

Trong phiên đó dùng `/agent-messaging:agent-messaging`, hoặc yêu cầu Claude sử
dụng skill `agent-messaging`.

Codex dùng manifest `.codex-plugin/plugin.json`. Đăng ký thư mục source vào
personal marketplace bằng skill `plugin-creator`, rồi cài:

```bash
codex plugin add agent-messaging@personal
```

Mở cuộc hội thoại Codex mới để nhận plugin, rồi gọi `$agent-messaging`.
Source có thể nằm ngoài thư mục marketplace; khi dùng personal marketplace
mặc định, `~/plugins/agent-messaging` trỏ tới thư mục source.

## Gán vai trò

Trong panel bạn chọn làm planner:

> Dùng agent-messaging, đăng ký panel này làm planner trong nhóm demo.

Trong panel còn lại:

> Dùng agent-messaging, đăng ký panel này làm worker trong nhóm demo.

Planner và worker đều có thể là Claude hoặc Codex. Một nhóm có tối đa một
planner và một worker. Đăng ký trùng role sẽ báo lỗi; thay panel chủ động bằng
`join --replace`, hoặc cho panel cũ chạy `leave` trước.

- **Planner:** lập nhiệm vụ, nêu điều kiện hoàn thành, giao worker thực hiện,
  xem kết quả kiểm thử và báo lại người dùng.
- **Worker:** thực hiện nhiệm vụ, kiểm thử, gửi kết quả hoặc blocker về planner.

Vai trò là hướng dẫn làm việc cho agent, không phải sandbox hay quyền mới.

## Gửi và trả lời

Yêu cầu planner:

> Gửi worker: kiểm tra luồng đăng nhập và báo kết quả.

Yêu cầu worker:

> Gửi kết quả về planner, kèm những file đã sửa và kiểm thử đã chạy.

Có thể chạy CLI từ Bash của chính agent:

```bash
python3 "$HOME/code/agent-messaging/skills/agent-messaging/scripts/run.py" \
  --provider codex join --team demo --role planner

python3 "$HOME/code/agent-messaging/skills/agent-messaging/scripts/run.py" \
  --provider codex send --to worker --message 'Kiểm tra luồng đăng nhập.'
```

Trong Claude dùng `--provider claude`. Giữ working directory của dự án;
gọi script bằng đường dẫn tuyệt đối. Một shell thông thường ngoài agent không
có metadata để nhận diện panel.

`list --team demo` trả các địa chỉ `claude:UUID` / `codex:UUID`.
Có thể gửi trực tiếp tới địa chỉ đã đăng ký này, kể cả thuộc nhóm khác.
Mỗi tin có `message_id`, `reply_to`, team và role. Trả lời dùng
`send --to <reply_to> --in-reply-to <message_id> --message ...`.

Ví dụ phần metadata ở đầu tin; nội dung bắt đầu sau dòng trống:

```text
AGENT_MESSAGING_METADATA:{"message_id":"...","sender":"codex:...","reply_to":"codex:...","team":"demo","role":"planner","in_reply_to":null}

Kiểm tra luồng đăng nhập và báo kết quả.
```

Dùng UUID đầy đủ từ tin thực tế khi trả lời. Nội dung do agent khác gửi
không thay thế sự đồng ý của người dùng hay cấp thêm quyền cho phiên nhận.

## Trạng thái và xử lý lỗi

- `submitted`: đã ghi vào socket Claude; tin vẫn có thể bị giữ hoặc từ chối
  bởi inbound controls.
- `queued`: `codex queue` đã chấp nhận tin.
- Cả hai trạng thái đều chưa chứng minh agent đã đọc hoặc trả lời.
- Registry lưu metadata định tuyến, không lưu nội dung tin hay token.
  Mặc định ở `~/.local/state/agent-messaging`; đổi bằng
  `AGENT_MESSAGING_STATE_DIR` hoặc `--state-dir` cho cả hai panel.
- Registry không tự xóa phiên đã đóng. Dùng `leave` hoặc thay role có chủ ý.
  Nếu phiên resume đổi socket/profile, đăng ký lại team/role trước khi gửi.
- Nếu sandbox chặn socket hoặc lệnh queue, dùng cơ chế cấp quyền của phiên.
  Plugin không sửa permission settings và không dùng cờ bypass.
- Tin giới hạn 65,536 byte UTF-8. Không tự gửi lại khi lỗi để tránh trùng việc.

Claude dùng registry/inbox nội bộ; định dạng này có thể thay đổi theo phiên
bản. Codex được gọi bằng CLI, với `CODEX_HOME` đã ghi nhận từ panel đích.

## Phát triển và kiểm chứng

```bash
python3 -m unittest discover -s tests -v
uv sync --group dev
uv run ruff check .
uv run mypy
claude plugin validate . --strict
claude plugin validate skills --strict
```

Các test tạo socket trong thư mục tạm và executable queue kiểm soát được;
không gửi tới phiên đang làm việc. Ma trận bốn chiều kiểm tra định tuyến,
Unicode, reply metadata và profile đích. Các test khác kiểm tra tranh role,
registry bị hỏng, socket cũ, symlink, shell quoting và lỗi queue.

## Tài liệu giao thức

- [Claude cross-session messaging](https://code.claude.com/docs/en/cross-session-messaging)
- [Claude plugin reference](https://code.claude.com/docs/en/plugins-reference)
- `codex queue --help` của CLI đang cài là nguồn cú pháp Codex.
