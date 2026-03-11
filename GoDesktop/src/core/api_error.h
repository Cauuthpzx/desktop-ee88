#pragma once

#include <QString>
#include <QJsonObject>
#include <QNetworkReply>

enum class ApiErrorKind {
    None,
    Network,
    Timeout,
    ServerError,
    AuthError,
    ValidationError,
    ParseError,
    Unknown
};

struct ApiError {
    ApiErrorKind kind = ApiErrorKind::None;
    int http_code = 0;
    QString message;

    bool is_ok() const { return kind == ApiErrorKind::None; }
    bool is_retryable() const {
        return kind == ApiErrorKind::Network
            || kind == ApiErrorKind::Timeout
            || kind == ApiErrorKind::ServerError;
    }

    static ApiError none() { return {}; }
    static ApiError from_reply(QNetworkReply* reply, const QJsonObject& body);
};
