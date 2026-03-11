#pragma once

#include <QDialog>
#include <QLabel>
#include <QPushButton>

class ThemeManager;

/**
 * Confirm dialog — tương đương layer.confirm() bên web.
 * Hiển thị câu hỏi xác nhận với 2 nút Huỷ/Xác nhận.
 */
class ConfirmDialog : public QDialog {
    Q_OBJECT

public:
    /**
     * Hiển thị confirm dialog.
     * @return true nếu user nhấn Xác nhận
     */
    static bool ask(QWidget* parent, ThemeManager* theme,
                    const QString& message,
                    const QString& confirm_text = QString(),
                    const QString& cancel_text = QString());

private:
    explicit ConfirmDialog(QWidget* parent, ThemeManager* theme,
                           const QString& message,
                           const QString& confirm_text,
                           const QString& cancel_text);
};
