#pragma once

#include <QWidget>
#include <QLineEdit>
#include <QPushButton>
#include <QLabel>

class ApiClient;

class LoginWidget : public QWidget {
    Q_OBJECT

public:
    explicit LoginWidget(ApiClient* api, QWidget* parent = nullptr);

signals:
    void login_success();
    void switch_to_register();

private slots:
    void on_submit();

private:
    void setup_ui();
    void set_error(const QString& msg);
    void clear_error();

    ApiClient* m_api;
    QLineEdit* m_username_input;
    QLineEdit* m_password_input;
    QPushButton* m_submit_btn;
    QLabel* m_error_label;
    QWidget* m_error_box;
    bool m_loading;
};
