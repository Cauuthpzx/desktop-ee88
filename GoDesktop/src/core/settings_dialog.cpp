#include "core/settings_dialog.h"
#include "core/theme_manager.h"
#include "core/translator.h"
#include "core/icon_defs.h"
#include "core/toggle_switch.h"

// ════════════════════════════════════════
// AddAgentDialog
// ════════════════════════════════════════

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

QString AddAgentDialog::agent_name() const { return m_edit_name->text(); }
QString AddAgentDialog::agent_username() const { return m_edit_username->text(); }
QString AddAgentDialog::agent_password() const { return m_edit_password->text(); }
QString AddAgentDialog::agent_base_url() const { return m_edit_base_url->text(); }

// ════════════════════════════════════════
// CookiesDialog
// ════════════════════════════════════════

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

    // Agent row
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

    // Cookies row
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

// ════════════════════════════════════════
// SettingsDialog
// ════════════════════════════════════════

SettingsDialog::SettingsDialog(ThemeManager* theme, Translator* tr, QWidget* parent)
    : QDialog(parent), m_theme(theme), m_tr(tr)
{
    setWindowFlags(windowFlags() & ~Qt::WindowContextHelpButtonHint);
    setFixedSize(920, 580);
    setup_ui();
    populate_sample_data();
    refresh_table();
    apply_theme();
}

void SettingsDialog::setup_ui()
{
    auto* root = new QVBoxLayout(this);
    root->setContentsMargins(0, 0, 0, 0);
    root->setSpacing(0);

    // Title
    m_title_label = new QLabel(m_tr->t("settings.agent_list_title"));
    m_title_label->setAlignment(Qt::AlignCenter);
    m_title_label->setFixedHeight(IconDefs::k_table_row_height + 4);
    m_title_label->setStyleSheet("font-size: 14px; font-weight: bold;");
    root->addWidget(m_title_label);

    // Header buttons
    auto* header = new QWidget;
    auto* header_lay = new QHBoxLayout(header);
    header_lay->setContentsMargins(20, 8, 20, 8);
    header_lay->setSpacing(8);
    header_lay->addStretch();

    m_btn_check_all = new QPushButton(QIcon(":/icons/check_all"), m_tr->t("settings.check_all"));
    m_btn_check_all->setCursor(Qt::PointingHandCursor);
    m_btn_check_all->setFixedHeight(IconDefs::k_header_btn_height);
    m_btn_check_all->setIconSize(IconDefs::header_icon());
    header_lay->addWidget(m_btn_check_all);

    m_btn_login_all = new QPushButton(QIcon(":/icons/login_agent"), m_tr->t("settings.login_all"));
    m_btn_login_all->setCursor(Qt::PointingHandCursor);
    m_btn_login_all->setFixedHeight(IconDefs::k_header_btn_height);
    m_btn_login_all->setIconSize(IconDefs::header_icon());
    header_lay->addWidget(m_btn_login_all);

    m_btn_delete_all = new QPushButton(QIcon(":/icons/delete"), m_tr->t("settings.delete_all"));
    m_btn_delete_all->setCursor(Qt::PointingHandCursor);
    m_btn_delete_all->setFixedHeight(IconDefs::k_header_btn_height);
    m_btn_delete_all->setIconSize(IconDefs::header_icon());
    header_lay->addWidget(m_btn_delete_all);

    m_btn_add = new QPushButton(QIcon(":/icons/add_agent"), m_tr->t("settings.add_agent"));
    m_btn_add->setCursor(Qt::PointingHandCursor);
    m_btn_add->setFixedHeight(IconDefs::k_header_btn_height);
    m_btn_add->setIconSize(IconDefs::header_icon());
    header_lay->addWidget(m_btn_add);

    root->addWidget(header);

    // Separator
    auto* sep = new QFrame;
    sep->setFrameShape(QFrame::HLine);
    sep->setFixedHeight(IconDefs::k_separator_height);
    root->addWidget(sep);

    // Table
    m_table = new QTableWidget;
    m_table->setColumnCount(7);
    m_table->setHorizontalHeaderLabels({
        m_tr->t("settings.col_code"),
        m_tr->t("settings.col_name"),
        m_tr->t("settings.col_account"),
        m_tr->t("settings.col_status"),
        m_tr->t("settings.col_created"),
        m_tr->t("settings.col_actions"),
        m_tr->t("settings.col_auto_login")
    });
    m_table->setSelectionBehavior(QAbstractItemView::SelectRows);
    m_table->setSelectionMode(QAbstractItemView::SingleSelection);
    m_table->setEditTriggers(QAbstractItemView::NoEditTriggers);
    m_table->verticalHeader()->setVisible(false);
    m_table->setShowGrid(true);
    m_table->horizontalHeader()->setStretchLastSection(false);
    m_table->horizontalHeader()->setSectionResizeMode(5, QHeaderView::Stretch);

    m_table->setColumnWidth(0, 55);   // code
    m_table->setColumnWidth(1, 60);   // name
    m_table->setColumnWidth(2, 95);   // account
    m_table->setColumnWidth(3, 90);   // status
    m_table->setColumnWidth(4, 140);  // created
    // col 5 (actions) stretches
    m_table->setColumnWidth(6, 80);   // auto login

    root->addWidget(m_table, 1);

    // Connects
    connect(m_btn_check_all, &QPushButton::clicked, this, &SettingsDialog::on_check_all);
    connect(m_btn_login_all, &QPushButton::clicked, this, &SettingsDialog::on_login_all);
    connect(m_btn_delete_all, &QPushButton::clicked, this, &SettingsDialog::on_delete_all);
    connect(m_btn_add, &QPushButton::clicked, this, &SettingsDialog::on_add_agent);

    setWindowTitle(m_tr->t("settings.agent_list_title"));
}

