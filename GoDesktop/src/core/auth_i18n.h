#pragma once

#include <QMap>
#include <QString>

namespace AuthI18n {

const QMap<QString, QMap<QString, QString>>& translations();
QString t(const QString& lang, const QString& key);

} // namespace AuthI18n
