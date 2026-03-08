# KIẾN TRÚC DATA SYNC NHÓM — PHÂN TÍCH ĐẦY ĐỦ

## Ràng buộc đã xác nhận
- Mỗi đại lý chỉ thuộc **1 nhóm** (đơn giản hóa schema: bỏ bảng group_members, 
  thêm `group_id` vào bảng agents)
- Cookies lưu **2 nơi**: Server DB + Client QSettings
- Client hiện tại fetch upstream **trực tiếp** bằng cookie local (0ms read, nhanh)
- Server dùng FastAPI + uvicorn, chưa có WebSocket/Redis

---

## SO SÁNH 5 PHƯƠNG ÁN

### Phương án A: Client push → Server merge → Server push (ý tưởng của bạn)

```
Client A fetch upstream → push data lên server
Client B fetch upstream → push data lên server
Server merge tất cả → broadcast xuống tất cả clients
```

| Ưu | Nhược |
|----|-------|
| Client tận dụng cookie local (nhanh) | 2x network: upstream + server |
| Server có data tập trung | Race condition: ai push trước? |
| | Server phải lưu + merge data liên tục |
| | **Không realtime** — Client B phải đợi Client A push xong |
| | Server thành bottleneck storage |

**Tốc độ: ★★☆☆☆** — Chậm vì 2 hop + đợi merge

---

### Phương án B: Server làm proxy (tài liệu trước đề xuất)

```
Client → Server → fetch từ tất cả agents (dùng cookie DB) → merge → trả về Client
```

| Ưu | Nhược |
|----|-------|
| Cookie an toàn (chỉ ở server) | 2x network: server→upstream + server→client |
| Tất cả client thấy cùng data | Server fetch nhiều agents = chậm |
| Logic merge tập trung | Server bandwidth gấp đôi |

**Tốc độ: ★★☆☆☆** — Tương tự A

---

### Phương án C: ~~Client fetch trực tiếp~~ → Server proxy fetch ⚠️ BẢO MẬT

> **⛔ CẢNH BÁO BẢO MẬT:** Phiên bản cũ của Phương án C gửi session cookies
> của các agents khác về client (QSettings). Đây là lỗ hổng nghiêm trọng —
> cookie KHÔNG BAO GIỜ được chia sẻ với client. Thay vào đó, dùng server-proxy:

```
Client join nhóm → Client authenticate bằng credentials riêng
→ Server giữ TẤT CẢ upstream cookies trên server (DB)
→ Client gọi: GET /api/groups/{id}/data?data_type=customers
→ Server dùng stored cookies fetch từ upstream (song song)
→ Server merge + trả kết quả (KHÔNG trả cookies)
→ Server ghi audit log (who requested what)
```

| Ưu | Nhược |
|----|-------|
| Cookie an toàn (chỉ ở server) | 2 hop: client→server→upstream |
| Audit trail đầy đủ | Server bandwidth cao hơn |
| Access control tập trung | Cần server có đủ tài nguyên |
| Client KHÔNG CẦN biết cookie | |

**Tốc độ: ★★★☆☆** — Chậm hơn fetch trực tiếp, nhưng an toàn

---

### Phương án D: Hybrid + WebSocket realtime ⭐ TỐI ƯU NHẤT

```
FETCH: Client fetch trực tiếp (Cách C — nhanh nhất)
SYNC:  WebSocket thông báo khi có thay đổi

Timeline:
1. Client A mở tab nhóm → fetch song song tất cả agents → hiển thị (1-2s)
2. Client A fetch xong → push "snapshot hash" lên server qua WS
3. Server broadcast hash cho tất cả member
4. Client B nhận hash → so sánh với local → nếu khác → re-fetch
```

| Ưu | Nhược |
|----|-------|
| Fetch nhanh nhất (trực tiếp) | Cần thêm WebSocket server |
| **Gần realtime** giữa members | Phức tạp hơn |
| Chỉ sync khi có thay đổi | Cookie vẫn nằm trên máy member |
| Nhẹ — chỉ gửi hash, không gửi data |  |

**Tốc độ: ★★★★★ + Realtime: ★★★★☆**

---

