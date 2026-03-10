#pragma once

#include <QObject>
#include <QJsonObject>
#include <QString>
#include <QMap>

class Translator : public QObject {
    Q_OBJECT

public:
    explicit Translator(QObject* parent = nullptr);

    void load_language(const QString& locale, const QString& json_path);
    void set_locale(const QString& locale);
    QString locale() const;

    // t("nav.home") → "Trang chủ"
    QString t(const QString& key) const;

    QStringList available_locales() const;
    QString locale_label(const QString& locale) const;

signals:
    void locale_changed(const QString& locale);

private:
    QString m_locale;
    QMap<QString, QJsonObject> m_translations;

    QString resolve(const QJsonObject& obj, const QStringList& parts) const;
};
