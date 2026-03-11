#include "core/report_page_builder.h"
#include "core/flow_layout.h"
#include "core/theme_manager.h"
#include "core/translator.h"
#include "core/icon_defs.h"

#include <QPixmap>
#include <QScrollArea>
#include <QIntValidator>

QWidget* ReportPageBuilder::make_field(const QString& label_text, QWidget* field, QVector<QLabel*>& labels)
{
    auto* w = new QWidget;
    w->setStyleSheet("border: none;");
    auto* h = new QHBoxLayout(w);
    h->setContentsMargins(0, 0, 0, 0);
    h->setSpacing(6);
    auto* lbl = new QLabel(label_text);
    lbl->setObjectName("searchLabel");
    labels.push_back(lbl);
    h->addWidget(lbl);
    h->addWidget(field);
    return w;
}

ReportPageWidgets ReportPageBuilder::build_page(
    const QString& icon_path,
    const QString& title_text,
    const QStringList& column_headers,
    FlowLayout* &out_flow,
    Translator* tr)
{
    ReportPageWidgets w;

    w.page = new QWidget;
    w.page->setObjectName("reportPage");

    auto* page_layout = new QVBoxLayout(w.page);
    page_layout->setContentsMargins(10, 10, 10, 10);
    page_layout->setSpacing(0);

    // Card
    w.card = new QWidget;
    w.card->setObjectName("reportCard");
    auto* card_layout = new QVBoxLayout(w.card);
    card_layout->setContentsMargins(16, 16, 16, 16);
    card_layout->setSpacing(12);

    // Field header
    w.field_header = new QWidget;
    auto* header_layout = new QHBoxLayout(w.field_header);
    header_layout->setContentsMargins(0, 0, 0, 8);
    header_layout->setSpacing(6);
    header_layout->setAlignment(Qt::AlignLeft);

    auto* header_icon = new QLabel;
    QPixmap icon_pix(icon_path);
    header_icon->setPixmap(icon_pix.scaled(18, 18, Qt::KeepAspectRatio, Qt::SmoothTransformation));
    header_icon->setStyleSheet("border: none;");
    header_layout->addWidget(header_icon);

    w.title_label = new QLabel(title_text);
    w.title_label->setStyleSheet("font-size: 16px; font-weight: 700; border: none;");
    header_layout->addWidget(w.title_label);
    header_layout->addStretch();

    card_layout->addWidget(w.field_header);

    // Separator
    auto* separator = new QWidget;
    separator->setFixedHeight(IconDefs::k_separator_height);
    separator->setObjectName("fieldSep");
    card_layout->addWidget(separator);
    card_layout->addSpacing(12);

    // Search form (FlowLayout)
    w.search_form = new QWidget;
    w.search_form->setObjectName("searchForm");
    out_flow = new FlowLayout(w.search_form, 0, 12, 8);

    card_layout->addWidget(w.search_form);

    // Table group
    auto* table_group = new QWidget;
    auto* tg_layout = new QVBoxLayout(table_group);
    tg_layout->setContentsMargins(0, 0, 0, 0);
    tg_layout->setSpacing(0);

    // Table toolbar
    w.table_toolbar = new QWidget;
    w.table_toolbar->setObjectName("tableToolbar");
    auto* tb_layout = new QHBoxLayout(w.table_toolbar);
    tb_layout->setContentsMargins(8, 6, 8, 6);
    tb_layout->setSpacing(4);

    tb_layout->addStretch();

    auto make_tool_icon = [](const QString& icon_res, const QString& tooltip) -> QPushButton* {
        auto* btn = new QPushButton;
        btn->setObjectName("toolIcon");
        btn->setIcon(QIcon(icon_res));
        btn->setIconSize(IconDefs::search_icon());
        btn->setFixedSize(28, IconDefs::k_toolbar_btn_height);
        btn->setCursor(Qt::PointingHandCursor);
        btn->setToolTip(tooltip);
        return btn;
    };

    w.filter_btn = make_tool_icon(":/icons/settings", tr ? tr->t("common.filter_columns") : "Filter");
    w.export_btn = make_tool_icon(":/icons/report", tr ? tr->t("common.export_file") : "Export");
    w.print_btn = make_tool_icon(":/icons/browser", tr ? tr->t("common.print") : "Print");
    tb_layout->addWidget(w.filter_btn);
    tb_layout->addWidget(w.export_btn);
    tb_layout->addWidget(w.print_btn);

    tg_layout->addWidget(w.table_toolbar);

    // Table
    int col_count = column_headers.size();
    w.table = new QTableWidget(0, col_count);
    w.table->setObjectName("reportTable");
    w.table->setHorizontalHeaderLabels(column_headers);
    w.table->horizontalHeader()->setSectionResizeMode(QHeaderView::Stretch);
    w.table->horizontalHeader()->setDefaultAlignment(Qt::AlignLeft | Qt::AlignVCenter);
    w.table->verticalHeader()->setVisible(false);
    w.table->setSelectionBehavior(QAbstractItemView::SelectRows);
    w.table->setSelectionMode(QAbstractItemView::SingleSelection);
    w.table->setEditTriggers(QAbstractItemView::NoEditTriggers);
    w.table->setAlternatingRowColors(false);
    w.table->setShowGrid(true);
    w.table->horizontalHeader()->setHighlightSections(false);
    w.table->setFrameShape(QFrame::NoFrame);
    w.table->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Minimum);
    w.table->setVerticalScrollBarPolicy(Qt::ScrollBarAlwaysOff);

    tg_layout->addWidget(w.table, 0);

    // Pagination — layout: count | prev | page buttons | next | limits | refresh | skip
    w.pagination_bar = new QWidget;
    w.pagination_bar->setObjectName("paginationBar");
    auto* pg_layout = new QHBoxLayout(w.pagination_bar);
    pg_layout->setContentsMargins(8, 6, 8, 6);
    pg_layout->setSpacing(4);

    // [count]
    w.page_info = new QLabel(tr ? tr->t("common.total_rows").arg(0) : "Total 0 rows");
    w.page_info->setObjectName("pageInfo");
    pg_layout->addWidget(w.page_info);

    pg_layout->addSpacing(8);

    // [prev]
    w.page_prev_btn = new QPushButton;
    w.page_prev_btn->setIcon(QIcon(":/icons/chevron_left"));
    w.page_prev_btn->setIconSize(QSize(14, 14));
    w.page_prev_btn->setObjectName("pageBtn");
    w.page_prev_btn->setFixedSize(30, 28);
    w.page_prev_btn->setCursor(Qt::PointingHandCursor);
    w.page_prev_btn->setEnabled(false);
    pg_layout->addWidget(w.page_prev_btn);

    // [page buttons]
    w.page_btn_container = new QWidget;
    w.page_btn_container->setStyleSheet("border: none;");
    w.page_btn_layout = new QHBoxLayout(w.page_btn_container);
    w.page_btn_layout->setContentsMargins(0, 0, 0, 0);
    w.page_btn_layout->setSpacing(2);
    pg_layout->addWidget(w.page_btn_container);

    // [next]
    w.page_next_btn = new QPushButton;
    w.page_next_btn->setIcon(QIcon(":/icons/chevron_right"));
    w.page_next_btn->setIconSize(QSize(14, 14));
    w.page_next_btn->setObjectName("pageBtn");
    w.page_next_btn->setFixedSize(30, 28);
    w.page_next_btn->setCursor(Qt::PointingHandCursor);
    w.page_next_btn->setEnabled(false);
    pg_layout->addWidget(w.page_next_btn);

    pg_layout->addSpacing(8);

    // [limits]
    w.page_size_combo = new QComboBox;
    w.page_size_combo->setObjectName("pageSizeCombo");
    const int page_sizes[] = {10, 20, 30, 50, 100};
    for (int ps : page_sizes) {
        w.page_size_combo->addItem(
            tr ? tr->t("common.rows_per_page").arg(ps) : QString("%1/page").arg(ps), ps);
    }
    w.page_size_combo->setFixedHeight(IconDefs::k_page_combo_height);
    w.page_size_combo->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    w.page_size_combo->setMinimumWidth(120);
    pg_layout->addWidget(w.page_size_combo);

    pg_layout->addSpacing(4);

    // [refresh]
    w.refresh_btn = new QPushButton(QIcon(":/icons/refresh"), "");
    w.refresh_btn->setObjectName("pageBtn");
    w.refresh_btn->setFixedSize(30, 28);
    w.refresh_btn->setIconSize(QSize(14, 14));
    w.refresh_btn->setCursor(Qt::PointingHandCursor);
    w.refresh_btn->setToolTip(tr ? tr->t("common.refresh") : "Refresh");
    pg_layout->addWidget(w.refresh_btn);

    pg_layout->addSpacing(4);

    // [skip]
    w.skip_label = new QLabel(tr ? tr->t("common.goto_page") : "Go to");
    w.skip_label->setObjectName("pageInfo");
    pg_layout->addWidget(w.skip_label);

    w.skip_input = new QLineEdit;
    w.skip_input->setObjectName("skipInput");
    w.skip_input->setFixedSize(50, 28);
    w.skip_input->setAlignment(Qt::AlignCenter);
    w.skip_input->setValidator(new QIntValidator(1, 99999, w.skip_input));
    pg_layout->addWidget(w.skip_input);

    w.skip_confirm = new QPushButton(tr ? tr->t("common.confirm") : "OK");
    w.skip_confirm->setObjectName("skipConfirmBtn");
    w.skip_confirm->setFixedHeight(28);
    w.skip_confirm->setMinimumWidth(60);
    w.skip_confirm->setCursor(Qt::PointingHandCursor);
    pg_layout->addWidget(w.skip_confirm);

    pg_layout->addStretch();
    tg_layout->addWidget(w.pagination_bar);

    card_layout->addWidget(table_group, 0);
    page_layout->addWidget(w.card);
    page_layout->addStretch();

    return w;
}

