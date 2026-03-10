#include "core/main_widget.h"
#include "core/api_client.h"
#include "core/theme_manager.h"
#include "core/translator.h"
#include "core/home_page.h"
#include "core/customers_page.h"
#include "core/report_pages.h"
#include "core/settings_dialog.h"
#include "core/icon_defs.h"

#include <QHBoxLayout>
#include <QVBoxLayout>
#include <QInputDialog>
#include <QMessageBox>

MainWidget::MainWidget(ApiClient* api, ThemeManager* theme, Translator* tr, QWidget* parent)
    : QWidget(parent)
    , m_api(api)
    , m_theme(theme)
    , m_tr(tr)
{
    setup_ui();

    connect(m_theme, &ThemeManager::theme_changed, this, &MainWidget::on_theme_changed);
    connect(m_tr, &Translator::locale_changed, this, &MainWidget::on_locale_changed);
}

void MainWidget::set_username(const QString& username)
{
    m_username = username;
    m_username_label->setText(username);
    m_home_page->set_username(username);
    m_account_button->setText(username);
}

void MainWidget::setup_ui()
{
    auto* root = new QVBoxLayout(this);
    root->setContentsMargins(0, 0, 0, 0);
    root->setSpacing(0);

    setup_toolbar();
    root->addWidget(m_toolbar);

    // Sub-widgets
    m_home_page = new HomePage(m_theme, m_tr, this);
    m_customers_page = new CustomersPage(m_theme, m_tr, this);
    m_report_pages = new ReportPages(m_theme, m_tr, this);

    m_content_stack = new QStackedWidget;
    m_content_stack->addWidget(m_home_page);                                  // 0
    m_content_stack->addWidget(m_customers_page);                             // 1
    m_content_stack->addWidget(m_report_pages->create_lottery_report_page());  // 2
    m_content_stack->addWidget(m_report_pages->create_transaction_log_page()); // 3
    m_content_stack->addWidget(m_report_pages->create_provider_report_page()); // 4
    m_content_stack->addWidget(m_report_pages->create_lottery_bets_page());    // 5
    m_content_stack->addWidget(m_report_pages->create_provider_bets_page());   // 6
    m_content_stack->addWidget(m_report_pages->create_withdrawal_history_page()); // 7
    m_content_stack->addWidget(m_report_pages->create_deposit_history_page());    // 8
    root->addWidget(m_content_stack, 1);

    apply_theme();
}

