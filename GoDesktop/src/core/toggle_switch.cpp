#include "core/toggle_switch.h"
#include "core/icon_defs.h"

#include <QPainter>
#include <QMouseEvent>

ToggleSwitch::ToggleSwitch(bool checked, QWidget* parent)
    : QWidget(parent)
    , m_checked(checked)
{
    setFixedSize(IconDefs::k_toggle_width, IconDefs::k_toggle_height);
    setCursor(Qt::PointingHandCursor);
}

void ToggleSwitch::set_checked(bool c)
{
    m_checked = c;
    update();
}

void ToggleSwitch::paintEvent(QPaintEvent* /*event*/)
{
    QPainter p(this);
    p.setRenderHint(QPainter::Antialiasing);

    QColor track_color = m_checked ? QColor(IconDefs::k_color_primary) : QColor(IconDefs::k_color_muted);
    p.setBrush(track_color);
    p.setPen(Qt::NoPen);
    p.drawRoundedRect(0, 0, width(), height(), height() / 2, height() / 2);

    int thumb_size = height() - 4;
    int x = m_checked ? width() - thumb_size - 2 : 2;
    p.setBrush(Qt::white);
    p.drawEllipse(x, 2, thumb_size, thumb_size);

    p.setPen(Qt::white);
    QFont f = font();
    f.setPixelSize(IconDefs::k_font_toggle);
    p.setFont(f);
    if (m_checked) {
        p.drawText(QRect(4, 0, width() / 2, height()), Qt::AlignCenter, "Auto");
    } else {
        p.drawText(QRect(width() / 2, 0, width() / 2 - 2, height()), Qt::AlignCenter, "Off");
    }
}

void ToggleSwitch::mousePressEvent(QMouseEvent* e)
{
    if (e->button() == Qt::LeftButton) {
        m_checked = !m_checked;
        update();
        emit toggled(m_checked);
    }
}
