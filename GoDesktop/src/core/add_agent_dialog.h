#pragma once

#include <QDialog>
#include <QLabel>
#include <QLineEdit>
#include <QPushButton>

class ThemeManager;
class Translator;

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

    void set_edit_mode(const QString& name, const QString& username, const QString& base_url);

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
