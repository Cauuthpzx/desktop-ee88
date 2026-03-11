#include "core/customers_page.h"
#include "core/api_client.h"
#include "core/upstream_client.h"
#include "core/date_range_picker.h"
#include "core/flow_layout.h"
#include "core/theme_manager.h"
#include "core/translator.h"
#include "core/icon_defs.h"
#include "utils/upstream_translate.h"

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
#include <QJsonArray>
#include <QJsonObject>
#include <QUrlQuery>

CustomersPage::CustomersPage(ApiClient* api, UpstreamClient* upstream, ThemeManager* theme, Translator* tr, QWidget* parent)
    : QWidget(parent)
    , m_api(api)
    , m_upstream(upstream)
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
    separator->setFixedHeight(IconDefs::k_separator_height);
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
    m_search_username->setFixedHeight(IconDefs::k_input_height);
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
    m_search_status->setFixedHeight(IconDefs::k_input_height);
    flow->addWidget(make_field(m_tr->t("customers.status_label"), m_search_status));

    m_search_sort_field = new QComboBox;
    m_search_sort_field->addItem(m_tr->t("common.select"), QVariant());
    m_search_sort_field->addItem(m_tr->t("customers.sort_balance"), "balance");
    m_search_sort_field->addItem(m_tr->t("customers.sort_last_login"), "last_login");
    m_search_sort_field->addItem(m_tr->t("customers.sort_created_at"), "created_at");
    m_search_sort_field->addItem(m_tr->t("customers.sort_total_deposit"), "total_deposit");
    m_search_sort_field->addItem(m_tr->t("customers.sort_total_withdraw"), "total_withdraw");
    m_search_sort_field->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    m_search_sort_field->setFixedHeight(IconDefs::k_input_height);
    flow->addWidget(make_field(m_tr->t("customers.sort_field_label"), m_search_sort_field));

    m_search_sort_dir = new QComboBox;
    m_search_sort_dir->addItem(m_tr->t("customers.sort_desc"), "desc");
    m_search_sort_dir->addItem(m_tr->t("customers.sort_asc"), "asc");
    m_search_sort_dir->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    m_search_sort_dir->setFixedHeight(IconDefs::k_input_height);
    flow->addWidget(make_field(m_tr->t("customers.sort_dir_label"), m_search_sort_dir));

    m_search_btn = new QPushButton(QIcon(":/icons/search"), m_tr->t("common.search"));
    m_search_btn->setObjectName("searchBtn");
    m_search_btn->setCursor(Qt::PointingHandCursor);
    m_search_btn->setFixedHeight(IconDefs::k_search_btn_height);
    m_search_btn->setIconSize(IconDefs::search_icon());
    flow->addWidget(m_search_btn);

    m_reset_btn = new QPushButton(QIcon(":/icons/refresh"), m_tr->t("common.reset"));
    m_reset_btn->setObjectName("resetBtn");
    m_reset_btn->setCursor(Qt::PointingHandCursor);
    m_reset_btn->setFixedHeight(IconDefs::k_search_btn_height);
    m_reset_btn->setIconSize(IconDefs::search_icon());
    flow->addWidget(m_reset_btn);

    connect(m_search_btn, &QPushButton::clicked, this, [this]() {
        m_current_page = 1;
        fetch_customers();
    });

    connect(m_reset_btn, &QPushButton::clicked, this, [this]() {
        m_search_username->clear();
        m_date_range_picker->clear_dates();
        m_search_status->setCurrentIndex(0);
        m_search_sort_field->setCurrentIndex(0);
        m_search_sort_dir->setCurrentIndex(0);
        m_current_page = 1;
        fetch_customers();
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
    m_add_member_btn->setFixedHeight(IconDefs::k_toolbar_btn_height);
    tb_left_layout->addWidget(m_add_member_btn);

    m_add_agent_btn = new QPushButton("+ " + m_tr->t("customers.add_agent"));
    m_add_agent_btn->setObjectName("tbBtn");
    m_add_agent_btn->setCursor(Qt::PointingHandCursor);
    m_add_agent_btn->setFixedHeight(IconDefs::k_toolbar_btn_height);
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
        btn->setIconSize(IconDefs::search_icon());
        btn->setFixedSize(28, IconDefs::k_toolbar_btn_height);
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

    m_table->setFrameShape(QFrame::NoFrame);
    m_table->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Minimum);
    m_table->setVerticalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
    tg_layout->addWidget(m_table, 0);

    // ── Pagination — layout: count | prev | page | next | limits | refresh | skip ──
    m_pagination_bar = new QWidget;
    m_pagination_bar->setObjectName("paginationBar");
    auto* pg_layout = new QHBoxLayout(m_pagination_bar);
    pg_layout->setContentsMargins(8, 6, 8, 6);
    pg_layout->setSpacing(4);

    // [count]
    m_page_info = new QLabel(m_tr->t("common.total_rows").arg(0));
    m_page_info->setObjectName("pageInfo");
    pg_layout->addWidget(m_page_info);

    pg_layout->addSpacing(8);

    // [prev]
    m_page_prev_btn = new QPushButton;
    m_page_prev_btn->setIcon(QIcon(":/icons/chevron_left"));
    m_page_prev_btn->setIconSize(QSize(14, 14));
    m_page_prev_btn->setObjectName("pageBtn");
    m_page_prev_btn->setFixedSize(30, 28);
    m_page_prev_btn->setCursor(Qt::PointingHandCursor);
    m_page_prev_btn->setEnabled(false);
    pg_layout->addWidget(m_page_prev_btn);

    // [page] — page number buttons
    m_page_btn_container = new QWidget;
    m_page_btn_container->setStyleSheet("border: none;");
    m_page_btn_layout = new QHBoxLayout(m_page_btn_container);
    m_page_btn_layout->setContentsMargins(0, 0, 0, 0);
    m_page_btn_layout->setSpacing(2);
    pg_layout->addWidget(m_page_btn_container);

    // [next]
    m_page_next_btn = new QPushButton;
    m_page_next_btn->setIcon(QIcon(":/icons/chevron_right"));
    m_page_next_btn->setIconSize(QSize(14, 14));
    m_page_next_btn->setObjectName("pageBtn");
    m_page_next_btn->setFixedSize(30, 28);
    m_page_next_btn->setCursor(Qt::PointingHandCursor);
    m_page_next_btn->setEnabled(false);
    pg_layout->addWidget(m_page_next_btn);

    pg_layout->addSpacing(8);

    // [limits] — page size combo
    m_page_size_combo = new QComboBox;
    m_page_size_combo->setObjectName("pageSizeCombo");
    const int page_sizes[] = {10, 20, 30, 50, 100};
    for (int ps : page_sizes) {
        m_page_size_combo->addItem(
            m_tr->t("common.rows_per_page").arg(ps), ps);
    }
    m_page_size_combo->setFixedHeight(IconDefs::k_page_combo_height);
    m_page_size_combo->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    m_page_size_combo->setMinimumWidth(120);
    pg_layout->addWidget(m_page_size_combo);

    pg_layout->addSpacing(4);

    // [refresh]
    m_refresh_btn = new QPushButton(QIcon(":/icons/refresh"), "");
    m_refresh_btn->setObjectName("pageBtn");
    m_refresh_btn->setFixedSize(30, 28);
    m_refresh_btn->setIconSize(QSize(14, 14));
    m_refresh_btn->setCursor(Qt::PointingHandCursor);
    m_refresh_btn->setToolTip(m_tr->t("common.refresh"));
    pg_layout->addWidget(m_refresh_btn);

    pg_layout->addSpacing(4);

    // [skip] — go to page input
    m_skip_label = new QLabel(m_tr->t("common.goto_page"));
    m_skip_label->setObjectName("pageInfo");
    pg_layout->addWidget(m_skip_label);

    m_skip_input = new QLineEdit;
    m_skip_input->setObjectName("skipInput");
    m_skip_input->setFixedSize(50, 28);
    m_skip_input->setAlignment(Qt::AlignCenter);
    m_skip_input->setValidator(new QIntValidator(1, 99999, this));
    pg_layout->addWidget(m_skip_input);

    m_skip_confirm = new QPushButton(m_tr->t("common.confirm"));
    m_skip_confirm->setObjectName("skipConfirmBtn");
    m_skip_confirm->setFixedHeight(28);
    m_skip_confirm->setMinimumWidth(60);
    m_skip_confirm->setCursor(Qt::PointingHandCursor);
    pg_layout->addWidget(m_skip_confirm);

    pg_layout->addStretch();
    tg_layout->addWidget(m_pagination_bar);

    // Pagination signals
    connect(m_page_prev_btn, &QPushButton::clicked, this, [this]() {
        if (m_current_page > 1) {
            --m_current_page;
            fetch_customers();
        }
    });

    connect(m_page_next_btn, &QPushButton::clicked, this, [this]() {
        int max_page = (m_total + m_page_size - 1) / m_page_size;
        if (m_current_page < max_page) {
            ++m_current_page;
            fetch_customers();
        }
    });

    connect(m_refresh_btn, &QPushButton::clicked, this, [this]() {
        fetch_customers();
    });

    connect(m_page_size_combo, QOverload<int>::of(&QComboBox::currentIndexChanged), this, [this](int idx) {
        m_page_size = m_page_size_combo->itemData(idx).toInt();
        m_current_page = 1;
        fetch_customers();
    });

    connect(m_skip_confirm, &QPushButton::clicked, this, [this]() {
        int page = m_skip_input->text().toInt();
        int max_page = (m_total + m_page_size - 1) / m_page_size;
        if (max_page < 1) max_page = 1;
        if (page >= 1 && page <= max_page) {
            m_current_page = page;
            fetch_customers();
        }
        m_skip_input->clear();
    });

    connect(m_skip_input, &QLineEdit::returnPressed, m_skip_confirm, &QPushButton::click);

    card_layout->addWidget(table_group, 0);
    page_layout->addWidget(m_card);
    page_layout->addStretch();
}

