#pragma once

#include <QObject>
#include <QJsonObject>
#include <QString>

class ThemeManager : public QObject {
    Q_OBJECT

public:
    explicit ThemeManager(QObject* parent = nullptr);

    void load_colors(const QString& json_path);
    void set_theme(const QString& theme);
    QString theme() const;
    void toggle_theme();

    QString color(const QString& key) const;

    // Tiện ích lấy stylesheet cho toàn bộ app
    QString header_style() const;
    QString page_style() const;
    QString card_style() const;
    QString footer_style() const;
    QString nav_style(bool active) const;
    QString menu_style() const;

signals:
    void theme_changed(const QString& theme);

private:
    QString m_theme;
    QJsonObject m_light;
    QJsonObject m_dark;
};
