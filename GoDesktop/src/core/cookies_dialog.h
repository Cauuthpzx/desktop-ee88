#pragma once

#include <QDialog>
#include <QLabel>
#include <QLineEdit>
#include <QTextEdit>
#include <QPushButton>

class ThemeManager;
class Translator;

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
