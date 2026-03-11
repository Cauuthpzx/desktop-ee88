#include "core/loading_overlay.h"

#include <QPainter>
#include <QPainterPath>
#include <QConicalGradient>

LoadingOverlay::LoadingOverlay(QWidget* parent)
    : QWidget(parent)
{
    setAttribute(Qt::WA_TransparentForMouseEvents, false);
    setVisible(false);

    connect(&m_timer, &QTimer::timeout, this, [this]() {
        m_angle = (m_angle + 6) % 360;
        update();
    });
}

void LoadingOverlay::start()
{
    if (auto* p = parentWidget()) {
        setGeometry(0, 0, p->width(), p->height());
        raise();
    }
    setVisible(true);
    m_angle = 0;
    m_timer.start(16); // ~60fps
}

void LoadingOverlay::stop()
{
    m_timer.stop();
    setVisible(false);
}

void LoadingOverlay::paintEvent(QPaintEvent*)
{
    QPainter painter(this);
    painter.setRenderHint(QPainter::Antialiasing);

    // Semi-transparent background
    painter.fillRect(rect(), QColor(255, 255, 255, 180));

    // Spinning arc — center of widget
    const int arc_size = 32;
    const int pen_width = 3;
    QRectF arc_rect(
        (width() - arc_size) / 2.0,
        (height() - arc_size) / 2.0,
        arc_size,
        arc_size
    );

    // Conical gradient for smooth fade effect
    QConicalGradient gradient(arc_rect.center(), -m_angle);
    gradient.setColorAt(0.0, QColor(22, 93, 255));      // Primary blue
    gradient.setColorAt(0.5, QColor(22, 93, 255, 80));
    gradient.setColorAt(1.0, QColor(22, 93, 255, 0));    // Fade to transparent

    QPen pen(QBrush(gradient), pen_width, Qt::SolidLine, Qt::RoundCap);
    painter.setPen(pen);
    painter.drawArc(arc_rect, m_angle * 16, 270 * 16);
}
