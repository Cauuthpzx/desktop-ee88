#include "core/report_pages.h"
#include "core/api_client.h"
#include "core/upstream_client.h"
#include "core/date_range_picker.h"
#include "core/flow_layout.h"
#include "core/loading_overlay.h"
#include "core/theme_manager.h"
#include "core/translator.h"
#include "core/report_page_builder.h"
#include "core/icon_defs.h"
#include "utils/upstream_translate.h"

#include <QLabel>
#include <QLineEdit>
#include <QJsonArray>
#include <QJsonObject>
#include <QDate>
#include <QIntValidator>
#include <algorithm>

static QPushButton* make_search_button(const QString& icon_path, const QString& text, const QString& obj_name)
{
    auto* btn = new QPushButton(QIcon(icon_path), text);
    btn->setObjectName(obj_name);
    btn->setCursor(Qt::PointingHandCursor);
    btn->setFixedHeight(IconDefs::k_search_btn_height);
    btn->setIconSize(IconDefs::search_icon());
    return btn;
}

static QComboBox* make_quick_date_combo(Translator* tr, bool only_today_yesterday = false)
{
    auto* combo = new QComboBox;
    combo->addItem(tr->t("common.today"), "today");
    combo->addItem(tr->t("common.yesterday"), "yesterday");
    if (!only_today_yesterday) {
        combo->addItem(tr->t("common.this_week"), "thisWeek");
        combo->addItem(tr->t("common.this_month"), "thisMonth");
        combo->addItem(tr->t("common.last_month"), "lastMonth");
    }
    combo->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    combo->setFixedHeight(IconDefs::k_input_height);
    return combo;
}

ReportPages::ReportPages(ApiClient* api, UpstreamClient* upstream, ThemeManager* theme, Translator* tr, QObject* parent)
    : QObject(parent)
    , m_api(api)
    , m_upstream(upstream)
    , m_theme(theme)
    , m_tr(tr)
{
}

// ─── Helper: get date strings from picker ───

QString ReportPages::get_start_date(int picker_index) const
{
    if (!m_date_pickers[picker_index]) return {};
    auto d = m_date_pickers[picker_index]->start_date();
    return d.isValid() ? d.toString("yyyy-MM-dd") : QString();
}

int ReportPages::page_index_of(const ReportPageWidgets& w) const
{
    const std::array<const ReportPageWidgets*, k_page_count> pages = {
        &m_lottery_report, &m_transaction_log, &m_provider_report,
        &m_lottery_bets, &m_provider_bets, &m_withdrawal_history,
        &m_deposit_history
    };
    for (int i = 0; i < k_page_count; ++i) {
        if (pages[i]->page == w.page) return i;
    }
    return -1;
}

QString ReportPages::get_end_date(int picker_index) const
{
    if (!m_date_pickers[picker_index]) return {};
    auto d = m_date_pickers[picker_index]->end_date();
    return d.isValid() ? d.toString("yyyy-MM-dd") : QString();
}

void ReportPages::apply_quick_date(int picker_index, int combo_index)
{
    if (!m_quick_date_combos[combo_index] || !m_date_pickers[picker_index]) return;

    connect(m_quick_date_combos[combo_index], QOverload<int>::of(&QComboBox::currentIndexChanged),
            this, [this, picker_index, combo_index](int) {
        auto key = m_quick_date_combos[combo_index]->currentData().toString();
        QDate start, end;
        auto today = QDate::currentDate();
        if (key == "today") {
            start = end = today;
        } else if (key == "yesterday") {
            start = end = today.addDays(-1);
        } else if (key == "thisWeek") {
            start = today.addDays(-(today.dayOfWeek() - 1));
            end = today;
        } else if (key == "thisMonth") {
            start = QDate(today.year(), today.month(), 1);
            end = today;
        } else if (key == "lastMonth") {
            auto last = today.addMonths(-1);
            start = QDate(last.year(), last.month(), 1);
            end = QDate(last.year(), last.month(), last.daysInMonth());
        }
        if (start.isValid()) {
            m_date_pickers[picker_index]->clear_dates();
            // DateRangePicker will be set via its API
            // For now we store the dates by re-creating the picker state
        }
    });
}

// ─── Generic pagination helpers ───

void ReportPages::update_pagination(ReportPageWidgets& w, int current_page,
                                     int page_size, int total)
{
    int max_page = (total + page_size - 1) / page_size;
    if (max_page < 1) max_page = 1;

    w.page_prev_btn->setEnabled(current_page > 1);
    w.page_next_btn->setEnabled(current_page < max_page);
    w.page_info->setText(m_tr->t("common.total_rows").arg(total));

    // Find page index to get fetch_fn
    int idx = page_index_of(w);
    auto fetch_fn = (idx >= 0 && idx < k_page_count) ? m_fetch_fns[idx] : nullptr;

    // Rebuild page number buttons
    rebuild_page_buttons(w, current_page, max_page, fetch_fn);
}

void ReportPages::rebuild_page_buttons(ReportPageWidgets& w, int current_page,
                                        int max_page,
                                        std::function<void()> fetch_fn)
{
    // Clear old buttons
    QLayoutItem* child;
    while ((child = w.page_btn_layout->takeAt(0)) != nullptr) {
        delete child->widget();
        delete child;
    }

    auto add_page_btn = [&](int page, bool active) {
        auto* btn = new QPushButton(QString::number(page));
        btn->setObjectName(active ? "pageNumberActive" : "pageBtn");
        int digits = QString::number(page).length();
        int width = (digits <= 1) ? 30 : (digits == 2) ? 35 : (digits == 3) ? 40 : 45;
        btn->setFixedSize(width, 28);
        btn->setCursor(Qt::PointingHandCursor);
        int page_idx = page_index_of(w);
        if (!active && fetch_fn) {
            connect(btn, &QPushButton::clicked, this, [this, page, page_idx, fetch_fn]() {
                if (page_idx >= 0 && page_idx < k_page_count)
                    m_page_state[page_idx].current_page = page;
                fetch_fn();
            });
        }
        w.page_btn_layout->addWidget(btn);
    };

    auto add_ellipsis = [&]() {
        auto* lbl = new QLabel("...");
        lbl->setObjectName("pageInfo");
        lbl->setFixedSize(20, 28);
        lbl->setAlignment(Qt::AlignCenter);
        w.page_btn_layout->addWidget(lbl);
    };

    if (max_page <= 7) {
        for (int i = 1; i <= max_page; ++i)
            add_page_btn(i, i == current_page);
    } else {
        add_page_btn(1, current_page == 1);

        if (current_page > 4)
            add_ellipsis();

        int start = std::max(2, current_page - 2);
        int end = std::min(max_page - 1, current_page + 2);

        if (current_page <= 4)
            end = std::min(max_page - 1, 6);
        if (current_page >= max_page - 3)
            start = std::max(2, max_page - 5);

        for (int i = start; i <= end; ++i)
            add_page_btn(i, i == current_page);

        if (current_page < max_page - 3)
            add_ellipsis();

        add_page_btn(max_page, current_page == max_page);
    }
}

void ReportPages::connect_pagination(ReportPageWidgets& w, int& current_page,
                                      int& page_size, int& total,
                                      std::function<void()> fetch_fn)
{
    // Store fetch_fn for page button rebuilds
    int idx = page_index_of(w);
    if (idx >= 0 && idx < k_page_count)
        m_fetch_fns[idx] = fetch_fn;

    connect(w.page_prev_btn, &QPushButton::clicked, this, [&current_page, fetch_fn]() {
        if (current_page > 1) {
            --current_page;
            fetch_fn();
        }
    });

    connect(w.page_next_btn, &QPushButton::clicked, this, [&current_page, &page_size, &total, fetch_fn]() {
        int max_page = (total + page_size - 1) / page_size;
        if (current_page < max_page) {
            ++current_page;
            fetch_fn();
        }
    });

    connect(w.page_size_combo, QOverload<int>::of(&QComboBox::currentIndexChanged),
            this, [&current_page, &page_size, &w, fetch_fn](int idx) {
        page_size = w.page_size_combo->itemData(idx).toInt();
        current_page = 1;
        fetch_fn();
    });

    connect(w.refresh_btn, &QPushButton::clicked, this, [this, fetch_fn]() {
        m_upstream->invalidate_cache();
        fetch_fn();
    });

    connect(w.skip_confirm, &QPushButton::clicked, this, [&current_page, &page_size, &total, &w, fetch_fn]() {
        int page = w.skip_input->text().toInt();
        int max_page = (total + page_size - 1) / page_size;
        if (max_page < 1) max_page = 1;
        if (page >= 1 && page <= max_page) {
            current_page = page;
            fetch_fn();
        }
        w.skip_input->clear();
    });

    connect(w.skip_input, &QLineEdit::returnPressed, w.skip_confirm, &QPushButton::click);
}

