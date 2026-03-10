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

class ApiClient;
class ThemeManager;
class Translator;
class HomePage;
class CustomersPage;
class ReportPages;

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
    void apply_theme();
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
    QAction* m_settings_action;

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

    // Sub-widgets (tách SRP)
    HomePage* m_home_page;
    CustomersPage* m_customers_page;
    ReportPages* m_report_pages;
};
