#pragma once

#include <QString>
#include <QJsonObject>
#include <QNetworkReply>

/**
 * Hệ thống error cho API calls.
 * Thay thế raw bool success bằng typed error.
 */

enum class ApiErrorKind {
    None,           // Không lỗi
    Network,        // Mất kết nối, DNS fail, timeout
    Timeout,        // Request timeout
    ServerError,    // HTTP 5xx
    AuthError,      // HTTP 401/403
    ValidationError,// HTTP 400/422
    ParseError,     // Response không parse được
    Unknown         // Lỗi không xác định
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

    static ApiError from_reply(QNetworkReply* reply, const QJsonObject& body) {
        ApiError err;

        if (reply->error() == QNetworkReply::NoError) {
            // HTTP OK nhưng server trả error
            if (body.contains("error")) {
                err.kind = ApiErrorKind::ValidationError;
                err.message = body["error"].toString();
                err.http_code = reply->attribute(
                    QNetworkRequest::HttpStatusCodeAttribute).toInt();
            }
            return err;
        }

        err.http_code = reply->attribute(
            QNetworkRequest::HttpStatusCodeAttribute).toInt();
        err.message = body.contains("error")
            ? body["error"].toString()
            : reply->errorString();

        switch (reply->error()) {
        case QNetworkReply::TimeoutError:
        case QNetworkReply::OperationCanceledError:
            err.kind = ApiErrorKind::Timeout;
            break;
        case QNetworkReply::ConnectionRefusedError:
        case QNetworkReply::RemoteHostClosedError:
        case QNetworkReply::HostNotFoundError:
        case QNetworkReply::UnknownNetworkError:
            err.kind = ApiErrorKind::Network;
            break;
        case QNetworkReply::AuthenticationRequiredError:
            err.kind = ApiErrorKind::AuthError;
            break;
        default:
            if (err.http_code >= 500) {
                err.kind = ApiErrorKind::ServerError;
            } else if (err.http_code == 401 || err.http_code == 403) {
                err.kind = ApiErrorKind::AuthError;
            } else if (err.http_code >= 400) {
                err.kind = ApiErrorKind::ValidationError;
            } else {
                err.kind = ApiErrorKind::Unknown;
            }
            break;
        }
        return err;
    }
};