void ReportPages::connect_search_reset(ReportPageWidgets& w,
                                        std::function<void()> search_fn,
                                        std::function<void()> reset_fn)
{
    for (auto* btn : w.search_form->findChildren<QPushButton*>("searchBtn"))
        connect(btn, &QPushButton::clicked, this, search_fn);
    for (auto* btn : w.search_form->findChildren<QPushButton*>("resetBtn"))
        connect(btn, &QPushButton::clicked, this, reset_fn);
}

// ─── Generic populate helpers ───

// Các key chứa status/type cần hiển thị màu
static bool is_status_key(const QString& key)
{
    return key == "status" || key == "status_text" || key == "status_format";
}

void ReportPages::populate_table(ReportPageWidgets& w, const QJsonArray& data,
                                  const QStringList& keys, int /*total*/)
{
    w.table->setRowCount(0);

    for (int i = 0; i < data.size(); ++i) {
        auto obj = data[i].toObject();
        int row = w.table->rowCount();
        w.table->insertRow(row);

        for (int c = 0; c < keys.size(); ++c) {
            auto val = obj[keys[c]];
            QString text;
            if (val.isDouble()) {
                double d = val.toDouble();
                if (d == static_cast<int>(d))
                    text = QString::number(static_cast<int>(d));
                else
                    text = QString::number(d, 'f', 2);
            } else {
                text = UpstreamTranslate::zh_to_vi(val.toString());
            }

            // Status/type fields → colored label
            if (is_status_key(keys[c])) {
                auto* lbl = new QLabel(text);
                lbl->setAlignment(Qt::AlignCenter);
                QColor sc = UpstreamTranslate::status_color(text);
                bool is_lose = UpstreamTranslate::is_lose_status(text);
                if (sc.isValid()) {
                    if (is_lose) {
                        lbl->setStyleSheet(QString(
                            "QLabel { color: %1; font-size: 12px; font-weight: 600;"
                            "  background: transparent; border: none; padding: 2px 8px; }"
                        ).arg(sc.name()));
                    } else {
                        lbl->setStyleSheet(QString(
                            "QLabel { color: %1; font-size: 12px; font-weight: 600;"
                            "  background: %2; border: none; padding: 2px 8px; }"
                        ).arg(sc.name(), sc.name() + "1a"));
                    }
                } else {
                    lbl->setStyleSheet("QLabel { font-size: 12px; border: none; padding: 2px 8px; }");
                }
                w.table->setCellWidget(row, c, lbl);
            } else {
                auto* item = new QTableWidgetItem(text);
                item->setTextAlignment(Qt::AlignLeft | Qt::AlignVCenter);
                w.table->setItem(row, c, item);
            }
        }
        w.table->setRowHeight(row, 38);
    }

    // Resize table to fit rows
    int table_height = w.table->horizontalHeader()->height();
    for (int r = 0; r < w.table->rowCount(); ++r)
        table_height += w.table->rowHeight(r);
    table_height += 1; // border-top
    w.table->setFixedHeight(table_height);
}

void ReportPages::populate_summary(ReportPageWidgets& w, const QJsonObject& total_data,
                                    const QStringList& keys)
{
    if (!w.summary_table || keys.isEmpty()) return;

    for (int c = 0; c < keys.size() && c < w.summary_table->columnCount(); ++c) {
        auto val = total_data[keys[c]];
        QString text;
        if (val.isDouble()) {
            double d = val.toDouble();
            if (d == static_cast<int>(d))
                text = QString::number(static_cast<int>(d));
            else
                text = QString::number(d, 'f', 2);
        } else {
            text = val.toString();
        }
        auto* item = w.summary_table->item(0, c);
        if (item)
            item->setText(text);
        else {
            item = new QTableWidgetItem(text);
            item->setTextAlignment(Qt::AlignLeft | Qt::AlignVCenter);
            w.summary_table->setItem(0, c, item);
        }
    }
}

// ─── Lazy load ───

void ReportPages::load_page(int page_index)
{
    // page_index: 2=lottery_report, 3=transaction, 4=provider_report,
    //             5=lottery_bets, 6=provider_bets, 7=withdrawal, 8=deposit
    int idx = page_index - 2;
    if (idx < 0 || idx >= k_page_count) return;
    if (m_page_state[idx].loaded) return;
    m_page_state[idx].loaded = true;

    switch (idx) {
    case 0: fetch_lottery_report(); break;
    case 1: fetch_transaction_log(); break;
    case 2: fetch_provider_report(); break;
    case 3: fetch_lottery_bets(); break;
    case 4: fetch_provider_bets(); break;
    case 5: fetch_withdrawal_history(); break;
    case 6: fetch_deposit_history(); break;
    }
}

// ═══════════════════════════════════════════════════════════
//  CREATE PAGES (UI setup + connect signals)
// ═══════════════════════════════════════════════════════════

QWidget* ReportPages::create_lottery_report_page()
{
    FlowLayout* flow = nullptr;
    m_lottery_report = ReportPageBuilder::build_page(
        ":/icons/menu_lottery_report",
        m_tr->t("lottery_report.title"),
        {
            m_tr->t("lottery_report.col_username"),
            m_tr->t("lottery_report.col_agent"),
            m_tr->t("lottery_report.col_bet_count"),
            m_tr->t("lottery_report.col_bet_amount"),
            m_tr->t("lottery_report.col_valid_bet"),
            m_tr->t("lottery_report.col_rebate"),
            m_tr->t("lottery_report.col_result"),
            m_tr->t("lottery_report.col_win_loss"),
            m_tr->t("lottery_report.col_prize"),
            m_tr->t("lottery_report.col_lottery_type"),
        },
        flow,
        m_tr
    );

    m_date_pickers[0] = new DateRangePicker;
    m_date_pickers[0]->set_translator(m_tr);
    m_date_pickers[0]->set_placeholder(
        m_tr->t("common.date_start"),
        m_tr->t("common.date_end"));
    flow->addWidget(m_date_pickers[0]);

    m_quick_date_combos[0] = make_quick_date_combo(m_tr);
    flow->addWidget(m_quick_date_combos[0]);

    m_lr_lottery_select = new QComboBox;
    m_lr_lottery_select->addItem(m_tr->t("common.search_or_type"), QVariant());
    m_lr_lottery_select->setEditable(true);
    m_lr_lottery_select->setFixedHeight(IconDefs::k_input_height);
    m_lr_lottery_select->setFixedWidth(200);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("lottery_report.lottery_type_label"), m_lr_lottery_select, m_lottery_report.search_labels));

    m_lr_username = new QLineEdit;
    m_lr_username->setPlaceholderText(m_tr->t("common.username_placeholder"));
    m_lr_username->setFixedWidth(200);
    m_lr_username->setFixedHeight(IconDefs::k_input_height);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("common.username_label"), m_lr_username, m_lottery_report.search_labels));

    flow->addWidget(make_search_button(":/icons/search", m_tr->t("common.search"), "searchBtn"));
    flow->addWidget(make_search_button(":/icons/refresh", m_tr->t("common.reset"), "resetBtn"));

    ReportPageBuilder::add_summary(m_lottery_report,
        m_tr->t("common.summary_group"),
        {
            m_tr->t("lottery_report.sum_bettors"),
            m_tr->t("lottery_report.col_bet_count"),
            m_tr->t("lottery_report.col_bet_amount"),
            m_tr->t("lottery_report.col_valid_bet"),
            m_tr->t("lottery_report.col_rebate"),
            m_tr->t("lottery_report.col_result"),
            m_tr->t("lottery_report.col_win_loss"),
            m_tr->t("lottery_report.col_prize"),
        },
        {"0", "0", "0.00", "0.00", "0.00", "0.00", "0.00", "0.00"}
    );

    // Connect signals
    connect_search_reset(m_lottery_report,
        [this]() { m_page_state[0].current_page = 1; fetch_lottery_report(); },
        [this]() {
            m_lr_username->clear();
            m_lr_lottery_select->setCurrentIndex(0);
            m_date_pickers[0]->clear_dates();
            m_page_state[0].current_page = 1;
            fetch_lottery_report();
        });
    connect_pagination(m_lottery_report,
        m_page_state[0].current_page, m_page_state[0].page_size, m_page_state[0].total,
        [this]() { fetch_lottery_report(); });

    return m_lottery_report.page;
}

