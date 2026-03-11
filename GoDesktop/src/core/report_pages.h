#pragma once

#include <QWidget>
#include <QComboBox>
#include <QLineEdit>

#include "core/report_page_builder.h"

class ApiClient;
class DateRangePicker;
class ThemeManager;
class Translator;

class ReportPages : public QObject {
    Q_OBJECT

public:
    explicit ReportPages(ApiClient* api, ThemeManager* theme, Translator* tr, QObject* parent = nullptr);

    QWidget* create_lottery_report_page();
    QWidget* create_transaction_log_page();
    QWidget* create_provider_report_page();
    QWidget* create_lottery_bets_page();
    QWidget* create_provider_bets_page();
    QWidget* create_withdrawal_history_page();
    QWidget* create_deposit_history_page();

    void apply_theme();
    void retranslate();

    // Load data khi chuyển tới trang (lazy load)
    void load_page(int page_index);

private:
    // Fetch data cho từng trang
    void fetch_lottery_report();
    void fetch_transaction_log();
    void fetch_provider_report();
    void fetch_lottery_bets();
    void fetch_provider_bets();
    void fetch_withdrawal_history();
    void fetch_deposit_history();

    // Populate table + summary từ JSON
    void populate_table(ReportPageWidgets& w, const QJsonArray& data,
                        const QStringList& keys, int total);
    void populate_summary(ReportPageWidgets& w, const QJsonObject& total_data,
                          const QStringList& keys);

    // Pagination helpers
    void update_pagination(ReportPageWidgets& w, int current_page,
                           int page_size, int total);
    void connect_pagination(ReportPageWidgets& w, int& current_page,
                            int& page_size, int& total,
                            std::function<void()> fetch_fn);
    void connect_search_reset(ReportPageWidgets& w, std::function<void()> search_fn,
                              std::function<void()> reset_fn);

    // Quick date helper
    QString get_start_date(int picker_index) const;
    QString get_end_date(int picker_index) const;
    void apply_quick_date(int picker_index, int combo_index);

    ApiClient* m_api;
    ThemeManager* m_theme;
    Translator* m_tr;

    ReportPageWidgets m_lottery_report;
    ReportPageWidgets m_transaction_log;
    ReportPageWidgets m_provider_report;
    ReportPageWidgets m_lottery_bets;
    ReportPageWidgets m_provider_bets;
    ReportPageWidgets m_withdrawal_history;
    ReportPageWidgets m_deposit_history;

    DateRangePicker* m_date_pickers[7] = {};
    QComboBox* m_quick_date_combos[7] = {};

    // Search field references (để đọc giá trị khi fetch)
    // Lottery Report
    QComboBox* m_lr_lottery_select = nullptr;
    QLineEdit* m_lr_username = nullptr;

    // Transaction Log
    QLineEdit* m_tl_username = nullptr;

    // Provider Report
    QLineEdit* m_pr_username = nullptr;
    QComboBox* m_pr_provider_select = nullptr;

    // Lottery Bets
    QLineEdit* m_lb_username = nullptr;
    QLineEdit* m_lb_serial = nullptr;
    QComboBox* m_lb_game_select = nullptr;
    QComboBox* m_lb_play_type = nullptr;
    QComboBox* m_lb_play_method = nullptr;
    QComboBox* m_lb_status = nullptr;

    // Provider Bets
    QLineEdit* m_pb_serial = nullptr;
    QLineEdit* m_pb_platform_user = nullptr;

    // Withdrawal History
    QLineEdit* m_wh_username = nullptr;
    QLineEdit* m_wh_serial = nullptr;
    QComboBox* m_wh_status = nullptr;

    // Deposit History
    QLineEdit* m_dh_username = nullptr;
    QComboBox* m_dh_type = nullptr;
    QComboBox* m_dh_status = nullptr;

    // Pagination state per page
    struct PageState {
        int current_page = 1;
        int page_size = 10;
        int total = 0;
        bool loaded = false;
    };
    PageState m_page_state[7];
};