### Phương án E: Server cache + polling (THỰC TẾ NHẤT) ⭐⭐ RECOMMENDED

```
BƯỚC 1 — Lần đầu mở nhóm (COLD):
  Client fetch song song tất cả agents (trực tiếp, nhanh)
  → Push kết quả lên server: POST /api/groups/{id}/sync
  → Server lưu vào bảng group_data_cache

BƯỚC 2 — Lần sau mở nhóm (WARM):
  Client gọi GET /api/groups/{id}/cache?since=<timestamp>
  → Server trả data đã merge từ cache (cực nhanh)
  → Nếu cache cũ → Client re-fetch + push lại

BƯỚC 3 — Realtime bằng POLLING (đơn giản):
  Client poll mỗi 30-60s: GET /api/groups/{id}/cache/version
  → Nếu version thay đổi → re-fetch cache
  → Không cần WebSocket!
```

| Ưu | Nhược |
|----|-------|
| Fetch lần đầu nhanh (trực tiếp) | Cookie agents nằm trên máy member |
| Lần sau cực nhanh (đọc cache server) | Data delay 30-60s (polling interval) |
| **Mọi member thấy cùng data** | Server cần thêm bảng cache |
| Không cần WebSocket | |
| Đơn giản implement | |
| Phù hợp kiến trúc hiện tại | |

**Tốc độ: ★★★★★ (lần đầu) / ★★★★★ (lần sau từ cache)**
**Realtime: ★★★☆☆ (30-60s delay) — ĐỦ TỐT cho quản lý đại lý**

---

## RECOMMENDED: PHƯƠNG ÁN E — CHI TIẾT

### Tại sao chọn E?

1. **Lần đầu nhanh** — client fetch trực tiếp upstream (giống hiện tại)
2. **Lần sau nhanh hơn** — đọc cache server (1 request thay vì N requests)
3. **Mọi member thấy cùng data** — server là single source of truth
4. **Không cần WebSocket** — polling đủ tốt cho use case này
5. **Implement dễ** — thêm 1 bảng cache + 2 endpoints + timer client

### Database bổ sung

```sql
-- Cache data nhóm (server-side)
CREATE TABLE IF NOT EXISTS group_data_cache (
    id              BIGSERIAL PRIMARY KEY,
    group_id        BIGINT NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    data_type       VARCHAR(50) NOT NULL,   -- customers | deposits | withdrawals | ...
    data_json       JSONB NOT NULL DEFAULT '[]',
    total_count     INT DEFAULT 0,
    
    -- Metadata
    agents_fetched  JSONB DEFAULT '[]',     -- [{id, name, status, row_count}]
    agents_errors   JSONB DEFAULT '[]',     -- [{id, name, error}]
    
    -- Versioning cho polling
    version         BIGINT DEFAULT 1,
    
    -- Ai sync, khi nào
    synced_by       BIGINT REFERENCES users(id),
    synced_at       TIMESTAMPTZ DEFAULT NOW(),
    
    -- Expiry — tự động dọn cache cũ
    expires_at      TIMESTAMPTZ,            -- NULL = không hết hạn
    
    UNIQUE(group_id, data_type),
    
    -- Giới hạn kích thước data_json (tối đa ~5MB)
    CONSTRAINT chk_data_json_size CHECK (pg_column_size(data_json) <= 5242880),
    -- Giới hạn số phần tử trong mảng JSON (tối đa 10000 items)
    CONSTRAINT chk_data_json_length CHECK (
        jsonb_typeof(data_json) = 'array' AND jsonb_array_length(data_json) <= 10000
    )
);

CREATE INDEX idx_gdc_group ON group_data_cache(group_id);
-- Index cho polling theo version (composite: group + type + version)
CREATE INDEX idx_gdc_version ON group_data_cache(group_id, data_type, version);

-- Cleanup job: xóa cache hết hạn (chạy bằng pg_cron hoặc cron + DELETE)
-- pg_cron: SELECT cron.schedule('cleanup-expired-cache', '*/15 * * * *',
--   $$DELETE FROM group_data_cache WHERE expires_at IS NOT NULL AND expires_at < NOW()$$);
-- Hoặc cron shell: psql -c "DELETE FROM group_data_cache WHERE expires_at IS NOT NULL AND expires_at < NOW();"
```

