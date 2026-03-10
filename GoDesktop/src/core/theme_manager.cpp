#include "core/theme_manager.h"

#include <QFile>
#include <QJsonDocument>
#include <QJsonObject>

ThemeManager::ThemeManager(QObject* parent)
    : QObject(parent)
    , m_theme("light")
{
}

void ThemeManager::load_colors(const QString& json_path)
{
    QFile file(json_path);
    if (!file.open(QIODevice::ReadOnly)) {
        // Fallback defaults nếu không tìm thấy file
        m_light = QJsonObject{
            {"primary", "#16baaa"}, {"normal", "#1e9fff"},
            {"warm", "#ffb800"}, {"danger", "#ff5722"}, {"checked", "#16b777"},
            {"bg", "#ffffff"}, {"bg_secondary", "#f9f9f9"},
            {"bg_tertiary", "#f0f0f0"}, {"bg_hover", "#f5f5f5"},
            {"text_primary", "#213547"}, {"text_secondary", "#666666"},
            {"text_muted", "rgba(60, 60, 60, 0.7)"},
            {"text_footer", "rgba(60, 60, 60, 0.5)"},
            {"text_body", "rgba(0, 0, 0, 0.85)"},
            {"text_nav", "rgba(0, 0, 0, 0.8)"},
            {"logo_text", "#213547"},
            {"border", "#e2e2e2"}, {"border_light", "#eeeeee"},
            {"border_box", "#f0f0f0"},
            {"header_bg", "#ffffff"}, {"footer_bg", "#fafafa"},
        };
        m_dark = QJsonObject{
            {"primary", "#16baaa"}, {"normal", "#1e9fff"},
            {"warm", "#ffb800"}, {"danger", "#ff5722"}, {"checked", "#16b777"},
            {"bg", "#181a1b"}, {"bg_secondary", "#1f2122"},
            {"bg_tertiary", "#2b2d2e"}, {"bg_hover", "#2b2d2e"},
            {"text_primary", "#d8d4cf"}, {"text_secondary", "#b0ada8"},
            {"text_muted", "rgba(200, 195, 188, 0.7)"},
            {"text_footer", "rgba(200, 195, 188, 0.5)"},
            {"text_body", "rgba(216, 212, 207, 0.85)"},
            {"text_nav", "rgba(216, 212, 207, 0.8)"},
            {"logo_text", "#d8d4cf"},
            {"border", "#3c3f41"}, {"border_light", "#2e3133"},
            {"border_box", "#2e3133"},
            {"header_bg", "#1f2122"}, {"footer_bg", "#1a1c1d"},
        };
        return;
    }

    auto root = QJsonDocument::fromJson(file.readAll()).object();
    m_light = root.value("light").toObject();
    m_dark = root.value("dark").toObject();
}

void ThemeManager::set_theme(const QString& theme)
{
    if (m_theme != theme) {
        m_theme = theme;
        emit theme_changed(m_theme);
    }
}

QString ThemeManager::theme() const
{
    return m_theme;
}

void ThemeManager::toggle_theme()
{
    set_theme(m_theme == "light" ? "dark" : "light");
}

QString ThemeManager::color(const QString& key) const
{
    const auto& colors = (m_theme == "dark") ? m_dark : m_light;
    return colors.value(key).toString();
}

QString ThemeManager::header_style() const
{
    return QString(
        "background: %1; border-bottom: 1px solid %2;"
    ).arg(color("header_bg"), color("border_light"));
}

QString ThemeManager::page_style() const
{
    return QString("background: %1; border: none;").arg(color("bg"));
}

QString ThemeManager::card_style() const
{
    return QString(
        "background: %1; border: 1px solid %2; padding: 16px 20px;"
    ).arg(color("bg_secondary"), color("border_box"));
}

QString ThemeManager::footer_style() const
{
    return QString(
        "background: %1; border-top: 1px solid %2;"
    ).arg(color("footer_bg"), color("border_light"));
}

QString ThemeManager::nav_style(bool active) const
{
    if (active) {
        return QString(
            "QPushButton {"
            "  background: transparent; border: none;"
            "  color: %1; font-size: 14px; font-weight: bold;"
            "  padding: 6px 14px; border-bottom: 2px solid %1;"
            "}"
        ).arg(color("primary"));
    }
    return QString(
        "QPushButton {"
        "  background: transparent; border: none;"
        "  color: %1; font-size: 14px; padding: 6px 14px;"
        "}"
        "QPushButton:hover { color: %2; }"
    ).arg(color("text_secondary"), color("primary"));
}

QString ThemeManager::menu_style() const
{
    return QString(
        "QPushButton {"
        "  background: transparent; border: none;"
        "  text-align: left; padding: 8px 12px;"
        "  font-size: 13px; color: %1;"
        "}"
        "QPushButton:hover { background: %2; color: %3; }"
    ).arg(color("text_primary"), color("bg_hover"), color("primary"));
}
