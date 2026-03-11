#include "core/upstream_client.h"
#include "core/api_client.h"
#include "core/upstream_crypto.h"

#include <QJsonDocument>
#include <QJsonArray>
#include <QJsonObject>
#include <QNetworkRequest>
#include <QUrl>
#include <QUrlQuery>

#include <QDebug>
#include <algorithm>
#include <memory>

static const char* k_default_base_url = "https://a2u4k.ee88dly.com";
static const char* k_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                                   "Chrome/131.0.0.0 Safari/537.36";

UpstreamClient::UpstreamClient(ApiClient* api, QObject* parent)
    : QObject(parent)
    , m_api(api)
{
    m_nam.setRedirectPolicy(QNetworkRequest::ManualRedirectPolicy);
}

QString UpstreamClient::default_base_url()
{
    return QString::fromLatin1(k_default_base_url);
}

int UpstreamClient::agent_count() const
{
    return static_cast<int>(m_agents.size());
}

bool UpstreamClient::has_credentials() const
{
    return !m_agents.empty();
}

void UpstreamClient::invalidate_cache()
{
    m_agent_cache.clear();
    m_merged_cache.clear();
    m_revalidating.clear();
}

// ── Load credentials từ Goserver ──

void UpstreamClient::load_credentials(std::function<void(bool ok)> callback)
{
    m_api->get("/api/agents/upstream-info", [this, callback](const ApiError& err, const QJsonObject& data) {
        if (err.kind != ApiErrorKind::None) {
            if (callback) callback(false);
            return;
        }

        m_agents.clear();
        invalidate_cache();

        auto arr = data["agents"].toArray();
        m_agents.reserve(static_cast<size_t>(arr.size()));

        for (const auto& val : arr) {
            auto obj = val.toObject();
            AgentCredential cred;
            cred.id = obj["id"].toInteger();
            cred.name = obj["name"].toString();
            cred.base_url = obj["base_url"].toString();
            cred.cookie = obj["cookie"].toString();
            cred.encrypt_public_key = obj["encrypt_public_key"].toString();

            if (cred.base_url.isEmpty())
                cred.base_url = default_base_url();

            if (!cred.encrypt_public_key.isEmpty())
                cred.decoded_pem = UpstreamCrypto::decode_encrypt_public_key(cred.encrypt_public_key);

            if (!cred.cookie.isEmpty())
                m_agents.push_back(std::move(cred));
        }

        qDebug() << "[UpstreamClient] loaded" << m_agents.size() << "agents";
        if (callback) callback(true);
    });
}

// ── Cache key builders ──

QString UpstreamClient::make_agent_cache_key(int64_t agent_id, const QString& path,
                                              const QMap<QString, QString>& params)
{
    QString key = QString::number(agent_id) + ":" + path + ":";
    for (auto it = params.cbegin(); it != params.cend(); ++it) {
        if (it.key() == "page" || it.key() == "limit") continue;
        key += it.key() + "=" + it.value() + "&";
    }
    return key;
}

QString UpstreamClient::make_merged_cache_key(const QString& path,
                                               const QMap<QString, QString>& params)
{
    QString key = path + ":";
    for (auto it = params.cbegin(); it != params.cend(); ++it) {
        if (it.key() == "page" || it.key() == "limit") continue;
        key += it.key() + "=" + it.value() + "&";
    }
    return key;
}

// ── Paginate từ merged cache — O(limit) ──

MergedResult UpstreamClient::paginate_from_merged(const MergedCacheEntry& merged,
                                                    int page, int limit)
{
    int fetched = merged.all_items.size();
    int total = qMax(merged.total_count, fetched);
    int start = qMin((page - 1) * limit, fetched);
    int end = qMin(start + limit, fetched);

    QJsonArray page_data;
    for (int j = start; j < end; ++j)
        page_data.append(merged.all_items[j]);

    MergedResult result;
    result.data = page_data;
    result.total = total;
    result.page = page;
    result.limit = limit;
    result.total_data = merged.total_data;
    return result;
}

// ── Evict ──

