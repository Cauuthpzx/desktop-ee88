#pragma once

#include <QWidget>
#include <QPushButton>
#include <QCalendarWidget>
#include <QDate>
#include <QLabel>
#include <QVBoxLayout>
#include <QHBoxLayout>

class DateRangePopup;
class Translator;

/**
 * Single-calendar date range picker.
 * Click once → set start date, click again → set end date.
 * Displays "start - end" or placeholder text on a button.
 */
class DateRangePicker : public QWidget {
    Q_OBJECT

public:
    explicit DateRangePicker(QWidget* parent = nullptr);
    void set_translator(Translator* tr);

    QDate start_date() const;
    QDate end_date() const;
    void clear_dates();
    void set_placeholder(const QString& start, const QString& end);
    void set_button_style(const QString& style);
    void apply_popup_theme(bool dark);

signals:
    void dates_changed(const QDate& start, const QDate& end);

private slots:
    void toggle_popup();

private:
    QPushButton* m_button;
    DateRangePopup* m_popup;
    Translator* m_tr = nullptr;
    QString m_placeholder_start;
    QString m_placeholder_end;

    void update_button_text();
};

/**
 * Popup calendar panel for range selection.
 * Has Confirm + Clear buttons at the bottom.
 */
class DateRangePopup : public QWidget {
    Q_OBJECT

public:
    explicit DateRangePopup(QWidget* parent = nullptr);

    QDate start_date() const { return m_start; }
    QDate end_date() const { return m_end; }
    void clear();
    void apply_theme(bool dark);
    void set_translator(Translator* tr);
    void retranslate();

signals:
    void dates_confirmed(const QDate& start, const QDate& end);
    void dates_cleared();

private slots:
    void on_date_clicked(const QDate& date);
    void on_confirm();
    void on_clear();

private:
    QCalendarWidget* m_calendar;
    QLabel* m_hint_label;
    QPushButton* m_confirm_btn;
    QPushButton* m_clear_btn;
    Translator* m_tr = nullptr;
    QDate m_start;
    QDate m_end;
    bool m_selecting_end;

    void highlight_range();
    void clear_highlight();
};