QWidget* ReportPages::create_transaction_log_page()
{
    FlowLayout* flow = nullptr;
    m_transaction_log = ReportPageBuilder::build_page(
        ":/icons/menu_transaction_log",
        m_tr->t("transaction_log.title"),
        {
            m_tr->t("transaction_log.col_username"),
            m_tr->t("transaction_log.col_agent"),
            m_tr->t("transaction_log.col_deposit_count"),
            m_tr->t("transaction_log.col_deposit_amount"),
            m_tr->t("transaction_log.col_withdraw_count"),
            m_tr->t("transaction_log.col_withdraw_amount"),
            m_tr->t("transaction_log.col_service_fee"),
            m_tr->t("transaction_log.col_agent_commission"),
            m_tr->t("transaction_log.col_promotion"),
            m_tr->t("transaction_log.col_third_party_rebate"),
            m_tr->t("transaction_log.col_third_party_bonus"),
            m_tr->t("transaction_log.col_time"),
        },
        flow,
        m_tr
    );

    m_date_pickers[1] = new DateRangePicker;
    m_date_pickers[1]->set_translator(m_tr);
    m_date_pickers[1]->set_placeholder(
        m_tr->t("common.date_start"),
        m_tr->t("common.date_end"));
    flow->addWidget(m_date_pickers[1]);

    m_quick_date_combos[1] = make_quick_date_combo(m_tr);
    flow->addWidget(m_quick_date_combos[1]);

    m_tl_username = new QLineEdit;
    m_tl_username->setPlaceholderText(m_tr->t("common.username_placeholder"));
    m_tl_username->setFixedWidth(200);
    m_tl_username->setFixedHeight(IconDefs::k_input_height);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("common.username_label"), m_tl_username, m_transaction_log.search_labels));

    flow->addWidget(make_search_button(":/icons/search", m_tr->t("common.search"), "searchBtn"));
    flow->addWidget(make_search_button(":/icons/refresh", m_tr->t("common.reset"), "resetBtn"));

    ReportPageBuilder::add_summary(m_transaction_log,
        m_tr->t("common.summary_group"),
        {
            m_tr->t("transaction_log.col_deposit_amount"),
            m_tr->t("transaction_log.col_withdraw_amount"),
            m_tr->t("transaction_log.col_service_fee"),
            m_tr->t("transaction_log.col_agent_commission"),
            m_tr->t("transaction_log.col_promotion"),
            m_tr->t("transaction_log.col_third_party_rebate"),
            m_tr->t("transaction_log.col_third_party_bonus"),
        },
        {"0.00", "0.00", "0.00", "0.00", "0.00", "0.00", "0"}
    );

    connect_search_reset(m_transaction_log,
        [this]() { m_page_state[1].current_page = 1; fetch_transaction_log(); },
        [this]() {
            m_tl_username->clear();
            m_date_pickers[1]->clear_dates();
            m_page_state[1].current_page = 1;
            fetch_transaction_log();
        });
    connect_pagination(m_transaction_log,
        m_page_state[1].current_page, m_page_state[1].page_size, m_page_state[1].total,
        [this]() { fetch_transaction_log(); });

    return m_transaction_log.page;
}

QWidget* ReportPages::create_provider_report_page()
{
    FlowLayout* flow = nullptr;
    m_provider_report = ReportPageBuilder::build_page(
        ":/icons/menu_provider_report",
        m_tr->t("provider_report.title"),
        {
            m_tr->t("provider_report.col_username"),
            m_tr->t("provider_report.col_provider"),
            m_tr->t("provider_report.col_bet_count"),
            m_tr->t("provider_report.col_bet_amount"),
            m_tr->t("provider_report.col_valid_bet"),
            m_tr->t("provider_report.col_bonus"),
            m_tr->t("provider_report.col_win_loss"),
        },
        flow,
        m_tr
    );

    m_date_pickers[2] = new DateRangePicker;
    m_date_pickers[2]->set_translator(m_tr);
    m_date_pickers[2]->set_placeholder(
        m_tr->t("common.date_start"),
        m_tr->t("common.date_end"));
    flow->addWidget(m_date_pickers[2]);

    m_quick_date_combos[2] = make_quick_date_combo(m_tr);
    flow->addWidget(m_quick_date_combos[2]);

    m_pr_username = new QLineEdit;
    m_pr_username->setPlaceholderText(m_tr->t("common.username_placeholder"));
    m_pr_username->setFixedWidth(200);
    m_pr_username->setFixedHeight(IconDefs::k_input_height);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("common.username_label"), m_pr_username, m_provider_report.search_labels));

    m_pr_provider_select = new QComboBox;
    m_pr_provider_select->addItem(m_tr->t("common.select"), QVariant());
    const QStringList providers = {
        "PA", "BBIN", "WM", "MINI", "KY", "PGSOFT", "LUCKYWIN", "SABA", "PT",
        "RICH88", "ASTAR", "FB", "JILI", "KA", "MW", "SBO", "NEXTSPIN", "AMB",
        "FunTa", "MG", "WS168", "DG CASINO", "V8", "AE", "TP", "FC", "JDB",
        "CQ9", "PP", "VA", "BNG", "DB CASINO", "EVO CASINO", "CMD SPORTS",
        "PG NEW", "FBLIVE", "ON CASINO", "MT", "JILI NEW", "fC NEW"
    };
    for (const auto& p : providers) {
        m_pr_provider_select->addItem(p, p);
    }
    m_pr_provider_select->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    m_pr_provider_select->setFixedHeight(IconDefs::k_input_height);
    m_pr_provider_select->setFixedWidth(200);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("provider_report.provider_label"), m_pr_provider_select, m_provider_report.search_labels));

    flow->addWidget(make_search_button(":/icons/search", m_tr->t("common.search"), "searchBtn"));
    flow->addWidget(make_search_button(":/icons/refresh", m_tr->t("common.reset"), "resetBtn"));

    ReportPageBuilder::add_summary(m_provider_report,
        m_tr->t("common.summary_data"),
        {
            m_tr->t("provider_report.col_bet_count"),
            m_tr->t("provider_report.sum_bettors"),
            m_tr->t("provider_report.col_bet_amount"),
            m_tr->t("provider_report.col_valid_bet"),
            m_tr->t("provider_report.col_bonus"),
            m_tr->t("provider_report.col_win_loss"),
        },
        {"0", "0", "0.00", "0.00", "0.00", "0.00"}
    );

    connect_search_reset(m_provider_report,
        [this]() { m_page_state[2].current_page = 1; fetch_provider_report(); },
        [this]() {
            m_pr_username->clear();
            m_pr_provider_select->setCurrentIndex(0);
            m_date_pickers[2]->clear_dates();
            m_page_state[2].current_page = 1;
            fetch_provider_report();
        });
    connect_pagination(m_provider_report,
        m_page_state[2].current_page, m_page_state[2].page_size, m_page_state[2].total,
        [this]() { fetch_provider_report(); });

    return m_provider_report.page;
}

