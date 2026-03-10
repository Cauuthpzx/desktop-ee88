#include "core/report_pages.h"
#include "core/date_range_picker.h"
#include "core/flow_layout.h"
#include "core/theme_manager.h"
#include "core/translator.h"
#include "core/report_page_builder.h"

#include <QLineEdit>

static QPushButton* make_search_button(const QString& icon_path, const QString& text, const QString& obj_name)
{
    auto* btn = new QPushButton(QIcon(icon_path), text);
    btn->setObjectName(obj_name);
    btn->setCursor(Qt::PointingHandCursor);
    btn->setFixedHeight(32);
    btn->setIconSize(QSize(16, 16));
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
    combo->setFixedHeight(32);
    return combo;
}

ReportPages::ReportPages(ThemeManager* theme, Translator* tr, QObject* parent)
    : QObject(parent)
    , m_theme(theme)
    , m_tr(tr)
{
}

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
            m_tr->t("lottery_report.col_win_loss"),
            m_tr->t("lottery_report.col_result"),
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

    auto* lottery_select = new QComboBox;
    lottery_select->addItem(m_tr->t("common.search_or_type"), QVariant());
    lottery_select->setEditable(true);
    lottery_select->setFixedHeight(32);
    lottery_select->setFixedWidth(200);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("lottery_report.lottery_type_label"), lottery_select, m_lottery_report.search_labels));

    auto* username = new QLineEdit;
    username->setPlaceholderText(m_tr->t("common.username_placeholder"));
    username->setFixedWidth(200);
    username->setFixedHeight(32);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("common.username_label"), username, m_lottery_report.search_labels));

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
            m_tr->t("lottery_report.col_win_loss"),
            m_tr->t("lottery_report.col_result"),
            m_tr->t("lottery_report.col_prize"),
        },
        {"0", "0", "0.00", "0.00", "0.00", "0.00", "0.00", "0.00"}
    );

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

    auto* username = new QLineEdit;
    username->setPlaceholderText(m_tr->t("common.username_placeholder"));
    username->setFixedWidth(200);
    username->setFixedHeight(32);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("common.username_label"), username, m_transaction_log.search_labels));

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

    auto* username = new QLineEdit;
    username->setPlaceholderText(m_tr->t("common.username_placeholder"));
    username->setFixedWidth(200);
    username->setFixedHeight(32);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("common.username_label"), username, m_provider_report.search_labels));

    auto* provider_select = new QComboBox;
    provider_select->addItem(m_tr->t("common.select"), QVariant());
    const QStringList providers = {
        "PA", "BBIN", "WM", "MINI", "KY", "PGSOFT", "LUCKYWIN", "SABA", "PT",
        "RICH88", "ASTAR", "FB", "JILI", "KA", "MW", "SBO", "NEXTSPIN", "AMB",
        "FunTa", "MG", "WS168", "DG CASINO", "V8", "AE", "TP", "FC", "JDB",
        "CQ9", "PP", "VA", "BNG", "DB CASINO", "EVO CASINO", "CMD SPORTS",
        "PG NEW", "FBLIVE", "ON CASINO", "MT", "JILI NEW", "fC NEW"
    };
    for (const auto& p : providers) {
        provider_select->addItem(p, p);
    }
    provider_select->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    provider_select->setFixedHeight(32);
    provider_select->setFixedWidth(200);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("provider_report.provider_label"), provider_select, m_provider_report.search_labels));

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

    m_quick_date_combos[3] = make_quick_date_combo(m_tr, true);
    flow->addWidget(m_quick_date_combos[3]);

    auto* username = new QLineEdit;
    username->setPlaceholderText(m_tr->t("lottery_bets.user_placeholder"));
    username->setFixedWidth(200);
    username->setFixedHeight(32);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("lottery_bets.user_label"), username, m_lottery_bets.search_labels));

    auto* serial_no = new QLineEdit;
    serial_no->setPlaceholderText(m_tr->t("lottery_bets.serial_placeholder"));
    serial_no->setFixedWidth(200);
    serial_no->setFixedHeight(32);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("lottery_bets.serial_label"), serial_no, m_lottery_bets.search_labels));

    auto* game_select = new QComboBox;
    game_select->addItem(m_tr->t("common.select"), QVariant());
    game_select->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    game_select->setFixedHeight(32);
    game_select->setFixedWidth(150);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("lottery_bets.game_label"), game_select, m_lottery_bets.search_labels));

    auto* play_type = new QComboBox;
    play_type->addItem(m_tr->t("common.select"), QVariant());
    play_type->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    play_type->setFixedHeight(32);
    play_type->setFixedWidth(180);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("lottery_bets.game_type_label"), play_type, m_lottery_bets.search_labels));

    auto* play_method = new QComboBox;
    play_method->addItem(m_tr->t("common.select"), QVariant());
    play_method->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    play_method->setFixedHeight(32);
    play_method->setFixedWidth(180);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("lottery_bets.play_method_label"), play_method, m_lottery_bets.search_labels));

    auto* status_select = new QComboBox;
    status_select->addItem(m_tr->t("common.select"), QVariant());
    status_select->addItem(m_tr->t("lottery_bets.status_unpaid"), "-9");
    status_select->addItem(m_tr->t("lottery_bets.status_win"), "1");
    status_select->addItem(m_tr->t("lottery_bets.status_lose"), "-1");
    status_select->addItem(m_tr->t("lottery_bets.status_draw"), "2");
    status_select->addItem(m_tr->t("lottery_bets.status_user_cancel"), "3");
    status_select->addItem(m_tr->t("lottery_bets.status_system_cancel"), "4");
    status_select->addItem(m_tr->t("lottery_bets.status_abnormal"), "5");
    status_select->addItem(m_tr->t("lottery_bets.status_manual_restore"), "6");
    status_select->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    status_select->setFixedHeight(32);
    status_select->setFixedWidth(150);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("lottery_bets.status_label"), status_select, m_lottery_bets.search_labels));

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

    auto* serial_no = new QLineEdit;
    serial_no->setPlaceholderText(m_tr->t("provider_bets.serial_placeholder"));
    serial_no->setFixedWidth(200);
    serial_no->setFixedHeight(32);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("provider_bets.serial_label"), serial_no, m_provider_bets.search_labels));

    auto* platform_user = new QLineEdit;
    platform_user->setPlaceholderText(m_tr->t("provider_bets.platform_user_placeholder"));
    platform_user->setFixedWidth(200);
    platform_user->setFixedHeight(32);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("provider_bets.platform_user_label"), platform_user, m_provider_bets.search_labels));

    flow->addWidget(make_search_button(":/icons/search", m_tr->t("common.search"), "searchBtn"));
    flow->addWidget(make_search_button(":/icons/refresh", m_tr->t("common.reset"), "resetBtn"));

    return m_provider_bets.page;
}