### API Endpoints mới

```
POST /api/groups/{id}/sync
  Body: {
    data_type: "customers",
    data: [...],
    agents_fetched: [...],
    agents_errors: [...],
    base_version: 5          ← optimistic lock: version hiện tại client đang giữ
  }
  → Server kiểm tra: current_version == base_version?
    → Nếu khớp: lưu cache, tăng version atomically → Return: {ok, version: 6}
    → Nếu KHÔNG khớp (concurrent update): Return 409 {ok: false, 
        current_version: 7, synced_at: "...", message: "Version conflict"}
    → Client nhận 409 → refetch cache mới → retry nếu cần
  
  Server SQL (atomic compare-and-set):
    UPDATE group_data_cache
    SET data_json = %s, version = version + 1, synced_at = NOW(), ...
    WHERE group_id = %s AND data_type = %s AND version = %s  ← check base_version
    RETURNING version;
    -- Nếu affected_rows = 0 → 409 conflict

GET  /api/groups/{id}/cache?data_type=customers
  → Return: {ok, data, total_count, version, synced_at, agents_fetched, agents_errors}

GET  /api/groups/{id}/cache/version?data_type=customers  
  → Return: {version, synced_at}  (nhẹ, dùng cho polling)
```

### Client Flow chi tiết

```python
# Trong UpstreamTab (mode nhóm):

def _load_group_data(self):
    """Load data nhóm — ưu tiên cache, fallback fetch."""
    group_id = self._current_group_id
    
    # 1. Thử đọc cache server trước
    run_in_thread(
        lambda: api.get(f"/api/groups/{group_id}/cache?data_type={self._data_type}"),
        on_result=self._on_cache_result,
        on_error=self._on_cache_miss,
    )

def _on_cache_result(self, result):
    ok, data = result
    if ok and data.get("ok"):
        synced_at = data.get("synced_at")
        # Cache quá 5 phút → re-fetch
        if self._is_cache_stale(synced_at, max_age_seconds=300):
            self._fetch_and_sync()
        else:
            # Cache còn mới → hiển thị ngay
            self._render_group_data(data)
            self._cache_version = data.get("version", 0)
    else:
        self._fetch_and_sync()

def _fetch_and_sync(self):
    """Fetch trực tiếp từ tất cả agents → push lên server."""
    group_id = self._current_group_id
    
    # Lấy danh sách agents + cookies trong nhóm
    agents = self._get_group_agents()  # từ QSettings cache
    
    # Fetch song song (tái sử dụng UpstreamClient._post)
    run_in_thread(
        lambda: self._parallel_fetch(agents),
        on_result=self._on_parallel_done,
    )

FETCH_TIMEOUT = 30       # seconds per agent call
MAX_RETRIES = 3          # retry count per agent
RETRY_BACKOFF = [1, 2, 3]  # seconds between retries

def _fetch_one_agent(self, ag, cookie, base_url, path, params, max_retries=MAX_RETRIES):
    """Fetch 1 agent với retry + timeout. Raise nếu tất cả retry thất bại."""
    import time as _time
    from requests.exceptions import RequestException, Timeout
    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            result = upstream._post(cookie, base_url, path, params)
            return result
        except (RequestException, Timeout, ConnectionError, OSError) as e:
            last_exc = e
            if attempt < max_retries:
                _time.sleep(RETRY_BACKOFF[attempt - 1])
    raise last_exc

def _parallel_fetch(self, agents):
    """Fetch song song từ tất cả agents — chạy trong worker thread.
    Có retry (MAX_RETRIES lần, exponential backoff) và timeout per call."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from requests.exceptions import RequestException, Timeout
    
    all_data = []
    agents_fetched = []
    agents_errors = []
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {}
        for ag in agents:
            cookie_info = upstream.get_cookie(ag["id"])
            if not cookie_info:
                agents_errors.append({"id": ag["id"], "name": ag["name"], 
                                      "error": "no_session"})
                continue
            cookie, base_url = cookie_info
            futures[executor.submit(
                self._fetch_one_agent, ag, cookie, base_url,
                self._upstream_path, self._build_params()
            )] = ag
        
        for future in as_completed(futures):
            ag = futures[future]
            try:
                result = future.result(timeout=FETCH_TIMEOUT)
                rows = result.get("data", [])
                for row in rows:
                    row["_agent_id"] = ag["id"]
                    row["_agent_name"] = ag["name"]
                all_data.extend(rows)
                agents_fetched.append({
                    "id": ag["id"], "name": ag["name"], 
                    "row_count": len(rows)
                })
            except (RequestException, Timeout, ConnectionError, OSError) as e:
                agents_errors.append({
                    "id": ag["id"], "name": ag["name"],
                    "error": str(e), "reason": "network_error",
                    "retries": MAX_RETRIES,
                })
            except TimeoutError:
                agents_errors.append({
                    "id": ag["id"], "name": ag["name"],
                    "error": f"Timed out after {FETCH_TIMEOUT}s",
                    "reason": "timeout",
                })
            except Exception as e:
                agents_errors.append({
                    "id": ag["id"], "name": ag["name"],
                    "error": str(e), "reason": "unknown",
                })
    
    return {
        "data": all_data,
        "agents_fetched": agents_fetched,
        "agents_errors": agents_errors,
    }

def _on_parallel_done(self, result):
    # 1. Hiển thị ngay cho user (không đợi server)
    self._render_group_data(result)
    
    # 2. Push lên server (background, không block UI)
    run_in_thread(
        lambda: api.post(f"/api/groups/{self._current_group_id}/sync", {
            "data_type": self._data_type,
            "data": result["data"],
            "agents_fetched": result["agents_fetched"],
            "agents_errors": result["agents_errors"],
        }),
        on_result=lambda r: self._update_cache_version(r),
    )

# 3. Polling timer — check version mỗi 30s
def _start_polling(self):
    self._poll_timer = QTimer(self)
    self._poll_timer.setInterval(30_000)  # 30s
    self._poll_timer.timeout.connect(self._check_version)
    self._poll_timer.start()

def _check_version(self):
    """Lightweight poll — chỉ check version number."""
    run_in_thread(
        lambda: api.get(
            f"/api/groups/{self._current_group_id}/cache/version"
            f"?data_type={self._data_type}"
        ),
        on_result=self._on_version_check,
    )

def _on_version_check(self, result):
    ok, data = result
    if ok and data.get("version", 0) > self._cache_version:
        # Có member khác đã sync data mới → load cache
        self._load_group_data()
```

