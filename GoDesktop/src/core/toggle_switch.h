#pragma once

#include <QWidget>
#include <QPainter>
#include <QMouseEvent>
#include "core/icon_defs.h"

class ToggleSwitch : public QWidget {
    Q_OBJECT

public:
    explicit ToggleSwitch(bool checked = false, QWidget* parent = nullptr)
        : QWidget(parent), m_checked(checked)
    {
        setFixedSize(IconDefs::k_toggle_width, IconDefs::k_toggle_height);
        setCursor(Qt::PointingHandCursor);
    }

    bool is_checked() const { return m_checked; }
    void set_checked(bool c) { m_checked = c; update(); }

signals:
    void toggled(bool checked);

protected:
    void paintEvent(QPaintEvent*) override {
        QPainter p(this);
        p.setRenderHint(QPainter::Antialiasing);

        QColor track_color = m_checked ? QColor("#16baaa") : QColor("#cccccc");
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

    void mousePressEvent(QMouseEvent* e) override {
        if (e->button() == Qt::LeftButton) {
            m_checked = !m_checked;
            update();
            emit toggled(m_checked);
        }
    }

private:
    bool m_checked;
};
