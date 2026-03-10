#pragma once

#include <QObject>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QJsonObject>
#include <functional>

class ApiClient : public QObject {
    Q_OBJECT

public:
    using Callback = std::function<void(bool success, const QJsonObject& data)>;

    explicit ApiClient(QObject* parent = nullptr);

    void login(const QString& username, const QString& password, Callback callback);
    void register_user(const QString& username, const QString& password, Callback callback);
    void logout(Callback callback);
    void change_password(const QString& old_password, const QString& new_password, Callback callback);

    void set_token(const QString& token);
    QString token() const;

    void set_username(const QString& username);
    QString username() const;

    void set_base_url(const QString& url);
    QString base_url() const;

    // Session persistence
    void save_session();
    bool load_session();
    void clear_session();
    bool has_valid_session() const;

private:
    void post_request(const QString& path, const QJsonObject& body, Callback callback);
    void put_request(const QString& path, const QJsonObject& body, Callback callback);
    void handle_reply(QNetworkReply* reply, Callback callback);

    QNetworkAccessManager m_manager;
    QString m_token;
    QString m_username;
    QString m_base_url;
};