// ════════════════════════════════════════
// TOOLBAR
// ════════════════════════════════════════
void MainWidget::setup_toolbar()
{
    m_toolbar = new QToolBar;
    m_toolbar->setMovable(false);
    m_toolbar->setFloatable(false);
    m_toolbar->setIconSize(IconDefs::toolbar_icon());
    m_toolbar->setToolButtonStyle(Qt::ToolButtonTextBesideIcon);

    // Trang Chủ
    m_home_action = m_toolbar->addAction(
        QIcon(":/icons/home"),
        m_tr->t("nav.home"));
    connect(m_home_action, &QAction::triggered, this, [this]() { navigate_to(0); });

    // Quản Lý Khách Hàng
    m_customers_action = m_toolbar->addAction(
        QIcon(":/icons/customers"),
        m_tr->t("nav.customers"));
    connect(m_customers_action, &QAction::triggered, this, [this]() { navigate_to(1); });

    // Báo Cáo — dropdown
    m_report_menu = new QMenu(this);
    m_act_lottery_report = m_report_menu->addAction(QIcon(":/icons/menu_lottery_report"),
        m_tr->t("nav.report_lottery"));
    m_act_transaction_log = m_report_menu->addAction(QIcon(":/icons/menu_transaction_log"),
        m_tr->t("nav.report_transaction"));
    m_act_provider_report = m_report_menu->addAction(QIcon(":/icons/menu_provider_report"),
        m_tr->t("nav.report_provider"));
    connect(m_act_lottery_report, &QAction::triggered, this, [this]() { navigate_to(2); });
    connect(m_act_transaction_log, &QAction::triggered, this, [this]() { navigate_to(3); });
    connect(m_act_provider_report, &QAction::triggered, this, [this]() { navigate_to(4); });

    m_report_button = new QToolButton(this);
    m_report_button->setIcon(QIcon(":/icons/report"));
    m_report_button->setText(m_tr->t("nav.reports"));
    m_report_button->setToolButtonStyle(Qt::ToolButtonTextBesideIcon);
    m_report_button->setPopupMode(QToolButton::InstantPopup);
    m_report_button->setMenu(m_report_menu);
    m_toolbar->addWidget(m_report_button);

    // Đơn Cược — dropdown
    m_bet_order_menu = new QMenu(this);
    m_act_provider_bets = m_bet_order_menu->addAction(QIcon(":/icons/menu_third_party_bet"),
        m_tr->t("nav.bets_provider"));
    m_act_lottery_bets = m_bet_order_menu->addAction(QIcon(":/icons/menu_lottery_bet"),
        m_tr->t("nav.bets_lottery"));
    connect(m_act_provider_bets, &QAction::triggered, this, [this]() { navigate_to(6); });
    connect(m_act_lottery_bets, &QAction::triggered, this, [this]() { navigate_to(5); });

    m_bet_order_button = new QToolButton(this);
    m_bet_order_button->setIcon(QIcon(":/icons/bet_order"));
    m_bet_order_button->setText(m_tr->t("nav.bets"));
    m_bet_order_button->setToolButtonStyle(Qt::ToolButtonTextBesideIcon);
    m_bet_order_button->setPopupMode(QToolButton::InstantPopup);
    m_bet_order_button->setMenu(m_bet_order_menu);
    m_toolbar->addWidget(m_bet_order_button);

    // Nạp - Rút — dropdown
    m_deposit_withdraw_menu = new QMenu(this);
    m_act_deposit_log = m_deposit_withdraw_menu->addAction(QIcon(":/icons/menu_deposit_log"),
        m_tr->t("nav.commission_deposit"));
    m_act_withdraw_log = m_deposit_withdraw_menu->addAction(QIcon(":/icons/menu_withdraw_log"),
        m_tr->t("nav.commission_withdrawal"));
    connect(m_act_deposit_log, &QAction::triggered, this, [this]() { navigate_to(8); });
    connect(m_act_withdraw_log, &QAction::triggered, this, [this]() { navigate_to(7); });

    m_deposit_withdraw_button = new QToolButton(this);
    m_deposit_withdraw_button->setIcon(QIcon(":/icons/deposit_withdraw"));
    m_deposit_withdraw_button->setText(m_tr->t("nav.commission"));
    m_deposit_withdraw_button->setToolButtonStyle(Qt::ToolButtonTextBesideIcon);
    m_deposit_withdraw_button->setPopupMode(QToolButton::InstantPopup);
    m_deposit_withdraw_button->setMenu(m_deposit_withdraw_menu);
    m_toolbar->addWidget(m_deposit_withdraw_button);

    // Spacer
    auto* spacer = new QWidget(this);
    spacer->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Preferred);
    spacer->setStyleSheet("background: transparent; border: none;");
    m_toolbar->addWidget(spacer);

    // Theme toggle
    m_theme_action = m_toolbar->addAction(
        QIcon(m_theme->theme() == "dark" ? ":/icons/sun_theme" : ":/icons/moon_theme"),
        m_theme->theme() == "dark" ? m_tr->t("home.light_mode") : m_tr->t("home.dark_mode"));
    connect(m_theme_action, &QAction::triggered, this, [this]() {
        m_theme->toggle_theme();
    });

    // Language switcher
    m_lang_menu = new QMenu(this);
    const QStringList locales = {"vi_VN", "en_US", "zh_CN"};
    const QStringList locale_names = {
        QString::fromUtf8("Tiếng Việt"),
        "English",
        QString::fromUtf8("\u4e2d\u6587")
    };
    const QStringList flag_icons = {
        ":/icons/flag_vn", ":/icons/flag_us", ":/icons/flag_cn"
    };
    for (int i = 0; i < locales.size(); ++i) {
        auto* action = m_lang_menu->addAction(
            QIcon(flag_icons[i]), locale_names[i]);
        connect(action, &QAction::triggered, this, [this, locale = locales[i]]() {
            m_tr->set_locale(locale);
        });
    }

    m_lang_button = new QToolButton(this);
    m_lang_button->setIcon(lang_flag_icon(m_tr->locale()));
    m_lang_button->setText(m_tr->locale_label(m_tr->locale()));
    m_lang_button->setToolButtonStyle(Qt::ToolButtonTextBesideIcon);
    m_lang_button->setPopupMode(QToolButton::InstantPopup);
    m_lang_button->setMenu(m_lang_menu);
    m_toolbar->addWidget(m_lang_button);

    // Account dropdown
    m_account_menu = new QMenu(this);

    m_change_pwd_action = m_account_menu->addAction(
        QIcon(":/icons/password"), m_tr->t("auth.change_password"));
    connect(m_change_pwd_action, &QAction::triggered, this, &MainWidget::on_change_password);

    m_account_menu->addSeparator();

    m_logout_action = m_account_menu->addAction(
        QIcon(":/icons/logout"), m_tr->t("auth.logout"));
    connect(m_logout_action, &QAction::triggered, this, &MainWidget::on_logout);

    m_account_button = new QToolButton(this);
    m_account_button->setIcon(QIcon(":/icons/user"));
    m_account_button->setText(m_username.isEmpty() ? "User" : m_username);
    m_account_button->setToolButtonStyle(Qt::ToolButtonTextBesideIcon);
    m_account_button->setPopupMode(QToolButton::InstantPopup);
    m_account_button->setMenu(m_account_menu);
    m_toolbar->addWidget(m_account_button);

    // Cài Đặt — dropdown giống Báo cáo
    m_settings_menu = new QMenu(this);
    m_act_ee88_settings = m_settings_menu->addAction(
        QIcon(":/icons/user"), m_tr->t("settings.ee88_account_settings"));
    connect(m_act_ee88_settings, &QAction::triggered, this, [this]() {
        SettingsDialog dlg(m_theme, m_tr, this);
        dlg.exec();
    });

    m_settings_button = new QToolButton(this);
    m_settings_button->setIcon(QIcon(":/icons/settings"));
    m_settings_button->setText(m_tr->t("nav.settings"));
    m_settings_button->setToolButtonStyle(Qt::ToolButtonTextBesideIcon);
    m_settings_button->setCursor(Qt::PointingHandCursor);
    connect(m_settings_button, &QToolButton::clicked, this, [this]() {
        QPoint pos = m_settings_button->mapToGlobal(
            QPoint(m_settings_button->width(), m_settings_button->height()));
        QSize menu_size = m_settings_menu->sizeHint();
        pos.setX(pos.x() - menu_size.width());
        m_settings_menu->popup(pos);
    });
    m_toolbar->addWidget(m_settings_button);

    // Hidden label
    m_username_label = new QLabel;
    m_username_label->setVisible(false);
}

