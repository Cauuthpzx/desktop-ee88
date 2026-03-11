#include "core/toast_widget.h"

#include <QPainter>
#include <QPainterPath>

// ── Icon resource paths ──

static const char* icon_resource(ToastWidget::Icon type)
{
    switch (type) {
    case ToastWidget::Success:  return ":/icons/toast_success";
    case ToastWidget::Error:    return ":/icons/toast_error";
    case ToastWidget::Warning:  return ":/icons/toast_warning";
    case ToastWidget::Info:     return ":/icons/toast_info";
    case ToastWidget::Loading:  return ":/icons/toast_loading";
    }
    return ":/icons/toast_info";
}

static const char* toast_border_color(ToastWidget::Icon type)
{
    switch (type) {
    case ToastWidget::Success:  return "#d4edda";
    case ToastWidget::Error:    return "#f8d7da";
    case ToastWidget::Warning:  return "#fff3cd";
    case ToastWidget::Info:     return "#d1ecf1";
    case ToastWidget::Loading:  return "#e2e3e5";
    }
    return "#e2e3e5";
}

static const char* toast_bg_color(ToastWidget::Icon type)
{
    switch (type) {
    case ToastWidget::Success:  return "#f0fff4";
    case ToastWidget::Error:    return "#fff5f5";
    case ToastWidget::Warning:  return "#fffbeb";
    case ToastWidget::Info:     return "#eff8ff";
    case ToastWidget::Loading:  return "#f7f7f7";
    }
    return "#f7f7f7";
}

static const char* toast_text_color(ToastWidget::Icon type)
{
    switch (type) {
    case ToastWidget::Success:  return "#155724";
    case ToastWidget::Error:    return "#721c24";
    case ToastWidget::Warning:  return "#856404";
    case ToastWidget::Info:     return "#0c5460";
    case ToastWidget::Loading:  return "#383d41";
    }
    return "#383d41";
}

// ── Constructor ──

ToastWidget::ToastWidget(QWidget* parent, const QString& message, Icon icon, int duration)
    : QWidget(parent)
    , m_icon_type(icon)
{
    setWindowFlags(Qt::Widget);
    setAttribute(Qt::WA_TransparentForMouseEvents);
    setAttribute(Qt::WA_DeleteOnClose);

    auto* lay = new QHBoxLayout(this);
    lay->setContentsMargins(12, 8, 16, 8);
    lay->setSpacing(8);

    // Icon from PNG resource
    m_icon_label = new QLabel;
    m_icon_label->setFixedSize(24, 24);
    m_icon_label->setAlignment(Qt::AlignCenter);
    m_icon_label->setStyleSheet("QLabel { border: none; background: transparent; }");
    QPixmap pix(icon_resource(icon));
    if (!pix.isNull()) {
        m_icon_label->setPixmap(pix.scaled(24, 24, Qt::KeepAspectRatio, Qt::SmoothTransformation));
    }
    lay->addWidget(m_icon_label);

    // Text
    m_text_label = new QLabel(message);
    m_text_label->setStyleSheet(QString(
        "QLabel { color: %1; font-size: 13px; border: none; background: transparent; }"
    ).arg(toast_text_color(icon)));
    lay->addWidget(m_text_label);

    adjustSize();
    setFixedHeight(sizeHint().height());

    // Opacity effect for fade out
    m_opacity = new QGraphicsOpacityEffect(this);
    m_opacity->setOpacity(1.0);
    setGraphicsEffect(m_opacity);

    // Position at top center of parent
    position_self();

    // Auto-close after duration
    if (duration > 0) {
        QTimer::singleShot(duration, this, [this]() {
            auto* fade = new QPropertyAnimation(m_opacity, "opacity", this);
            fade->setDuration(300);
            fade->setStartValue(1.0);
            fade->setEndValue(0.0);
            connect(fade, &QPropertyAnimation::finished, this, &QWidget::close);
            fade->start();
        });
    }

    show();
    raise();
}

ToastWidget* ToastWidget::show_toast(QWidget* parent, const QString& message,
                                      Icon icon, int duration)
{
    return new ToastWidget(parent, message, icon, duration);
}

void ToastWidget::close_toast()
{
    auto* fade = new QPropertyAnimation(m_opacity, "opacity", this);
    fade->setDuration(200);
    fade->setStartValue(1.0);
    fade->setEndValue(0.0);
    connect(fade, &QPropertyAnimation::finished, this, &QWidget::close);
    fade->start();
}

void ToastWidget::position_self()
{
    if (!parentWidget()) return;
    int px = (parentWidget()->width() - sizeHint().width()) / 2;
    int py = 30;  // 30px from top
    move(px, py);
    setFixedWidth(sizeHint().width());
}

void ToastWidget::paintEvent(QPaintEvent*)
{
    QPainter p(this);
    p.setRenderHint(QPainter::Antialiasing);

    QRectF rect(0.5, 0.5, width() - 1, height() - 1);

    // Shadow
    p.setPen(Qt::NoPen);
    p.setBrush(QColor(0, 0, 0, 12));
    p.drawRoundedRect(rect.adjusted(1, 2, 1, 2), 6, 6);

    // Background
    QPainterPath path;
    path.addRoundedRect(rect, 6, 6);
    p.fillPath(path, QColor(toast_bg_color(m_icon_type)));

    // Border
    p.setPen(QPen(QColor(toast_border_color(m_icon_type)), 1));
    p.setBrush(Qt::NoBrush);
    p.drawPath(path);
}