void SettingsDialog::populate_sample_data()
{
    m_agents = {
        {"DL001", QString::fromUtf8("\u5c0f\u9762"), "huangxie01", QString::fromUtf8("Th\u1ea5t b\u1ea1i"), "2026-03-10 08:16:45", false},
        {"DL002", QString::fromUtf8("\u963f\u5f97"), "huangxie02", QString::fromUtf8("Th\u1ea5t b\u1ea1i"), "2026-03-10 08:16:46", true},
        {"DL003", QString::fromUtf8("\u66f4\u65b0"), "huangxie05", QString::fromUtf8("Th\u1ea5t b\u1ea1i"), "2026-03-10 08:16:47", false},
        {"DL004", QString::fromUtf8("\u4e9a\u7d22"), "huangxie06", QString::fromUtf8("Th\u1ea5t b\u1ea1i"), "2026-03-10 08:16:47", false},
        {"DL005", QString::fromUtf8("\u695a\u6052"), "huangxie07", QString::fromUtf8("Th\u1ea5t b\u1ea1i"), "2026-03-10 08:16:48", true},
        {"DL006", QString::fromUtf8("\u5927\u5e06"), "huangxie08", QString::fromUtf8("Th\u1ea5t b\u1ea1i"), "2026-03-10 08:16:49", false},
        {"DL007", QString::fromUtf8("\u9ec4\u8f89"), "huangxie09", QString::fromUtf8("Th\u1ea5t b\u1ea1i"), "2026-03-10 08:16:49", false},
        {"DL008", QString::fromUtf8("\u6625\u82b1"), "huangxie10", QString::fromUtf8("Th\u1ea5t b\u1ea1i"), "2026-03-10 08:16:50", true},
        {"DL009", QString::fromUtf8("\u5c0f\u7c73"), "huangxie13", QString::fromUtf8("Th\u1ea5t b\u1ea1i"), "2026-03-10 08:16:51", false},
        {"DL010", QString::fromUtf8("\u7231\u7389"), "huangxie15", QString::fromUtf8("Th\u1ea5t b\u1ea1i"), "2026-03-10 08:16:51", false},
        {"DL011", QString::fromUtf8("\u5c0f\u535a"), "huangxie16", QString::fromUtf8("Th\u1ea5t b\u1ea1i"), "2026-03-10 08:16:52", false},
    };
}

