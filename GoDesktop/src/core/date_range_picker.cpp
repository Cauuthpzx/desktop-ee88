#include "core/date_range_picker.h"

#include <QTextCharFormat>

// ── DateRangePicker ──

DateRangePicker::DateRangePicker(QWidget* parent)
    : QWidget(parent)
    , m_placeholder_start("Thời gian bắt đầu")
    , m_placeholder_end("Thời gian kết thúc")
{
    auto* lay = new QHBoxLayout(this);
    lay->setContentsMargins(0, 0, 0, 0);
    lay->setSpacing(0);

    m_button = new QPushButton;
    m_button->setObjectName("dateRangeBtn");
    m_button->setCursor(Qt::PointingHandCursor);
    m_button->setFixedHeight(32);
    lay->addWidget(m_button);

    m_popup = new DateRangePopup(nullptr);
    m_popup->setWindowFlags(Qt::Popup | Qt::FramelessWindowHint);
    m_popup->hide();

    connect(m_button, &QPushButton::clicked, this, &DateRangePicker::toggle_popup);

    // Confirm → update text, close popup
    connect(m_popup, &DateRangePopup::dates_confirmed, this, [this](const QDate& s, const QDate& e) {
        update_button_text();
        m_popup->hide();
        emit dates_changed(s, e);
    });

    // Clear → update text (popup stays open)
    connect(m_popup, &DateRangePopup::dates_cleared, this, [this]() {
        update_button_text();
    });

    update_button_text();
}

QDate DateRangePicker::start_date() const { return m_popup->start_date(); }
QDate DateRangePicker::end_date() const { return m_popup->end_date(); }

void DateRangePicker::clear_dates()
{
    m_popup->clear();
    update_button_text();
}

void DateRangePicker::set_placeholder(const QString& start, const QString& end)
{
    m_placeholder_start = start;
    m_placeholder_end = end;
    update_button_text();
}

void DateRangePicker::set_button_style(const QString& style)
{
    m_button->setStyleSheet(style);
}

void DateRangePicker::apply_popup_theme(bool dark)
{
    m_popup->apply_theme(dark);
}

void DateRangePicker::toggle_popup()
{
    if (m_popup->isVisible()) {
        m_popup->hide();
        return;
    }
    QPoint pos = m_button->mapToGlobal(QPoint(0, m_button->height() + 2));
    m_popup->move(pos);
    m_popup->show();
    m_popup->raise();
}

void DateRangePicker::update_button_text()
{
    QDate s = m_popup->start_date();
    QDate e = m_popup->end_date();
    if (s.isValid() && e.isValid()) {
        m_button->setText(s.toString("yyyy-MM-dd") + "  -  " + e.toString("yyyy-MM-dd"));
    } else {
        m_button->setText(m_placeholder_start + "  -  " + m_placeholder_end);
    }
}

// ── DateRangePopup ──

DateRangePopup::DateRangePopup(QWidget* parent)
    : QWidget(parent)
    , m_selecting_end(false)
{
    auto* lay = new QVBoxLayout(this);
    lay->setContentsMargins(8, 8, 8, 8);
    lay->setSpacing(6);

    m_hint_label = new QLabel(QString::fromUtf8("Chọn ngày bắt đầu"));
    m_hint_label->setAlignment(Qt::AlignCenter);
    m_hint_label->setStyleSheet("font-size: 12px; border: none;");
    lay->addWidget(m_hint_label);

    m_calendar = new QCalendarWidget;
    m_calendar->setGridVisible(true);
    m_calendar->setVerticalHeaderFormat(QCalendarWidget::NoVerticalHeader);
    m_calendar->setMinimumSize(280, 220);
    lay->addWidget(m_calendar);

    // Bottom buttons: Clear + Confirm
    auto* btn_layout = new QHBoxLayout;
    btn_layout->setSpacing(8);

    m_clear_btn = new QPushButton(QString::fromUtf8("Xoá"));
    m_clear_btn->setCursor(Qt::PointingHandCursor);
    m_clear_btn->setFixedHeight(28);
    btn_layout->addWidget(m_clear_btn);

    btn_layout->addStretch();

    m_confirm_btn = new QPushButton(QString::fromUtf8("Đồng ý"));
    m_confirm_btn->setCursor(Qt::PointingHandCursor);
    m_confirm_btn->setFixedHeight(28);
    btn_layout->addWidget(m_confirm_btn);

    lay->addLayout(btn_layout);

    connect(m_calendar, &QCalendarWidget::clicked, this, &DateRangePopup::on_date_clicked);
    connect(m_confirm_btn, &QPushButton::clicked, this, &DateRangePopup::on_confirm);
    connect(m_clear_btn, &QPushButton::clicked, this, &DateRangePopup::on_clear);

    setFixedSize(310, 330);
}

