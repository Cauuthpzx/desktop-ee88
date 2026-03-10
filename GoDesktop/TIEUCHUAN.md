# CLAUDE.md — BỘ QUY TẮC BẮT BUỘC CHO DỰ ÁN C++

> **200 quy tắc logic — không code — tập trung TỐI ƯU HIỆU NĂNG, SỰ ỔN ĐỊNH và SỰ MẠNH MẼ.**
> Bảo mật không phải ưu tiên hàng đầu. Hiệu năng và độ tin cậy là trên hết.

---

## I. CẤU TRÚC DỰ ÁN CHUẨN (Quy tắc 1–20)

### Cây thư mục bắt buộc

```
project-root/
├── CLAUDE.md                  # File này — quy tắc dự án
├── CMakeLists.txt             # Build system gốc
├── build/                     # Thư mục build (KHÔNG commit)
├── src/                       # Source code chính
│   ├── main.cpp               # Entry point duy nhất
│   ├── core/                  # Logic lõi, engine, thuật toán
│   ├── systems/               # Các hệ thống con (input, render, physics...)
│   ├── utils/                 # Tiện ích dùng chung
│   └── platform/              # Code phụ thuộc nền tảng (win32, linux, posix)
├── include/                   # Public headers
│   └── project_name/          # Namespace thư mục trùng tên dự án
├── libs/                      # Third-party libraries (submodule hoặc vendored)
├── tests/                     # Unit tests & integration tests
│   ├── unit/
│   └── integration/
├── benchmarks/                # Performance benchmarks
├── assets/                    # Dữ liệu, config, resource
├── scripts/                   # Build scripts, CI helpers
├── docs/                      # Tài liệu kỹ thuật
└── tools/                     # Công cụ phát triển nội bộ
```

**1.** Mỗi dự án PHẢI có đúng một `main.cpp` duy nhất trong `src/`. Không phân tán entry point.

**2.** Thư mục `build/` PHẢI nằm trong `.gitignore`. Không bao giờ commit artifact build.

**3.** Header public đặt trong `include/project_name/`. Header private đặt cùng `.cpp` tương ứng trong `src/`.

**4.** Mỗi module (thư mục con trong `src/`) PHẢI có trách nhiệm đơn nhất — không module nào làm hai việc không liên quan.

**5.** File `.cpp` và `.h` đi theo cặp. Nếu có `foo.cpp` thì PHẢI có `foo.h` (trừ `main.cpp`).

**6.** Không tạo file rỗng hoặc file placeholder. Mỗi file phải có nội dung thực.

**7.** Thư mục `libs/` chứa thư viện bên thứ ba — ưu tiên git submodule hơn copy thủ công.

**8.** Thư mục `tests/` phản ánh cấu trúc `src/`. Test cho `src/core/engine.cpp` nằm ở `tests/unit/core/engine_test.cpp`.

**9.** Thư mục `benchmarks/` bắt buộc cho mọi dự án quan tâm hiệu năng. Không benchmark = không tối ưu.

**10.** Tên file dùng `snake_case`. Tên thư mục dùng `snake_case`. Không ngoại lệ.

**11.** Mỗi thư mục con trong `src/` PHẢI có một file `README.md` ngắn mô tả trách nhiệm module (tối đa 5 dòng).

**12.** Không đặt code logic trong thư mục `include/`. Thư mục `include/` chỉ chứa khai báo interface.

**13.** File config dự án (`.json`, `.ini`, `.yaml`) đặt trong `assets/config/`.

**14.** Script build, CI/CD đặt trong `scripts/`. Không rải script ở root.

**15.** Mỗi dự án PHẢI có `CMakeLists.txt` ở root. Mỗi thư mục con có module PHẢI có `CMakeLists.txt` riêng.

**16.** Không tạo thư mục lồng quá 4 cấp tính từ `src/`. Quá sâu = thiết kế sai.

**17.** Thư mục `platform/` cách ly toàn bộ code phụ thuộc OS. Phần còn lại của `src/` PHẢI portable.

**18.** Tách biệt rõ ràng code runtime và code build-time. Không nhúng logic build vào source.

**19.** Mỗi third-party lib trong `libs/` PHẢI có file `THIRDPARTY_LICENSE` đi kèm.

**20.** Cấu trúc dự án phải tự giải thích — đọc cây thư mục phải hiểu được kiến trúc mà không cần đọc code.

---