void SettingsDialog::refresh_table()
{
    m_table->setRowCount(m_agents.size());
    for (int i = 0; i < m_agents.size(); ++i) {
        const auto& a = m_agents[i];

        // Code
        auto* code_item = new QTableWidgetItem(a.code);
        code_item->setTextAlignment(Qt::AlignCenter);
        m_table->setItem(i, 0, code_item);

        // Name
        auto* name_item = new QTableWidgetItem(a.name);
        name_item->setTextAlignment(Qt::AlignCenter);
        m_table->setItem(i, 1, name_item);

        // Username
        auto* user_item = new QTableWidgetItem(a.username);
        user_item->setTextAlignment(Qt::AlignCenter);
        m_table->setItem(i, 2, user_item);

        // Status — colored label
        auto* status_widget = new QWidget;
        auto* status_lay = new QHBoxLayout(status_widget);
        status_lay->setContentsMargins(4, 2, 4, 2);
        status_lay->setAlignment(Qt::AlignCenter);
        auto* status_label = new QLabel(a.status);
        status_label->setAlignment(Qt::AlignCenter);
        status_label->setFixedHeight(IconDefs::k_status_tag_height);
        status_label->setStyleSheet(QString(
            "QLabel { color: #fff; background: %1; padding: 2px 10px;"
            "  font-size: 11px; border: none; }"
        ).arg(a.status.contains("công") ? "#16b777" : "#ff5722"));
        status_lay->addWidget(status_label);
        m_table->setCellWidget(i, 3, status_widget);

        // Created
        auto* date_item = new QTableWidgetItem(a.created_at);
        date_item->setTextAlignment(Qt::AlignCenter);
        m_table->setItem(i, 4, date_item);

        // Action buttons
        m_table->setCellWidget(i, 5, make_action_buttons(i));

        // Auto Login toggle switch
        auto* auto_widget = new QWidget;
        auto* auto_lay = new QHBoxLayout(auto_widget);
        auto_lay->setContentsMargins(0, 0, 0, 0);
        auto_lay->setAlignment(Qt::AlignCenter);
        auto* toggle = new ToggleSwitch(a.auto_login);
        connect(toggle, &ToggleSwitch::toggled, this, [this, i](bool checked) {
            m_agents[i].auto_login = checked;
            on_toggle_auto_login(i);
        });
        auto_lay->addWidget(toggle);
        m_table->setCellWidget(i, 6, auto_widget);
    }

    for (int i = 0; i < m_agents.size(); ++i)
        m_table->setRowHeight(i, IconDefs::k_table_row_height);
}

QWidget* SettingsDialog::make_action_buttons(int row)
{
    auto* widget = new QWidget;
    auto* lay = new QHBoxLayout(widget);
    lay->setContentsMargins(2, 1, 2, 1);
    lay->setSpacing(3);
    lay->setAlignment(Qt::AlignCenter);

    auto make_btn = [&](const QIcon& icon, const QString& text, const QString& border_color) {
        auto* btn = new QPushButton(icon, text);
        btn->setCursor(Qt::PointingHandCursor);
        btn->setFixedHeight(IconDefs::k_table_btn_height);
        btn->setIconSize(IconDefs::table_icon());
        btn->setStyleSheet(QString(
            "QPushButton { background: transparent; color: %1; border: 1px solid %1;"
            "  padding: 0 5px; font-size: 11px; }"
            "QPushButton:hover { background: %1; color: #fff; }"
        ).arg(border_color));
        lay->addWidget(btn);
        return btn;
    };

    auto* btn_edit = make_btn(QIcon(":/icons/edit"), m_tr->t("settings.edit"), "#1e9fff");
    auto* btn_delete = make_btn(QIcon(":/icons/delete"), m_tr->t("settings.delete"), "#ff5722");
    auto* btn_check = make_btn(QIcon(":/icons/check"), m_tr->t("settings.check"), "#16b777");
    auto* btn_login = make_btn(QIcon(":/icons/login_agent"), m_tr->t("settings.login"), "#ffb800");
    auto* btn_cookies = make_btn(QIcon(":/icons/cookies"), m_tr->t("settings.assign_cookies"), "#16baaa");

    connect(btn_edit, &QPushButton::clicked, this, [this, row]() { on_edit_agent(row); });
    connect(btn_delete, &QPushButton::clicked, this, [this, row]() { on_delete_agent(row); });
    connect(btn_check, &QPushButton::clicked, this, [this, row]() { on_check_agent(row); });
    connect(btn_login, &QPushButton::clicked, this, [this, row]() { on_login_agent(row); });
    connect(btn_cookies, &QPushButton::clicked, this, [this, row]() { on_assign_cookies(row); });

    return widget;
}