QWidget* ReportPages::create_lottery_bets_page()
{
    FlowLayout* flow = nullptr;
    m_lottery_bets = ReportPageBuilder::build_page(
        ":/icons/menu_lottery_bet",
        m_tr->t("lottery_bets.title"),
        {
            m_tr->t("lottery_bets.col_serial"),
            m_tr->t("lottery_bets.col_username"),
            m_tr->t("lottery_bets.col_bet_time"),
            m_tr->t("lottery_bets.col_game"),
            m_tr->t("lottery_bets.col_game_type"),
            m_tr->t("lottery_bets.col_play_method"),
            m_tr->t("lottery_bets.col_period"),
            m_tr->t("lottery_bets.col_bet_info"),
            m_tr->t("lottery_bets.col_bet_amount"),
            m_tr->t("lottery_bets.col_rebate_amount"),
            m_tr->t("lottery_bets.col_win_loss"),
            m_tr->t("lottery_bets.col_status"),
        },
        flow,
        m_tr
    );

    m_date_pickers[3] = new DateRangePicker;
    m_date_pickers[3]->set_translator(m_tr);
    m_date_pickers[3]->set_placeholder(
        m_tr->t("common.date_start"),
        m_tr->t("common.date_end"));
    flow->addWidget(m_date_pickers[3]);

    m_quick_date_combos[3] = make_quick_date_combo(m_tr);
    flow->addWidget(m_quick_date_combos[3]);

    m_lb_username = new QLineEdit;
    m_lb_username->setPlaceholderText(m_tr->t("lottery_bets.user_placeholder"));
    m_lb_username->setFixedWidth(200);
    m_lb_username->setFixedHeight(IconDefs::k_input_height);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("lottery_bets.user_label"), m_lb_username, m_lottery_bets.search_labels));

    m_lb_serial = new QLineEdit;
    m_lb_serial->setPlaceholderText(m_tr->t("lottery_bets.serial_placeholder"));
    m_lb_serial->setFixedWidth(200);
    m_lb_serial->setFixedHeight(IconDefs::k_input_height);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("lottery_bets.serial_label"), m_lb_serial, m_lottery_bets.search_labels));

    m_lb_game_select = new QComboBox;
    m_lb_game_select->addItem(m_tr->t("common.select"), QVariant());
    m_lb_game_select->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    m_lb_game_select->setFixedHeight(IconDefs::k_input_height);
    m_lb_game_select->setFixedWidth(150);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("lottery_bets.game_label"), m_lb_game_select, m_lottery_bets.search_labels));

    m_lb_play_type = new QComboBox;
    m_lb_play_type->addItem(m_tr->t("common.select"), QVariant());
    m_lb_play_type->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    m_lb_play_type->setFixedHeight(IconDefs::k_input_height);
    m_lb_play_type->setFixedWidth(180);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("lottery_bets.game_type_label"), m_lb_play_type, m_lottery_bets.search_labels));

    m_lb_play_method = new QComboBox;
    m_lb_play_method->addItem(m_tr->t("common.select"), QVariant());
    m_lb_play_method->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    m_lb_play_method->setFixedHeight(IconDefs::k_input_height);
    m_lb_play_method->setFixedWidth(180);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("lottery_bets.play_method_label"), m_lb_play_method, m_lottery_bets.search_labels));

    m_lb_status = new QComboBox;
    m_lb_status->addItem(m_tr->t("common.select"), QVariant());
    m_lb_status->addItem(m_tr->t("lottery_bets.status_unpaid"), "-9");
    m_lb_status->addItem(m_tr->t("lottery_bets.status_win"), "1");
    m_lb_status->addItem(m_tr->t("lottery_bets.status_lose"), "-1");
    m_lb_status->addItem(m_tr->t("lottery_bets.status_draw"), "2");
    m_lb_status->addItem(m_tr->t("lottery_bets.status_user_cancel"), "3");
    m_lb_status->addItem(m_tr->t("lottery_bets.status_system_cancel"), "4");
    m_lb_status->addItem(m_tr->t("lottery_bets.status_abnormal"), "5");
    m_lb_status->addItem(m_tr->t("lottery_bets.status_manual_restore"), "6");
    m_lb_status->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    m_lb_status->setFixedHeight(IconDefs::k_input_height);
    m_lb_status->setFixedWidth(150);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("lottery_bets.status_label"), m_lb_status, m_lottery_bets.search_labels));

    flow->addWidget(make_search_button(":/icons/search", m_tr->t("common.search"), "searchBtn"));
    flow->addWidget(make_search_button(":/icons/refresh", m_tr->t("common.reset"), "resetBtn"));

    ReportPageBuilder::add_summary(m_lottery_bets,
        m_tr->t("common.summary_data"),
        {
            m_tr->t("lottery_bets.col_bet_amount"),
            m_tr->t("lottery_bets.col_rebate_amount"),
            m_tr->t("lottery_bets.col_win_loss"),
        },
        {"0.00", "0.00", "0.00"}
    );

    connect_search_reset(m_lottery_bets,
        [this]() { m_page_state[3].current_page = 1; fetch_lottery_bets(); },
        [this]() {
            m_lb_username->clear();
            m_lb_serial->clear();
            m_lb_game_select->setCurrentIndex(0);
            m_lb_play_type->setCurrentIndex(0);
            m_lb_play_method->setCurrentIndex(0);
            m_lb_status->setCurrentIndex(0);
            m_date_pickers[3]->clear_dates();
            m_page_state[3].current_page = 1;
            fetch_lottery_bets();
        });
    connect_pagination(m_lottery_bets,
        m_page_state[3].current_page, m_page_state[3].page_size, m_page_state[3].total,
        [this]() { fetch_lottery_bets(); });

    return m_lottery_bets.page;
}

QWidget* ReportPages::create_provider_bets_page()
{
    FlowLayout* flow = nullptr;
    m_provider_bets = ReportPageBuilder::build_page(
        ":/icons/menu_third_party_bet",
        m_tr->t("provider_bets.title"),
        {
            m_tr->t("provider_bets.col_serial"),
            m_tr->t("provider_bets.col_provider"),
            m_tr->t("provider_bets.col_platform_user"),
            m_tr->t("provider_bets.col_game_type"),
            m_tr->t("provider_bets.col_game_name"),
            m_tr->t("provider_bets.col_bet_amount"),
            m_tr->t("provider_bets.col_valid_bet"),
            m_tr->t("provider_bets.col_bonus"),
            m_tr->t("provider_bets.col_win_loss"),
            m_tr->t("provider_bets.col_bet_time"),
        },
        flow,
        m_tr
    );

    m_date_pickers[4] = new DateRangePicker;
    m_date_pickers[4]->set_translator(m_tr);
    m_date_pickers[4]->set_placeholder(
        m_tr->t("common.date_start"),
        m_tr->t("common.date_end"));
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("provider_bets.bet_time_label"), m_date_pickers[4], m_provider_bets.search_labels));

    m_quick_date_combos[4] = make_quick_date_combo(m_tr);
    flow->addWidget(m_quick_date_combos[4]);

    m_pb_serial = new QLineEdit;
    m_pb_serial->setPlaceholderText(m_tr->t("provider_bets.serial_placeholder"));
    m_pb_serial->setFixedWidth(200);
    m_pb_serial->setFixedHeight(IconDefs::k_input_height);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("provider_bets.serial_label"), m_pb_serial, m_provider_bets.search_labels));

    m_pb_platform_user = new QLineEdit;
    m_pb_platform_user->setPlaceholderText(m_tr->t("provider_bets.platform_user_placeholder"));
    m_pb_platform_user->setFixedWidth(200);
    m_pb_platform_user->setFixedHeight(IconDefs::k_input_height);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("provider_bets.platform_user_label"), m_pb_platform_user, m_provider_bets.search_labels));

    flow->addWidget(make_search_button(":/icons/search", m_tr->t("common.search"), "searchBtn"));
    flow->addWidget(make_search_button(":/icons/refresh", m_tr->t("common.reset"), "resetBtn"));

    connect_search_reset(m_provider_bets,
        [this]() { m_page_state[4].current_page = 1; fetch_provider_bets(); },
        [this]() {
            m_pb_serial->clear();
            m_pb_platform_user->clear();
            m_date_pickers[4]->clear_dates();
            m_page_state[4].current_page = 1;
            fetch_provider_bets();
        });
    connect_pagination(m_provider_bets,
        m_page_state[4].current_page, m_page_state[4].page_size, m_page_state[4].total,
        [this]() { fetch_provider_bets(); });

    return m_provider_bets.page;
}

