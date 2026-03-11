#include "core/confirm_dialog.h"
#include "core/theme_manager.h"
#include "core/icon_defs.h"

#include <QVBoxLayout>
#include <QHBoxLayout>

ConfirmDialog::ConfirmDialog(QWidget* parent, ThemeManager* theme,
                             const QString& message,
                             const QString& confirm_text,
                             const QString& cancel_text)
    : QDialog(parent)
{
    setWindowFlags(windowFlags() & ~Qt::WindowContextHelpButtonHint);
    setFixedSize(360, 170);

    auto bg = theme->color("bg");
    auto fg = theme->color("text_primary");
    auto border = theme->color("border");
    auto primary = theme->color("primary");
    auto bg_hover = theme->color("bg_hover");

    setStyleSheet(QString("QDialog { background: %1; }").arg(bg));

    auto* root = new QVBoxLayout(this);
    root->setContentsMargins(24, 24, 24, 20);
    root->setSpacing(20);

    // Icon + Message
    auto* msg_row = new QHBoxLayout;
    msg_row->setSpacing(12);

    auto* icon_lbl = new QLabel;
    icon_lbl->setFixedSize(28, 28);
    icon_lbl->setAlignment(Qt::AlignCenter);
    icon_lbl->setStyleSheet(
        "QLabel { background: #ffb800; color: #fff; border-radius: 14px;"
        "  font-size: 16px; font-weight: bold; border: none; }");
    icon_lbl->setText("?");
    msg_row->addWidget(icon_lbl, 0, Qt::AlignTop);

    auto* msg_lbl = new QLabel(message);
    msg_lbl->setWordWrap(true);
    msg_lbl->setStyleSheet(QString(
        "QLabel { color: %1; font-size: 14px; border: none; }").arg(fg));
    msg_row->addWidget(msg_lbl, 1);

    root->addLayout(msg_row);
    root->addStretch();

    // Buttons
    auto* btn_row = new QHBoxLayout;
    btn_row->setSpacing(10);
    btn_row->addStretch();

    auto* btn_cancel = new QPushButton(cancel_text.isEmpty() ? "Huỷ" : cancel_text);
    btn_cancel->setCursor(Qt::PointingHandCursor);
    btn_cancel->setFixedHeight(IconDefs::k_dialog_btn_height);
    btn_cancel->setStyleSheet(QString(
        "QPushButton { background: transparent; color: %1; border: 1px solid %2;"
        "  padding: 0 20px; font-size: 13px; }"
        "QPushButton:hover { background: %3; }"
    ).arg(fg, border, bg_hover));
    btn_row->addWidget(btn_cancel);

    auto* btn_confirm = new QPushButton(confirm_text.isEmpty() ? "Xác nhận" : confirm_text);
    btn_confirm->setCursor(Qt::PointingHandCursor);
    btn_confirm->setFixedHeight(IconDefs::k_dialog_btn_height);
    btn_confirm->setStyleSheet(QString(
        "QPushButton { background: %1; color: #fff; border: none;"
        "  padding: 0 20px; font-size: 13px; }"
        "QPushButton:hover { opacity: 0.9; }"
    ).arg(primary));
    btn_row->addWidget(btn_confirm);

    root->addLayout(btn_row);

    connect(btn_cancel, &QPushButton::clicked, this, &QDialog::reject);
    connect(btn_confirm, &QPushButton::clicked, this, &QDialog::accept);
}

bool ConfirmDialog::ask(QWidget* parent, ThemeManager* theme,
                        const QString& message,
                        const QString& confirm_text,
                        const QString& cancel_text)
{
    ConfirmDialog dlg(parent, theme, message, confirm_text, cancel_text);
    return dlg.exec() == QDialog::Accepted;
}
