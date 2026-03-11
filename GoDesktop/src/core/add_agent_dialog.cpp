#include "core/add_agent_dialog.h"
#include "core/theme_manager.h"
#include "core/translator.h"
#include "core/icon_defs.h"

#include <QVBoxLayout>
#include <QHBoxLayout>

AddAgentDialog::AddAgentDialog(ThemeManager* theme, Translator* tr, QWidget* parent)
    : QDialog(parent), m_theme(theme), m_tr(tr)
{
    setWindowFlags(windowFlags() & ~Qt::WindowContextHelpButtonHint);
    setFixedSize(420, 340);

    auto* root = new QVBoxLayout(this);
    root->setContentsMargins(24, 20, 24, 20);
    root->setSpacing(14);

    m_title_label = new QLabel(m_tr->t("settings.add_agent_title"));
    m_title_label->setAlignment(Qt::AlignCenter);
    m_title_label->setStyleSheet("font-size: 15px; font-weight: bold; border: none;");
    root->addWidget(m_title_label);

    auto make_row = [&](QLabel*& lbl, QLineEdit*& edit, const QString& label_text,
                        const QString& placeholder, QLineEdit::EchoMode echo = QLineEdit::Normal) {
        auto* row = new QHBoxLayout;
        row->setSpacing(10);
        lbl = new QLabel(label_text);
        lbl->setFixedWidth(100);
        lbl->setAlignment(Qt::AlignRight | Qt::AlignVCenter);
        lbl->setStyleSheet("font-size: 13px; border: none;");
        edit = new QLineEdit;
        edit->setPlaceholderText(placeholder);
        edit->setFixedHeight(IconDefs::k_input_height);
        edit->setEchoMode(echo);
        row->addWidget(lbl);
        row->addWidget(edit);
        root->addLayout(row);
    };

    make_row(m_lbl_name, m_edit_name,
             m_tr->t("settings.display_name_label"), m_tr->t("settings.display_name_placeholder"));
    make_row(m_lbl_username, m_edit_username,
             m_tr->t("settings.account_label"), m_tr->t("settings.account_placeholder"));
    make_row(m_lbl_password, m_edit_password,
             m_tr->t("settings.password_label"), m_tr->t("settings.password_placeholder"),
             QLineEdit::Password);
    make_row(m_lbl_base_url, m_edit_base_url,
             m_tr->t("settings.url_label"), "https://...");

    root->addStretch();

    auto* btn_row = new QHBoxLayout;
    btn_row->setSpacing(10);
    m_btn_cancel = new QPushButton(m_tr->t("settings.cancel"));
    m_btn_cancel->setFixedHeight(IconDefs::k_dialog_btn_height);
    m_btn_cancel->setCursor(Qt::PointingHandCursor);
    m_btn_add = new QPushButton(m_tr->t("settings.add_agent"));
    m_btn_add->setFixedHeight(IconDefs::k_dialog_btn_height);
    m_btn_add->setCursor(Qt::PointingHandCursor);
    btn_row->addWidget(m_btn_cancel);
    btn_row->addWidget(m_btn_add);
    root->addLayout(btn_row);

    connect(m_btn_cancel, &QPushButton::clicked, this, &QDialog::reject);
    connect(m_btn_add, &QPushButton::clicked, this, &QDialog::accept);

    setWindowTitle(m_tr->t("settings.add_agent_title"));
    apply_theme();
}

void AddAgentDialog::apply_theme()
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
        "QLineEdit:focus { border-color: %4; }"
    ).arg(bg, fg, border, primary);

    m_edit_name->setStyleSheet(input_style);
    m_edit_username->setStyleSheet(input_style);
    m_edit_password->setStyleSheet(input_style);
    m_edit_base_url->setStyleSheet(input_style);

    for (auto* lbl : {m_lbl_name, m_lbl_username, m_lbl_password, m_lbl_base_url})
        lbl->setStyleSheet(QString("font-size: 13px; color: %1; border: none;").arg(fg));

    m_btn_cancel->setStyleSheet(QString(
        "QPushButton { background: transparent; color: %1; border: 1px solid %2;"
        "  padding: 0 16px; font-size: 13px; }"
        "QPushButton:hover { background: %3; }"
    ).arg(warm, warm, bg_hover));

    m_btn_add->setStyleSheet(QString(
        "QPushButton { background: %1; color: #fff; border: none;"
        "  padding: 0 16px; font-size: 13px; }"
        "QPushButton:hover { opacity: 0.9; }"
    ).arg(primary));
}

void AddAgentDialog::retranslate()
{
    setWindowTitle(m_tr->t("settings.add_agent_title"));
    m_title_label->setText(m_tr->t("settings.add_agent_title"));
    m_lbl_name->setText(m_tr->t("settings.display_name_label"));
    m_lbl_username->setText(m_tr->t("settings.account_label"));
    m_lbl_password->setText(m_tr->t("settings.password_label"));
    m_lbl_base_url->setText(m_tr->t("settings.url_label"));
    m_edit_name->setPlaceholderText(m_tr->t("settings.display_name_placeholder"));
    m_edit_username->setPlaceholderText(m_tr->t("settings.account_placeholder"));
    m_edit_password->setPlaceholderText(m_tr->t("settings.password_placeholder"));
    m_btn_cancel->setText(m_tr->t("settings.cancel"));
    m_btn_add->setText(m_tr->t("settings.add_agent"));
}

void AddAgentDialog::set_edit_mode(const QString& name, const QString& username, const QString& base_url)
{
    m_title_label->setText(m_tr->t("settings.edit_agent_title"));
    setWindowTitle(m_tr->t("settings.edit_agent_title"));
    m_btn_add->setText(m_tr->t("settings.update"));
    m_edit_name->setText(name);
    m_edit_username->setText(username);
    m_edit_username->setReadOnly(true);
    m_edit_base_url->setText(base_url);
}

QString AddAgentDialog::agent_name() const { return m_edit_name->text(); }
QString AddAgentDialog::agent_username() const { return m_edit_username->text(); }
QString AddAgentDialog::agent_password() const { return m_edit_password->text(); }
QString AddAgentDialog::agent_base_url() const { return m_edit_base_url->text(); }
