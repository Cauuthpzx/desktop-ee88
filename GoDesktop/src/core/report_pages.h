#pragma once

#include <QWidget>
#include <QComboBox>

#include "core/report_page_builder.h"

class DateRangePicker;
class ThemeManager;
class Translator;

class ReportPages : public QObject {
    Q_OBJECT

public:
    explicit ReportPages(ThemeManager* theme, Translator* tr, QObject* parent = nullptr);

    QWidget* create_lottery_report_page();
    QWidget* create_transaction_log_page();
    QWidget* create_provider_report_page();
    QWidget* create_lottery_bets_page();
    QWidget* create_provider_bets_page();
    QWidget* create_withdrawal_history_page();
    QWidget* create_deposit_history_page();

    void apply_theme();
    void retranslate();

private:
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
};