## II. QUY TẮC NAMING & CONVENTION (Quy tắc 21–40)

**21.** Class, struct dùng `PascalCase`. Ví dụ: `RenderEngine`, `PhysicsWorld`.

**22.** Hàm, method dùng `snake_case`. Ví dụ: `calculate_damage()`, `update_frame()`.

**23.** Biến cục bộ và tham số dùng `snake_case`. Ví dụ: `frame_count`, `delta_time`.

**24.** Biến member của class có prefix `m_`. Ví dụ: `m_position`, `m_velocity`.

**25.** Biến static của class có prefix `s_`. Ví dụ: `s_instance_count`.

**26.** Biến global (hạn chế tối đa) có prefix `g_`. Ví dụ: `g_frame_allocator`.

**27.** Hằng số compile-time dùng `k_` prefix + `PascalCase`. Ví dụ: `k_MaxPlayers`, `k_BufferSize`.

**28.** Enum class bắt buộc. Không dùng enum C-style. Tên enum dùng `PascalCase`, giá trị dùng `PascalCase`.

**29.** Namespace dùng `snake_case`, trùng tên dự án hoặc module. Ví dụ: `namespace game_engine`.

**30.** Macro (hạn chế tối đa) dùng `UPPER_SNAKE_CASE` với prefix dự án. Ví dụ: `GE_ASSERT()`.

**31.** Template parameter dùng `PascalCase` với suffix gợi ý. Ví dụ: `typename AllocatorType`, `size_t BufferSize`.

**32.** Typedef/using alias dùng `PascalCase` với suffix `_t` chỉ cho POD type. Ví dụ: `using Vec3 = ...`.

**33.** File header guard dùng format: `PROJECT_MODULE_FILENAME_H`. Hoặc dùng `#pragma once` nếu compiler hỗ trợ.

**34.** Tên hàm phải là ĐỘNG TỪ mô tả hành động: `compute_hash()`, `destroy_buffer()`. Không đặt tên mơ hồ.

**35.** Tên biến phải là DANH TỪ mô tả dữ liệu: `player_health`, `world_matrix`. Không viết tắt trừ quy ước phổ biến (`idx`, `ptr`, `ctx`).

**36.** Hàm boolean bắt đầu bằng `is_`, `has_`, `can_`, `should_`. Ví dụ: `is_valid()`, `has_children()`.

**37.** Hàm getter không prefix `get_` — dùng trực tiếp tên: `position()` thay vì `get_position()`. Setter dùng `set_position()`.

**38.** Callback và function pointer dùng suffix `_fn` hoặc `_callback`. Ví dụ: `on_collision_fn`.

**39.** Namespace ẩn danh (anonymous namespace) dùng cho internal linkage thay vì `static` ở file scope.

**40.** Không dùng tên biến đơn ký tự trừ vòng lặp (`i`, `j`, `k`) và lambda ngắn (`[](auto& e)`).

---

## III. QUY TẮC QUẢN LÝ BỘ NHỚ (Quy tắc 41–65)

**41.** KHÔNG dùng `new`/`delete` trực tiếp trong code logic. Mọi allocation phải qua allocator hoặc smart pointer.

**42.** `std::unique_ptr` là lựa chọn MẶC ĐỊNH cho ownership đơn. Không dùng raw pointer cho ownership.

**43.** `std::shared_ptr` CHỈ dùng khi ownership thật sự được chia sẻ và có lý do rõ ràng. Ghi comment giải thích tại sao.

**44.** Raw pointer chỉ dùng cho non-owning reference (quan sát, không sở hữu). Đây là quy ước bất di bất dịch.

**45.** Ưu tiên stack allocation hơn heap allocation. Nếu object sống trong scope — đặt trên stack.

**46.** Dùng custom allocator cho hot path. `std::allocator` mặc định quá chậm cho game loop / real-time.

**47.** Pool allocator cho object cùng kích thước được tạo/hủy liên tục (particle, bullet, entity).

**48.** Arena/linear allocator cho dữ liệu sống trong một frame rồi bị xóa sạch (per-frame allocation).

**49.** Không allocate bộ nhớ trong vòng lặp hot path. Pre-allocate và tái sử dụng.

**50.** `std::vector` — luôn `reserve()` nếu biết trước kích thước gần đúng. Tránh reallocation liên tục.

**51.** Dùng `std::vector` làm container mặc định. Chỉ chuyển sang container khác khi có lý do đo lường được.

