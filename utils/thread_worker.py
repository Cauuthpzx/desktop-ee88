"""
utils/thread_worker.py
Chạy task nặng (gọi API, đọc file lớn, xử lý DB...) trong thread riêng
để UI không bị đơ.

Dùng cơ bản:
    from utils.thread_worker import Worker

    def do_heavy_task():
        import time; time.sleep(2)
        return {"status": "done", "count": 100}

    worker = Worker(do_heavy_task)
    worker.signals.result.connect(self._on_done)
    worker.signals.error.connect(self._on_error)
    worker.signals.finished.connect(self._on_finished)
    worker.start()

Dùng với progress:
    def do_task(progress_callback):
        for i in range(100):
            progress_callback(i)
        return "done"

    worker = Worker(do_task, use_progress=True)
    worker.signals.progress.connect(self._progress_bar.setValue)
    worker.start()

Dùng với loading overlay:
    self._loading = LoadingOverlay(self)
    worker = Worker(fetch_data)
    worker.signals.result.connect(self._load_table)
    worker.signals.finished.connect(self._loading.stop)
    worker.signals.error.connect(lambda e: error(self, str(e)))
    self._loading.start("Đang tải...")
    worker.start()
"""
import traceback
from PyQt6.QtCore import QRunnable, QThreadPool, QObject, pyqtSignal, pyqtSlot


class WorkerSignals(QObject):
    started  = pyqtSignal()           # khi bắt đầu chạy
    result   = pyqtSignal(object)     # khi hoàn thành, kèm kết quả
    error    = pyqtSignal(str)        # khi có exception, kèm message
    progress = pyqtSignal(int)        # 0–100, nếu dùng use_progress=True
    finished = pyqtSignal()           # luôn emit sau khi xong (dù lỗi hay không)


class Worker(QRunnable):
    """
    Chạy hàm trong QThreadPool.
    fn: callable — hàm cần chạy
    *args, **kwargs: tham số truyền vào fn

    Nếu use_progress=True: fn nhận thêm tham số progress_callback(int)
    """
    def __init__(self, fn, *args, use_progress: bool = False, **kwargs):
        super().__init__()
        self.fn           = fn
        self.args         = args
        self.kwargs       = kwargs
        self.use_progress = use_progress
        self.signals      = WorkerSignals()
        self.setAutoDelete(True)

    @pyqtSlot()
    def run(self):
        self.signals.started.emit()
        try:
            if self.use_progress:
                result = self.fn(
                    *self.args,
                    progress_callback=self.signals.progress.emit,
                    **self.kwargs
                )
            else:
                result = self.fn(*self.args, **self.kwargs)
            self.signals.result.emit(result)
        except Exception as e:
            self.signals.error.emit(f"{type(e).__name__}: {e}\n{traceback.format_exc()}")
        finally:
            self.signals.finished.emit()

    def start(self):
        """Shortcut: tự submit vào global thread pool."""
        QThreadPool.globalInstance().start(self)


# ── Convenience function ──────────────────────────────────

def run_in_thread(fn, *args,
                  on_result=None,
                  on_error=None,
                  on_finished=None,
                  on_progress=None,
                  use_progress: bool = False,
                  **kwargs) -> Worker:
    """
    Shortcut tạo và chạy Worker trong 1 dòng.

    Dùng:
        run_in_thread(
            fetch_data, user_id,
            on_result=self._load_table,
            on_error=lambda e: error(self, e),
            on_finished=self._loading.stop,
        )
    """
    worker = Worker(fn, *args, use_progress=use_progress, **kwargs)
    if on_result:   worker.signals.result.connect(on_result)
    if on_error:    worker.signals.error.connect(on_error)
    if on_finished: worker.signals.finished.connect(on_finished)
    if on_progress: worker.signals.progress.connect(on_progress)
    worker.start()
    return worker
