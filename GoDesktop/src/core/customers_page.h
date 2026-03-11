#pragma once

#include <QWidget>
#include <QLabel>
#include <QPushButton>
#include <QLineEdit>
#include <QComboBox>
#include <QTableWidget>
#include <QHeaderView>
#include <QHBoxLayout>
#include <QIntValidator>
#include <QVector>

class ApiClient;
class DateRangePicker;
class ThemeManager;
class Translator;

class CustomersPage : public QWidget {
    Q_OBJECT

public:
    explicit CustomersPage(ApiClient* api, ThemeManager* theme, Translator* tr, QWidget* parent = nullptr);

    void apply_theme();
    void retranslate();
    void load_data();

private:
    void setup_ui();
    void fetch_customers();
    void populate_table(const QJsonArray& data, int total);
    void rebuild_page_buttons(int max_page);
    void on_filter_columns();
    void on_export_csv();
    void on_print_table();

    ApiClient* m_api;
    ThemeManager* m_theme;
    Translator* m_tr;

    int m_current_page = 1;
    int m_page_size = 10;
    int m_total = 0;
    bool m_ready = false;

    QWidget* m_card;
    QWidget* m_field_header;
    QLabel* m_title;
    QLineEdit* m_search_username;
    DateRangePicker* m_date_range_picker;
    QComboBox* m_search_status;
    QComboBox* m_search_sort_field;
    QComboBox* m_search_sort_dir;
    QPushButton* m_search_btn;
    QPushButton* m_reset_btn;
    QVector<QLabel*> m_search_labels;

    QWidget* m_table_toolbar;
    QPushButton* m_add_member_btn;
    QPushButton* m_add_agent_btn;
    QPushButton* m_filter_btn;
    QPushButton* m_export_btn;
    QPushButton* m_print_btn;
    QTableWidget* m_table;
    QWidget* m_pagination_bar;
    QWidget* m_page_btn_container;
    QHBoxLayout* m_page_btn_layout;
    QComboBox* m_page_size_combo;
    QPushButton* m_page_prev_btn;
    QPushButton* m_page_next_btn;
    QPushButton* m_refresh_btn;
    QLabel* m_page_info;
    QLabel* m_skip_label;
    QLineEdit* m_skip_input;
    QPushButton* m_skip_confirm;
};