void ReportPageBuilder::add_summary(
    ReportPageWidgets& w,
    const QString& summary_title_text,
    const QStringList& summary_headers,
    const QStringList& summary_defaults)
{
    // Insert summary between table group and end of card
    auto* card_layout = qobject_cast<QVBoxLayout*>(w.card->layout());
    if (!card_layout) return;

    w.summary_section = new QWidget;
    auto* sum_layout = new QVBoxLayout(w.summary_section);
    sum_layout->setContentsMargins(0, 10, 0, 0);
    sum_layout->setSpacing(6);

    w.summary_title = new QLabel(summary_title_text);
    w.summary_title->setObjectName("summaryTitle");
    sum_layout->addWidget(w.summary_title);

    int col_count = summary_headers.size();
    w.summary_table = new QTableWidget(1, col_count);
    w.summary_table->setObjectName("summaryTable");
    w.summary_table->setHorizontalHeaderLabels(summary_headers);
    w.summary_table->horizontalHeader()->setSectionResizeMode(QHeaderView::Stretch);
    w.summary_table->horizontalHeader()->setDefaultAlignment(Qt::AlignLeft | Qt::AlignVCenter);
    w.summary_table->verticalHeader()->setVisible(false);
    w.summary_table->setEditTriggers(QAbstractItemView::NoEditTriggers);
    w.summary_table->setSelectionMode(QAbstractItemView::NoSelection);
    w.summary_table->setShowGrid(true);
    w.summary_table->horizontalHeader()->setHighlightSections(false);
    w.summary_table->setMaximumHeight(70);

    for (int c = 0; c < col_count && c < summary_defaults.size(); ++c) {
        auto* item = new QTableWidgetItem(summary_defaults[c]);
        item->setTextAlignment(Qt::AlignLeft | Qt::AlignVCenter);
        w.summary_table->setItem(0, c, item);
    }
    w.summary_table->setRowHeight(0, 32);

    sum_layout->addWidget(w.summary_table);

    card_layout->addWidget(w.summary_section);
}

