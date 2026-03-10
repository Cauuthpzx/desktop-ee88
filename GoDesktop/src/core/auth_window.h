#pragma once

#include <QMainWindow>
#include <QStackedWidget>
#include <QMouseEvent>
#include <QPoint>
#include <memory>

class ApiClient;
class AuthWidget;
class MainWidget;
class ThemeManager;
class Translator;

class AuthWindow : public QMainWindow {
    Q_OBJECT

public:
    explicit AuthWindow(QWidget* parent = nullptr);
    ~AuthWindow() override;

protected:
    void mousePressEvent(QMouseEvent* event) override;
    void mouseMoveEvent(QMouseEvent* event) override;
    void mouseReleaseEvent(QMouseEvent* event) override;

private slots:
    void show_login();
    void on_auth_success();

private:
    std::unique_ptr<ApiClient> m_api;
    ThemeManager* m_theme;
    Translator* m_tr;
    QStackedWidget* m_stack;
    AuthWidget* m_auth;
    MainWidget* m_main;
    bool m_dragging;
    QPoint m_drag_pos;
};