**52.** `std::array` cho collection kích thước cố định compile-time. Không dùng C-array.

**53.** `std::string_view` cho tham chiếu string chỉ đọc. Không copy string khi không cần thiết.

**54.** Small Buffer Optimization (SBO) — hiểu và tận dụng SBO của `std::string`, `std::function`. Tránh vượt SBO threshold.

**55.** Không dùng `std::list` trừ khi chứng minh được iterator stability quan trọng hơn cache performance.

**56.** `std::deque` ít khi đúng lựa chọn. Ưu tiên `std::vector` + circular buffer logic.

**57.** `std::unordered_map` — cẩn thận với hash collision và rehash. Dùng flat hash map (absl, robin-hood) cho hiệu năng cao.

**58.** Tránh fragmentation: gom các allocation nhỏ thành một allocation lớn rồi chia nhỏ.

**59.** Mọi allocation PHẢI có deallocation tương ứng. Không leak detector = không ship. Dùng ASAN/valgrind trong CI.

**60.** `std::make_unique` và `std::make_shared` — luôn ưu tiên hơn `new` + constructor trực tiếp.

**61.** Move semantics bắt buộc hiểu và áp dụng. Nếu object có resource — implement move constructor và move assignment.

**62.** Tránh `std::shared_ptr` cycle. Nếu cần weak reference — dùng `std::weak_ptr` rõ ràng.

**63.** Placement new chỉ dùng trong custom allocator. Không dùng bừa bãi.

**64.** Memory-mapped file cho dữ liệu lớn chỉ đọc. Không load toàn bộ file vào RAM nếu có thể mmap.

**65.** Mọi class quản lý resource PHẢI tuân theo Rule of Five (hoặc Rule of Zero nếu dùng smart pointer).

---

## IV. QUY TẮC HIỆU NĂNG (Quy tắc 66–100)

**66.** Không tối ưu khi chưa đo. Profile TRƯỚC, tối ưu SAU. Premature optimization là sai, nhưng KHÔNG đo lường cũng là sai.

**67.** Hot path phải được xác định và đánh dấu rõ ràng bằng comment `// HOT PATH`.

**68.** Cache locality là vua. Dữ liệu truy cập cùng nhau PHẢI nằm cạnh nhau trong bộ nhớ (Structure of Arrays > Array of Structures khi cần).

**69.** Tránh cache miss: dữ liệu nên fit trong L1/L2 cache cho hot loop. Đo bằng `perf` hoặc VTune.

**70.** Branch prediction: sắp xếp `if/else` sao cho nhánh phổ biến nhất ở trước. Dùng `[[likely]]`/`[[unlikely]]`.

**71.** Tránh virtual function call trong hot path. Vtable lookup phá cache. Dùng CRTP hoặc type erasure thay thế.

**72.** Inline function nhỏ và gọi thường xuyên. Dùng `[[gnu::always_inline]]` hoặc `__forceinline` cho critical path.

**73.** `constexpr` mọi thứ có thể tính tại compile-time. Không để runtime tính cái compile-time tính được.

**74.** `consteval` cho hàm BẮT BUỘC chạy tại compile-time (C++20+).

**75.** `if constexpr` thay cho `#ifdef` khi có thể. Giữ code trong cùng compilation path.

**76.** Tránh allocation/deallocation trong game loop. Zero-allocation trong hot path là mục tiêu.

**77.** SIMD — dùng intrinsics (SSE/AVX/NEON) cho toán vector/matrix nặng. Không dựa vào auto-vectorization.

**78.** Alignment: struct chứa SIMD data PHẢI align đúng (`alignas(16)`, `alignas(32)`).

**79.** Tránh false sharing trong multi-thread: padding struct để mỗi thread truy cập cache line riêng.

**80.** `std::move` — dùng khi truyền temporary hoặc khi không cần object cũ nữa. Không move rồi dùng lại.

**81.** Return Value Optimization (RVO/NRVO) — để compiler tối ưu. Không `std::move` khi return local variable.

**82.** Pass by const reference cho object > 16 bytes. Pass by value cho scalar và object nhỏ.

**83.** `noexcept` cho hàm không throw — cho phép compiler tối ưu aggressively hơn, đặc biệt move operations.

**84.** Loop unrolling: để compiler tự làm (`#pragma unroll`) hoặc unroll thủ công khi profile cho thấy lợi ích.

