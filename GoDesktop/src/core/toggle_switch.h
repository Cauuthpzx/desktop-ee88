#pragma once

#include <QWidget>

class ToggleSwitch : public QWidget {
    Q_OBJECT

public:
    explicit ToggleSwitch(bool checked = false, QWidget* parent = nullptr);

    bool is_checked() const { return m_checked; }
    void set_checked(bool c);

signals:
    void toggled(bool checked);

protected:
    void paintEvent(QPaintEvent* event) override;
    void mousePressEvent(QMouseEvent* event) override;

private:
    bool m_checked;
};