QWidget* ReportPages::create_withdrawal_history_page()
{
    FlowLayout* flow = nullptr;
    m_withdrawal_history = ReportPageBuilder::build_page(
        ":/icons/menu_withdraw_log",
        m_tr->t("withdrawal_history.title"),
        {
            m_tr->t("withdrawal_history.col_serial"),
            m_tr->t("withdrawal_history.col_order_time"),
            m_tr->t("withdrawal_history.col_username"),
            m_tr->t("withdrawal_history.col_agent"),
            m_tr->t("withdrawal_history.col_amount"),
            m_tr->t("withdrawal_history.col_member_fee"),
            m_tr->t("withdrawal_history.col_actual_amount"),
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

    auto* username = new QLineEdit;
    username->setPlaceholderText(m_tr->t("common.username_placeholder"));
    username->setFixedWidth(150);
    username->setFixedHeight(32);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("common.username_label"), username, m_withdrawal_history.search_labels));

    auto* serial_no = new QLineEdit;
    serial_no->setPlaceholderText(m_tr->t("withdrawal_history.serial_placeholder"));
    serial_no->setFixedWidth(300);
    serial_no->setFixedHeight(32);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("withdrawal_history.serial_label"), serial_no, m_withdrawal_history.search_labels));

    auto* status_select = new QComboBox;
    status_select->addItem(m_tr->t("common.select"), QVariant());
    status_select->addItem(m_tr->t("common.status_pending"), "0");
    status_select->addItem(m_tr->t("common.status_completed"), "1");
    status_select->addItem(m_tr->t("common.status_processing"), "2");
    status_select->addItem(m_tr->t("common.status_failed"), "3");
    status_select->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    status_select->setFixedHeight(32);
    status_select->setFixedWidth(200);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("withdrawal_history.status_label"), status_select, m_withdrawal_history.search_labels));

    flow->addWidget(make_search_button(":/icons/search", m_tr->t("common.search"), "searchBtn"));
    flow->addWidget(make_search_button(":/icons/refresh", m_tr->t("common.reset"), "resetBtn"));

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

    auto* username = new QLineEdit;
    username->setPlaceholderText(m_tr->t("common.username_placeholder"));
    username->setFixedWidth(300);
    username->setFixedHeight(32);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("common.username_label"), username, m_deposit_history.search_labels));

    auto* type_select = new QComboBox;
    type_select->addItem(m_tr->t("common.select"), QVariant());
    type_select->addItem(m_tr->t("deposit_history.type_deposit"), "1");
    type_select->addItem(m_tr->t("deposit_history.type_withdraw"), "2");
    type_select->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    type_select->setFixedHeight(32);
    type_select->setFixedWidth(220);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("deposit_history.type_label"), type_select, m_deposit_history.search_labels));

    auto* status_select = new QComboBox;
    status_select->addItem(m_tr->t("common.select"), QVariant());
    status_select->addItem(m_tr->t("common.status_pending"), "0");
    status_select->addItem(m_tr->t("common.status_completed"), "1");
    status_select->addItem(m_tr->t("common.status_processing"), "2");
    status_select->addItem(m_tr->t("common.status_failed"), "3");
    status_select->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    status_select->setFixedHeight(32);
    status_select->setFixedWidth(180);
    flow->addWidget(ReportPageBuilder::make_field(
        m_tr->t("deposit_history.status_label"), status_select, m_deposit_history.search_labels));

    flow->addWidget(make_search_button(":/icons/search", m_tr->t("common.search"), "searchBtn"));
    flow->addWidget(make_search_button(":/icons/refresh", m_tr->t("common.reset"), "resetBtn"));

    return m_deposit_history.page;
}

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
    for (int i = 0; i < 7; ++i) {
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
            const int page_sizes[] = {10, 20, 30, 40, 50, 60, 70, 80, 90};
            for (int i = 0; i < 9 && i < w.page_size_combo->count(); ++i)
                w.page_size_combo->setItemText(i, m_tr->t("common.rows_per_page").arg(page_sizes[i]));
        }
        if (w.filter_btn) w.filter_btn->setToolTip(m_tr->t("common.filter_columns"));
        if (w.export_btn) w.export_btn->setToolTip(m_tr->t("common.export_file"));
        if (w.print_btn) w.print_btn->setToolTip(m_tr->t("common.print"));
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
    update_quick_date(m_quick_date_combos[3], true);
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
            m_tr->t("withdrawal_history.col_serial"), m_tr->t("withdrawal_history.col_order_time"),
            m_tr->t("withdrawal_history.col_username"), m_tr->t("withdrawal_history.col_agent"),
            m_tr->t("withdrawal_history.col_amount"), m_tr->t("withdrawal_history.col_member_fee"),
            m_tr->t("withdrawal_history.col_actual_amount"), m_tr->t("withdrawal_history.col_status"),
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
    for (int i = 0; i < 7; ++i) {
        if (m_date_pickers[i])
            m_date_pickers[i]->set_translator(m_tr);
    }
}