void CustomersPage::load_data()
{
    m_ready = true;
    if (m_table->rowCount() == 0 && m_total == 0)
        fetch_customers();
}

void CustomersPage::fetch_customers()
{
    if (!m_ready || m_api->token().isEmpty())
        return;

    QMap<QString, QString> params;

    auto username = m_search_username->text().trimmed();
    if (!username.isEmpty())
        params["username"] = username;

    auto status_data = m_search_status->currentData().toString();
    if (!status_data.isEmpty())
        params["status"] = status_data;

    // sort_field, sort_dir — upstream hỗ trợ qua user_type
    auto sort_field = m_search_sort_field->currentData().toString();
    if (!sort_field.isEmpty())
        params["sort_field"] = sort_field;

    auto sort_dir = m_search_sort_dir->currentData().toString();
    if (!sort_dir.isEmpty())
        params["sort_dir"] = sort_dir;

    m_search_btn->setEnabled(false);
    m_search_btn->setText(m_tr->t("common.loading"));

    m_upstream->fetch_all("/agent/user.html", params, m_current_page, m_page_size,
        [this](const MergedResult& result) {
            m_search_btn->setEnabled(true);
            m_search_btn->setText(m_tr->t("common.search"));
            populate_table(result.data, result.total);
        });
}

void CustomersPage::populate_table(const QJsonArray& data, int total)
{
    m_total = total;
    m_table->setRowCount(0);

    for (int i = 0; i < data.size(); ++i) {
        auto obj = data[i].toObject();
        int row = m_table->rowCount();
        m_table->insertRow(row);

        const QStringList cells = {
            obj["username"].toString(),
            UpstreamTranslate::zh_to_vi(obj["type_format"].toString()),
            obj["parent_user"].toString(),
            obj["money"].toString(),
            QString::number(obj["deposit_count"].toInt()),
            QString::number(obj["withdrawal_count"].toInt()),
            obj["deposit_amount"].toString(),
            obj["withdrawal_amount"].toString(),
            obj["login_time"].toString(),
            obj["register_time"].toString(),
        };

        for (int c = 0; c < cells.size(); ++c) {
            auto* item = new QTableWidgetItem(cells[c]);
            item->setTextAlignment(Qt::AlignLeft | Qt::AlignVCenter);
            m_table->setItem(row, c, item);
        }

        // Status column (col 10) — colored text
        int status_col = 10;
        QString status_raw = obj["status_format"].toString();
        QString status_text = UpstreamTranslate::zh_to_vi(status_raw);
        auto* status_label = new QLabel(status_text);
        status_label->setAlignment(Qt::AlignCenter);
        QColor sc = UpstreamTranslate::status_color(status_text);
        if (sc.isValid()) {
            status_label->setStyleSheet(QString(
                "QLabel { color: %1; font-size: 12px; font-weight: 600;"
                "  background: %2; border: none; padding: 2px 8px; }"
            ).arg(sc.name(), sc.name() + "1a")); // 1a = ~10% opacity bg
        } else {
            status_label->setStyleSheet("QLabel { font-size: 12px; border: none; padding: 2px 8px; }");
        }
        m_table->setCellWidget(row, status_col, status_label);

        // Action column (col 11) — "Cài đặt hoàn trả" button
        int action_col = 11;
        auto* rebate_btn = new QPushButton(m_tr->t("customers.rebate_settings"));
        rebate_btn->setObjectName("rebateBtn");
        rebate_btn->setCursor(Qt::PointingHandCursor);
        rebate_btn->setFixedHeight(24);
        rebate_btn->setStyleSheet(QString(
            "QPushButton { background: %1; color: #fff; border: none;"
            "  padding: 2px 8px; font-size: 11px; }"
            "QPushButton:hover { background: #0d8a7e; }"
        ).arg(m_theme->color("primary")));
        m_table->setCellWidget(row, action_col, rebate_btn);

        m_table->setRowHeight(row, 38);
    }

    // Resize table to fit rows
    int table_height = m_table->horizontalHeader()->height();
    for (int r = 0; r < m_table->rowCount(); ++r)
        table_height += m_table->rowHeight(r);
    table_height += 1; // border-top only
    m_table->setFixedHeight(table_height);

    // Update pagination UI
    int max_page = (m_total + m_page_size - 1) / m_page_size;
    if (max_page < 1) max_page = 1;

    m_page_prev_btn->setEnabled(m_current_page > 1);
    m_page_next_btn->setEnabled(m_current_page < max_page);
    m_page_info->setText(m_tr->t("common.total_rows").arg(m_total));

    // Rebuild page number buttons
    rebuild_page_buttons(max_page);

    // Re-apply theme for new rows
    apply_theme();
}

