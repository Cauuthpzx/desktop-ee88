#pragma once

#include <QWidget>
#include <QLabel>
#include <QPushButton>
#include <QVector>

class ThemeManager;
class Translator;

class HomePage : public QWidget {
    Q_OBJECT

public:
    explicit HomePage(ThemeManager* theme, Translator* tr, QWidget* parent = nullptr);

    void set_username(const QString& username);
    void apply_theme();
    void retranslate();

private:
    void setup_ui();

    ThemeManager* m_theme;
    Translator* m_tr;

    QWidget* m_hero_widget;
    QLabel* m_hero_title;
    QLabel* m_hero_tagline;
    QPushButton* m_explore_btn;
    QLabel* m_welcome_text;
    QLabel* m_welcome_name;

    QWidget* m_boxes_container;
    QVector<QWidget*> m_feature_boxes;
    QVector<QWidget*> m_feature_icon_bgs;
    QVector<QLabel*> m_feature_titles;
    QVector<QLabel*> m_feature_descs;

    QWidget* m_footer;
    QLabel* m_footer_text;
};
