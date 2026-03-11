import { layer } from "@layui/layui-vue";
import { useAppStore } from "../store/app";

// ============================================================================
// Feedback utility — wrap layer API theo quy tắc Layer.md
// Dùng chung cho toàn app, tránh config rải rác.
// ============================================================================

/** Shade style theo theme: đen 70% (light) / trắng 30% (dark) */
function getShadeStyle(): Record<string, string> {
  try {
    const appStore = useAppStore();
    if (appStore.theme === "dark") {
      return { backgroundColor: "rgba(255, 255, 255, 0.3)" };
    }
  } catch {
    // store chưa sẵn sàng
  }
  return { backgroundColor: "rgba(0, 0, 0, 0.7)" };
}

// ── Toast messages ──────────────────────────────────────────────────────────

/** Success toast — 3s tự biến mất (Layer.md: 3-4 giây) */
export function msgSuccess(text: string, time = 3000) {
  return layer.msg(text, { icon: 1, time });
}

/** Error toast — 4s tự biến mất (Layer.md: 4-5 giây) */
export function msgError(text: string, time = 4000) {
  return layer.msg(text, { icon: 2, time });
}

/** Info toast — 3s */
export function msgInfo(text: string, time = 3000) {
  return layer.msg(text, { icon: 0, time });
}

/** Warning toast — 5s (Layer.md: 5-7 giây) */
export function msgWarn(text: string, time = 5000) {
  return layer.msg(text, { icon: 7, time });
}

// ── Loading ─────────────────────────────────────────────────────────────────

/** Hiện loading spinner, trả về ID để close sau */
export function showLoading() {
  return layer.load(0, {
    shadeStyle: getShadeStyle(),
    shadeOpacity: "1",
  });
}

/** Đóng loading */
export function closeLoading(id: string | number) {
  layer.close(id as any);
}

// ── Confirm dialog ──────────────────────────────────────────────────────────

interface ConfirmOptions {
  yesText?: string;
  noText?: string;
}

/** Confirm dialog — trả Promise<boolean> */
export function confirm(
  message: string,
  opts: ConfirmOptions = {}
): Promise<boolean> {
  const { yesText = "Xác nhận", noText = "Huỷ" } = opts;
  return new Promise((resolve) => {
    layer.confirm(message, {
      shadeStyle: getShadeStyle(),
      shadeOpacity: "1",
      btn: [
        {
          text: yesText,
          callback: (id: any) => {
            layer.close(id);
            resolve(true);
          },
        },
        {
          text: noText,
          callback: (id: any) => {
            layer.close(id);
            resolve(false);
          },
        },
      ],
    });
  });
}

// ── Wrap async operation (loading + success/error) ──────────────────────────

interface RunOptions {
  loadingText?: string;
  successMsg?: string;
  errorMsg?: string | ((err: any) => string);
}

/**
 * Wrap một async operation với loading + feedback tự động.
 *
 * @example
 * const result = await feedback.run(
 *   () => api.post("/api/agents", data),
 *   { successMsg: "Thêm thành công", errorMsg: "Thêm thất bại" }
 * );
 */
export async function run<T>(
  fn: () => Promise<T>,
  opts: RunOptions = {}
): Promise<T | null> {
  const loading = showLoading();
  try {
    const result = await fn();
    if (opts.successMsg) {
      msgSuccess(opts.successMsg);
    }
    return result;
  } catch (err: any) {
    const msg =
      typeof opts.errorMsg === "function"
        ? opts.errorMsg(err)
        : opts.errorMsg ||
          err.response?.data?.message ||
          err.response?.data?.error ||
          "Thao tác thất bại";
    msgError(msg);
    return null;
  } finally {
    closeLoading(loading);
  }
}

// ── Confirm rồi chạy (delete, logout, ...) ─────────────────────────────────

interface ConfirmRunOptions extends RunOptions {
  confirmMsg: string;
  yesText?: string;
  noText?: string;
}

/**
 * Confirm trước, nếu OK thì chạy async operation với loading + feedback.
 *
 * @example
 * await feedback.confirmRun({
 *   confirmMsg: 'Xác nhận xoá đại lý "ABC"?',
 *   yesText: "Xoá",
 *   successMsg: "Đã xoá",
 * }, () => api.delete(`/api/agents/${id}?mode=destroy`));
 */
export async function confirmRun<T>(
  opts: ConfirmRunOptions,
  fn: () => Promise<T>
): Promise<T | null> {
  const confirmed = await confirm(opts.confirmMsg, {
    yesText: opts.yesText,
    noText: opts.noText,
  });
  if (!confirmed) return null;
  return run(fn, opts);
}

/** Shade style getter — dùng cho declarative lay-layer components */
export { getShadeStyle };

const feedback = {
  msgSuccess,
  msgError,
  msgInfo,
  msgWarn,
  showLoading,
  closeLoading,
  confirm,
  run,
  confirmRun,
  getShadeStyle,
};

export default feedback;
