#include "core/customers_page.h"
#include "core/date_range_picker.h"
#include "core/flow_layout.h"
#include "core/theme_manager.h"
#include "core/translator.h"

#include <QHBoxLayout>
#include <QVBoxLayout>
#include <QPixmap>
#include <QFileDialog>
#include <QTextStream>
#include <QPrinter>
#include <QPrintDialog>
#include <QTextDocument>
#include <QCheckBox>
#include <QDialogButtonBox>
#include <QDialog>
#include <QMessageBox>

CustomersPage::CustomersPage(ThemeManager* theme, Translator* tr, QWidget* parent)
    : QWidget(parent)
    , m_theme(theme)
    , m_tr(tr)
{
    setup_ui();
}

void CustomersPage::setup_ui()
{
    setObjectName("customersPage");

    auto* page_layout = new QVBoxLayout(this);
    page_layout->setContentsMargins(10, 10, 10, 10);
    page_layout->setSpacing(0);

    // ── Card container ──
    m_card = new QWidget;
    m_card->setObjectName("customersCard");
    auto* card_layout = new QVBoxLayout(m_card);
    card_layout->setContentsMargins(16, 16, 16, 16);
    card_layout->setSpacing(12);

    // ── Field header ──
    m_field_header = new QWidget;
    auto* header_layout = new QHBoxLayout(m_field_header);
    header_layout->setContentsMargins(0, 0, 0, 8);
    header_layout->setSpacing(6);
    header_layout->setAlignment(Qt::AlignLeft);

    auto* header_icon = new QLabel;
    QPixmap icon_pix(":/icons/customers");
    header_icon->setPixmap(icon_pix.scaled(18, 18, Qt::KeepAspectRatio, Qt::SmoothTransformation));
    header_icon->setStyleSheet("border: none;");
    header_layout->addWidget(header_icon);

    m_title = new QLabel(m_tr->t("customers.title"));
    m_title->setStyleSheet("font-size: 16px; font-weight: 700; border: none;");
    header_layout->addWidget(m_title);
    header_layout->addStretch();

    card_layout->addWidget(m_field_header);

    // ── Separator ──
    auto* separator = new QWidget;
    separator->setFixedHeight(1);
    separator->setObjectName("fieldSeparator");
    card_layout->addWidget(separator);
    card_layout->addSpacing(12);

    // ── Search form ──
    auto make_field = [this](const QString& label_text, QWidget* field) -> QWidget* {
        auto* w = new QWidget;
        w->setStyleSheet("border: none;");
        auto* h = new QHBoxLayout(w);
        h->setContentsMargins(0, 0, 0, 0);
        h->setSpacing(6);
        auto* lbl = new QLabel(label_text);
        lbl->setObjectName("searchLabel");
        m_search_labels.push_back(lbl);
        h->addWidget(lbl);
        h->addWidget(field);
        return w;
    };

    auto* form_widget = new QWidget;
    form_widget->setObjectName("searchForm");
    auto* flow = new FlowLayout(form_widget, 0, 12, 8);
    Q_UNUSED(flow);

    m_search_username = new QLineEdit;
    m_search_username->setPlaceholderText(m_tr->t("common.username_placeholder"));
    m_search_username->setFixedWidth(160);
    m_search_username->setFixedHeight(32);
    flow->addWidget(make_field(m_tr->t("common.username_label"), m_search_username));

    m_date_range_picker = new DateRangePicker;
    m_date_range_picker->set_translator(m_tr);
    m_date_range_picker->set_placeholder(
        m_tr->t("common.date_start"),
        m_tr->t("common.date_end")
    );
    flow->addWidget(make_field(m_tr->t("customers.first_deposit_date"), m_date_range_picker));

    m_search_status = new QComboBox;
    m_search_status->addItem(m_tr->t("common.select"), QVariant());
    m_search_status->addItem(m_tr->t("customers.status_unrated"), "unrated");
    m_search_status->addItem(m_tr->t("customers.status_normal"), "normal");
    m_search_status->addItem(m_tr->t("customers.status_frozen"), "frozen");
    m_search_status->addItem(m_tr->t("customers.status_locked"), "locked");
    m_search_status->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    m_search_status->setFixedHeight(32);
    flow->addWidget(make_field(m_tr->t("customers.status_label"), m_search_status));

    m_search_sort_field = new QComboBox;
    m_search_sort_field->addItem(m_tr->t("common.select"), QVariant());
    m_search_sort_field->addItem(m_tr->t("customers.sort_balance"), "balance");
    m_search_sort_field->addItem(m_tr->t("customers.sort_last_login"), "last_login");
    m_search_sort_field->addItem(m_tr->t("customers.sort_created_at"), "created_at");
    m_search_sort_field->addItem(m_tr->t("customers.sort_total_deposit"), "total_deposit");
    m_search_sort_field->addItem(m_tr->t("customers.sort_total_withdraw"), "total_withdraw");
    m_search_sort_field->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    m_search_sort_field->setFixedHeight(32);
    flow->addWidget(make_field(m_tr->t("customers.sort_field_label"), m_search_sort_field));

    m_search_sort_dir = new QComboBox;
    m_search_sort_dir->addItem(m_tr->t("customers.sort_desc"), "desc");
    m_search_sort_dir->addItem(m_tr->t("customers.sort_asc"), "asc");
    m_search_sort_dir->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    m_search_sort_dir->setFixedHeight(32);
    flow->addWidget(make_field(m_tr->t("customers.sort_dir_label"), m_search_sort_dir));

    m_search_btn = new QPushButton(QIcon(":/icons/search"), m_tr->t("common.search"));
    m_search_btn->setObjectName("searchBtn");
    m_search_btn->setCursor(Qt::PointingHandCursor);
    m_search_btn->setFixedHeight(32);
    m_search_btn->setIconSize(QSize(16, 16));
    flow->addWidget(m_search_btn);

    m_reset_btn = new QPushButton(QIcon(":/icons/refresh"), m_tr->t("common.reset"));
    m_reset_btn->setObjectName("resetBtn");
    m_reset_btn->setCursor(Qt::PointingHandCursor);
    m_reset_btn->setFixedHeight(32);
    m_reset_btn->setIconSize(QSize(16, 16));
    flow->addWidget(m_reset_btn);

    connect(m_reset_btn, &QPushButton::clicked, this, [this]() {
        m_search_username->clear();
        m_date_range_picker->clear_dates();
        m_search_status->setCurrentIndex(0);
        m_search_sort_field->setCurrentIndex(0);
        m_search_sort_dir->setCurrentIndex(0);
    });

    card_layout->addWidget(form_widget);

    // ── Table group ──
    auto* table_group = new QWidget;
    auto* tg_layout = new QVBoxLayout(table_group);
    tg_layout->setContentsMargins(0, 0, 0, 0);
    tg_layout->setSpacing(0);

    // Table toolbar
    m_table_toolbar = new QWidget;
    m_table_toolbar->setObjectName("tableToolbar");
    auto* tb_layout = new QHBoxLayout(m_table_toolbar);
    tb_layout->setContentsMargins(0, 0, 0, 0);
    tb_layout->setSpacing(0);

    auto* tb_left = new QWidget;
    auto* tb_left_layout = new QHBoxLayout(tb_left);
    tb_left_layout->setContentsMargins(8, 6, 0, 6);
    tb_left_layout->setSpacing(0);

    m_add_member_btn = new QPushButton("+ " + m_tr->t("customers.add_member"));
    m_add_member_btn->setObjectName("tbBtn");
    m_add_member_btn->setCursor(Qt::PointingHandCursor);
    m_add_member_btn->setFixedHeight(26);
    tb_left_layout->addWidget(m_add_member_btn);

    m_add_agent_btn = new QPushButton("+ " + m_tr->t("customers.add_agent"));
    m_add_agent_btn->setObjectName("tbBtn");
    m_add_agent_btn->setCursor(Qt::PointingHandCursor);
    m_add_agent_btn->setFixedHeight(26);
    tb_left_layout->addWidget(m_add_agent_btn);

    tb_left_layout->addStretch();
    tb_layout->addWidget(tb_left, 1);

    auto* tb_right = new QWidget;
    auto* tb_right_layout = new QHBoxLayout(tb_right);
    tb_right_layout->setContentsMargins(0, 6, 8, 6);
    tb_right_layout->setSpacing(4);

    auto make_tool_icon = [](const QString& icon_path, const QString& tooltip) -> QPushButton* {
        auto* btn = new QPushButton;
        btn->setObjectName("toolIcon");
        btn->setIcon(QIcon(icon_path));
        btn->setIconSize(QSize(16, 16));
        btn->setFixedSize(28, 26);
        btn->setCursor(Qt::PointingHandCursor);
        btn->setToolTip(tooltip);
        return btn;
    };

    m_filter_btn = make_tool_icon(":/icons/settings", m_tr->t("common.filter_columns"));
    m_export_btn = make_tool_icon(":/icons/report", m_tr->t("common.export_file"));
    m_print_btn = make_tool_icon(":/icons/browser", m_tr->t("common.print"));
    tb_right_layout->addWidget(m_filter_btn);
    tb_right_layout->addWidget(m_export_btn);
    tb_right_layout->addWidget(m_print_btn);

    connect(m_filter_btn, &QPushButton::clicked, this, &CustomersPage::on_filter_columns);
    connect(m_export_btn, &QPushButton::clicked, this, &CustomersPage::on_export_csv);
    connect(m_print_btn, &QPushButton::clicked, this, &CustomersPage::on_print_table);

    tb_layout->addWidget(tb_right);
    tg_layout->addWidget(m_table_toolbar);

    // ── Table ──
    m_table = new QTableWidget(0, 12);
    m_table->setObjectName("customersTable");

    const QStringList headers = {
        m_tr->t("customers.col_member"),
        m_tr->t("customers.col_member_type"),
        m_tr->t("customers.col_agent_account"),
        m_tr->t("customers.col_balance"),
        m_tr->t("customers.col_deposit_count"),
        m_tr->t("customers.col_withdraw_count"),
        m_tr->t("customers.col_total_deposit"),
        m_tr->t("customers.col_total_withdraw"),
        m_tr->t("customers.col_last_login"),
        m_tr->t("customers.col_register_time"),
        m_tr->t("customers.col_status"),
        m_tr->t("customers.col_action"),
    };
    m_table->setHorizontalHeaderLabels(headers);
    m_table->horizontalHeader()->setSectionResizeMode(QHeaderView::Stretch);
    m_table->horizontalHeader()->setDefaultAlignment(Qt::AlignLeft | Qt::AlignVCenter);
    m_table->verticalHeader()->setVisible(false);
    m_table->setSelectionBehavior(QAbstractItemView::SelectRows);
    m_table->setSelectionMode(QAbstractItemView::SingleSelection);
    m_table->setEditTriggers(QAbstractItemView::NoEditTriggers);
    m_table->setAlternatingRowColors(false);
    m_table->setShowGrid(true);
    m_table->horizontalHeader()->setHighlightSections(false);

    // Sample data
    m_table->insertRow(0);
    const QStringList sample = {
        "an10tynghichoi",
        m_tr->t("customers.type_official"),
        "vozer123",
        "0.0000", "0", "0", "0.0000", "0.0000",
        "",
        "2026-03-09 16:20:58",
        m_tr->t("customers.status_normal"),
        ""
    };
    for (int c = 0; c < 11; ++c) {
        auto* item = new QTableWidgetItem(sample[c]);
        item->setTextAlignment(Qt::AlignLeft | Qt::AlignVCenter);
        m_table->setItem(0, c, item);
    }
    auto* rebate_btn = new QPushButton(m_tr->t("customers.rebate_settings"));
    rebate_btn->setObjectName("rebateBtn");
    rebate_btn->setCursor(Qt::PointingHandCursor);
    rebate_btn->setFixedHeight(24);
    m_table->setCellWidget(0, 11, rebate_btn);
    m_table->setRowHeight(0, 38);

    tg_layout->addWidget(m_table, 1);

    // ── Pagination ──
    m_pagination_bar = new QWidget;
    m_pagination_bar->setObjectName("paginationBar");
    auto* pg_layout = new QHBoxLayout(m_pagination_bar);
    pg_layout->setContentsMargins(8, 6, 8, 6);
    pg_layout->setSpacing(8);

    m_page_prev_btn = new QPushButton("<");
    m_page_prev_btn->setObjectName("pageBtn");
    m_page_prev_btn->setFixedSize(30, 28);
    m_page_prev_btn->setEnabled(false);
    pg_layout->addWidget(m_page_prev_btn);

    m_page_number = new QLabel("1");
    m_page_number->setObjectName("pageNumber");
    m_page_number->setFixedSize(30, 28);
    m_page_number->setAlignment(Qt::AlignCenter);
    pg_layout->addWidget(m_page_number);

    m_page_next_btn = new QPushButton(">");
    m_page_next_btn->setObjectName("pageBtn");
    m_page_next_btn->setFixedSize(30, 28);
    m_page_next_btn->setEnabled(false);
    pg_layout->addWidget(m_page_next_btn);

    pg_layout->addSpacing(12);

    m_page_info = new QLabel(m_tr->t("common.total_rows").arg(1));
    m_page_info->setObjectName("pageInfo");
    pg_layout->addWidget(m_page_info);

    pg_layout->addSpacing(8);

    m_page_size_combo = new QComboBox;
    m_page_size_combo->setObjectName("pageSizeCombo");
    const int page_sizes[] = {10, 20, 30, 40, 50, 60, 70, 80, 90};
    for (int ps : page_sizes) {
        m_page_size_combo->addItem(
            m_tr->t("common.rows_per_page").arg(ps), ps);
    }
    m_page_size_combo->setFixedHeight(28);
    pg_layout->addWidget(m_page_size_combo);

    pg_layout->addStretch();
    tg_layout->addWidget(m_pagination_bar);

    card_layout->addWidget(table_group, 1);
    page_layout->addWidget(m_card, 1);
}

