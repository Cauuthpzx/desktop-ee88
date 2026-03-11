#pragma once

#include <QWidget>
#include <QLabel>
#include <QPushButton>
#include <QStackedWidget>
#include <QToolBar>
#include <QToolButton>
#include <QMenu>
#include <QAction>
#include <QIcon>
#include <QListWidget>
#include <QScrollArea>

class ApiClient;
class ThemeManager;
class Translator;
class HomePage;
class CustomersPage;
class ReportPages;
class UpstreamClient;

class MainWidget : public QWidget {
    Q_OBJECT

public:
    explicit MainWidget(ApiClient* api, ThemeManager* theme, Translator* tr, QWidget* parent = nullptr);
    void set_username(const QString& username);

signals:
    void logout_requested();

private slots:
    void on_change_password();
    void on_logout();
    void navigate_to(int index);
    void on_theme_changed();
    void on_locale_changed();

private:
    void setup_ui();
    void setup_toolbar();
    void setup_sidebar();
    void apply_theme();
    void apply_sidebar_theme();
    void update_active_nav();
    void update_sidebar_selection();
    void retranslate_sidebar();
    void toggle_sidebar();
    void reposition_toggle();
    void resizeEvent(QResizeEvent* event) override;
    QIcon lang_flag_icon(const QString& locale) const;

    ApiClient* m_api;
    ThemeManager* m_theme;
    Translator* m_tr;

    // Toolbar
    QToolBar* m_toolbar;
    QAction* m_home_action;
    QAction* m_customers_action;
    QToolButton* m_report_button;
    QMenu* m_report_menu;
    QToolButton* m_bet_order_button;
    QMenu* m_bet_order_menu;
    QToolButton* m_deposit_withdraw_button;
    QMenu* m_deposit_withdraw_menu;
    QToolButton* m_settings_button;
    QMenu* m_settings_menu;
    QAction* m_act_ee88_settings;

    // Menu actions (for retranslation)
    QAction* m_act_lottery_report;
    QAction* m_act_transaction_log;
    QAction* m_act_provider_report;
    QAction* m_act_provider_bets;
    QAction* m_act_lottery_bets;
    QAction* m_act_deposit_log;
    QAction* m_act_withdraw_log;

    // Account dropdown
    QToolButton* m_account_button;
    QMenu* m_account_menu;
    QAction* m_change_pwd_action;
    QAction* m_logout_action;
    QAction* m_theme_action;
    QToolButton* m_lang_button;
    QMenu* m_lang_menu;

    QLabel* m_username_label;
    QString m_username;
    QStackedWidget* m_content_stack;
    int m_active_nav_index = 0;

    // Sidebar
    QWidget* m_sidebar;
    QScrollArea* m_sidebar_scroll = nullptr;
    QListWidget* m_sidebar_list;
    QPushButton* m_sidebar_toggle;
    bool m_sidebar_collapsed = true;
    QLabel* m_sidebar_nav_label;
    QLabel* m_sidebar_reports_label;
    QLabel* m_sidebar_system_label;

    // Cached toolbar buttons (lazy init in update_active_nav)
    QToolButton* m_home_btn = nullptr;
    QToolButton* m_customers_btn = nullptr;

    // Upstream direct fetch
    UpstreamClient* m_upstream;

    // Sub-widgets (tách SRP)
    HomePage* m_home_page;
    CustomersPage* m_customers_page;
    ReportPages* m_report_pages;
};