void UpstreamClient::evict_expired_cache()
{
    auto it = m_agent_cache.begin();
    while (it != m_agent_cache.end()) {
        if (it.value().timer.elapsed() > k_stale_ttl_ms)
            it = m_agent_cache.erase(it);
        else
            ++it;
    }

    auto it2 = m_merged_cache.begin();
    while (it2 != m_merged_cache.end()) {
        if (it2.value().timer.elapsed() > k_stale_ttl_ms)
            it2 = m_merged_cache.erase(it2);
        else
            ++it2;
    }

    // Cap memory
    while (m_merged_cache.size() > k_max_cache_entries) {
        QString oldest_key;
        qint64 oldest_elapsed = 0;
        for (auto it3 = m_merged_cache.cbegin(); it3 != m_merged_cache.cend(); ++it3) {
            qint64 elapsed = it3.value().timer.elapsed();
            if (elapsed > oldest_elapsed) {
                oldest_elapsed = elapsed;
                oldest_key = it3.key();
            }
        }
        if (!oldest_key.isEmpty())
            m_merged_cache.remove(oldest_key);
        else
            break;
    }
}

// ── Fetch từ 1 agent ──

void UpstreamClient::fetch_from_agent(const AgentCredential& agent,
                                       const QString& path,
                                       const QMap<QString, QString>& params,
                                       SingleCallback callback)
{
    QString full_url = agent.base_url + path;

    QJsonObject params_obj;
    for (auto it = params.cbegin(); it != params.cend(); ++it)
        params_obj[it.key()] = it.value();
    QByteArray params_json = QJsonDocument(params_obj).toJson(QJsonDocument::Compact);

    QByteArray body_bytes;
    QString cek_k;
    QByteArray aes_key;
    bool encrypted = false;

    if (!agent.encrypt_public_key.isEmpty()) {
        auto enc = agent.decoded_pem.isEmpty()
            ? UpstreamCrypto::encrypt_request(params_json, agent.encrypt_public_key)
            : UpstreamCrypto::encrypt_request_with_pem(params_json, agent.decoded_pem);
        if (enc.ok) {
            body_bytes = enc.encrypted_body;
            cek_k = enc.cek_k;
            aes_key = enc.aes_key;
            encrypted = true;
        }
    }

    if (!encrypted) {
        QUrlQuery query;
        for (auto it = params.cbegin(); it != params.cend(); ++it)
            query.addQueryItem(it.key(), it.value());
        body_bytes = query.toString(QUrl::FullyEncoded).toUtf8();
    }

    QUrl url(full_url);
    QNetworkRequest req(url);
    req.setRawHeader("Cookie", ("PHPSESSID=" + agent.cookie).toUtf8());
    req.setRawHeader("User-Agent", k_user_agent);
    req.setRawHeader("Accept", "application/json, text/javascript, */*; q=0.01");
    req.setRawHeader("X-Requested-With", "XMLHttpRequest");
    req.setRawHeader("Referer", agent.base_url.toUtf8());
    req.setRawHeader("Origin", agent.base_url.toUtf8());
    req.setTransferTimeout(15000);

    if (encrypted) {
        req.setHeader(QNetworkRequest::ContentTypeHeader, "text/plain");
        req.setRawHeader("cek-k", cek_k.toUtf8());
    } else {
        req.setHeader(QNetworkRequest::ContentTypeHeader, "application/x-www-form-urlencoded");
    }

    auto* reply = m_nam.post(req, body_bytes);
    auto agent_id = agent.id;
    auto agent_name = agent.name;

    connect(reply, &QNetworkReply::finished, this, [=]() {
        reply->deleteLater();

        AgentFetchResult result;
        result.agent_id = agent_id;
        result.agent_name = agent_name;

        if (reply->error() != QNetworkReply::NoError) {
            int status = reply->attribute(QNetworkRequest::HttpStatusCodeAttribute).toInt();
            if (status == 301 || status == 302) {
                result.error = "SESSION_EXPIRED";
            } else {
                result.error = reply->errorString();
            }
            callback(result);
            return;
        }

        QByteArray body = reply->readAll();

        bool resp_encrypted = encrypted && reply->rawHeader("cek-s") == "1";
        if (!resp_encrypted && encrypted)
            resp_encrypted = reply->rawHeader("Cek-S") == "1";

        result = parse_response(agent_id, agent_name, body, aes_key, resp_encrypted);
        callback(result);
    });
}

// ── Parse response ──

