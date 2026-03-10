# CLAUDE.md — QUY TẮC DỰ ÁN DUANGO

> **Tuân thủ xuyên suốt. Mọi code sinh ra PHẢI theo đúng quy tắc này.**
> **Tiêu chí cao nhất: TỐC ĐỘ → ỔN ĐỊNH → HIỆU NĂNG. Bảo mật KHÔNG phải ưu tiên hàng đầu.**

---

## I. TỔNG QUAN DỰ ÁN

```
DUANGO/
├── Goserver/       # Backend — Go (Clean Architecture)
├── GoDesktop/      # Desktop client — C++ Qt6
└── GoWeb/          # Web client — Vue 3 (Layui-Vue)
```

- **Goserver**: REST API server, Go 1.24+, PostgreSQL, JWT + Session Cookie
- **GoDesktop**: Desktop app, C++ Qt6, CMake, kết nối Goserver API
- **GoWeb**: Web SPA, Vue 3 + Layui-Vue monorepo, Vite, kết nối Goserver API

---

## II. QUY TẮC CHUNG (ÁP DỤNG MỌI MODULE)

**1.** Commit message viết bằng **tiếng Việt**.

**2.** Không commit file build (`dist/`, `build/`, `node_modules/`, `*.exe`). Dùng `.gitignore`.

**3.** Mỗi module (`Goserver`, `GoDesktop`, `GoWeb`) hoạt động độc lập, giao tiếp qua API.

**4.** Không hardcode URL/port/credentials. Dùng biến môi trường hoặc file config.

**5.** Không tạo file rỗng, file placeholder, hoặc code chết. Mỗi file phải có nội dung thực.

**6.** DRY — code/logic dùng chung gom 1 chỗ duy nhất. Không copy paste.

**7.** Tên file dùng `snake_case`. Không ngoại lệ.

**8.** Mỗi thay đổi phải test được trước khi merge.

---

## III. GOSERVER — Backend Go

### Kiến trúc
```
Goserver/
├── cmd/server/main.go          # Entry point duy nhất
├── internal/
│   ├── config/                 # Env config
│   ├── database/               # PostgreSQL connection + migration
│   ├── model/                  # Struct + DTO
│   ├── repository/             # Data access (CRUD)
│   ├── service/                # Business logic
│   ├── handler/                # HTTP handlers
│   └── middleware/             # Auth, rate limit
├── pkg/utils/                  # Tiện ích dùng chung
├── docs/                       # Tài liệu API
├── go.mod / go.sum
└── .env.example
```

### Quy tắc Go
- **Clean Architecture**: Handler → Service → Repository → Database. Không bỏ tầng.
- **Naming**: package `lowercase`, function/type `PascalCase`, biến `camelCase`
- **Error handling**: Luôn kiểm tra `err != nil`. Không nuốt error.
- **Context**: Mọi database/API call phải truyền `context.Context`.
- **Dependency**: Inject qua constructor, không dùng global state.
- Auth: JWT (HS256, 24h) + Session Cookie (HttpOnly, Secure, SameSite=Strict)
- OAuth: Google + Facebook
- Rate limiting per-IP cho auth endpoints
- CORS middleware bắt buộc
- Response format nhất quán: `{ "user": {...}, "token": "..." }` hoặc `{ "error": "..." }`

### Chạy server
```bash
cd Goserver
DB_PASSWORD=<password> go run cmd/server/main.go
```

---

## IV. GODESKTOP — Desktop C++ Qt6

### Quy tắc C++
**Tuân thủ đầy đủ `GoDesktop/TIEUCHUAN.md` (200 quy tắc).** Dưới đây là tóm tắt then chốt:

### Cấu trúc bắt buộc
```
GoDesktop/
├── TIEUCHUAN.md                # 200 quy tắc C++ — đọc kỹ
├── CMakeLists.txt              # Root build
├── src/
│   ├── main.cpp                # Entry point duy nhất
│   ├── core/                   # Logic lõi, API client
│   ├── utils/                  # Tiện ích dùng chung
│   └── platform/               # Code phụ thuộc OS
├── include/go_desktop/         # Public headers
├── assets/                     # Icons, resources, config
├── tests/                      # Unit + integration tests
└── docs/                       # Tài liệu kỹ thuật
```

### Naming C++
| Loại | Convention | Ví dụ |
|------|-----------|-------|
| Class/Struct | `PascalCase` | `LoginDialog`, `ApiClient` |
| Function/Method | `snake_case` | `send_request()`, `on_login()` |
| Biến cục bộ | `snake_case` | `frame_count`, `user_name` |
| Member | `m_` prefix | `m_api`, `m_status` |
| Hằng số | `k_` prefix | `k_MaxRetries` |
| File | `snake_case` | `login_dialog.cpp` |

### Quy tắc then chốt
- **RAII bắt buộc**: Mọi resource qua destructor
- **Smart pointer**: `std::unique_ptr` mặc định, raw pointer chỉ cho non-owning
- **Không** `new`/`delete` trực tiếp, không `goto`, không C-style cast
- **`const`** mọi nơi có thể. `noexcept` cho destructor
- **`#pragma once`** cho header guard
- **CMake 3.20+**, C++17 tối thiểu, `-Wall -Wextra -Werror`
- Mỗi `.cpp` đi kèm `.h` (trừ `main.cpp`)
- Mỗi thư mục con có `CMakeLists.txt` riêng + `README.md` ngắn

### Build
```bash
cd GoDesktop
PATH="/c/msys64/mingw64/bin:$PATH"
cmake -B build -G "MinGW Makefiles" -DCMAKE_PREFIX_PATH="/c/msys64/mingw64"
cmake --build build
```

---

## V. GOWEB — Web Client Vue 3

