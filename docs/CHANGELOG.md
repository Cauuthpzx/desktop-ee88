# Changelog

Tất cả thay đổi đáng chú ý được ghi lại ở đây.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)

## [1.0.0] - 2026-03-08

### Added
- Hệ thống quản lý nhóm đại lý (group management)
- WebSocket realtime sync cho group data
- Phân quyền admin/user cho group operations
- Agent key system cho group membership
- Test suite hoàn chỉnh (unit, integration, UI, performance)
- Monitoring system (crash reporter, health checker, metrics, audit trail)
- Auto-update với SHA256 verification

### Security
- JWT secret random nếu chưa set (không hardcode)
- Thread-safe token management với Lock
- session_cookie chỉ trả cho agent owner
- Block reserved usernames khi register
- Signal disconnect cleanup chống memory leak
- Connection pooling cho server database
- Transaction safety cho multi-step operations
- Payload size limit cho sync endpoints

### Changed
- Cải thiện performance tinted_icon với cache
- ExpandCard animation không bị accumulation khi toggle nhanh
- Token refresh timer guard chống duplicate

### Fixed
- Memory leak theme_signals trong 7 widgets/tabs
- clear_local đọc cache trước khi xóa
- closeEvent disconnect guard trong AppWindow