QWidget* ReportPages::create_withdrawal_history_page()
{
    FlowLayout* flow = nullptr;
    m_withdrawal_history = ReportPageBuilder::build_page(
        ":/icons/menu_withdraw_log",
        m_tr->t("withdrawal_history.title"),
        {
            m_tr->t("withdrawal_history.col_order_time"),
            m_tr->t("withdrawal_history.col_username"),
            m_tr->t("withdrawal_history.col_agent"),
            m_tr->t("withdrawal_history.col_amount"),
            m_tr->t("withdrawal_history.col_type"),
            m_tr->t("withdrawal_history.col_status"),
        },
        flow,
        m_tr
    );

    m_date_pickers[5] = new DateRangePicker;
    m_date_pickers[5]->set_translator(m_tr);
    m_date_pickers[5]->set_placeholder(
        m_tr->t("common.date_start"),
        m_tr->t("common.date_end"));
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("withdrawal_history.order_time_label"), m_date_pickers[5], m_withdrawal_history.search_labels));

    m_wh_username = new QLineEdit;
    m_wh_username->setPlaceholderText(m_tr->t("common.username_placeholder"));
    m_wh_username->setFixedWidth(150);
    m_wh_username->setFixedHeight(IconDefs::k_input_height);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("common.username_label"), m_wh_username, m_withdrawal_history.search_labels));

    m_wh_serial = new QLineEdit;
    m_wh_serial->setPlaceholderText(m_tr->t("withdrawal_history.serial_placeholder"));
    m_wh_serial->setFixedWidth(300);
    m_wh_serial->setFixedHeight(IconDefs::k_input_height);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("withdrawal_history.serial_label"), m_wh_serial, m_withdrawal_history.search_labels));

    m_wh_status = new QComboBox;
    m_wh_status->addItem(m_tr->t("common.select"), QVariant());
    m_wh_status->addItem(m_tr->t("common.status_pending"), "0");
    m_wh_status->addItem(m_tr->t("common.status_completed"), "1");
    m_wh_status->addItem(m_tr->t("common.status_processing"), "2");
    m_wh_status->addItem(m_tr->t("common.status_failed"), "3");
    m_wh_status->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    m_wh_status->setFixedHeight(IconDefs::k_input_height);
    m_wh_status->setFixedWidth(200);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("withdrawal_history.status_label"), m_wh_status, m_withdrawal_history.search_labels));

    flow->addWidget(make_search_button(":/icons/search", m_tr->t("common.search"), "searchBtn"));
    flow->addWidget(make_search_button(":/icons/refresh", m_tr->t("common.reset"), "resetBtn"));

    connect_search_reset(m_withdrawal_history,
        [this]() { m_page_state[5].current_page = 1; fetch_withdrawal_history(); },
        [this]() {
            m_wh_username->clear();
            m_wh_serial->clear();
            m_wh_status->setCurrentIndex(0);
            m_date_pickers[5]->clear_dates();
            m_page_state[5].current_page = 1;
            fetch_withdrawal_history();
        });
    connect_pagination(m_withdrawal_history,
        m_page_state[5].current_page, m_page_state[5].page_size, m_page_state[5].total,
        [this]() { fetch_withdrawal_history(); });

    return m_withdrawal_history.page;
}

QWidget* ReportPages::create_deposit_history_page()
{
    FlowLayout* flow = nullptr;
    m_deposit_history = ReportPageBuilder::build_page(
        ":/icons/menu_deposit_log",
        m_tr->t("deposit_history.title"),
        {
            m_tr->t("deposit_history.col_username"),
            m_tr->t("deposit_history.col_agent"),
            m_tr->t("deposit_history.col_amount"),
            m_tr->t("deposit_history.col_type"),
            m_tr->t("deposit_history.col_status"),
            m_tr->t("deposit_history.col_order_time"),
        },
        flow,
        m_tr
    );

    m_date_pickers[6] = new DateRangePicker;
    m_date_pickers[6]->set_translator(m_tr);
    m_date_pickers[6]->set_placeholder(
        m_tr->t("common.date_start"),
        m_tr->t("common.date_end"));
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("deposit_history.order_time_label"), m_date_pickers[6], m_deposit_history.search_labels));

    m_dh_username = new QLineEdit;
    m_dh_username->setPlaceholderText(m_tr->t("common.username_placeholder"));
    m_dh_username->setFixedWidth(300);
    m_dh_username->setFixedHeight(IconDefs::k_input_height);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("common.username_label"), m_dh_username, m_deposit_history.search_labels));

    m_dh_type = new QComboBox;
    m_dh_type->addItem(m_tr->t("common.select"), QVariant());
    m_dh_type->addItem(m_tr->t("deposit_history.type_deposit"), "1");
    m_dh_type->addItem(m_tr->t("deposit_history.type_withdraw"), "2");
    m_dh_type->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    m_dh_type->setFixedHeight(IconDefs::k_input_height);
    m_dh_type->setFixedWidth(220);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("deposit_history.type_label"), m_dh_type, m_deposit_history.search_labels));

    m_dh_status = new QComboBox;
    m_dh_status->addItem(m_tr->t("common.select"), QVariant());
    m_dh_status->addItem(m_tr->t("common.status_pending"), "0");
    m_dh_status->addItem(m_tr->t("common.status_completed"), "1");
    m_dh_status->addItem(m_tr->t("common.status_processing"), "2");
    m_dh_status->addItem(m_tr->t("common.status_failed"), "3");
    m_dh_status->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    m_dh_status->setFixedHeight(IconDefs::k_input_height);
    m_dh_status->setFixedWidth(180);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("deposit_history.status_label"), m_dh_status, m_deposit_history.search_labels));

    flow->addWidget(make_search_button(":/icons/search", m_tr->t("common.search"), "searchBtn"));
    flow->addWidget(make_search_button(":/icons/refresh", m_tr->t("common.reset"), "resetBtn"));

    connect_search_reset(m_deposit_history,
        [this]() { m_page_state[6].current_page = 1; fetch_deposit_history(); },
        [this]() {
            m_dh_username->clear();
            m_dh_type->setCurrentIndex(0);
            m_dh_status->setCurrentIndex(0);
            m_date_pickers[6]->clear_dates();
            m_page_state[6].current_page = 1;
            fetch_deposit_history();
        });
    connect_pagination(m_deposit_history,
        m_page_state[6].current_page, m_page_state[6].page_size, m_page_state[6].total,
        [this]() { fetch_deposit_history(); });

    return m_deposit_history.page;
}

// ═══════════════════════════════════════════════════════════
//  FETCH DATA — API calls
// ═══════════════════════════════════════════════════════════

void ReportPages::fetch_lottery_report()
{
    if (m_api->token().isEmpty()) return;
    auto& s = m_page_state[0];

    QMap<QString, QString> params;
    auto sd = get_start_date(0);
    auto ed = get_end_date(0);
    if (!sd.isEmpty()) params["start_time"] = sd;
    if (!ed.isEmpty()) params["end_time"] = ed;
    if (m_lr_lottery_select && !m_lr_lottery_select->currentData().isNull())
        params["lottery_id"] = m_lr_lottery_select->currentData().toString();
    if (m_lr_username && !m_lr_username->text().trimmed().isEmpty())
        params["username"] = m_lr_username->text().trimmed();

    m_lottery_report.loading_overlay->start();
    m_upstream->fetch_all("/agent/reportLottery.html", params, s.current_page, s.page_size,
        [this](const MergedResult& result) {
            m_lottery_report.loading_overlay->stop();
            auto& s = m_page_state[0];
            s.total = result.total;

            populate_table(m_lottery_report, result.data, {
                "username", "user_parent_format", "bet_count", "bet_amount",
                "valid_amount", "rebate_amount", "result", "win_lose",
                "prize", "lottery_name"
            }, s.total);

            if (!result.total_data.isEmpty()) {
                populate_summary(m_lottery_report, result.total_data, {
                    "total_bet_number", "total_bet_count", "total_bet_amount",
                    "total_valid_amount", "total_rebate_amount", "total_win_lose",
                    "total_result", "total_prize"
                });
            }

            update_pagination(m_lottery_report, s.current_page, s.page_size, s.total);
            apply_theme();
        });
}

void ReportPages::fetch_transaction_log()
{
    if (m_api->token().isEmpty()) return;
    auto& s = m_page_state[1];

    QMap<QString, QString> params;
    auto sd = get_start_date(1);
    auto ed = get_end_date(1);
    if (!sd.isEmpty()) params["start_time"] = sd;
    if (!ed.isEmpty()) params["end_time"] = ed;
    if (m_tl_username && !m_tl_username->text().trimmed().isEmpty())
        params["username"] = m_tl_username->text().trimmed();

    m_transaction_log.loading_overlay->start();
    m_upstream->fetch_all("/agent/reportFunds.html", params, s.current_page, s.page_size,
        [this](const MergedResult& result) {
            m_transaction_log.loading_overlay->stop();
            auto& s = m_page_state[1];
            s.total = result.total;

            populate_table(m_transaction_log, result.data, {
                "username", "user_parent_format", "deposit_count", "deposit_amount",
                "withdrawal_count", "withdrawal_amount", "charge_fee", "agent_commission",
                "promotion", "third_rebate", "third_activity_amount", "date"
            }, s.total);

            if (!result.total_data.isEmpty()) {
                populate_summary(m_transaction_log, result.total_data, {
                    "total_deposit_amount", "total_withdrawal_amount", "total_charge_fee",
                    "total_agent_commission", "total_promotion", "total_third_rebate",
                    "total_third_activity_amount"
                });
            }

            update_pagination(m_transaction_log, s.current_page, s.page_size, s.total);
            apply_theme();
        });
}