**85.** Tránh `std::endl` — dùng `'\n'`. `std::endl` flush buffer, giảm throughput I/O nghiêm trọng.

**86.** I/O buffering: batch I/O operations. Không đọc/ghi file từng byte trong loop.

**87.** String concatenation: dùng `std::string::reserve()` + `append()` hoặc `fmt::format`. Không dùng `+` operator trong loop.

**88.** `std::sort` mặc định tốt. Chỉ thay bằng radix sort / counting sort khi dữ liệu phù hợp và profile xác nhận.

**89.** Lazy evaluation: không tính toán cho đến khi thật sự cần kết quả.

**90.** Precompute: bảng lookup tính trước (sin/cos table, hash table) thay vì tính lại mỗi frame.

**91.** Bit manipulation: dùng bitwise operations cho flags, masks, power-of-two checks. Nhanh hơn arithmetic.

**92.** Fixed-point arithmetic khi float precision không cần thiết và integer performance quan trọng hơn.

**93.** Object pooling cho mọi object tạo/hủy thường xuyên. Constructor/destructor cost tích lũy rất lớn.

**94.** Data-Oriented Design (DOD) ưu tiên hơn Object-Oriented Design (OOD) cho hệ thống performance-critical.

**95.** ECS (Entity-Component-System) pattern cho game/simulation: tách data khỏi logic, tối ưu iteration.

**96.** Compile-time polymorphism (template, CRTP) ưu tiên hơn runtime polymorphism (virtual) cho hot path.

**97.** PGO (Profile-Guided Optimization) — bật trong release build. Cho compiler data thực tế để tối ưu.

**98.** LTO (Link-Time Optimization) — bật trong release build. Cho phép tối ưu cross-translation-unit.

**99.** Tránh exception trong hot path. Exception có zero-cost khi không throw, nhưng throw path rất đắt.

**100.** Benchmark mọi thay đổi hiệu năng với dữ liệu thực tế. Micro-benchmark không đủ — cần integration benchmark.

---

## V. QUY TẮC ỔN ĐỊNH & TIN CẬY (Quy tắc 101–130)

**101.** RAII (Resource Acquisition Is Initialization) là BẮT BUỘC. Mọi resource PHẢI được quản lý qua destructor.

**102.** Không dùng `goto`. Không ngoại lệ. RAII thay thế hoàn toàn mọi use case của `goto`.

**103.** Assert cho invariant: `assert()` trong debug, custom assert macro có logging trong release.

**104.** Mọi switch PHẢI có `default` case, kể cả khi đã cover hết enum values. Dùng `[[fallthrough]]` nếu cố ý fall-through.

**105.** Không dùng C-style cast. Dùng `static_cast`, `dynamic_cast`, `reinterpret_cast`, `const_cast` rõ ràng.

**106.** `const` mọi thứ có thể const. Biến, tham số, method, con trỏ. Const-correctness không phải tùy chọn.

**107.** Tránh undefined behavior (UB) bằng mọi giá. Signed overflow, null dereference, buffer overrun = UB = disaster.

**108.** Initialize mọi biến khi khai báo. Biến chưa khởi tạo = UB tiềm ẩn.

**109.** Không dùng `reinterpret_cast` trừ khi giao tiếp với C API hoặc hardware. Luôn comment giải thích.

**110.** Narrowing conversion bị CẤM. Dùng `static_cast` rõ ràng nếu thật sự cần.

**111.** Integer overflow: dùng unsigned cho bit manipulation, signed cho arithmetic. Kiểm tra overflow cho input từ bên ngoài.

**112.** Floating-point comparison: không dùng `==`. Dùng epsilon comparison với tolerance phù hợp.

**113.** Null check trước mỗi dereference con trỏ từ bên ngoài module. Bên trong module — assert thay vì check.

**114.** Error handling: dùng `std::expected` (C++23), `std::optional`, hoặc error code. Exception chỉ cho trường hợp thật sự exceptional.

**115.** Destructor KHÔNG BAO GIỜ throw exception. Dùng `noexcept` cho mọi destructor.

**116.** Constructor fail — throw exception hoặc factory function trả `std::optional`. Không để object ở trạng thái nửa vời.