void SettingsDialog::apply_theme()
{
    auto bg = m_theme->color("bg");
    auto fg = m_theme->color("text_primary");
    auto border = m_theme->color("border");
    auto border_light = m_theme->color("border_light");
    auto primary = m_theme->color("primary");
    auto bg2 = m_theme->color("bg_secondary");
    auto bg_hover = m_theme->color("bg_hover");

    setStyleSheet(QString("QDialog { background: %1; }").arg(bg));

    m_title_label->setStyleSheet(QString(
        "QLabel { font-size: 14px; font-weight: bold; color: %1;"
        "  background: %2; border-bottom: 1px solid %3; border-top: none;"
        "  border-left: none; border-right: none; }"
    ).arg(fg, bg2, border_light));

    // Header buttons
    m_btn_check_all->setStyleSheet(QString(
        "QPushButton { background: transparent; color: #16b777; border: 1px solid #16b777;"
        "  padding: 0 12px; font-size: 12px; }"
        "QPushButton:hover { background: #16b777; color: #fff; }"
    ));
    m_btn_login_all->setStyleSheet(QString(
        "QPushButton { background: transparent; color: #ffb800; border: 1px solid #ffb800;"
        "  padding: 0 12px; font-size: 12px; }"
        "QPushButton:hover { background: #ffb800; color: #fff; }"
    ));
    m_btn_delete_all->setStyleSheet(QString(
        "QPushButton { background: transparent; color: #ff5722; border: 1px solid #ff5722;"
        "  padding: 0 12px; font-size: 12px; }"
        "QPushButton:hover { background: #ff5722; color: #fff; }"
    ));
    m_btn_add->setStyleSheet(QString(
        "QPushButton { background: %1; color: #fff; border: none;"
        "  padding: 0 12px; font-size: 12px; }"
        "QPushButton:hover { opacity: 0.9; }"
    ).arg(primary));

    // Table
    m_table->setStyleSheet(QString(
        "QTableWidget { background: %1; color: %2; border: 1px solid %3;"
        "  gridline-color: %3; font-size: 12px; }"
        "QTableWidget::item { padding: 4px; }"
        "QTableWidget::item:selected { background: %4; }"
        "QHeaderView::section { background: %5; color: %2; border: none;"
        "  border-bottom: 1px solid %3; border-right: 1px solid %3;"
        "  padding: 6px; font-size: 12px; font-weight: normal; }"
    ).arg(bg, fg, border_light, bg_hover, bg2));
}

void SettingsDialog::retranslate()
{
    setWindowTitle(m_tr->t("settings.agent_list_title"));
    m_title_label->setText(m_tr->t("settings.agent_list_title"));
    m_btn_check_all->setText(m_tr->t("settings.check_all"));
    m_btn_login_all->setText(m_tr->t("settings.login_all"));
    m_btn_delete_all->setText(m_tr->t("settings.delete_all"));
    m_btn_add->setText(m_tr->t("settings.add_agent"));
    m_table->setHorizontalHeaderLabels({
        m_tr->t("settings.col_code"),
        m_tr->t("settings.col_name"),
        m_tr->t("settings.col_account"),
        m_tr->t("settings.col_status"),
        m_tr->t("settings.col_created"),
        m_tr->t("settings.col_actions"),
        m_tr->t("settings.col_auto_login")
    });
    refresh_table();
}

// ── Slots ──

void SettingsDialog::on_add_agent()
{
    AddAgentDialog dlg(m_theme, m_tr, this);
    if (dlg.exec() == QDialog::Accepted) {
        AgentInfo info;
        info.code = QString("DL%1").arg(m_agents.size() + 1, 3, 10, QChar('0'));
        info.name = dlg.agent_name();
        info.username = dlg.agent_username();
        info.status = m_tr->t("settings.status_failed");
        info.created_at = QDateTime::currentDateTime().toString("yyyy-MM-dd hh:mm:ss");
        info.auto_login = false;
        m_agents.append(info);
        refresh_table();
    }
}

void SettingsDialog::on_check_all()
{
    // TODO: API call to check all agents
}

void SettingsDialog::on_login_all()
{
    // TODO: API call to login all agents
}

void SettingsDialog::on_delete_all()
{
    m_agents.clear();
    refresh_table();
}

void SettingsDialog::on_edit_agent(int row)
{
    if (row < 0 || row >= m_agents.size()) return;
    // TODO: open edit dialog
}

void SettingsDialog::on_delete_agent(int row)
{
    if (row < 0 || row >= m_agents.size()) return;
    m_agents.removeAt(row);
    refresh_table();
}

void SettingsDialog::on_check_agent(int row)
{
    if (row < 0 || row >= m_agents.size()) return;
    // TODO: API call to check agent status
}

void SettingsDialog::on_login_agent(int row)
{
    if (row < 0 || row >= m_agents.size()) return;
    // TODO: API call to login agent
}

void SettingsDialog::on_assign_cookies(int row)
{
    if (row < 0 || row >= m_agents.size()) return;
    CookiesDialog dlg(m_theme, m_tr, this);
    dlg.set_agent(m_agents[row].name, m_agents[row].username);
    if (dlg.exec() == QDialog::Accepted) {
        // TODO: save cookies via API
    }
}

void SettingsDialog::on_toggle_auto_login(int row)
{
    if (row < 0 || row >= m_agents.size()) return;
    // TODO: API call to toggle auto login
}