void DateRangePopup::clear()
{
    m_start = QDate();
    m_end = QDate();
    m_selecting_end = false;
    m_hint_label->setText(QString::fromUtf8("Chọn ngày bắt đầu"));
    clear_highlight();
}

void DateRangePopup::apply_theme(bool dark)
{
    QString bg = dark ? "#23272e" : "#ffffff";
    QString fg = dark ? "#e0e0e0" : "#333333";
    QString border = dark ? "#444" : "#e0e0e0";
    QString primary = dark ? "#1a73e8" : "#16baaa";

    setStyleSheet(QString(
        "DateRangePopup { background: %1; border: 1px solid %2; border-radius: 4px; }"
        "QLabel { color: %3; background: transparent; border: none; }"
    ).arg(bg, border, fg));

    m_confirm_btn->setStyleSheet(QString(
        "QPushButton { background: %1; color: #fff; border: none;"
        "  padding: 0 16px; border-radius: 3px; font-size: 12px; }"
        "QPushButton:hover { opacity: 0.85; }"
    ).arg(primary));

    m_clear_btn->setStyleSheet(QString(
        "QPushButton { background: transparent; color: %1; border: 1px solid %2;"
        "  padding: 0 16px; border-radius: 3px; font-size: 12px; }"
        "QPushButton:hover { background: %3; }"
    ).arg(fg, border, dark ? "#2a2e35" : "#f5f5f5"));
}

void DateRangePopup::on_date_clicked(const QDate& date)
{
    if (!m_selecting_end) {
        // First click → set start
        m_start = date;
        m_end = QDate();
        m_selecting_end = true;
        m_hint_label->setText(QString::fromUtf8("Chọn ngày kết thúc"));
        clear_highlight();
        QTextCharFormat fmt;
        fmt.setBackground(QColor("#16baaa"));
        fmt.setForeground(Qt::white);
        m_calendar->setDateTextFormat(m_start, fmt);
    } else {
        // Second click → set end
        m_end = date;
        m_selecting_end = false;

        if (m_start > m_end) {
            qSwap(m_start, m_end);
        }

        m_hint_label->setText(
            m_start.toString("yyyy-MM-dd") + "  →  " + m_end.toString("yyyy-MM-dd")
        );

        highlight_range();
        // Don't auto-close — user must click Confirm
    }
}

void DateRangePopup::on_confirm()
{
    if (m_start.isValid() && m_end.isValid()) {
        emit dates_confirmed(m_start, m_end);
    }
}

void DateRangePopup::on_clear()
{
    clear();
    emit dates_cleared();
}

void DateRangePopup::highlight_range()
{
    clear_highlight();
    if (!m_start.isValid() || !m_end.isValid()) return;

    QTextCharFormat range_fmt;
    range_fmt.setBackground(QColor(22, 186, 170, 40));
    range_fmt.setForeground(QColor("#333"));

    QTextCharFormat endpoint_fmt;
    endpoint_fmt.setBackground(QColor("#16baaa"));
    endpoint_fmt.setForeground(Qt::white);

    QDate d = m_start;
    while (d <= m_end) {
        if (d == m_start || d == m_end) {
            m_calendar->setDateTextFormat(d, endpoint_fmt);
        } else {
            m_calendar->setDateTextFormat(d, range_fmt);
        }
        d = d.addDays(1);
    }
}

void DateRangePopup::clear_highlight()
{
    m_calendar->setDateTextFormat(QDate(), QTextCharFormat());
}