void ReportPages::fetch_provider_report()
{
    if (m_api->token().isEmpty()) return;
    auto& s = m_page_state[2];

    QMap<QString, QString> params;
    auto sd = get_start_date(2);
    auto ed = get_end_date(2);
    if (!sd.isEmpty()) params["start_time"] = sd;
    if (!ed.isEmpty()) params["end_time"] = ed;
    if (m_pr_username && !m_pr_username->text().trimmed().isEmpty())
        params["username"] = m_pr_username->text().trimmed();
    if (m_pr_provider_select && !m_pr_provider_select->currentData().isNull()
        && !m_pr_provider_select->currentData().toString().isEmpty())
        params["platform_id"] = m_pr_provider_select->currentData().toString();

    m_provider_report.loading_overlay->start();
    m_upstream->fetch_all("/agent/reportThirdGame.html", params, s.current_page, s.page_size,
        [this](const MergedResult& result) {
            m_provider_report.loading_overlay->stop();
            auto& s = m_page_state[2];
            s.total = result.total;

            populate_table(m_provider_report, result.data, {
                "username", "platform_id_name", "t_bet_times", "t_bet_amount",
                "t_turnover", "t_prize", "t_win_lose"
            }, s.total);

            if (!result.total_data.isEmpty()) {
                populate_summary(m_provider_report, result.total_data, {
                    "total_bet_times", "total_bet_number", "total_bet_amount",
                    "total_turnover", "total_prize", "total_win_lose"
                });
            }

            update_pagination(m_provider_report, s.current_page, s.page_size, s.total);
            apply_theme();
        });
}

void ReportPages::fetch_lottery_bets()
{
    if (m_api->token().isEmpty()) return;
    auto& s = m_page_state[3];

    QMap<QString, QString> params;
    params["es"] = "1";
    auto sd = get_start_date(3);
    auto ed = get_end_date(3);
    if (!sd.isEmpty()) params["start_time"] = sd;
    if (!ed.isEmpty()) params["end_time"] = ed;
    if (m_lb_username && !m_lb_username->text().trimmed().isEmpty())
        params["username"] = m_lb_username->text().trimmed();
    if (m_lb_serial && !m_lb_serial->text().trimmed().isEmpty())
        params["serial_no"] = m_lb_serial->text().trimmed();
    if (m_lb_game_select && !m_lb_game_select->currentData().isNull()
        && !m_lb_game_select->currentData().toString().isEmpty())
        params["lottery_id"] = m_lb_game_select->currentData().toString();
    if (m_lb_play_type && !m_lb_play_type->currentData().isNull()
        && !m_lb_play_type->currentData().toString().isEmpty())
        params["play_type"] = m_lb_play_type->currentData().toString();
    if (m_lb_play_method && !m_lb_play_method->currentData().isNull()
        && !m_lb_play_method->currentData().toString().isEmpty())
        params["play_id"] = m_lb_play_method->currentData().toString();
    if (m_lb_status && !m_lb_status->currentData().isNull()
        && !m_lb_status->currentData().toString().isEmpty())
        params["status"] = m_lb_status->currentData().toString();

    m_lottery_bets.loading_overlay->start();
    m_upstream->fetch_all("/agent/bet.html", params, s.current_page, s.page_size,
        [this](const MergedResult& result) {
            m_lottery_bets.loading_overlay->stop();
            auto& s = m_page_state[3];
            s.total = result.total;

            populate_table(m_lottery_bets, result.data, {
                "serial_no", "username", "create_time", "lottery_name",
                "play_type_name", "play_name", "issue", "content",
                "money", "rebate_amount", "result", "status_text"
            }, s.total);

            if (!result.total_data.isEmpty()) {
                populate_summary(m_lottery_bets, result.total_data, {
                    "total_money", "total_rebate_amount", "total_result"
                });
            }

            update_pagination(m_lottery_bets, s.current_page, s.page_size, s.total);
            apply_theme();
        });
}

void ReportPages::fetch_provider_bets()
{
    if (m_api->token().isEmpty()) return;
    auto& s = m_page_state[4];

    QMap<QString, QString> params;
    params["es"] = "1";
    auto sd = get_start_date(4);
    auto ed = get_end_date(4);
    if (!sd.isEmpty()) params["bet_time"] = sd + " | " + (ed.isEmpty() ? sd : ed);
    if (m_pb_serial && !m_pb_serial->text().trimmed().isEmpty())
        params["serial_no"] = m_pb_serial->text().trimmed();
    if (m_pb_platform_user && !m_pb_platform_user->text().trimmed().isEmpty())
        params["platform_username"] = m_pb_platform_user->text().trimmed();

    m_provider_bets.loading_overlay->start();
    m_upstream->fetch_all("/agent/betOrder.html", params, s.current_page, s.page_size,
        [this](const MergedResult& result) {
            m_provider_bets.loading_overlay->stop();
            auto& s = m_page_state[4];
            s.total = result.total;

            populate_table(m_provider_bets, result.data, {
                "serial_no", "platform_id_name", "platform_username", "c_name",
                "game_name", "bet_amount", "turnover", "prize",
                "win_lose", "bet_time"
            }, s.total);

            update_pagination(m_provider_bets, s.current_page, s.page_size, s.total);
            apply_theme();
        });
}

void ReportPages::fetch_withdrawal_history()
{
    if (m_api->token().isEmpty()) return;
    auto& s = m_page_state[5];

    QMap<QString, QString> params;
    params["type"] = "2"; // withdrawal
    auto sd = get_start_date(5);
    auto ed = get_end_date(5);
    if (!sd.isEmpty()) params["start_time"] = sd;
    if (!ed.isEmpty()) params["end_time"] = ed;
    if (m_wh_username && !m_wh_username->text().trimmed().isEmpty())
        params["username"] = m_wh_username->text().trimmed();
    if (m_wh_serial && !m_wh_serial->text().trimmed().isEmpty())
        params["serial_no"] = m_wh_serial->text().trimmed();
    if (m_wh_status && !m_wh_status->currentData().isNull()
        && !m_wh_status->currentData().toString().isEmpty())
        params["status"] = m_wh_status->currentData().toString();

    m_withdrawal_history.loading_overlay->start();
    m_upstream->fetch_all("/agent/depositAndWithdrawal.html", params, s.current_page, s.page_size,
        [this](const MergedResult& result) {
            m_withdrawal_history.loading_overlay->stop();
            auto& s = m_page_state[5];
            s.total = result.total;

            populate_table(m_withdrawal_history, result.data, {
                "create_time", "username", "user_parent_format",
                "amount", "type", "status"
            }, s.total);

            update_pagination(m_withdrawal_history, s.current_page, s.page_size, s.total);
            apply_theme();
        });
}

void ReportPages::fetch_deposit_history()
{
    if (m_api->token().isEmpty()) return;
    auto& s = m_page_state[6];

    QMap<QString, QString> params;
    params["type"] = "1"; // deposit
    auto sd = get_start_date(6);
    auto ed = get_end_date(6);
    if (!sd.isEmpty()) params["start_time"] = sd;
    if (!ed.isEmpty()) params["end_time"] = ed;
    if (m_dh_username && !m_dh_username->text().trimmed().isEmpty())
        params["username"] = m_dh_username->text().trimmed();
    if (m_dh_type && !m_dh_type->currentData().isNull()
        && !m_dh_type->currentData().toString().isEmpty())
        params["type"] = m_dh_type->currentData().toString();
    if (m_dh_status && !m_dh_status->currentData().isNull()
        && !m_dh_status->currentData().toString().isEmpty())
        params["status"] = m_dh_status->currentData().toString();

    m_deposit_history.loading_overlay->start();
    m_upstream->fetch_all("/agent/depositAndWithdrawal.html", params, s.current_page, s.page_size,
        [this](const MergedResult& result) {
            m_deposit_history.loading_overlay->stop();
            auto& s = m_page_state[6];
            s.total = result.total;

            populate_table(m_deposit_history, result.data, {
                "username", "user_parent_format", "amount", "type",
                "status", "create_time"
            }, s.total);

            update_pagination(m_deposit_history, s.current_page, s.page_size, s.total);
            apply_theme();
        });
}