AgentFetchResult UpstreamClient::parse_response(int64_t agent_id, const QString& agent_name,
                                                  const QByteArray& body, const QByteArray& aes_key,
                                                  bool encrypted)
{
    AgentFetchResult result;
    result.agent_id = agent_id;
    result.agent_name = agent_name;

    QByteArray json_bytes = body;

    if (encrypted && !aes_key.isEmpty()) {
        json_bytes = UpstreamCrypto::decrypt_response(body.trimmed(), aes_key);
        if (json_bytes.isEmpty()) {
            result.error = "DECRYPT_FAILED";
            return result;
        }
    }

    // HTML response → session expired (check first 2 chars, tránh trimmed() copy)
    if (json_bytes.size() > 2) {
        char c0 = json_bytes[0];
        if (c0 == '<' || c0 == ' ' || c0 == '\n' || c0 == '\r') {
            auto trimmed = json_bytes.trimmed();
            if (trimmed.startsWith("<!") || trimmed.startsWith("<html")
                || trimmed.startsWith("<HTML") || trimmed.startsWith("<?xml")
                || trimmed.startsWith("<head")) {
                result.error = "SESSION_EXPIRED";
                return result;
            }
        }
    }

    QJsonParseError parse_err;
    auto doc = QJsonDocument::fromJson(json_bytes, &parse_err);
    if (parse_err.error != QJsonParseError::NoError) {
        result.error = "JSON_PARSE: " + parse_err.errorString();
        return result;
    }

    auto obj = doc.object();
    int code = obj["code"].toInt(-1);

    if (code == 0 || code == 1) {
        QString msg = obj["msg"].toString().toLower();
        if (msg.contains("login") || msg.contains(QString::fromUtf8("đăng nhập"))) {
            result.error = "SESSION_EXPIRED";
            return result;
        }

        result.data = obj["data"].toArray();
        result.count = obj["count"].toInt();
        result.total_data = obj["total_data"].toObject();
        result.ok = true;
        return result;
    }

    if (code == 2) {
        result.ok = true;
        return result;
    }

    if (code == 302) {
        result.error = "SESSION_EXPIRED";
        return result;
    }

    result.error = QString("CODE_%1: %2").arg(code).arg(obj["msg"].toString());
    return result;
}

// ══════════════════════════════════════════════════════════════════════════════
// fetch_all — entry point chính
//
// Chiến lược tốc độ:
//   1. Merged cache FRESH  → paginate O(limit), trả ngay      (~0ms)
//   2. Merged cache STALE  → trả stale ngay + revalidate bg   (~0ms)
//   3. Cache MISS          → fetch all agents → build cache    (~500-2000ms)
// ══════════════════════════════════════════════════════════════════════════════

void UpstreamClient::fetch_all(const QString& path,
                                const QMap<QString, QString>& params,
                                int page, int limit,
                                FetchCallback callback)
{
    if (m_agents.empty()) {
        MergedResult empty;
        empty.page = page;
        empty.limit = limit;
        callback(empty);
        return;
    }

    evict_expired_cache();

    auto merged_key = make_merged_cache_key(path, params);
    auto merged_it = m_merged_cache.find(merged_key);

    if (merged_it != m_merged_cache.end() && merged_it.value().valid) {
        qint64 age = merged_it.value().timer.elapsed();

        if (age <= k_cache_ttl_ms) {
            // FRESH — trả ngay
            callback(paginate_from_merged(merged_it.value(), page, limit));
            return;
        }

        if (age <= k_stale_ttl_ms) {
            // STALE — trả ngay + background revalidate
            qDebug() << "[UpstreamClient] stale-while-revalidate, age:" << age << "ms";
            callback(paginate_from_merged(merged_it.value(), page, limit));
            revalidate_background(path, params);
            return;
        }

        // Quá stale
        m_merged_cache.erase(merged_it);
    }

    // MISS — fetch tất cả agents
    fetch_all_internal(path, params,
        [this, merged_key, page, limit, callback](const MergedResult&) {
            auto it = m_merged_cache.find(merged_key);
            if (it != m_merged_cache.end() && it.value().valid) {
                callback(paginate_from_merged(it.value(), page, limit));
            } else {
                MergedResult empty;
                empty.page = page;
                empty.limit = limit;
                callback(empty);
            }
        });
}

// ── Background revalidate ──

void UpstreamClient::revalidate_background(const QString& path,
                                             const QMap<QString, QString>& params)
{
    auto merged_key = make_merged_cache_key(path, params);
    if (m_revalidating.contains(merged_key))
        return;

    m_revalidating.insert(merged_key);

    fetch_all_internal(path, params,
        [this, merged_key](const MergedResult&) {
            m_revalidating.remove(merged_key);
            qDebug() << "[UpstreamClient] background revalidate done";
        });
}

// ── fetch_all_internal — core fetch + build merged cache ──

