#include "core/api_error.h"

ApiError ApiError::from_reply(QNetworkReply* reply, const QJsonObject& body)
{
    if (!reply) {
        return ApiError{ApiErrorKind::Unknown, 0, "null reply"};
    }

    ApiError err;

    if (reply->error() == QNetworkReply::NoError) {
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
