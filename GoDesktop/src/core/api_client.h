#pragma once

#include <QObject>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QJsonObject>
#include <QTimer>
#include <functional>

#include "core/api_error.h"

class ApiClient : public QObject {
    Q_OBJECT

public:
    using Callback = std::function<void(bool success, const QJsonObject& data)>;
    using ApiCallback = std::function<void(const ApiError& error, const QJsonObject& data)>;

    explicit ApiClient(QObject* parent = nullptr);

    // Auth endpoints
    void login(const QString& username, const QString& password, Callback callback);
    void register_user(const QString& username, const QString& password, Callback callback);
    void logout(Callback callback);
    void change_password(const QString& old_password, const QString& new_password, Callback callback);

    // Generic requests
    void get(const QString& path, ApiCallback callback);
    void post(const QString& path, const QJsonObject& body, ApiCallback callback);
    void put(const QString& path, const QJsonObject& body, ApiCallback callback);
    void patch(const QString& path, const QJsonObject& body, ApiCallback callback);
    void del(const QString& path, ApiCallback callback);

    void set_token(const QString& token);
    QString token() const;

    void set_username(const QString& username);
    QString username() const;

    void set_base_url(const QString& url);
    QString base_url() const;

    // Retry config
    void set_max_retries(int n);
    void set_request_timeout(int ms);

    // Session persistence
    void save_session();
    bool load_session();
    void clear_session();
    bool has_valid_session() const;

private:
    // Legacy helpers (backward compat for auth endpoints)
    void post_request(const QString& path, const QJsonObject& body, Callback callback);
    void put_request(const QString& path, const QJsonObject& body, Callback callback);
    void handle_reply(QNetworkReply* reply, Callback callback);

    // New request system with retry
    QNetworkRequest build_request(const QString& path) const;
    void execute_with_retry(
        const QString& method,
        const QString& path,
        const QJsonObject& body,
        ApiCallback callback,
        int attempt = 0
    );
    void handle_api_reply(QNetworkReply* reply, ApiCallback callback,
                          const QString& method, const QString& path,
                          const QJsonObject& body, int attempt);

    QNetworkAccessManager m_manager;
    QString m_token;
    QString m_username;
    QString m_base_url;
    int m_max_retries = 2;
    int m_request_timeout = 15000;  // 15s

    static constexpr int k_retry_base_delay = 500;  // ms
};