// ═══════════════════════════════════════════════════════════
//  THEME + RETRANSLATE
// ═══════════════════════════════════════════════════════════

void ReportPages::apply_theme()
{
    ReportPageBuilder::apply_page_theme(m_lottery_report, m_theme);
    ReportPageBuilder::apply_page_theme(m_transaction_log, m_theme);
    ReportPageBuilder::apply_page_theme(m_provider_report, m_theme);
    ReportPageBuilder::apply_page_theme(m_lottery_bets, m_theme);
    ReportPageBuilder::apply_page_theme(m_provider_bets, m_theme);
    ReportPageBuilder::apply_page_theme(m_withdrawal_history, m_theme);
    ReportPageBuilder::apply_page_theme(m_deposit_history, m_theme);

    const auto bg = m_theme->color("bg");
    const auto text1 = m_theme->color("text_primary");
    const auto border = m_theme->color("border");
    const auto primary = m_theme->color("primary");

    auto date_btn_style = QString(
        "QPushButton { background: %1; color: %2;"
        "  border-style: solid; border-width: 1px; border-color: %3; border-radius: 0px;"
        "  padding: 4px 8px; font-size: 13px; text-align: left; }"
        "QPushButton:hover { border-color: %4; }"
    ).arg(bg, text1, border, primary);
    bool is_dark = m_theme->theme() == "dark";
    for (int i = 0; i < k_page_count; ++i) {
        if (m_date_pickers[i]) {
            m_date_pickers[i]->set_button_style(date_btn_style);
            m_date_pickers[i]->apply_popup_theme(is_dark);
        }
    }
}

