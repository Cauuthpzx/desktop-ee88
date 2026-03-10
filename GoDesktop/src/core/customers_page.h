#pragma once

#include <QWidget>
#include <QLabel>
#include <QPushButton>
#include <QLineEdit>
#include <QComboBox>
#include <QTableWidget>
#include <QHeaderView>
#include <QVector>

class DateRangePicker;
class ThemeManager;
class Translator;

class CustomersPage : public QWidget {
    Q_OBJECT

public:
    explicit CustomersPage(ThemeManager* theme, Translator* tr, QWidget* parent = nullptr);

    void apply_theme();
    void retranslate();

private:
    void setup_ui();
    void on_filter_columns();
    void on_export_csv();
    void on_print_table();

    ThemeManager* m_theme;
    Translator* m_tr;

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
    QLabel* m_page_info;
    QComboBox* m_page_size_combo;
    QPushButton* m_page_prev_btn;
    QPushButton* m_page_next_btn;
    QLabel* m_page_number;
};