void ReportPageBuilder::apply_page_theme(ReportPageWidgets& w, ThemeManager* theme)
{
    const auto bg = theme->color("bg");
    const auto bg2 = theme->color("bg_secondary");
    const auto bg_hover = theme->color("bg_hover");
    const auto text1 = theme->color("text_primary");
    const auto text2 = theme->color("text_secondary");
    const auto border = theme->color("border");
    const auto border_light = theme->color("border_light");
    const auto border_box = theme->color("border_box");
    const auto primary = theme->color("primary");

    w.page->setStyleSheet(QString(
        "QWidget#reportPage { background: %1; }"
    ).arg(bg2));

    w.card->setStyleSheet(QString(
        "QWidget#reportCard { background: %1; border: 1px solid %2; }"
    ).arg(bg, border_box));

    w.title_label->setStyleSheet(QString(
        "font-size: 16px; font-weight: 700; color: %1; border: none;"
    ).arg(text1));

    // Separator
    for (auto* sep : w.card->findChildren<QWidget*>("fieldSep")) {
        sep->setStyleSheet(QString("background: %1;").arg(border_light));
    }

    // Search labels
    for (auto* lbl : w.search_labels) {
        lbl->setStyleSheet(QString(
            "font-size: 13px; color: %1; border: none;"
        ).arg(text2));
    }

    // Input style
    auto input_style = QString(
        "QLineEdit, QComboBox, QDateEdit {"
        "  background: %1; color: %2; border: 1px solid %3;"
        "  padding: 4px 8px; font-size: 13px;"
        "}"
        "QLineEdit:focus, QComboBox:focus {"
        "  border-color: %4;"
        "}"
        "QComboBox::drop-down {"
        "  subcontrol-origin: padding; subcontrol-position: center right;"
        "  width: 20px; border-left: 1px solid %3;"
        "}"
        "QComboBox::down-arrow {"
        "  image: url(:/icons/dropdown_arrow);"
        "  width: 10px; height: 10px;"
        "}"
        "QComboBox QAbstractItemView {"
        "  background: %1; color: %2; border: 1px solid %3;"
        "  selection-background-color: %5;"
        "}"
    ).arg(bg, text1, border, primary, bg_hover);

    // Apply to all inputs in search form
    for (auto* le : w.search_form->findChildren<QLineEdit*>()) {
        le->setStyleSheet(input_style);
    }
    for (auto* cb : w.search_form->findChildren<QComboBox*>()) {
        cb->setStyleSheet(input_style);
    }

    // Search/Reset buttons
    for (auto* btn : w.search_form->findChildren<QPushButton*>("searchBtn")) {
        btn->setStyleSheet(QString(
            "QPushButton { background: %1; color: #fff; border: none;"
            "  padding: 0 16px; font-size: 13px; }"
            "QPushButton:hover { background: #0d8a7e; }"
        ).arg(primary));
    }
    for (auto* btn : w.search_form->findChildren<QPushButton*>("resetBtn")) {
        btn->setStyleSheet(QString(
            "QPushButton { background: %1; color: %2; border: 1px solid %3;"
            "  padding: 0 16px; font-size: 13px; }"
            "QPushButton:hover { background: %4; }"
        ).arg(bg, text1, border, bg_hover));
    }

    // Table toolbar
    w.table_toolbar->setStyleSheet(QString(
        "QWidget#tableToolbar { background: %1;"
        "  border-top: 1px solid %2; border-left: 1px solid %2;"
        "  border-right: 1px solid %2; border-bottom: none;"
        "  padding-right: 2px; }"
    ).arg(bg2, border));

    auto tool_icon_style = QString(
        "QPushButton#toolIcon { background: transparent; border: 1px solid %1; }"
        "QPushButton#toolIcon:hover { background: %2; }"
    ).arg(border, bg_hover);
    w.filter_btn->setStyleSheet(tool_icon_style);
    w.export_btn->setStyleSheet(tool_icon_style);
    w.print_btn->setStyleSheet(tool_icon_style);

    // Table
    w.table->setStyleSheet(QString(
        "QTableWidget { background: %1; color: %2;"
        "  border-left: 1px solid %3; border-right: none;"
        "  border-top: 1px solid %3; border-bottom: none;"
        "  gridline-color: %3; font-size: 13px; }"
        "QTableWidget::item { padding: 4px 8px; }"
        "QTableWidget::item:selected { background: %4; color: %2; }"
        "QHeaderView::section { background: %5; color: %2; border: none;"
        "  border-bottom: 1px solid %3; border-right: 1px solid %3;"
        "  padding: 6px 8px; font-size: 13px; font-weight: 600; }"
        "QHeaderView::section:last { border-right: 1px solid %3; }"
    ).arg(bg, text1, border, bg_hover, bg2));

    // Pagination
    w.pagination_bar->setStyleSheet(QString(
        "QWidget#paginationBar { background: %1;"
        "  border-top: none; border-left: 1px solid %2;"
        "  border-right: 1px solid %2; border-bottom: 1px solid %2; }"
    ).arg(bg, border));

    auto page_btn_style = QString(
        "QPushButton#pageBtn { background: %1; color: %2; border: 1px solid %3;"
        "  font-size: 13px; padding: 0; }"
        "QPushButton#pageBtn:hover { background: %4; }"
        "QPushButton#pageBtn:disabled { color: %5; }"
    ).arg(bg, text1, border, bg_hover, text2);
    w.page_prev_btn->setStyleSheet(page_btn_style);
    w.page_next_btn->setStyleSheet(page_btn_style);
    w.refresh_btn->setStyleSheet(page_btn_style);

    // Active page button
    auto active_page_style = QString(
        "QPushButton#pageNumberActive { background: %1; color: #fff; border: 1px solid %1;"
        "  font-size: 13px; padding: 0; }"
    ).arg(primary);
    for (auto* btn : w.page_btn_container->findChildren<QPushButton*>("pageNumberActive")) {
        btn->setStyleSheet(active_page_style);
    }

    // Inactive page buttons
    for (auto* btn : w.page_btn_container->findChildren<QPushButton*>("pageBtn")) {
        btn->setStyleSheet(page_btn_style);
    }

    w.page_info->setStyleSheet(QString(
        "font-size: 13px; color: %1; border: none;"
    ).arg(text2));

    if (w.skip_label) {
        w.skip_label->setStyleSheet(QString(
            "font-size: 13px; color: %1; border: none;"
        ).arg(text2));
    }

    if (w.skip_input) {
        w.skip_input->setStyleSheet(QString(
            "QLineEdit { background: %1; color: %2; border: 1px solid %3;"
            "  font-size: 13px; padding: 0 4px; }"
            "QLineEdit:focus { border-color: %4; }"
        ).arg(bg, text1, border, primary));
    }

    if (w.skip_confirm) {
        w.skip_confirm->setStyleSheet(QString(
            "QPushButton#skipConfirmBtn { background: %1; color: #fff; border: 1px solid %1;"
            "  font-size: 13px; padding: 0 8px; }"
            "QPushButton#skipConfirmBtn:hover { background: #0d8a7e; }"
        ).arg(primary));
    }

    w.page_size_combo->setStyleSheet(input_style);

    // Summary
    if (w.summary_title) {
        w.summary_title->setStyleSheet(QString(
            "font-weight: bold; font-size: 13px; color: %1; border: none;"
        ).arg(text1));
    }
    if (w.summary_table) {
        w.summary_table->setStyleSheet(QString(
            "QTableWidget { background: %1; color: %2; border: 1px solid %3;"
            "  gridline-color: %3; font-size: 13px; }"
            "QTableWidget::item { padding: 4px 8px; border: none; }"
            "QHeaderView::section { background: %4; color: %2; border: none;"
            "  border-bottom: 1px solid %3; border-right: 1px solid %3;"
            "  padding: 6px 8px; font-size: 13px; font-weight: 400; }"
            "QHeaderView::section:last { border-right: 1px solid %3; }"
        ).arg(bg, text1, border, bg2));
    }
}