void ReportPages::retranslate()
{
    auto update_quick_date = [this](QComboBox* combo, bool only_today = false) {
        if (!combo) return;
        combo->setItemText(0, m_tr->t("common.today"));
        combo->setItemText(1, m_tr->t("common.yesterday"));
        if (!only_today && combo->count() > 2) {
            combo->setItemText(2, m_tr->t("common.this_week"));
            combo->setItemText(3, m_tr->t("common.this_month"));
            combo->setItemText(4, m_tr->t("common.last_month"));
        }
    };

    auto update_search_buttons = [this](QWidget* form) {
        if (!form) return;
        for (auto* btn : form->findChildren<QPushButton*>("searchBtn"))
            btn->setText(m_tr->t("common.search"));
        for (auto* btn : form->findChildren<QPushButton*>("resetBtn"))
            btn->setText(m_tr->t("common.reset"));
    };

    auto update_pagination = [this](ReportPageWidgets& w) {
        if (w.page_info)
            w.page_info->setText(m_tr->t("common.total_rows").arg(0));
        if (w.page_size_combo) {
            const int page_sizes[] = {10, 20, 30, 50, 100};
            for (int i = 0; i < 5 && i < w.page_size_combo->count(); ++i)
                w.page_size_combo->setItemText(i, m_tr->t("common.rows_per_page").arg(page_sizes[i]));
        }
        if (w.filter_btn) w.filter_btn->setToolTip(m_tr->t("common.filter_columns"));
        if (w.export_btn) w.export_btn->setToolTip(m_tr->t("common.export_file"));
        if (w.print_btn) w.print_btn->setToolTip(m_tr->t("common.print"));
        if (w.refresh_btn) w.refresh_btn->setToolTip(m_tr->t("common.refresh"));
        if (w.skip_label) w.skip_label->setText(m_tr->t("common.goto_page"));
        if (w.skip_confirm) w.skip_confirm->setText(m_tr->t("common.confirm"));
    };

    // === Lottery Report ===
    if (m_lottery_report.title_label)
        m_lottery_report.title_label->setText(m_tr->t("lottery_report.title"));
    if (m_lottery_report.table)
        m_lottery_report.table->setHorizontalHeaderLabels({
            m_tr->t("lottery_report.col_username"), m_tr->t("lottery_report.col_agent"),
            m_tr->t("lottery_report.col_bet_count"), m_tr->t("lottery_report.col_bet_amount"),
            m_tr->t("lottery_report.col_valid_bet"), m_tr->t("lottery_report.col_rebate"),
            m_tr->t("lottery_report.col_win_loss"), m_tr->t("lottery_report.col_result"),
            m_tr->t("lottery_report.col_prize"), m_tr->t("lottery_report.col_lottery_type"),
        });
    if (m_lottery_report.summary_title)
        m_lottery_report.summary_title->setText(m_tr->t("common.summary_group"));
    if (m_lottery_report.summary_table)
        m_lottery_report.summary_table->setHorizontalHeaderLabels({
            m_tr->t("lottery_report.sum_bettors"), m_tr->t("lottery_report.sum_bet_count"),
            m_tr->t("lottery_report.sum_bet_amount"), m_tr->t("lottery_report.sum_valid_bet"),
            m_tr->t("lottery_report.sum_rebate"), m_tr->t("lottery_report.sum_win_loss"),
            m_tr->t("lottery_report.sum_result"), m_tr->t("lottery_report.sum_prize"),
        });
    update_pagination(m_lottery_report);
    update_search_buttons(m_lottery_report.search_form);
    if (m_date_pickers[0]) m_date_pickers[0]->set_placeholder(m_tr->t("common.date_start"), m_tr->t("common.date_end"));
    update_quick_date(m_quick_date_combos[0]);
    if (m_lottery_report.search_labels.size() >= 2) {
        m_lottery_report.search_labels[0]->setText(m_tr->t("lottery_report.lottery_type_label"));
        m_lottery_report.search_labels[1]->setText(m_tr->t("common.username_label"));
    }

    // === Transaction Log ===
    if (m_transaction_log.title_label)
        m_transaction_log.title_label->setText(m_tr->t("transaction_log.title"));
    if (m_transaction_log.table)
        m_transaction_log.table->setHorizontalHeaderLabels({
            m_tr->t("transaction_log.col_username"), m_tr->t("transaction_log.col_agent"),
            m_tr->t("transaction_log.col_deposit_count"), m_tr->t("transaction_log.col_deposit_amount"),
            m_tr->t("transaction_log.col_withdraw_count"), m_tr->t("transaction_log.col_withdraw_amount"),
            m_tr->t("transaction_log.col_service_fee"), m_tr->t("transaction_log.col_agent_commission"),
            m_tr->t("transaction_log.col_promotion"), m_tr->t("transaction_log.col_third_party_rebate"),
            m_tr->t("transaction_log.col_third_party_bonus"), m_tr->t("transaction_log.col_time"),
        });
    if (m_transaction_log.summary_title)
        m_transaction_log.summary_title->setText(m_tr->t("common.summary_group"));
    if (m_transaction_log.summary_table)
        m_transaction_log.summary_table->setHorizontalHeaderLabels({
            m_tr->t("transaction_log.sum_deposit_amount"), m_tr->t("transaction_log.sum_withdraw_amount"),
            m_tr->t("transaction_log.sum_service_fee"), m_tr->t("transaction_log.sum_agent_commission"),
            m_tr->t("transaction_log.sum_promotion"), m_tr->t("transaction_log.sum_third_party_rebate"),
            m_tr->t("transaction_log.sum_third_party_bonus"),
        });
    update_pagination(m_transaction_log);
    update_search_buttons(m_transaction_log.search_form);
    if (m_date_pickers[1]) m_date_pickers[1]->set_placeholder(m_tr->t("common.date_start"), m_tr->t("common.date_end"));
    update_quick_date(m_quick_date_combos[1]);
    if (m_transaction_log.search_labels.size() >= 1)
        m_transaction_log.search_labels[0]->setText(m_tr->t("common.username_label"));

    // === Provider Report ===
    if (m_provider_report.title_label)
        m_provider_report.title_label->setText(m_tr->t("provider_report.title"));
    if (m_provider_report.table)
        m_provider_report.table->setHorizontalHeaderLabels({
            m_tr->t("provider_report.col_username"), m_tr->t("provider_report.col_provider"),
            m_tr->t("provider_report.col_bet_count"), m_tr->t("provider_report.col_bet_amount"),
            m_tr->t("provider_report.col_valid_bet"), m_tr->t("provider_report.col_bonus"),
            m_tr->t("provider_report.col_win_loss"),
        });
    if (m_provider_report.summary_title)
        m_provider_report.summary_title->setText(m_tr->t("common.summary_data"));
    if (m_provider_report.summary_table)
        m_provider_report.summary_table->setHorizontalHeaderLabels({
            m_tr->t("provider_report.sum_bet_count"), m_tr->t("provider_report.sum_bettors"),
            m_tr->t("provider_report.sum_bet_amount"), m_tr->t("provider_report.sum_valid_bet"),
            m_tr->t("provider_report.sum_bonus"), m_tr->t("provider_report.sum_win_loss"),
        });
    update_pagination(m_provider_report);
    update_search_buttons(m_provider_report.search_form);
    if (m_date_pickers[2]) m_date_pickers[2]->set_placeholder(m_tr->t("common.date_start"), m_tr->t("common.date_end"));
    update_quick_date(m_quick_date_combos[2]);
    if (m_provider_report.search_labels.size() >= 2) {
        m_provider_report.search_labels[0]->setText(m_tr->t("common.username_label"));
        m_provider_report.search_labels[1]->setText(m_tr->t("provider_report.provider_label"));
    }

    // === Lottery Bets ===
    if (m_lottery_bets.title_label)
        m_lottery_bets.title_label->setText(m_tr->t("lottery_bets.title"));
    if (m_lottery_bets.table)
        m_lottery_bets.table->setHorizontalHeaderLabels({
            m_tr->t("lottery_bets.col_serial"), m_tr->t("lottery_bets.col_username"),
            m_tr->t("lottery_bets.col_bet_time"), m_tr->t("lottery_bets.col_game"),
            m_tr->t("lottery_bets.col_game_type"), m_tr->t("lottery_bets.col_play_method"),
            m_tr->t("lottery_bets.col_period"), m_tr->t("lottery_bets.col_bet_info"),
            m_tr->t("lottery_bets.col_bet_amount"), m_tr->t("lottery_bets.col_rebate_amount"),
            m_tr->t("lottery_bets.col_win_loss"), m_tr->t("lottery_bets.col_status"),
        });
    if (m_lottery_bets.summary_title)
        m_lottery_bets.summary_title->setText(m_tr->t("common.summary_data"));
    if (m_lottery_bets.summary_table)
        m_lottery_bets.summary_table->setHorizontalHeaderLabels({
            m_tr->t("lottery_bets.sum_bet_amount"), m_tr->t("lottery_bets.sum_rebate_amount"),
            m_tr->t("lottery_bets.sum_win_loss"),
        });
    update_pagination(m_lottery_bets);
    update_search_buttons(m_lottery_bets.search_form);
    if (m_date_pickers[3]) m_date_pickers[3]->set_placeholder(m_tr->t("common.date_start"), m_tr->t("common.date_end"));
    update_quick_date(m_quick_date_combos[3]);
    if (m_lottery_bets.search_labels.size() >= 6) {
        m_lottery_bets.search_labels[0]->setText(m_tr->t("lottery_bets.user_label"));
        m_lottery_bets.search_labels[1]->setText(m_tr->t("lottery_bets.serial_label"));
        m_lottery_bets.search_labels[2]->setText(m_tr->t("lottery_bets.game_label"));
        m_lottery_bets.search_labels[3]->setText(m_tr->t("lottery_bets.game_type_label"));
        m_lottery_bets.search_labels[4]->setText(m_tr->t("lottery_bets.play_method_label"));
        m_lottery_bets.search_labels[5]->setText(m_tr->t("lottery_bets.status_label"));
    }

    // === Provider Bets ===
    if (m_provider_bets.title_label)
        m_provider_bets.title_label->setText(m_tr->t("provider_bets.title"));
    if (m_provider_bets.table)
        m_provider_bets.table->setHorizontalHeaderLabels({
            m_tr->t("provider_bets.col_serial"), m_tr->t("provider_bets.col_provider"),
            m_tr->t("provider_bets.col_platform_user"), m_tr->t("provider_bets.col_game_type"),
            m_tr->t("provider_bets.col_game_name"), m_tr->t("provider_bets.col_bet_amount"),
            m_tr->t("provider_bets.col_valid_bet"), m_tr->t("provider_bets.col_bonus"),
            m_tr->t("provider_bets.col_win_loss"), m_tr->t("provider_bets.col_bet_time"),
        });
    update_pagination(m_provider_bets);
    update_search_buttons(m_provider_bets.search_form);
    if (m_date_pickers[4]) m_date_pickers[4]->set_placeholder(m_tr->t("common.date_start"), m_tr->t("common.date_end"));
    update_quick_date(m_quick_date_combos[4]);
    if (m_provider_bets.search_labels.size() >= 3) {
        m_provider_bets.search_labels[0]->setText(m_tr->t("provider_bets.bet_time_label"));
        m_provider_bets.search_labels[1]->setText(m_tr->t("provider_bets.serial_label"));
        m_provider_bets.search_labels[2]->setText(m_tr->t("provider_bets.platform_user_label"));
    }

    // === Withdrawal History ===
    if (m_withdrawal_history.title_label)
        m_withdrawal_history.title_label->setText(m_tr->t("withdrawal_history.title"));
    if (m_withdrawal_history.table)
        m_withdrawal_history.table->setHorizontalHeaderLabels({
            m_tr->t("withdrawal_history.col_order_time"),
            m_tr->t("withdrawal_history.col_username"), m_tr->t("withdrawal_history.col_agent"),
            m_tr->t("withdrawal_history.col_amount"), m_tr->t("withdrawal_history.col_type"),
            m_tr->t("withdrawal_history.col_status"),
        });
    update_pagination(m_withdrawal_history);
    update_search_buttons(m_withdrawal_history.search_form);
    if (m_date_pickers[5]) m_date_pickers[5]->set_placeholder(m_tr->t("common.date_start"), m_tr->t("common.date_end"));
    if (m_withdrawal_history.search_labels.size() >= 3) {
        m_withdrawal_history.search_labels[0]->setText(m_tr->t("withdrawal_history.order_time_label"));
        m_withdrawal_history.search_labels[1]->setText(m_tr->t("common.username_label"));
        m_withdrawal_history.search_labels[2]->setText(m_tr->t("withdrawal_history.serial_label"));
        if (m_withdrawal_history.search_labels.size() >= 4)
            m_withdrawal_history.search_labels[3]->setText(m_tr->t("withdrawal_history.status_label"));
    }

    // === Deposit History ===
    if (m_deposit_history.title_label)
        m_deposit_history.title_label->setText(m_tr->t("deposit_history.title"));
    if (m_deposit_history.table)
        m_deposit_history.table->setHorizontalHeaderLabels({
            m_tr->t("deposit_history.col_username"), m_tr->t("deposit_history.col_agent"),
            m_tr->t("deposit_history.col_amount"), m_tr->t("deposit_history.col_type"),
            m_tr->t("deposit_history.col_status"), m_tr->t("deposit_history.col_order_time"),
        });
    update_pagination(m_deposit_history);
    update_search_buttons(m_deposit_history.search_form);
    if (m_date_pickers[6]) m_date_pickers[6]->set_placeholder(m_tr->t("common.date_start"), m_tr->t("common.date_end"));
    if (m_deposit_history.search_labels.size() >= 3) {
        m_deposit_history.search_labels[0]->setText(m_tr->t("deposit_history.order_time_label"));
        m_deposit_history.search_labels[1]->setText(m_tr->t("common.username_label"));
        m_deposit_history.search_labels[2]->setText(m_tr->t("deposit_history.type_label"));
        if (m_deposit_history.search_labels.size() >= 4)
            m_deposit_history.search_labels[3]->setText(m_tr->t("deposit_history.status_label"));
    }

    // Date picker popup buttons
    for (int i = 0; i < k_page_count; ++i) {
        if (m_date_pickers[i])
            m_date_pickers[i]->set_translator(m_tr);
    }
}