### Sequence Diagram

```
Member A mở tab nhóm (lần đầu, chưa có cache):
═══════════════════════════════════════════════
A                    Server              Upstream EE88
│                      │                      │
│─GET /cache──────────>│                      │
│<─404 no cache────────│                      │
│                      │                      │
│─────────────────fetch agents[1,2,3]────────>│
│<────────────────data from 3 agents──────────│
│                      │                      │
│ HIỂN THỊ NGAY        │                      │
│                      │                      │
│─POST /sync(data)────>│                      │
│                      │─lưu cache, version=1─│
│<─{ok, version=1}─────│                      │


Member B mở tab nhóm (có cache):
═══════════════════════════════════════════════
B                    Server              
│                      │                 
│─GET /cache──────────>│                 
│<─{data, version=1}───│  ← NHANH! 1 request
│                      │                 
│ HIỂN THỊ NGAY        │                 


Member A refresh (fetch mới + sync):
═══════════════════════════════════════════════
A                    Server              Upstream
│─────────────────fetch agents[1,2,3]────────>│
│<────────────────data mới───────────────────│
│ HIỂN THỊ NGAY        │                      │
│─POST /sync(data)────>│                      │
│                      │─version=2─────────── │
│<─{ok, version=2}─────│                      │

B đang polling:
B                    Server
│─GET /cache/version──>│
│<─{version=2}─────────│  ← version thay đổi!
│─GET /cache──────────>│
│<─{data mới}──────────│
│ CẬP NHẬT HIỂN THỊ    │
```

---

## SCHEMA CUỐI CÙNG (CẬP NHẬT)

Vì mỗi đại lý chỉ thuộc 1 nhóm → **BỎ bảng group_members**, 
thêm trực tiếp vào bảng agents:

