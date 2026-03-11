#pragma once

#include <QWidget>
#include <QLabel>
#include <QHBoxLayout>
#include <QTimer>
#include <QPropertyAnimation>
#include <QGraphicsOpacityEffect>
#include "core/icon_defs.h"

/**
 * Toast notification — tương đương layer.msg() bên web.
 * Hiển thị thông báo ngắn tự động biến mất.
 * Dùng icon PNG (icons8 fluency) thay vì tự vẽ.
 *
 * Icon types (giống web):
 *   1 = Success (dấu tích xanh lá)
 *   2 = Error   (X đỏ tròn)
 *   3 = Warning (! vàng)
 *   4 = Info    (chat xanh dương)
 *   5 = Loading (mũi tên xoay)
 */
class ToastWidget : public QWidget {
    Q_OBJECT

public:
    enum Icon { Success = 1, Error = 2, Warning = 3, Info = 4, Loading = 5 };

    /**
     * Hiển thị toast trên parent widget.
     * @param parent   Widget cha (toast sẽ hiển thị ở giữa trên cùng)
     * @param message  Nội dung thông báo
     * @param icon     Loại icon (1-5)
     * @param duration Thời gian hiển thị (ms), 0 = không tự đóng
     */
    static ToastWidget* show_toast(QWidget* parent, const QString& message,
                                   Icon icon = Success, int duration = 2000);

    /// Đóng toast thủ công (dùng cho Loading)
    void close_toast();

protected:
    void paintEvent(QPaintEvent* event) override;

private:
    explicit ToastWidget(QWidget* parent, const QString& message, Icon icon, int duration);
    void position_self();

    QLabel* m_icon_label;
    QLabel* m_text_label;
    QGraphicsOpacityEffect* m_opacity;
    Icon m_icon_type;
};
