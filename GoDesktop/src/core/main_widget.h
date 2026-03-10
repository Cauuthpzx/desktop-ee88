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
#include <QVector>
#include <QLineEdit>
#include <QComboBox>
#include <QDateEdit>
#include <QTableWidget>
#include <QHeaderView>

class ApiClient;
class DateRangePicker;
class ThemeManager;
class Translator;

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
    QWidget* create_home_page();
    QWidget* create_customers_page();
    void apply_theme();
    QIcon lang_flag_icon(const QString& locale) const;
    void on_filter_columns();
    void on_export_csv();
    void on_print_table();

    ApiClient* m_api;
    ThemeManager* m_theme;
    Translator* m_tr;

    // Toolbar (y hệt Cqt)
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

    // Account dropdown (bên phải, sau spacer)
    QToolButton* m_account_button;
    QMenu* m_account_menu;
    QAction* m_change_pwd_action;
    QAction* m_logout_action;
    QAction* m_theme_action;
    QToolButton* m_lang_button;
    QMenu* m_lang_menu;

    // Labels
    QLabel* m_username_label;
    QLabel* m_hero_title;
    QLabel* m_hero_tagline;
    QPushButton* m_explore_btn;
    QLabel* m_footer_text;
    QLabel* m_welcome_text;
    QLabel* m_welcome_name;

    QString m_username;
    QStackedWidget* m_content_stack;

    // Feature box labels (for theme/lang update)
    QVector<QLabel*> m_feature_titles;
    QVector<QLabel*> m_feature_descs;
    QVector<QWidget*> m_feature_boxes;
    QVector<QWidget*> m_feature_icon_bgs;

    QWidget* m_home_page;
    QWidget* m_hero_widget;
    QWidget* m_boxes_container;
    QWidget* m_footer;

    // Customers page widgets (for theme update)
    QWidget* m_customers_page;
    QWidget* m_customers_card;
    QWidget* m_customers_field_header;
    QLabel* m_customers_title;
    QLineEdit* m_search_username;
    DateRangePicker* m_date_range_picker;
    QComboBox* m_search_status;
    QComboBox* m_search_sort_field;
    QComboBox* m_search_sort_dir;
    QPushButton* m_search_btn;
    QPushButton* m_reset_btn;
    QVector<QLabel*> m_search_labels;

    // Table toolbar + table + pagination
    QWidget* m_table_toolbar;
    QPushButton* m_add_member_btn;
    QPushButton* m_add_agent_btn;
    QPushButton* m_filter_btn;
    QPushButton* m_export_btn;
    QPushButton* m_print_btn;
    QTableWidget* m_customers_table;
    QWidget* m_pagination_bar;
    QLabel* m_page_info;
    QComboBox* m_page_size_combo;
    QPushButton* m_page_prev_btn;
    QPushButton* m_page_next_btn;
    QLabel* m_page_number;
};
