#include "utils/feedback.h"
#include "core/toast_widget.h"
#include "core/confirm_dialog.h"
#include <stdexcept>

Feedback::Feedback(QWidget* parent, ThemeManager* theme)
    : m_parent(parent)
    , m_theme(theme)
{
}

// ── Toast messages ──────────────────────────────────────────────────────────

void Feedback::msg_success(const QString& text, int duration_ms)
{
    ToastWidget::show_toast(m_parent, text, ToastWidget::Success, duration_ms);
}

void Feedback::msg_error(const QString& text, int duration_ms)
{
    ToastWidget::show_toast(m_parent, text, ToastWidget::Error, duration_ms);
}

void Feedback::msg_warn(const QString& text, int duration_ms)
{
    ToastWidget::show_toast(m_parent, text, ToastWidget::Warning, duration_ms);
}

void Feedback::msg_info(const QString& text, int duration_ms)
{
    ToastWidget::show_toast(m_parent, text, ToastWidget::Info, duration_ms);
}

// ── Loading ─────────────────────────────────────────────────────────────────

ToastWidget* Feedback::show_loading(const QString& text)
{
    const QString msg = text.isEmpty() ? QStringLiteral("Đang xử lý...") : text;
    return ToastWidget::show_toast(m_parent, msg, ToastWidget::Loading, 0);
}

void Feedback::close_loading(ToastWidget* loading)
{
    if (loading) {
        loading->close_toast();
    }
}

// ── Confirm dialog ──────────────────────────────────────────────────────────

bool Feedback::confirm(const QString& message,
                       const QString& yes_text,
                       const QString& no_text)
{
    return ConfirmDialog::ask(m_parent, m_theme, message, yes_text, no_text);
}

// ── Wrap async pattern ──────────────────────────────────────────────────────

void Feedback::run(std::function<void(ToastWidget*)> fn,
                   const QString& success_msg,
                   const QString& error_msg)
{
    auto* loading = show_loading();
    try {
        fn(loading);
        close_loading(loading);
        if (!success_msg.isEmpty()) {
            msg_success(success_msg);
        }
    } catch (const std::exception& e) {
        close_loading(loading);
        const QString msg = error_msg.isEmpty()
            ? QString::fromUtf8(e.what())
            : error_msg;
        msg_error(msg);
    } catch (...) {
        close_loading(loading);
        msg_error(error_msg.isEmpty()
            ? QStringLiteral("Thao tác thất bại")
            : error_msg);
    }
}

bool Feedback::confirm_run(const QString& confirm_msg,
                           std::function<void(ToastWidget*)> fn,
                           const QString& success_msg,
                           const QString& error_msg,
                           const QString& yes_text,
                           const QString& no_text)
{
    if (!confirm(confirm_msg, yes_text, no_text)) {
        return false;
    }

    auto* loading = show_loading();
    try {
        fn(loading);
        close_loading(loading);
        if (!success_msg.isEmpty()) {
            msg_success(success_msg);
        }
        return true;
    } catch (const std::exception& e) {
        close_loading(loading);
        const QString msg = error_msg.isEmpty()
            ? QString::fromUtf8(e.what())
            : error_msg;
        msg_error(msg);
        return false;
    } catch (...) {
        close_loading(loading);
        msg_error(error_msg.isEmpty()
            ? QStringLiteral("Thao tác thất bại")
            : error_msg);
        return false;
    }
}
