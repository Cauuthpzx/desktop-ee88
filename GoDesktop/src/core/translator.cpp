#include "core/translator.h"

#include <QFile>
#include <QJsonDocument>

Translator::Translator(QObject* parent)
    : QObject(parent)
    , m_locale("vi_VN")
{
}

void Translator::load_language(const QString& locale, const QString& json_path)
{
    QFile file(json_path);
    if (!file.open(QIODevice::ReadOnly)) {
        return;
    }
    m_translations[locale] = QJsonDocument::fromJson(file.readAll()).object();
}

void Translator::set_locale(const QString& locale)
{
    if (m_locale != locale && m_translations.contains(locale)) {
        m_locale = locale;
        emit locale_changed(m_locale);
    }
}

QString Translator::locale() const
{
    return m_locale;
}

QString Translator::t(const QString& key) const
{
    if (!m_translations.contains(m_locale)) {
        return key;
    }
    const auto parts = key.split('.');
    return resolve(m_translations[m_locale], parts);
}

QStringList Translator::available_locales() const
{
    return m_translations.keys();
}

QString Translator::locale_label(const QString& locale) const
{
    if (locale == "vi_VN") return "VN";
    if (locale == "en_US") return "EN";
    if (locale == "zh_CN") return QString::fromUtf8("\u4e2d");
    return locale;
}

QString Translator::resolve(const QJsonObject& obj, const QStringList& parts) const
{
    if (parts.isEmpty()) {
        return {};
    }

    auto value = obj.value(parts.first());
    if (parts.size() == 1) {
        return value.toString(parts.first());
    }

    if (value.isObject()) {
        return resolve(value.toObject(), parts.mid(1));
    }

    return parts.join('.');
}