```sql
-- Mở rộng bảng agents
ALTER TABLE agents ADD COLUMN IF NOT EXISTS agent_key VARCHAR(12) UNIQUE;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS key_generated_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE agents ADD COLUMN IF NOT EXISTS group_id BIGINT REFERENCES groups(id) ON DELETE SET NULL;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS group_joined_at TIMESTAMPTZ;

-- Phân quyền trong nhóm (gắn trực tiếp vào agent)
ALTER TABLE agents ADD COLUMN IF NOT EXISTS grp_can_view_data BOOLEAN DEFAULT TRUE;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS grp_can_view_reports BOOLEAN DEFAULT TRUE;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS grp_can_edit_data BOOLEAN DEFAULT FALSE;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS grp_can_manage BOOLEAN DEFAULT FALSE;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS grp_can_tools BOOLEAN DEFAULT TRUE;

-- Bảng groups (giữ nguyên)
CREATE TABLE IF NOT EXISTS groups (
    id              BIGSERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    description     VARCHAR(500) DEFAULT '',
    owner_id        BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    max_members     INT DEFAULT 50,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

-- Cache (mới)
CREATE TABLE IF NOT EXISTS group_data_cache (
    id              BIGSERIAL PRIMARY KEY,
    group_id        BIGINT NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    data_type       VARCHAR(50) NOT NULL,
    data_json       JSONB NOT NULL DEFAULT '[]',
    total_count     INT DEFAULT 0,
    agents_fetched  JSONB DEFAULT '[]',
    agents_errors   JSONB DEFAULT '[]',
    version         BIGINT DEFAULT 1,
    synced_by       BIGINT REFERENCES users(id),
    synced_at       TIMESTAMPTZ DEFAULT NOW(),
    expires_at      TIMESTAMPTZ,
    UNIQUE(group_id, data_type),
    CONSTRAINT chk_data_json_size CHECK (pg_column_size(data_json) <= 5242880),
    CONSTRAINT chk_data_json_length CHECK (
        jsonb_typeof(data_json) = 'array' AND jsonb_array_length(data_json) <= 10000
    )
);

-- Audit log (giữ nguyên)
CREATE TABLE IF NOT EXISTS group_audit_log (
    id              BIGSERIAL PRIMARY KEY,
    group_id        BIGINT NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    user_id         BIGINT NOT NULL REFERENCES users(id),
    action          VARCHAR(50) NOT NULL,
    target_agent_id BIGINT REFERENCES agents(id),
    details         JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### So sánh schema cũ vs mới:

```
CŨ (tài liệu trước):                    MỚI (đơn giản hơn):
agents ──┐                                agents ──── group_id ──> groups
         │                                  │
group_members ──> groups                    │ (bỏ group_members)
  agent_id                                  │
  group_id                                  └── grp_can_view_data
  can_view_data                                 grp_can_view_reports
  can_view_reports                              grp_can_edit_data
  ...                                           grp_can_manage
                                                grp_can_tools
```

**Lợi ích:** Bỏ 1 bảng, bớt JOIN, query nhanh hơn, logic đơn giản hơn.

---

## FLOW DATA NHÓM QUA SERVER PROXY (AN TOÀN)

> **⛔ KHÔNG BAO GIỜ chia sẻ session cookies với client.**
> Cookies/tokens upstream chỉ được lưu và sử dụng trên server.
> Client authenticate bằng credentials riêng, server proxy mọi upstream request.

Đây là phần mấu chốt — khi admin thêm agent vào nhóm,
server giữ cookies và proxy data cho members:

```
ADMIN thêm agent (key=ABC...) vào nhóm
  → Server: UPDATE agents SET group_id = X WHERE agent_key = 'ABC...'
  → Server: trả về OK

MEMBER mở tab nhóm
  → Client: GET /api/groups/{id}/agents  
  → Server trả: [{id, name, ext_username, status}, ...]
     ↑ KHÔNG TRẢ COOKIE — chỉ metadata
  → Client muốn data: GET /api/groups/{id}/data?data_type=customers
  → Server dùng stored cookies fetch upstream (server-side)
  → Server merge + ghi audit log → trả kết quả cho client
