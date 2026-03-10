#pragma once

#include <QDialog>
#include <QTableWidget>
#include <QPushButton>
#include <QLineEdit>
#include <QLabel>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QHeaderView>
#include <QTextEdit>
#include <QComboBox>

class ThemeManager;
class Translator;

struct AgentInfo {
    QString code;
    QString name;
    QString username;
    QString status;
    QString created_at;
    bool auto_login = false;
};

// ── Add Agent Dialog ──
class AddAgentDialog : public QDialog {
    Q_OBJECT

public:
    explicit AddAgentDialog(ThemeManager* theme, Translator* tr, QWidget* parent = nullptr);
    void apply_theme();
    void retranslate();

    QString agent_name() const;
    QString agent_username() const;
    QString agent_password() const;
    QString agent_base_url() const;

private:
    ThemeManager* m_theme;
    Translator* m_tr;
    QLabel* m_lbl_name;
    QLabel* m_lbl_username;
    QLabel* m_lbl_password;
    QLabel* m_lbl_base_url;
    QLineEdit* m_edit_name;
    QLineEdit* m_edit_username;
    QLineEdit* m_edit_password;
    QLineEdit* m_edit_base_url;
    QPushButton* m_btn_cancel;
    QPushButton* m_btn_add;
    QLabel* m_title_label;
};

// ── Cookies Dialog ──
class CookiesDialog : public QDialog {
    Q_OBJECT

public:
    explicit CookiesDialog(ThemeManager* theme, Translator* tr, QWidget* parent = nullptr);
    void apply_theme();
    void retranslate();
    void set_agent(const QString& name, const QString& username);
    QString cookies_value() const;

private:
    ThemeManager* m_theme;
    Translator* m_tr;
    QLabel* m_lbl_agent;
    QLineEdit* m_edit_agent;
    QLabel* m_lbl_cookies;
    QTextEdit* m_edit_cookies;
    QPushButton* m_btn_cancel;
    QPushButton* m_btn_save;
    QLabel* m_title_label;
};

// ── Main Settings Dialog ──
class SettingsDialog : public QDialog {
    Q_OBJECT

public:
    explicit SettingsDialog(ThemeManager* theme, Translator* tr, QWidget* parent = nullptr);
    void apply_theme();
    void retranslate();

private slots:
    void on_add_agent();
    void on_check_all();
    void on_login_all();
    void on_delete_all();
    void on_edit_agent(int row);
    void on_delete_agent(int row);
    void on_check_agent(int row);
    void on_login_agent(int row);
    void on_assign_cookies(int row);
    void on_toggle_auto_login(int row);

private:
    void setup_ui();
    void populate_sample_data();
    void refresh_table();
    QWidget* make_action_buttons(int row);

    ThemeManager* m_theme;
    Translator* m_tr;
    QLabel* m_title_label;
    QTableWidget* m_table;
    QPushButton* m_btn_check_all;
    QPushButton* m_btn_login_all;
    QPushButton* m_btn_delete_all;
    QPushButton* m_btn_add;
    QVector<AgentInfo> m_agents;
};