QIcon MainWidget::lang_flag_icon(const QString& locale) const
{
    if (locale == "vi_VN") return QIcon(":/icons/flag_vn");
    if (locale == "zh_CN") return QIcon(":/icons/flag_cn");
    return QIcon(":/icons/flag_us");
}

void MainWidget::navigate_to(int index)
{
    if (index < m_content_stack->count()) {
        m_content_stack->setCurrentIndex(index);
    }
    m_active_nav_index = index;
    apply_theme();
}

// ════════════════════════════════════════
// THEME — delegate to sub-widgets
// ════════════════════════════════════════
void MainWidget::apply_theme()
{
    const auto bg_hover = m_theme->color("bg_hover");
    const auto bg2 = m_theme->color("bg_secondary");
    const auto text1 = m_theme->color("text_primary");
    const auto text2 = m_theme->color("text_secondary");
    const auto text_nav = m_theme->color("text_nav");
    const auto border = m_theme->color("border");
    const auto border_light = m_theme->color("border_light");
    const auto primary = m_theme->color("primary");
    const auto header_bg = m_theme->color("header_bg");
    const auto bg = m_theme->color("bg");

    // Toolbar
    m_toolbar->setStyleSheet(QString(
        "QToolBar { spacing: 0px; padding: 2px 0px; border-bottom: 1px solid %1;"
        "  background: %2; }"
        "QToolBar > QWidget { background: transparent; }"
        "QToolButton { padding: 3px 6px; border: 1px solid %3; border-right: none;"
        "  border-radius: 0px; background-color: %4; font-size: 12px; color: %5; }"
        "QToolButton:hover { background-color: %6; border-color: %7; }"
        "QToolButton::menu-indicator { image: none; }"
    ).arg(border_light, header_bg, border, bg2, text_nav, bg_hover, text2));

    // Theme toggle icon + text
    m_theme_action->setIcon(QIcon(m_theme->theme() == "dark"
        ? ":/icons/sun_theme" : ":/icons/moon_theme"));
    m_theme_action->setText(m_theme->theme() == "dark"
        ? m_tr->t("home.light_mode") : m_tr->t("home.dark_mode"));

    // Lang button
    m_lang_button->setIcon(lang_flag_icon(m_tr->locale()));
    m_lang_button->setText(m_tr->locale_label(m_tr->locale()));

    // Menu styling
    auto menu_style = QString(
        "QMenu { background: %1; border: 1px solid %2; padding: 4px; font-size: 14px; }"
        "QMenu::item { padding: 6px 12px; color: %3; }"
        "QMenu::item:selected { background: %4; color: %5; }"
        "QMenu::separator { height: 1px; background: %2; margin: 4px 8px; }"
    ).arg(bg, border, text1, bg_hover, primary);

    m_lang_menu->setStyleSheet(menu_style);
    m_account_menu->setStyleSheet(menu_style);
    m_report_menu->setStyleSheet(menu_style);
    m_bet_order_menu->setStyleSheet(menu_style);
    m_deposit_withdraw_menu->setStyleSheet(menu_style);
    m_settings_menu->setStyleSheet(menu_style);

    // Active nav highlight
    update_active_nav();

    // Delegate to sub-widgets
    m_home_page->apply_theme();
    m_customers_page->apply_theme();
    m_report_pages->apply_theme();
}