**117.** Tránh static initialization order fiasco: dùng function-local static (Meyers' singleton) hoặc explicit init order.

**118.** Không dùng `std::terminate` hoặc `std::abort` trong production code trừ trường hợp unrecoverable.

**119.** Thread safety: document rõ ràng mỗi class/function là thread-safe hay không. Không giả định.

**120.** `std::mutex` bảo vệ shared state. Lock scope nhỏ nhất có thể. Dùng `std::lock_guard` / `std::scoped_lock`.

**121.** Deadlock prevention: luôn lock mutex theo thứ tự cố định. Dùng `std::scoped_lock` cho multiple mutexes.

**122.** Race condition: mọi access vào shared data PHẢI được bảo vệ. Không có "nó chạy đúng trên máy tôi".

**123.** `std::atomic` cho flag và counter đơn giản. Hiểu memory order trước khi dùng relaxed.

**124.** Lock-free data structure CHỈ khi đã hiểu rõ memory model. Sai = bug không thể reproduce.

**125.** Timeout cho mọi operation chờ đợi (network, I/O, lock). Không chờ vô hạn.

**126.** Graceful shutdown: mọi thread, resource, handle PHẢI được cleanup đúng thứ tự khi thoát.

**127.** Signal handling: chỉ dùng async-signal-safe functions trong signal handler. Set flag, xử lý sau.

**128.** Không dùng `volatile` cho thread synchronization. `volatile` không phải `atomic`.

**129.** Stack overflow prevention: không recursion sâu không kiểm soát. Dùng iterative hoặc giới hạn depth.

**130.** Mọi path code phải reachable và testable. Dead code phải bị xóa, không comment out.

---

## VI. QUY TẮC THIẾT KẾ & KIẾN TRÚC (Quy tắc 131–160)

**131.** Single Responsibility Principle (SRP): mỗi class/module làm MỘT việc. Class > 500 dòng = nghi ngờ thiết kế.

**132.** Dependency Injection: module cấp cao không phụ thuộc module cấp thấp. Cả hai phụ thuộc abstraction.

**133.** Interface segregation: interface nhỏ, tập trung. Không ép client phụ thuộc method không dùng.

**134.** Composition over Inheritance. Kế thừa chỉ khi quan hệ "is-a" thật sự đúng và cần polymorphism.

**135.** Kế thừa tối đa 2 cấp. Hệ thống kế thừa sâu = không thể maintain.

**136.** Diamond inheritance bị CẤM trừ khi dùng virtual inheritance và có lý do kiến trúc rõ ràng.

**137.** Encapsulation: data member LUÔN private. Public interface qua method. Struct chỉ cho POD/data bundle.

**138.** Coupling thấp: module giao tiếp qua interface rõ ràng. Không access internal state của module khác.

**139.** Cohesion cao: mọi thành phần trong module phải liên quan chặt chẽ. Nếu không liên quan — tách ra.

**140.** Forward declaration thay include khi chỉ cần con trỏ/tham chiếu. Giảm compile time.

**141.** Pimpl idiom cho API ổn định — ẩn implementation, giữ ABI stability, giảm recompilation.

**142.** Factory pattern cho object creation phức tạp. Client không cần biết concrete type.

**143.** Observer/Event pattern cho communication giữa module. Tránh direct dependency.

**144.** State machine pattern cho object có lifecycle phức tạp (connection, game state, animation).

**145.** Command pattern cho undo/redo, replay, và deferred execution.

**146.** Flyweight pattern cho dữ liệu chia sẻ giữa nhiều instance (texture, mesh, font).

**147.** Không singleton trừ khi resource thật sự global và unique (hardware interface, logging). Singleton = global state = khó test.

**148.** Type erasure cho polymorphism không cần hierarchy. `std::function`, `std::any`, custom type-erased wrapper.

**149.** Strong typedef: `using PlayerId = uint32_t` không đủ — dùng strong type wrapper ngăn nhầm lẫn tham số.

**150.** API design: hàm nhận tối đa 4 tham số. Nhiều hơn — dùng struct config/options.

**151.** Fail-fast: phát hiện lỗi sớm nhất có thể. Validate input ngay khi nhận, không truyền data sai qua nhiều layer.

**152.** Layer architecture: tầng trên gọi tầng dưới, KHÔNG bao giờ ngược lại. Dùng callback/event nếu cần.

**153.** Module boundary rõ ràng: mỗi module expose header tối thiểu. Internal header không được include từ bên ngoài.

**154.** Versioning API: thay đổi breaking phải bump major version. Backward-compatible thay đổi bump minor.

**155.** Zero-cost abstraction: abstraction KHÔNG được tốn thêm runtime cost. Nếu có cost — document rõ.

**156.** Không premature abstraction. Đợi đến khi pattern lặp lại 3 lần mới abstract. Abstraction sớm gây complexity vô ích.

**157.** Plugin architecture dùng interface + dynamic loading khi cần extensibility. Không hardcode mọi thứ.

**158.** Configuration qua file, không hardcode. Nhưng config phải có default hợp lý — chạy được không cần config.

**159.** Deterministic behavior: cùng input — cùng output. Random phải seedable. Timestamp phải injectable.

**160.** Error propagation rõ ràng: caller PHẢI xử lý hoặc propagate error. Không nuốt error im lặng.

---

## VII. QUY TẮC BUILD & COMPILE (Quy tắc 161–180)

**161.** CMake là build system bắt buộc. Minimum version: 3.20. Dùng modern CMake target-based approach.

**162.** Compiler warnings = errors: `-Wall -Wextra -Werror` (GCC/Clang) hoặc `/W4 /WX` (MSVC). Không suppress warning.

**163.** Debug build: `-O0 -g -fsanitize=address,undefined`. Bật mọi sanitizer trong development.

**164.** Release build: `-O2` hoặc `-O3 -march=native -flto`. Bật LTO và PGO.

**165.** C++ standard tối thiểu: C++17. Ưu tiên C++20 trở lên cho dự án mới.

**166.** Unity build (jumbo build) cho dự án lớn để giảm compile time. Nhưng giữ khả năng build từng file.

**167.** Precompiled header (PCH) cho header thay đổi ít (STL, third-party). Giảm compile time đáng kể.

**168.** Incremental build PHẢI hoạt động đúng. Thay đổi 1 file không được rebuild toàn bộ.

**169.** Cross-compilation: CMake toolchain file cho mỗi target platform. Không hardcode path.

**170.** CI build trên ít nhất 2 compiler (GCC + Clang, hoặc GCC + MSVC). Mỗi compiler bắt bug khác nhau.

**171.** Static analysis trong CI: `clang-tidy`, `cppcheck`. Chạy tự động mỗi commit.

**172.** Sanitizer chạy trong CI: ASAN, UBSAN, TSAN. Mỗi loại bắt bug khác nhau.

**173.** Compile time PHẢI được giám sát. Nếu tăng — tìm và sửa nguyên nhân (include bloat, template bloat).

**174.** Không dùng `-fpermissive` hoặc disable warning cụ thể trừ third-party code.

**175.** Header include order: (1) corresponding header, (2) project headers, (3) third-party headers, (4) system/STL headers. Mỗi nhóm cách một dòng trống.

**176.** Mỗi header PHẢI self-contained — include nó một mình phải compile thành công.

**177.** Không circular include. Nếu A include B và B include A — thiết kế sai, refactor.

**178.** `#include` chỉ dùng `""` cho project header và `<>` cho system/third-party header.

**179.** Tách biệt rõ build configuration: Debug, Release, RelWithDebInfo, Profile. Mỗi config có flag riêng.

**180.** Reproducible build: cùng source + cùng toolchain = cùng binary. Không phụ thuộc environment biến.

---

## VIII. QUY TẮC TESTING & QUALITY (Quy tắc 181–195)

**181.** Unit test cho mọi function/class non-trivial. Không test = không hoàn thành.

**182.** Test framework: Google Test hoặc Catch2. Chọn một, dùng xuyên suốt dự án.

**183.** Test naming: `TEST(ModuleName, behavior_when_condition)`. Tên test phải mô tả kịch bản.

**184.** Mỗi test PHẢI independent. Không test nào phụ thuộc kết quả test khác.

**185.** Test chạy nhanh: mỗi unit test < 100ms. Tổng test suite < 60 giây.

**186.** Integration test cho interaction giữa modules. Đặt trong `tests/integration/`.

**187.** Performance benchmark cho mọi hot path. Dùng Google Benchmark hoặc Catch2 benchmark.

**188.** Regression test cho mọi bug đã fix. Bug fix không có test = sẽ quay lại.

**189.** Code coverage tối thiểu 80% cho core module. Không chase 100% — tập trung logic phức tạp.

**190.** Fuzz testing cho parser, serializer, input handler. Dùng libFuzzer hoặc AFL.

**191.** Test trên mọi target platform trong CI. "Chạy trên máy tôi" không phải đảm bảo.

**192.** Mock/stub cho dependency bên ngoài (file system, network, time). Test không phụ thuộc môi trường.

**193.** Golden test (snapshot test) cho output ổn định (serialization format, render output).

**194.** Chaos testing: inject lỗi (allocation failure, I/O error) để verify error handling hoạt động.

**195.** Test PHẢI chạy trong CI trước mỗi merge. Không merge code chưa pass test.

---

## IX. PHƯƠNG THỨC LÀM VIỆC (Quy tắc 196–200)

**196.** Workflow bắt buộc cho mỗi thay đổi:
   1. Tạo branch từ `main` — đặt tên `feature/mô-tả` hoặc `fix/mô-tả`
   2. Code + test trên branch
   3. Chạy toàn bộ test suite + static analysis + sanitizer
   4. Benchmark nếu thay đổi hot path
   5. Code review (hoặc self-review có checklist)
   6. Merge vào `main` khi pass tất cả

**197.** Trước khi viết code mới — đọc code liên quan. Hiểu context trước khi sửa. Không đoán.

**198.** Mỗi commit là một thay đổi logic duy nhất. Không trộn refactor với feature. Không trộn fix với cleanup.

**199.** Code review checklist bắt buộc:
   - [ ] Có test không?
   - [ ] Có benchmark nếu liên quan hiệu năng không?
   - [ ] Memory leak possibility?
   - [ ] Thread safety nếu shared state?
   - [ ] Const-correctness?
   - [ ] Naming convention đúng?
   - [ ] Include order đúng?
   - [ ] Không warning mới?
   - [ ] Build trên tất cả platform pass?

**200.** Tài liệu kỹ thuật bắt buộc cho mọi module:
   - **Trách nhiệm** module là gì (1-2 câu)
   - **Interface** module expose những gì
   - **Dependency** module phụ thuộc những gì
   - **Thread safety** guarantee
   - **Performance** characteristics (big-O, allocation behavior)
   - **Known limitations** và trade-offs

---

## X. TÀI LIỆU THAM KHẢO

### Sách bắt buộc đọc
- **"Effective Modern C++"** — Scott Meyers (C++11/14 best practices)
- **"C++ Concurrency in Action"** — Anthony Williams (multi-threading)
- **"Game Engine Architecture"** — Jason Gregory (kiến trúc engine)
- **"Data-Oriented Design"** — Richard Fabian (DOD cho hiệu năng)
- **"The C++ Programming Language"** — Bjarne Stroustrup (reference toàn diện)

### Tài liệu online
- **C++ Core Guidelines** — isocpp.github.io/CppCoreGuidelines (guidelines chính thức)
- **cppreference.com** — Reference chuẩn cho mọi STL feature
- **Godbolt Compiler Explorer** — godbolt.org (xem assembly output)
- **Quick C++ Benchmark** — quick-bench.com (micro-benchmark online)

### Công cụ bắt buộc
- **CMake** (>= 3.20) — Build system
- **clang-tidy** — Static analysis
- **clang-format** — Code formatting (config file bắt buộc trong repo)
- **AddressSanitizer (ASAN)** — Phát hiện memory bug
- **UndefinedBehaviorSanitizer (UBSAN)** — Phát hiện UB
- **ThreadSanitizer (TSAN)** — Phát hiện race condition
- **Valgrind** — Memory profiling (Linux)
- **perf / VTune / Tracy** — Performance profiling
- **Google Test / Catch2** — Test framework
- **Google Benchmark** — Benchmark framework

### Compiler flags reference
| Mục đích | GCC/Clang | MSVC |
|---|---|---|
| All warnings | `-Wall -Wextra -Wpedantic` | `/W4` |
| Warnings as errors | `-Werror` | `/WX` |
| Optimization (release) | `-O2` hoặc `-O3` | `/O2` |
| Debug info | `-g` | `/Zi` |
| ASAN | `-fsanitize=address` | `/fsanitize=address` |
| UBSAN | `-fsanitize=undefined` | N/A (dùng /RTC) |
| LTO | `-flto` | `/GL` + `/LTCG` |
| Native arch | `-march=native` | `/arch:AVX2` |

---

> **Nguyên tắc cốt lõi: MEASURE → UNDERSTAND → OPTIMIZE → VERIFY.**
> Không đo = không tối ưu. Không hiểu = không sửa. Không verify = không ship.