### Cấu trúc
```
GoWeb/
├── package.json                # Root monorepo
├── pnpm-workspace.yaml         # pnpm workspace
├── pnpm-lock.yaml
├── vitest.config.ts            # Test config
├── build/                      # Shared build config
├── docs/                       # Web app chính (Vue 3 SPA)
│   └── src/
│       ├── view/               # Pages
│       ├── router/             # Vue Router
│       ├── store/              # Pinia state
│       ├── layouts/            # Layout components
│       ├── components/         # Shared components
│       ├── language/           # i18n
│       └── assets/             # Static files
├── packages/                   # UI library source
│   ├── component/              # 100+ Vue components
│   ├── layui/                  # Main library
│   ├── icons/                  # Icon library
│   ├── layer/                  # Dialog/modal
│   └── json-schema-form/       # Form builder
└── play/                       # Dev playground
```

### Quy tắc Web
- **Vue 3 Composition API** + TypeScript. Không Options API.
- **Layui-Vue** là UI library — sửa trực tiếp trong `packages/`, KHÔNG override CSS bên ngoài.
- **CẤM override CSS class `.layui-*`** trong global CSS khi chưa được phép.
- **Hạn chế tối đa `!important`**. Fix triệt để trong source gốc.
- **Pinia** cho state management. Mỗi store có trách nhiệm đơn nhất.
- **Vue Router** cho navigation.
- Composables cho logic tái sử dụng (`composables/`).
- **Vite** build tool. Thay đổi trong `packages/` cần restart dev server.
- Tên file component: `PascalCase.vue`. Tên file khác: `snake_case`.

### ⚠️ DÙNG MẶC ĐỊNH, KHÔNG CUSTOM
- **PHẢI dùng component Layui-Vue có sẵn** (100+ component). KHÔNG tự viết component thay thế.
- Danh sách component có sẵn: xem `docs/src/document/zh-CN/components/` (77 file tài liệu).
- **Component sẵn có**: Button, Input, Select, Table, Form, Tree, Tabs, Menu, Dropdown, DatePicker, Upload, Modal (Layer), Drawer, Tooltip, Pagination, Card, Collapse, Steps, Tag, Badge, Avatar, Empty, Transfer, Cascader, Rate, Slider, Switch, Radio, Checkbox, Icon, Layout, Grid, v.v.
- **KHÔNG custom lại** giao diện, theme, hoặc behavior của component mặc định.
- **KHÔNG viết CSS riêng** cho component đã có style. Dùng props/slots do component cung cấp.
- **KHÔNG tạo wrapper component** bọc lại component Layui-Vue khi không cần thiết.
- Nếu component mặc định thiếu tính năng → sửa trực tiếp trong `packages/component/` source gốc.
- Tham khảo cách dùng: đọc file `.md` tương ứng trong `docs/src/document/zh-CN/components/`.

### Dev
```bash
cd GoWeb
pnpm install
pnpm dev          # Playground
pnpm dev:docs     # Web app chính
```

---

## VI. API CONTRACT

Goserver phục vụ cả GoDesktop và GoWeb. Các endpoint:

| Method | Path | Mô tả |
|--------|------|--------|
| POST | `/register` | Đăng ký |
| POST | `/login` | Đăng nhập → JWT + Cookie |
| POST | `/logout` | Đăng xuất |
| PUT | `/change-password` | Đổi mật khẩu (cần auth) |
| GET | `/auth/google` | OAuth Google redirect |
| GET | `/auth/google/callback` | OAuth Google callback |
| GET | `/auth/facebook` | OAuth Facebook redirect |
| GET | `/auth/facebook/callback` | OAuth Facebook callback |

### Response format
```json
// Success
{ "user": { "id": 1, "email": "...", "created_at": "..." }, "token": "jwt..." }

// Error
{ "error": "mô tả lỗi" }
```

---

## VII. ICONS — ICONS8 FLUENCY

- **Thư mục gốc**: `C:\Users\Admin\Desktop\icons8-download\icons8-fluency\`
- **Số lượng**: 1450+ icon PNG (fluency style, màu sắc)
- **SỬ DỤNG CHUNG** cho cả GoWeb và GoDesktop. Không dùng icon từ nguồn khác.
- Khi cần icon, tìm trong thư mục này trước. Tên file mô tả nội dung (VD: `add-file.png`, `login.png`).
- GoDesktop: embed qua Qt resource file (`.qrc`)
- GoWeb: copy icon cần dùng vào `GoWeb/docs/public/icons/` hoặc `src/assets/icons/`

---

## IX. MÔI TRƯỜNG PHÁT TRIỂN

- **OS**: Windows 10 (MSYS2/MinGW64)
- **Go**: 1.24+
- **PostgreSQL**: localhost:5432, DB `goserver`
- **C++ Compiler**: GCC 15.2 (msys64/mingw64)
- **Qt**: Qt6 (msys64/mingw64)
- **Node.js**: pnpm package manager
- **Editor**: VSCode

---

## X. NGUYÊN TẮC CỐT LÕI

> **Ưu tiên theo thứ tự: TỐC ĐỘ → ỔN ĐỊNH → HIỆU NĂNG → bảo mật**

> 1. **Tốc độ là vua** — response nhanh, render nhanh, build nhanh. Mọi quyết định đều hướng tới tốc độ
> 2. **Ổn định không thỏa hiệp** — không crash, không leak, không race condition. Chạy 24/7 không lỗi
> 3. **Hiệu năng đo được** — profile trước khi tối ưu, benchmark mọi thay đổi quan trọng
> 4. **Đơn giản trước** — không over-engineering, dùng cái có sẵn trước khi tự viết
> 5. **Mỗi module độc lập** — giao tiếp qua API, fail fast, không truyền data sai qua nhiều layer