void CustomersPage::apply_theme()
{
    const auto bg = m_theme->color("bg");
    const auto bg2 = m_theme->color("bg_secondary");
    const auto bg_hover = m_theme->color("bg_hover");
    const auto text1 = m_theme->color("text_primary");
    const auto text2 = m_theme->color("text_secondary");
    const auto border = m_theme->color("border");
    const auto border_light = m_theme->color("border_light");
    const auto border_box = m_theme->color("border_box");
    const auto primary = m_theme->color("primary");

    setStyleSheet(QString("QWidget#customersPage { background: %1; }").arg(bg2));

    m_card->setStyleSheet(QString(
        "QWidget#customersCard { background: %1; border: 1px solid %2; }"
    ).arg(bg, border_box));

    m_title->setStyleSheet(QString(
        "font-size: 16px; font-weight: 700; color: %1; border: none;"
    ).arg(text1));

    findChild<QWidget*>("fieldSeparator")->setStyleSheet(QString(
        "background: %1;"
    ).arg(border_light));

    for (auto* lbl : m_search_labels) {
        lbl->setStyleSheet(QString(
            "font-size: 13px; color: %1; border: none;"
        ).arg(text2));
    }

    auto input_style = QString(
        "QLineEdit, QComboBox, QDateEdit {"
        "  background: %1; color: %2; border: 1px solid %3;"
        "  padding: 4px 8px; font-size: 13px;"
        "}"
        "QLineEdit:focus, QComboBox:focus, QDateEdit:focus {"
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

    m_search_username->setStyleSheet(input_style);

    m_date_range_picker->set_button_style(QString(
        "QPushButton { background: %1; color: %2;"
        "  border-style: solid; border-width: 1px; border-color: %3; border-radius: 0px;"
        "  padding: 4px 8px; font-size: 13px; text-align: left; }"
        "QPushButton:hover { border-color: %4; }"
    ).arg(bg, text1, border, primary));

    m_search_status->setStyleSheet(input_style);
    m_search_sort_field->setStyleSheet(input_style);
    m_search_sort_dir->setStyleSheet(input_style);

    m_search_btn->setStyleSheet(QString(
        "QPushButton { background: %1; color: #fff; border: none;"
        "  padding: 0 16px; font-size: 13px; }"
        "QPushButton:hover { background: #0d8a7e; }"
    ).arg(primary));

    m_reset_btn->setStyleSheet(QString(
        "QPushButton { background: %1; color: %2; border: 1px solid %3;"
        "  padding: 0 16px; font-size: 13px; }"
        "QPushButton:hover { background: %4; }"
    ).arg(bg, text1, border, bg_hover));

    m_date_range_picker->apply_popup_theme(m_theme->theme() == "dark");

    // Table toolbar
    m_table_toolbar->setStyleSheet(QString(
        "QWidget#tableToolbar { background: %1; border: 1px solid %2; border-bottom: none; }"
    ).arg(bg2, border));

    auto tb_btn_style = QString(
        "QPushButton#tbBtn { background: %1; color: #fff; border: none;"
        "  padding: 0 10px; font-size: 12px; }"
        "QPushButton#tbBtn:hover { background: #0d8a7e; }"
    ).arg(primary);
    m_add_member_btn->setStyleSheet(tb_btn_style);
    m_add_agent_btn->setStyleSheet(tb_btn_style);

    auto tool_icon_style = QString(
        "QPushButton#toolIcon { background: transparent; border: 1px solid %1; }"
        "QPushButton#toolIcon:hover { background: %2; }"
    ).arg(border, bg_hover);
    for (auto* btn : m_table_toolbar->findChildren<QPushButton*>("toolIcon")) {
        btn->setStyleSheet(tool_icon_style);
    }

    // Table
    m_table->setStyleSheet(QString(
        "QTableWidget { background: %1; color: %2; border: 1px solid %3;"
        "  gridline-color: %3; font-size: 13px; }"
        "QTableWidget::item { padding: 4px 8px; border: none; }"
        "QTableWidget::item:selected { background: %4; color: %2; }"
        "QHeaderView::section { background: %5; color: %2; border: none;"
        "  border-bottom: 1px solid %3; border-right: 1px solid %3;"
        "  padding: 6px 8px; font-size: 13px; font-weight: 600; }"
        "QHeaderView::section:last { border-right: none; }"
    ).arg(bg, text1, border, bg_hover, bg2));

    for (int r = 0; r < m_table->rowCount(); ++r) {
        if (auto* w = m_table->cellWidget(r, 11)) {
            w->setStyleSheet(QString(
                "QPushButton { background: %1; color: #fff; border: none;"
                "  padding: 2px 8px; font-size: 11px; }"
                "QPushButton:hover { background: #0d8a7e; }"
            ).arg(primary));
        }
    }

    // Pagination
    m_pagination_bar->setStyleSheet(QString(
        "QWidget#paginationBar { background: %1; border: 1px solid %2; border-top: none; }"
    ).arg(bg, border));

    auto page_btn_style = QString(
        "QPushButton#pageBtn { background: %1; color: %2; border: 1px solid %3;"
        "  font-size: 13px; padding: 0; }"
        "QPushButton#pageBtn:hover { background: %4; }"
        "QPushButton#pageBtn:disabled { color: %5; }"
    ).arg(bg, text1, border, bg_hover, text2);
    m_page_prev_btn->setStyleSheet(page_btn_style);
    m_page_next_btn->setStyleSheet(page_btn_style);

    m_page_number->setStyleSheet(QString(
        "QLabel#pageNumber { background: %1; color: #fff; border: 1px solid %1;"
        "  font-size: 13px; padding: 0; qproperty-alignment: 'AlignCenter'; }"
    ).arg(primary));

    m_page_info->setStyleSheet(QString(
        "font-size: 13px; color: %1; border: none;"
    ).arg(text2));

    m_page_size_combo->setStyleSheet(input_style);
}

void CustomersPage::on_filter_columns()
{
    QDialog dlg(this);
    dlg.setWindowTitle(m_tr->t("common.filter_columns"));
    dlg.setMinimumWidth(250);

    auto* layout = new QVBoxLayout(&dlg);
    QVector<QCheckBox*> checks;

    for (int i = 0; i < m_table->columnCount(); ++i) {
        auto* cb = new QCheckBox(m_table->horizontalHeaderItem(i)->text());
        cb->setChecked(!m_table->isColumnHidden(i));
        layout->addWidget(cb);
        checks.append(cb);
    }

    auto* buttons = new QDialogButtonBox(QDialogButtonBox::Ok | QDialogButtonBox::Cancel);
    layout->addWidget(buttons);
    connect(buttons, &QDialogButtonBox::accepted, &dlg, &QDialog::accept);
    connect(buttons, &QDialogButtonBox::rejected, &dlg, &QDialog::reject);

    if (dlg.exec() == QDialog::Accepted) {
        for (int i = 0; i < checks.size(); ++i) {
            m_table->setColumnHidden(i, !checks[i]->isChecked());
        }
    }
}

void CustomersPage::on_export_csv()
{
    QString path = QFileDialog::getSaveFileName(
        this, m_tr->t("common.export_csv"), "customers.csv",
        "CSV (*.csv);;All Files (*)");
    if (path.isEmpty()) return;

    QFile file(path);
    if (!file.open(QIODevice::WriteOnly | QIODevice::Text)) {
        QMessageBox::warning(this, m_tr->t("common.export_file"),
            m_tr->t("common.export_error").arg(path));
        return;
    }

    QTextStream out(&file);
    int cols = m_table->columnCount();
    int rows = m_table->rowCount();

    QStringList header_parts;
    for (int c = 0; c < cols; ++c) {
        if (!m_table->isColumnHidden(c)) {
            QString h = m_table->horizontalHeaderItem(c)->text();
            h.replace("\"", "\"\"");
            header_parts << "\"" + h + "\"";
        }
    }
    out << header_parts.join(",") << "\n";

    for (int r = 0; r < rows; ++r) {
        QStringList row_parts;
        for (int c = 0; c < cols; ++c) {
            if (m_table->isColumnHidden(c)) continue;
            QString val;
            if (auto* item = m_table->item(r, c)) {
                val = item->text();
            } else if (auto* w = m_table->cellWidget(r, c)) {
                if (auto* btn = qobject_cast<QPushButton*>(w))
                    val = btn->text();
            }
            val.replace("\"", "\"\"");
            row_parts << "\"" + val + "\"";
        }
        out << row_parts.join(",") << "\n";
    }

    file.close();
    QMessageBox::information(this, m_tr->t("common.export_success"),
        m_tr->t("common.export_done").arg(path));
}

void CustomersPage::on_print_table()
{
    QPrinter printer(QPrinter::HighResolution);
    QPrintDialog dlg(&printer, this);
    dlg.setWindowTitle(m_tr->t("common.print_table"));
    if (dlg.exec() != QDialog::Accepted) return;

    int cols = m_table->columnCount();
    int rows = m_table->rowCount();

    QString html = "<html><head><style>"
        "table { border-collapse: collapse; width: 100%; font-size: 12px; }"
        "th, td { border: 1px solid #ccc; padding: 6px 8px; text-align: left; }"
        "th { background: #f0f0f0; font-weight: bold; }"
        "</style></head><body>";
    html += "<h3>" + m_tr->t("customers.title") + "</h3>";
    html += "<table><tr>";

    for (int c = 0; c < cols; ++c) {
        if (!m_table->isColumnHidden(c)) {
            html += "<th>" + m_table->horizontalHeaderItem(c)->text() + "</th>";
        }
    }
    html += "</tr>";

    for (int r = 0; r < rows; ++r) {
        html += "<tr>";
        for (int c = 0; c < cols; ++c) {
            if (m_table->isColumnHidden(c)) continue;
            QString val;
            if (auto* item = m_table->item(r, c))
                val = item->text();
            html += "<td>" + val + "</td>";
        }
        html += "</tr>";
    }
    html += "</table></body></html>";

    QTextDocument doc;
    doc.setHtml(html);
    doc.print(&printer);
}

void CustomersPage::retranslate()
{
    m_title->setText(m_tr->t("customers.title"));

    // Search labels
    if (m_search_labels.size() >= 5) {
        m_search_labels[0]->setText(m_tr->t("common.username_label"));
        m_search_labels[1]->setText(m_tr->t("customers.first_deposit_date"));
        m_search_labels[2]->setText(m_tr->t("customers.status_label"));
        m_search_labels[3]->setText(m_tr->t("customers.sort_field_label"));
        m_search_labels[4]->setText(m_tr->t("customers.sort_dir_label"));
    }

    m_search_username->setPlaceholderText(m_tr->t("common.username_placeholder"));
    m_date_range_picker->set_placeholder(m_tr->t("common.date_start"), m_tr->t("common.date_end"));

    // Status combo
    m_search_status->setItemText(0, m_tr->t("common.select"));
    m_search_status->setItemText(1, m_tr->t("customers.status_unrated"));
    m_search_status->setItemText(2, m_tr->t("customers.status_normal"));
    m_search_status->setItemText(3, m_tr->t("customers.status_frozen"));
    m_search_status->setItemText(4, m_tr->t("customers.status_locked"));

    // Sort field combo
    m_search_sort_field->setItemText(0, m_tr->t("common.select"));
    m_search_sort_field->setItemText(1, m_tr->t("customers.sort_balance"));
    m_search_sort_field->setItemText(2, m_tr->t("customers.sort_last_login"));
    m_search_sort_field->setItemText(3, m_tr->t("customers.sort_created_at"));
    m_search_sort_field->setItemText(4, m_tr->t("customers.sort_total_deposit"));
    m_search_sort_field->setItemText(5, m_tr->t("customers.sort_total_withdraw"));

    // Sort dir combo
    m_search_sort_dir->setItemText(0, m_tr->t("customers.sort_desc"));
    m_search_sort_dir->setItemText(1, m_tr->t("customers.sort_asc"));

    // Buttons
    m_search_btn->setText(m_tr->t("common.search"));
    m_reset_btn->setText(m_tr->t("common.reset"));
    m_add_member_btn->setText("+ " + m_tr->t("customers.add_member"));
    m_add_agent_btn->setText("+ " + m_tr->t("customers.add_agent"));

    // Toolbar tooltips
    m_filter_btn->setToolTip(m_tr->t("common.filter_columns"));
    m_export_btn->setToolTip(m_tr->t("common.export_file"));
    m_print_btn->setToolTip(m_tr->t("common.print"));

    // Table headers
    m_table->setHorizontalHeaderLabels({
        m_tr->t("customers.col_member"), m_tr->t("customers.col_member_type"),
        m_tr->t("customers.col_agent_account"), m_tr->t("customers.col_balance"),
        m_tr->t("customers.col_deposit_count"), m_tr->t("customers.col_withdraw_count"),
        m_tr->t("customers.col_total_deposit"), m_tr->t("customers.col_total_withdraw"),
        m_tr->t("customers.col_last_login"), m_tr->t("customers.col_register_time"),
        m_tr->t("customers.col_status"), m_tr->t("customers.col_action"),
    });

    // Pagination
    m_page_info->setText(m_tr->t("common.total_rows").arg(m_table->rowCount()));
    const int page_sizes[] = {10, 20, 30, 40, 50, 60, 70, 80, 90};
    for (int i = 0; i < 9 && i < m_page_size_combo->count(); ++i)
        m_page_size_combo->setItemText(i, m_tr->t("common.rows_per_page").arg(page_sizes[i]));

    // Date picker popup
    m_date_range_picker->set_translator(m_tr);
}
