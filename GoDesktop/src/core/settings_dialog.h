#pragma once

#include <QDialog>
#include <QTableWidget>
#include <QPushButton>
#include <QLabel>
#include <QVector>
#include <cstdint>

class ThemeManager;
class Translator;
class ApiClient;
class Feedback;

struct AgentInfo {
    int64_t id = 0;
    QString name;
    QString username;
    QString status;
    QString base_url;
    QString created_at;
    bool auto_login = false;
};

class SettingsDialog : public QDialog {
    Q_OBJECT

public:
    explicit SettingsDialog(ThemeManager* theme, Translator* tr,
                            ApiClient* api, QWidget* parent = nullptr);
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
    void load_agents();
    void refresh_table();
    QWidget* make_action_buttons(int row);

    ThemeManager* m_theme;
    Translator* m_tr;
    ApiClient* m_api;
    Feedback* m_feedback;
    QLabel* m_title_label;
    QTableWidget* m_table;
    QPushButton* m_btn_check_all;
    QPushButton* m_btn_login_all;
    QPushButton* m_btn_delete_all;
    QPushButton* m_btn_add;
    QVector<AgentInfo> m_agents;
};
