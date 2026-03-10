#include "core/api_client.h"

#include <QJsonDocument>
#include <QJsonArray>
#include <QNetworkRequest>
#include <QSettings>
#include <QUrl>

ApiClient::ApiClient(QObject* parent)
    : QObject(parent)
    , m_base_url("http://localhost:8080")
{
}

void ApiClient::set_token(const QString& token)
{
    m_token = token;
}

QString ApiClient::token() const
{
    return m_token;
}

void ApiClient::set_username(const QString& username)
{
    m_username = username;
}

QString ApiClient::username() const
{
    return m_username;
}

void ApiClient::set_base_url(const QString& url)
{
    m_base_url = url;
}

QString ApiClient::base_url() const
{
    return m_base_url;
}

void ApiClient::login(const QString& username, const QString& password, Callback callback)
{
    QJsonObject body;
    body["username"] = username;
    body["password"] = password;
    post_request("/api/auth/login", body, callback);
}

void ApiClient::register_user(const QString& username, const QString& password, Callback callback)
{
    QJsonObject body;
    body["username"] = username;
    body["password"] = password;
    post_request("/api/auth/register", body, callback);
}

void ApiClient::logout(Callback callback)
{
    post_request("/api/auth/logout", QJsonObject{}, callback);
}

void ApiClient::change_password(const QString& old_password, const QString& new_password, Callback callback)
{
    QJsonObject body;
    body["old_password"] = old_password;
    body["new_password"] = new_password;
    post_request("/api/auth/change-password", body, callback);
}

void ApiClient::post_request(const QString& path, const QJsonObject& body, Callback callback)
{
    QNetworkRequest request(QUrl(m_base_url + path));
    request.setHeader(QNetworkRequest::ContentTypeHeader, "application/json");
    if (!m_token.isEmpty()) {
        request.setRawHeader("Authorization", ("Bearer " + m_token).toUtf8());
    }

    auto* reply = m_manager.post(request, QJsonDocument(body).toJson());
    handle_reply(reply, std::move(callback));
}

void ApiClient::put_request(const QString& path, const QJsonObject& body, Callback callback)
{
    QNetworkRequest request(QUrl(m_base_url + path));
    request.setHeader(QNetworkRequest::ContentTypeHeader, "application/json");
    if (!m_token.isEmpty()) {
        request.setRawHeader("Authorization", ("Bearer " + m_token).toUtf8());
    }

    auto* reply = m_manager.put(request, QJsonDocument(body).toJson());
    handle_reply(reply, std::move(callback));
}

void ApiClient::save_session()
{
    QSettings settings("MaxHub", "GoDesktop");
    settings.setValue("session/token", m_token);
    settings.setValue("session/username", m_username);
}

bool ApiClient::load_session()
{
    QSettings settings("MaxHub", "GoDesktop");
    const auto token = settings.value("session/token").toString();
    const auto username = settings.value("session/username").toString();

    if (token.isEmpty() || username.isEmpty()) {
        return false;
    }

    // Decode JWT payload to check expiry (base64 decode middle part)
    const auto parts = token.split('.');
    if (parts.size() != 3) {
        clear_session();
        return false;
    }

    // Decode base64url payload
    auto payload_b64 = parts[1];
    // base64url → base64
    payload_b64.replace('-', '+');
    payload_b64.replace('_', '/');
    // Pad to multiple of 4
    while (payload_b64.size() % 4 != 0) {
        payload_b64.append('=');
    }

    const auto payload_json = QByteArray::fromBase64(payload_b64.toUtf8());
    const auto payload = QJsonDocument::fromJson(payload_json).object();

    if (!payload.contains("exp")) {
        clear_session();
        return false;
    }

    const auto exp = static_cast<qint64>(payload["exp"].toDouble());
    const auto now = QDateTime::currentSecsSinceEpoch();

    if (now >= exp) {
        clear_session();
        return false;
    }

    m_token = token;
    m_username = username;
    return true;
}

void ApiClient::clear_session()
{
    QSettings settings("MaxHub", "GoDesktop");
    settings.remove("session/token");
    settings.remove("session/username");
    m_token.clear();
}

bool ApiClient::has_valid_session() const
{
    return !m_token.isEmpty() && !m_username.isEmpty();
}

void ApiClient::handle_reply(QNetworkReply* reply, Callback callback)
{
    connect(reply, &QNetworkReply::finished, this, [reply, cb = std::move(callback)]() {
        auto root = QJsonDocument::fromJson(reply->readAll()).object();
        const bool success = (root.value("status").toString() == "success");
        // Trả về object "data" nếu success, hoặc root nếu error
        const auto data = success ? root.value("data").toObject() : root;
        cb(success, data);
        reply->deleteLater();
    });
}
