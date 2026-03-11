#include "core/cookies_dialog.h"
#include "core/theme_manager.h"
#include "core/translator.h"
#include "core/icon_defs.h"

#include <QVBoxLayout>
#include <QHBoxLayout>

CookiesDialog::CookiesDialog(ThemeManager* theme, Translator* tr, QWidget* parent)
    : QDialog(parent), m_theme(theme), m_tr(tr)
{
    setWindowFlags(windowFlags() & ~Qt::WindowContextHelpButtonHint);
    setFixedSize(500, 320);

    auto* root = new QVBoxLayout(this);
    root->setContentsMargins(24, 20, 24, 20);
    root->setSpacing(14);

    m_title_label = new QLabel(m_tr->t("settings.assign_cookies_title"));
    m_title_label->setAlignment(Qt::AlignCenter);
    m_title_label->setStyleSheet("font-size: 15px; font-weight: bold; border: none;");
    root->addWidget(m_title_label);

    auto* agent_row = new QHBoxLayout;
    agent_row->setSpacing(10);
    m_lbl_agent = new QLabel(m_tr->t("settings.agent_label"));
    m_lbl_agent->setFixedWidth(80);
    m_lbl_agent->setAlignment(Qt::AlignRight | Qt::AlignVCenter);
    m_lbl_agent->setStyleSheet("font-size: 13px; border: none;");
    m_edit_agent = new QLineEdit;
    m_edit_agent->setReadOnly(true);
    m_edit_agent->setFixedHeight(IconDefs::k_input_height);
    agent_row->addWidget(m_lbl_agent);
    agent_row->addWidget(m_edit_agent);
    root->addLayout(agent_row);

    auto* cookies_row = new QHBoxLayout;
    cookies_row->setSpacing(10);
    cookies_row->setAlignment(Qt::AlignTop);
    m_lbl_cookies = new QLabel("COOKIES :");
    m_lbl_cookies->setFixedWidth(80);
    m_lbl_cookies->setAlignment(Qt::AlignRight | Qt::AlignTop);
    m_lbl_cookies->setStyleSheet("font-size: 13px; border: none; padding-top: 6px;");
    m_edit_cookies = new QTextEdit;
    m_edit_cookies->setFixedHeight(120);
    m_edit_cookies->setPlaceholderText(m_tr->t("settings.cookies_placeholder"));
    cookies_row->addWidget(m_lbl_cookies);
    cookies_row->addWidget(m_edit_cookies);
    root->addLayout(cookies_row);

    root->addStretch();

    auto* btn_row = new QHBoxLayout;
    btn_row->setSpacing(10);
    m_btn_cancel = new QPushButton(m_tr->t("settings.cancel"));
    m_btn_cancel->setFixedHeight(IconDefs::k_dialog_btn_height);
    m_btn_cancel->setCursor(Qt::PointingHandCursor);
    m_btn_save = new QPushButton(m_tr->t("settings.save"));
    m_btn_save->setFixedHeight(IconDefs::k_dialog_btn_height);
    m_btn_save->setCursor(Qt::PointingHandCursor);
    btn_row->addWidget(m_btn_cancel);
    btn_row->addWidget(m_btn_save);
    root->addLayout(btn_row);

    connect(m_btn_cancel, &QPushButton::clicked, this, &QDialog::reject);
    connect(m_btn_save, &QPushButton::clicked, this, &QDialog::accept);

    setWindowTitle(m_tr->t("settings.assign_cookies_title"));
    apply_theme();
}

void CookiesDialog::apply_theme()
{
    auto bg = m_theme->color("bg");
    auto fg = m_theme->color("text_primary");
    auto border = m_theme->color("border");
    auto primary = m_theme->color("primary");
    auto warm = m_theme->color("warm");
    auto bg_hover = m_theme->color("bg_hover");

    setStyleSheet(QString("QDialog { background: %1; }").arg(bg));
    m_title_label->setStyleSheet(QString("font-size: 15px; font-weight: bold; color: %1; border: none;").arg(fg));

    auto input_style = QString(
        "QLineEdit { background: %1; color: %2; border: 1px solid %3;"
        "  padding: 4px 8px; font-size: 13px; }"
    ).arg(bg, fg, border);
    m_edit_agent->setStyleSheet(input_style);

    m_edit_cookies->setStyleSheet(QString(
        "QTextEdit { background: %1; color: %2; border: 1px solid %3;"
        "  padding: 4px 8px; font-size: 13px; }"
        "QTextEdit:focus { border-color: %4; }"
    ).arg(bg, fg, border, primary));

    for (auto* lbl : {m_lbl_agent, m_lbl_cookies})
        lbl->setStyleSheet(QString("font-size: 13px; color: %1; border: none;").arg(fg));

    m_btn_cancel->setStyleSheet(QString(
        "QPushButton { background: transparent; color: %1; border: 1px solid %2;"
        "  padding: 0 16px; font-size: 13px; }"
        "QPushButton:hover { background: %3; }"
    ).arg(warm, warm, bg_hover));

    m_btn_save->setStyleSheet(QString(
        "QPushButton { background: %1; color: #fff; border: none;"
        "  padding: 0 16px; font-size: 13px; }"
        "QPushButton:hover { opacity: 0.9; }"
    ).arg(primary));
}

void CookiesDialog::retranslate()
{
    setWindowTitle(m_tr->t("settings.assign_cookies_title"));
    m_title_label->setText(m_tr->t("settings.assign_cookies_title"));
    m_lbl_agent->setText(m_tr->t("settings.agent_label"));
    m_edit_cookies->setPlaceholderText(m_tr->t("settings.cookies_placeholder"));
    m_btn_cancel->setText(m_tr->t("settings.cancel"));
    m_btn_save->setText(m_tr->t("settings.save"));
}

void CookiesDialog::set_agent(const QString& name, const QString& username)
{
    m_edit_agent->setText(name + " (" + username + ")");
}

QString CookiesDialog::cookies_value() const { return m_edit_cookies->toPlainText(); }