void MainWidget::update_active_nav()
{
    const auto primary = m_theme->color("primary");
    const auto bg2 = m_theme->color("bg_secondary");
    const auto text_nav = m_theme->color("text_nav");
    const auto border = m_theme->color("border");
    const auto bg_hover = m_theme->color("bg_hover");
    const auto text2 = m_theme->color("text_secondary");

    // Style for active nav button: primary bottom border + primary text
    auto active_style = QString(
        "QToolButton { padding: 3px 6px; border: 1px solid %1; border-right: none;"
        "  border-bottom: 2px solid %2; border-radius: 0px;"
        "  background-color: %3; font-size: 12px; color: %2; font-weight: bold; }"
        "QToolButton:hover { background-color: %4; border-color: %1; border-bottom: 2px solid %2; }"
        "QToolButton::menu-indicator { image: none; }"
    ).arg(border, primary, bg2, bg_hover);

    // Style for inactive nav button (default)
    auto inactive_style = QString(
        "QToolButton { padding: 3px 6px; border: 1px solid %1; border-right: none;"
        "  border-radius: 0px; background-color: %2; font-size: 12px; color: %3; }"
        "QToolButton:hover { background-color: %4; border-color: %5; }"
        "QToolButton::menu-indicator { image: none; }"
    ).arg(border, bg2, text_nav, bg_hover, text2);

    // Map page index to nav group: 0=home, 1=customers, 2-4=reports, 5-6=bets, 7-8=deposit
    int active_group = -1;
    if (m_active_nav_index == 0) active_group = 0;
    else if (m_active_nav_index == 1) active_group = 1;
    else if (m_active_nav_index >= 2 && m_active_nav_index <= 4) active_group = 2;
    else if (m_active_nav_index >= 5 && m_active_nav_index <= 6) active_group = 3;
    else if (m_active_nav_index >= 7 && m_active_nav_index <= 8) active_group = 4;

    // Find QToolButtons for QAction-based items (Home, Customers)
    auto find_action_button = [this](QAction* action) -> QToolButton* {
        for (auto* child : m_toolbar->findChildren<QToolButton*>()) {
            if (child->defaultAction() == action) return child;
        }
        return nullptr;
    };

    QToolButton* home_btn = find_action_button(m_home_action);
    QToolButton* customers_btn = find_action_button(m_customers_action);

    if (home_btn) home_btn->setStyleSheet(active_group == 0 ? active_style : inactive_style);
    if (customers_btn) customers_btn->setStyleSheet(active_group == 1 ? active_style : inactive_style);
    m_report_button->setStyleSheet(active_group == 2 ? active_style : inactive_style);
    m_bet_order_button->setStyleSheet(active_group == 3 ? active_style : inactive_style);
    m_deposit_withdraw_button->setStyleSheet(active_group == 4 ? active_style : inactive_style);
}

