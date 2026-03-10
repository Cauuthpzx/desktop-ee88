#pragma once

#include <QWidget>
#include <QLineEdit>
#include <QPushButton>
#include <QLabel>
#include <QStackedWidget>

class ApiClient;

class AuthWidget : public QWidget {
    Q_OBJECT

public:
    explicit AuthWidget(ApiClient* api, QWidget* parent = nullptr);
    void show_login_tab();
    void show_register_tab();

signals:
    void login_success();

private slots:
    void on_login_submit();
    void on_register_submit();

private:
    void setup_ui();
    void apply_theme();
    void toggle_theme();
    void switch_tab(int index);
    void set_error(const QString& msg);
    void clear_error();
    void update_strength();
    QString t(const QString& key) const;

    ApiClient* m_api;
    bool m_dark;
    QString m_lang;
    int m_active_tab; // 0=login, 1=register

    // Theme-dependent widgets (need re-styling)
    QWidget* m_root;
    QWidget* m_left_panel;
    QWidget* m_right_panel;
    QWidget* m_card;
    QLabel* m_heading;
    QLabel* m_desc;
    QLabel* m_logo_label;
    QList<QLabel*> m_pills;

    // Tab buttons
    QPushButton* m_tab_login_btn;
    QPushButton* m_tab_register_btn;
    QWidget* m_tab_indicator;

    // Login form
    QWidget* m_login_page;
    QLabel* m_login_title;
    QLabel* m_login_subtitle;
    QLineEdit* m_login_user;
    QLineEdit* m_login_pass;
    QLabel* m_login_user_lbl;
    QLabel* m_login_pass_lbl;
    QPushButton* m_login_submit;
    QLabel* m_login_remember_lbl;

    // Register form
    QWidget* m_register_page;
    QLabel* m_reg_title;
    QLabel* m_reg_subtitle;
    QLineEdit* m_reg_user;
    QLineEdit* m_reg_pass;
    QLineEdit* m_reg_confirm;
    QLabel* m_reg_user_lbl;
    QLabel* m_reg_pass_lbl;
    QLabel* m_reg_confirm_lbl;
    QPushButton* m_reg_submit;
    QWidget* m_strength_bar_1;
    QWidget* m_strength_bar_2;
    QWidget* m_strength_bar_3;
    QWidget* m_strength_bar_4;
    QLabel* m_strength_label;
    QWidget* m_strength_row;
    QLabel* m_reg_terms_lbl;

    // Shared
    QStackedWidget* m_form_stack;
    QLabel* m_error_label;
    QWidget* m_error_box;
    QPushButton* m_cancel_btn;
    QPushButton* m_theme_toggle;
    QList<QPushButton*> m_lang_btns;
    QPushButton* m_social_google;
    QPushButton* m_social_github;
    QWidget* m_divider_row;
    QWidget* m_social_row;
    QLabel* m_or_label;
    QLabel* m_footer_text;
    QPushButton* m_footer_link;
    QPushButton* m_close_btn;
    QWidget* m_divider_line_1;
    QWidget* m_divider_line_2;

    int m_password_strength;
    bool m_loading;
};