void UpstreamClient::fetch_all_internal(const QString& path,
                                          const QMap<QString, QString>& params,
                                          FetchCallback callback)
{
    constexpr int k_page_size = 10000;
    constexpr int k_max_pages = 10;

    struct SharedState {
        QJsonArray all_items;
        QJsonObject total_data;
        int total_count = 0;
        int agents_remaining = 0;
        FetchCallback callback;
        UpstreamClient* self = nullptr;
        QString merged_key;

        void finalize() {
            // Build merged cache
            if (self) {
                MergedCacheEntry merged;
                merged.all_items = all_items;
                merged.total_count = total_count;
                merged.total_data = total_data;
                merged.valid = true;
                merged.timer.start();
                self->m_merged_cache[merged_key] = std::move(merged);
            }

            MergedResult result;
            result.total = qMax(total_count, static_cast<int>(all_items.size()));
            result.total_data = total_data;
            callback(result);
        }
    };

    auto state = std::make_shared<SharedState>();
    state->agents_remaining = static_cast<int>(m_agents.size());
    state->callback = std::move(callback);
    state->self = this;
    state->merged_key = make_merged_cache_key(path, params);

    QMap<QString, QString> upstream_params = params;
    upstream_params["page"] = "1";
    upstream_params["limit"] = QString::number(k_page_size);

    for (size_t i = 0; i < m_agents.size(); ++i) {
        auto& agent = m_agents[i];

        // Per-agent cache hit?
        auto agent_key = make_agent_cache_key(agent.id, path, params);
        auto agent_it = m_agent_cache.find(agent_key);
        if (agent_it != m_agent_cache.end() && agent_it.value().valid
            && agent_it.value().timer.elapsed() <= k_cache_ttl_ms) {
            const auto& entry = agent_it.value();
            for (const auto& item : entry.data)
                state->all_items.append(item);
            state->total_count += entry.count;
            if (state->total_data.isEmpty() && !entry.total_data.isEmpty())
                state->total_data = entry.total_data;
            --state->agents_remaining;
            if (state->agents_remaining <= 0)
                state->finalize();
            continue;
        }

        fetch_from_agent(agent, path, upstream_params,
            [this, state, agent_ref = agent, path, params,
             k_page_size, k_max_pages](const AgentFetchResult& result) {
                if (!result.ok) {
                    --state->agents_remaining;
                    if (state->agents_remaining <= 0)
                        state->finalize();
                    return;
                }

                for (const auto& item : result.data)
                    state->all_items.append(item);
                state->total_count += result.count;
                if (state->total_data.isEmpty() && !result.total_data.isEmpty())
                    state->total_data = result.total_data;

                // Cache per-agent
                auto ak = make_agent_cache_key(agent_ref.id, path, params);
                AgentCacheEntry agent_entry;
                agent_entry.data = result.data;
                agent_entry.count = result.count;
                agent_entry.total_data = result.total_data;
                agent_entry.valid = true;
                agent_entry.timer.start();

                int total_pages = (result.count + k_page_size - 1) / k_page_size;
                if (total_pages > k_max_pages) total_pages = k_max_pages;

                if (total_pages <= 1 || result.data.size() < k_page_size) {
                    m_agent_cache[ak] = std::move(agent_entry);
                    --state->agents_remaining;
                    if (state->agents_remaining <= 0)
                        state->finalize();
                    return;
                }

                auto pages_remaining = std::make_shared<int>(total_pages - 1);
                auto cache_entry = std::make_shared<AgentCacheEntry>(std::move(agent_entry));

                for (int p = 2; p <= total_pages; ++p) {
                    QMap<QString, QString> extra_params = params;
                    extra_params["page"] = QString::number(p);
                    extra_params["limit"] = QString::number(k_page_size);

                    fetch_from_agent(agent_ref, path, extra_params,
                        [this, state, pages_remaining, cache_entry,
                         ak](const AgentFetchResult& extra) {
                            if (extra.ok) {
                                for (const auto& item : extra.data) {
                                    state->all_items.append(item);
                                    cache_entry->data.append(item);
                                }
                                cache_entry->count += extra.count;
                            }

                            --(*pages_remaining);
                            if (*pages_remaining <= 0) {
                                m_agent_cache[ak] = std::move(*cache_entry);
                                --state->agents_remaining;
                                if (state->agents_remaining <= 0)
                                    state->finalize();
                            }
                        });
                }
            });
    }
}
