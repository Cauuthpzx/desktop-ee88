#pragma once

#include <QWidget>
#include <QLineEdit>
#include <QPushButton>
#include <QLabel>

class ApiClient;

class RegisterWidget : public QWidget {
    Q_OBJECT

public:
    explicit RegisterWidget(ApiClient* api, QWidget* parent = nullptr);

signals:
    void register_success();
    void switch_to_login();

private slots:
    void on_submit();

private:
    void setup_ui();
    void set_error(const QString& msg);
    void clear_error();

    ApiClient* m_api;
    QLineEdit* m_username_input;
    QLineEdit* m_password_input;
    QLineEdit* m_confirm_input;
    QPushButton* m_submit_btn;
    QLabel* m_error_label;
    QWidget* m_error_box;
    bool m_loading;
};
