#pragma once

#include <QWidget>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QPushButton>
#include <QLineEdit>
#include <QComboBox>
#include <QTableWidget>
#include <QHeaderView>
#include <QIcon>
#include <QStringList>
#include <QVector>

class DateRangePicker;
class FlowLayout;
class ThemeManager;
class Translator;

// Cấu trúc chứa tất cả widget của 1 trang báo cáo
struct ReportPageWidgets {
    QWidget* page = nullptr;
    QWidget* card = nullptr;
    QWidget* field_header = nullptr;
    QLabel* title_label = nullptr;
    QWidget* search_form = nullptr;
    QVector<QLabel*> search_labels;

    // Table group
    QWidget* table_toolbar = nullptr;
    QPushButton* filter_btn = nullptr;
    QPushButton* export_btn = nullptr;
    QPushButton* print_btn = nullptr;
    QTableWidget* table = nullptr;

    // Pagination
    QWidget* pagination_bar = nullptr;
    QPushButton* page_prev_btn = nullptr;
    QPushButton* page_next_btn = nullptr;
    QLabel* page_number = nullptr;
    QLabel* page_info = nullptr;
    QComboBox* page_size_combo = nullptr;

    // Summary (optional)
    QWidget* summary_section = nullptr;
    QLabel* summary_title = nullptr;
    QTableWidget* summary_table = nullptr;
};

class ReportPageBuilder {
public:
    // Tạo trang hoàn chỉnh: card > field header > search form > table > pagination
    static ReportPageWidgets build_page(
        const QString& icon_path,
        const QString& title_text,
        const QStringList& column_headers,
        FlowLayout* &out_flow,  // trả về flow layout để caller thêm search fields
        Translator* tr = nullptr
    );

    // Thêm summary section bên dưới table
    static void add_summary(
        ReportPageWidgets& w,
        const QString& summary_title,
        const QStringList& summary_headers,
        const QStringList& summary_defaults
    );

    // Apply theme cho 1 trang
    static void apply_page_theme(
        ReportPageWidgets& w,
        ThemeManager* theme
    );

    // Helper: tạo cặp label + widget
    static QWidget* make_field(const QString& label_text, QWidget* field, QVector<QLabel*>& labels);
};