void CustomersPage::rebuild_page_buttons(int max_page)
{
    // Clear old buttons
    QLayoutItem* child;
    while ((child = m_page_btn_layout->takeAt(0)) != nullptr) {
        delete child->widget();
        delete child;
    }

    // Show max 7 page buttons with ellipsis
    auto add_page_btn = [this](int page, bool active) {
        auto* btn = new QPushButton(QString::number(page));
        btn->setObjectName(active ? "pageNumberActive" : "pageBtn");
        int digits = QString::number(page).length();
        int width = (digits <= 1) ? 30 : (digits == 2) ? 35 : (digits == 3) ? 40 : 45;
        btn->setFixedSize(width, 28);
        btn->setCursor(Qt::PointingHandCursor);
        if (!active) {
            connect(btn, &QPushButton::clicked, this, [this, page]() {
                m_current_page = page;
                fetch_customers();
            });
        }
        m_page_btn_layout->addWidget(btn);
    };

    auto add_ellipsis = [this]() {
        auto* lbl = new QLabel("...");
        lbl->setObjectName("pageInfo");
        lbl->setFixedSize(20, 28);
        lbl->setAlignment(Qt::AlignCenter);
        m_page_btn_layout->addWidget(lbl);
    };

    if (max_page <= 7) {
        for (int i = 1; i <= max_page; ++i)
            add_page_btn(i, i == m_current_page);
    } else {
        // Always show first page
        add_page_btn(1, m_current_page == 1);

        if (m_current_page > 4)
            add_ellipsis();

        int start = std::max(2, m_current_page - 2);
        int end = std::min(max_page - 1, m_current_page + 2);

        // Adjust range to show at least 5 middle pages
        if (m_current_page <= 4)
            end = std::min(max_page - 1, 6);
        if (m_current_page >= max_page - 3)
            start = std::max(2, max_page - 5);

        for (int i = start; i <= end; ++i)
            add_page_btn(i, i == m_current_page);

        if (m_current_page < max_page - 3)
            add_ellipsis();

        // Always show last page
        add_page_btn(max_page, m_current_page == max_page);
    }

    apply_theme();
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
        "QWidget#tableToolbar { background: %1;"
        "  border-top: 1px solid %2; border-left: 1px solid %2;"
        "  border-right: 1px solid %2; border-bottom: none;"
        "  padding-right: 2px; }"
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

    for (int r = 0; r < m_table->rowCount(); ++r) {
        // Re-style action buttons
        if (auto* w = m_table->cellWidget(r, 11)) {
            if (auto* btn = qobject_cast<QPushButton*>(w)) {
                btn->setStyleSheet(QString(
                    "QPushButton { background: %1; color: #fff; border: none;"
                    "  padding: 2px 8px; font-size: 11px; }"
                    "QPushButton:hover { background: #0d8a7e; }"
                ).arg(primary));
            }
        }
        // Re-style status labels
        if (auto* w = m_table->cellWidget(r, 10)) {
            if (auto* lbl = qobject_cast<QLabel*>(w)) {
                QString status_text = lbl->text();
                QColor sc = UpstreamTranslate::status_color(status_text);
                if (sc.isValid()) {
                    lbl->setStyleSheet(QString(
                        "QLabel { color: %1; font-size: 12px; font-weight: 600;"
                        "  background: %2; border: none; padding: 2px 8px; }"
                    ).arg(sc.name(), sc.name() + "1a"));
                }
            }
        }
    }

    // Pagination
    m_pagination_bar->setStyleSheet(QString(
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
    m_page_prev_btn->setStyleSheet(page_btn_style);
    m_page_next_btn->setStyleSheet(page_btn_style);
    m_refresh_btn->setStyleSheet(page_btn_style);

    auto skip_confirm_style = QString(
        "QPushButton#skipConfirmBtn { background: %1; color: #fff; border: 1px solid %1;"
        "  font-size: 13px; padding: 0 8px; }"
        "QPushButton#skipConfirmBtn:hover { background: #0d8a7e; }"
    ).arg(primary);
    m_skip_confirm->setStyleSheet(skip_confirm_style);

    // Active page button
    auto active_page_style = QString(
        "QPushButton#pageNumberActive { background: %1; color: #fff; border: 1px solid %1;"
        "  font-size: 13px; padding: 0; }"
    ).arg(primary);
    for (auto* btn : m_page_btn_container->findChildren<QPushButton*>("pageNumberActive")) {
        btn->setStyleSheet(active_page_style);
    }
    for (auto* btn : m_page_btn_container->findChildren<QPushButton*>("pageBtn")) {
        btn->setStyleSheet(page_btn_style);
    }

    m_page_info->setStyleSheet(QString(
        "font-size: 13px; color: %1; border: none;"
    ).arg(text2));

    m_skip_label->setStyleSheet(QString(
        "font-size: 13px; color: %1; border: none;"
    ).arg(text2));

    m_skip_input->setStyleSheet(QString(
        "QLineEdit { background: %1; color: %2; border: 1px solid %3;"
        "  padding: 2px 4px; font-size: 13px; }"
        "QLineEdit:focus { border-color: %4; }"
    ).arg(bg, text1, border, primary));

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
    });

    // Pagination
    m_page_info->setText(m_tr->t("common.total_rows").arg(m_total));
    m_refresh_btn->setToolTip(m_tr->t("common.refresh"));
    m_skip_label->setText(m_tr->t("common.goto_page"));
    m_skip_confirm->setText(m_tr->t("common.confirm"));
    const int page_sizes[] = {10, 20, 30, 50, 100};
    for (int i = 0; i < 5 && i < m_page_size_combo->count(); ++i)
        m_page_size_combo->setItemText(i, m_tr->t("common.rows_per_page").arg(page_sizes[i]));

    // Date picker popup
    m_date_range_picker->set_translator(m_tr);
}
