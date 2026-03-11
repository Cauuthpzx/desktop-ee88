#pragma once

#include <QWidget>
#include <QTimer>

// LoadingOverlay — spinning arc overlay (matches Layui-Vue type=1).
// Đặt làm child widget, gọi show()/hide() để bật/tắt loading.
class LoadingOverlay : public QWidget {
    Q_OBJECT

public:
    explicit LoadingOverlay(QWidget* parent = nullptr);

    void start();
    void stop();

protected:
    void paintEvent(QPaintEvent* event) override;

private:
    QTimer m_timer;
    int m_angle = 0;
};