void MainWidget::on_theme_changed()
{
    apply_theme();
}

void MainWidget::on_locale_changed()
{
    // Language button
    m_lang_button->setIcon(lang_flag_icon(m_tr->locale()));
    m_lang_button->setText(m_tr->locale_label(m_tr->locale()));

    // Account menu
    m_change_pwd_action->setText(m_tr->t("auth.change_password"));
    m_logout_action->setText(m_tr->t("auth.logout"));

    // Toolbar nav items
    m_home_action->setText(m_tr->t("nav.home"));
    m_customers_action->setText(m_tr->t("nav.customers"));
    m_report_button->setText(m_tr->t("nav.reports"));
    m_bet_order_button->setText(m_tr->t("nav.bets"));
    m_deposit_withdraw_button->setText(m_tr->t("nav.commission"));
    m_settings_button->setText(m_tr->t("nav.settings"));
    m_act_ee88_settings->setText(m_tr->t("settings.ee88_account_settings"));

    // Report menu actions
    m_act_lottery_report->setText(m_tr->t("nav.report_lottery"));
    m_act_transaction_log->setText(m_tr->t("nav.report_transaction"));
    m_act_provider_report->setText(m_tr->t("nav.report_provider"));

    // Bet order menu actions
    m_act_provider_bets->setText(m_tr->t("nav.bets_provider"));
    m_act_lottery_bets->setText(m_tr->t("nav.bets_lottery"));

    // Deposit/withdraw menu actions
    m_act_deposit_log->setText(m_tr->t("nav.commission_deposit"));
    m_act_withdraw_log->setText(m_tr->t("nav.commission_withdrawal"));

    // Theme toggle text
    m_theme_action->setText(m_theme->theme() == "dark"
        ? m_tr->t("home.light_mode") : m_tr->t("home.dark_mode"));

    // Sub-widgets
    m_home_page->retranslate();
    m_customers_page->retranslate();
    m_report_pages->retranslate();
}

void MainWidget::on_change_password()
{
    bool ok = false;
    const auto old_pwd = QInputDialog::getText(
        this, m_tr->t("auth.change_password"),
        m_tr->t("auth.old_password") + ":",
        QLineEdit::Password, "", &ok
    );
    if (!ok || old_pwd.isEmpty()) return;

    const auto new_pwd = QInputDialog::getText(
        this, m_tr->t("auth.change_password"),
        m_tr->t("auth.new_password") + ":",
        QLineEdit::Password, "", &ok
    );
    if (!ok || new_pwd.isEmpty()) return;

    if (new_pwd.length() < 8) {
        QMessageBox::warning(this,
            m_tr->t("auth.change_password"),
            m_tr->t("auth.password_min"));
        return;
    }

    const auto confirm = QInputDialog::getText(
        this, m_tr->t("auth.change_password"),
        m_tr->t("auth.confirm_new") + ":",
        QLineEdit::Password, "", &ok
    );
    if (!ok || confirm != new_pwd) {
        QMessageBox::warning(this,
            m_tr->t("auth.change_password"),
            m_tr->t("auth.password_mismatch"));
        return;
    }

    m_api->change_password(old_pwd, new_pwd, [this](bool success, const QJsonObject& data) {
        if (success) {
            QMessageBox::information(this,
                m_tr->t("auth.change_password"),
                m_tr->t("auth.change_success"));
        } else {
            const auto msg = data.value("message").toString(m_tr->t("auth.change_failed"));
            QMessageBox::warning(this, m_tr->t("auth.change_password"), msg);
        }
    });
}

void MainWidget::on_logout()
{
    m_api->logout([this](bool /*success*/, const QJsonObject& /*data*/) {
        emit logout_requested();
    });
}
