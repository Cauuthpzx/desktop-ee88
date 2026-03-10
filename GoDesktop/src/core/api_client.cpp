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

void ApiClient::set_max_retries(int n)
{
    m_max_retries = n;
}

void ApiClient::set_request_timeout(int ms)
{
    m_request_timeout = ms;
}

// ── Auth endpoints (legacy Callback) ──

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

// ── Generic request methods (new ApiCallback with retry) ──

void ApiClient::get(const QString& path, ApiCallback callback)
{
    execute_with_retry("GET", path, QJsonObject{}, std::move(callback));
}

void ApiClient::post(const QString& path, const QJsonObject& body, ApiCallback callback)
{
    execute_with_retry("POST", path, body, std::move(callback));
}

void ApiClient::put(const QString& path, const QJsonObject& body, ApiCallback callback)
{
    execute_with_retry("PUT", path, body, std::move(callback));
}

void ApiClient::del(const QString& path, ApiCallback callback)
{
    execute_with_retry("DELETE", path, QJsonObject{}, std::move(callback));
}

// ── Request building ──

QNetworkRequest ApiClient::build_request(const QString& path) const
{
    QNetworkRequest request(QUrl(m_base_url + path));
    request.setHeader(QNetworkRequest::ContentTypeHeader, "application/json");
    request.setTransferTimeout(m_request_timeout);
    if (!m_token.isEmpty()) {
        request.setRawHeader("Authorization", ("Bearer " + m_token).toUtf8());
    }
    return request;
}

// ── Retry logic ──

void ApiClient::execute_with_retry(
    const QString& method,
    const QString& path,
    const QJsonObject& body,
    ApiCallback callback,
    int attempt)
{
    auto request = build_request(path);
    QNetworkReply* reply = nullptr;

    if (method == "GET") {
        reply = m_manager.get(request);
    } else if (method == "POST") {
        reply = m_manager.post(request, QJsonDocument(body).toJson());
    } else if (method == "PUT") {
        reply = m_manager.put(request, QJsonDocument(body).toJson());
    } else if (method == "DELETE") {
        reply = m_manager.deleteResource(request);
    }

    if (!reply) {
        ApiError err;
        err.kind = ApiErrorKind::Unknown;
        err.message = "Invalid HTTP method";
        callback(err, {});
        return;
    }

    handle_api_reply(reply, std::move(callback), method, path, body, attempt);
}

void ApiClient::handle_api_reply(
    QNetworkReply* reply,
    ApiCallback callback,
    const QString& method,
    const QString& path,
    const QJsonObject& body,
    int attempt)
{
    connect(reply, &QNetworkReply::finished, this,
        [this, reply, cb = std::move(callback), method, path, body, attempt]() mutable {
            auto root = QJsonDocument::fromJson(reply->readAll()).object();
            auto err = ApiError::from_reply(reply, root);
            reply->deleteLater();

            // Retry nếu lỗi retryable và chưa hết số lần
            if (!err.is_ok() && err.is_retryable() && attempt < m_max_retries) {
                int delay = k_retry_base_delay * (1 << attempt);  // exponential backoff
                QTimer::singleShot(delay, this, [this, method, path, body,
                                                  cb = std::move(cb), attempt]() mutable {
                    execute_with_retry(method, path, body, std::move(cb), attempt + 1);
                });
                return;
            }

            if (err.is_ok()) {
                // Success: check server response format
                const bool status_ok = (root.value("status").toString() == "success");
                if (!status_ok && root.contains("error")) {
                    err.kind = ApiErrorKind::ValidationError;
                    err.message = root["error"].toString();
                    cb(err, root);
                } else {
                    cb(ApiError::none(), root.value("data").toObject());
                }
            } else {
                cb(err, root);
            }
        });
}

// ── Legacy helpers (backward compat) ──

void ApiClient::post_request(const QString& path, const QJsonObject& body, Callback callback)
{
    auto request = build_request(path);
    auto* reply = m_manager.post(request, QJsonDocument(body).toJson());
    handle_reply(reply, std::move(callback));
}

void ApiClient::put_request(const QString& path, const QJsonObject& body, Callback callback)
{
    auto request = build_request(path);
    auto* reply = m_manager.put(request, QJsonDocument(body).toJson());
    handle_reply(reply, std::move(callback));
}

// ── Session ──

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

    auto payload_b64 = parts[1];
    payload_b64.replace('-', '+');
    payload_b64.replace('_', '/');
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
        const auto data = success ? root.value("data").toObject() : root;
        cb(success, data);
        reply->deleteLater();
    });
}