```

### API Endpoint — Danh sách agents (KHÔNG có cookie):

```python
@router.get("/{group_id}/agents")
def get_group_agents_with_cookies(
    group_id: int,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Lấy danh sách agents trong nhóm (metadata only, KHÔNG trả cookie)."""
    cur = db.cursor()
    
    # Verify access
    group = _verify_group_access(cur, group_id, user["id"])
    
    cur.execute(
        """SELECT id, name, ext_username, base_url, 
                  status, user_id
           FROM agents 
           WHERE group_id = %s AND is_active = TRUE
           ORDER BY name""",
        (group_id,),
    )
    agents = cur.fetchall()
    
    # Ghi audit log
    _log_access(cur, group_id, user["id"], "list_agents")
    
    return {
        "ok": True,
        "agents": [
            {
                "id": a["id"],
                "name": a["name"],
                "ext_username": a["ext_username"],
                # ⛔ KHÔNG trả session_cookie
                "base_url": a.get("base_url") or UPSTREAM_BASE_URL,
                "status": a["status"],
                "is_mine": a["user_id"] == user["id"],
            }
            for a in agents
        ],
    }


@router.get("/{group_id}/data")
def fetch_from_upstream(
    group_id: int,
    data_type: str,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Server-side proxy: fetch data từ upstream cho nhóm.
    Server dùng stored cookies, client KHÔNG cần biết cookie."""
    cur = db.cursor()
    group = _verify_group_access(cur, group_id, user["id"])
    
    # Lấy agents + cookies (server-side only)
    cur.execute(
        """SELECT id, name, ext_username, session_cookie, base_url
           FROM agents
           WHERE group_id = %s AND is_active = TRUE AND session_cookie IS NOT NULL""",
        (group_id,),
    )
    agents = cur.fetchall()
    
    # Fetch upstream song song (server-side)
    result = _get_group_data(agents, data_type)
    
    # Ghi audit log
    _log_access(cur, group_id, user["id"], "fetch_data", 
                details={"data_type": data_type, "agent_count": len(agents)})
    
    # Trả kết quả KHÔNG chứa cookies
    return {"ok": True, **result}


def _get_group_data(agents: list[dict], data_type: str) -> dict:
    """Server-side: dùng stored cookies fetch upstream, merge kết quả."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    all_data, agents_fetched, agents_errors = [], [], []
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {}
        for ag in agents:
            futures[executor.submit(
                upstream._post, ag["session_cookie"], 
                ag.get("base_url") or UPSTREAM_BASE_URL,
                _data_type_to_path(data_type), ""
            )] = ag
        for future in as_completed(futures):
            ag = futures[future]
            try:
                result = future.result(timeout=30)
                rows = result.get("data", [])
                for row in rows:
                    row["_agent_id"] = ag["id"]
                    row["_agent_name"] = ag["name"]
                all_data.extend(rows)
                agents_fetched.append({"id": ag["id"], "name": ag["name"], "row_count": len(rows)})
            except Exception as e:
                agents_errors.append({"id": ag["id"], "name": ag["name"], "error": str(e)})
    
    return {"data": all_data, "agents_fetched": agents_fetched, "agents_errors": agents_errors,
            "total_count": len(all_data)}


def _log_access(cur, group_id: int, user_id: int, action: str, details: dict = None):
    """Ghi audit log cho group access."""
    cur.execute(
        """INSERT INTO group_audit_log (group_id, user_id, action, details)
           VALUES (%s, %s, %s, %s)""",
        (group_id, user_id, action, json.dumps(details or {})),
    )
```

---

## TÓM TẮT QUYẾT ĐỊNH CUỐI CÙNG

| Quyết định | Chọn |
|------------|------|
| Fetch data | Server proxy (an toàn) hoặc client fetch agent riêng (nhanh) |
| Sync giữa members | Server cache + polling 30s |
| Đại lý/nhóm | 1 đại lý = 1 nhóm (thêm group_id vào agents) |
| Cookie sharing | **⛔ KHÔNG chia sẻ** — cookies chỉ ở server, proxy qua API |
| Bảng group_members | **BỎ** — gắn trực tiếp vào agents |
| Realtime | Polling (đủ tốt, không cần WebSocket) |
