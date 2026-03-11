#pragma once

#include <QWidget>
#include <QString>
#include <functional>

class ThemeManager;
class ToastWidget;

/**
 * Feedback utility — wrap ToastWidget + ConfirmDialog theo quy tắc Layer.md.
 * Dùng chung cho toàn app, tránh config rải rác.
 *
 * Timing theo Layer.md:
 *   Success toast: 3s tự biến mất
 *   Error toast:   4s tự biến mất
 *   Warning toast: 5s tự biến mất
 *   Info toast:    3s tự biến mất
 *   Loading:       không tự biến mất, đóng thủ công
 */
class Feedback {
public:
    /// Khởi tạo với parent widget và theme manager
    explicit Feedback(QWidget* parent, ThemeManager* theme = nullptr);

    // ── Toast messages ──────────────────────────────────────────────

    /// Success toast — 3s (Layer.md: 3-4 giây)
    void msg_success(const QString& text, int duration_ms = 3000);

    /// Error toast — 4s (Layer.md: 4-5 giây)
    void msg_error(const QString& text, int duration_ms = 4000);

    /// Warning toast — 5s (Layer.md: 5-7 giây)
    void msg_warn(const QString& text, int duration_ms = 5000);

    /// Info toast — 3s
    void msg_info(const QString& text, int duration_ms = 3000);

    // ── Loading ─────────────────────────────────────────────────────

    /// Hiện loading spinner, trả về pointer để close sau
    ToastWidget* show_loading(const QString& text = "");

    /// Đóng loading
    static void close_loading(ToastWidget* loading);

    // ── Confirm dialog ──────────────────────────────────────────────

    /// Confirm dialog — trả true nếu user xác nhận
    bool confirm(const QString& message,
                 const QString& yes_text = QString(),
                 const QString& no_text = QString());

    // ── Wrap async pattern ──────────────────────────────────────────

    /**
     * Chạy async callback với loading + feedback tự động.
     * @param fn         Callback thực hiện thao tác (nhận loading widget)
     * @param success_msg  Thông báo khi thành công (rỗng = không hiện)
     * @param error_msg    Thông báo khi thất bại (rỗng = không hiện)
     *
     * Ví dụ:
     *   m_feedback->run([this](auto*) {
     *       m_api->delete_agent(id);
     *   }, "Đã xoá đại lý", "Xoá thất bại");
     */
    void run(std::function<void(ToastWidget*)> fn,
             const QString& success_msg = QString(),
             const QString& error_msg = QString());

    /**
     * Confirm trước rồi chạy với loading + feedback.
     * @return true nếu user xác nhận VÀ thao tác thành công
     */
    bool confirm_run(const QString& confirm_msg,
                     std::function<void(ToastWidget*)> fn,
                     const QString& success_msg = QString(),
                     const QString& error_msg = QString(),
                     const QString& yes_text = QString(),
                     const QString& no_text = QString());

    /// Đổi parent widget (khi chuyển window)
    void set_parent(QWidget* parent) { m_parent = parent; }

    /// Đổi theme manager
    void set_theme(ThemeManager* theme) { m_theme = theme; }

private:
    QWidget* m_parent;
    ThemeManager* m_theme;
};
