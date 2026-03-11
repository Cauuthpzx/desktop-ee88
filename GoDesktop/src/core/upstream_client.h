#pragma once

#include <QObject>
#include <QJsonArray>
#include <QJsonObject>
#include <QNetworkAccessManager>
#include <QNetworkReply>

#include <functional>
#include <memory>
#include <vector>
#include <QElapsedTimer>
#include <QHash>
#include <QMap>
#include <QTimer>

class ApiClient;

// ============================================================================
// UpstreamClient — fetch trực tiếp từ EE88 agents, parallel, AES encrypt.
// Thay thế proxy qua Goserver → tăng tốc x3-5.
//
// Tối ưu tốc độ:
//   1. Cached decoded PEM key per agent (skip decode mỗi request)
//   2. Per-agent cache (30s TTL) — chỉ fetch agent bị miss
//   3. Merged cache — cache kết quả merge, đổi trang = slice O(limit)
//   4. Stale-while-revalidate — trả stale data ngay, refresh background
//   5. Connection keep-alive qua QNetworkAccessManager
// ============================================================================

struct AgentCredential {
    int64_t id = 0;
    QString name;
    QString base_url;
    QString cookie;
    QString encrypt_public_key;
    QString decoded_pem;  // Cache decoded PEM — tránh decode mỗi request
};

// Kết quả fetch từ 1 agent.
struct AgentFetchResult {
    int64_t agent_id = 0;
    QString agent_name;
    QJsonArray data;
    int count = 0;
    QJsonObject total_data;
    bool ok = false;
    QString error;
};

// Kết quả merge từ tất cả agents.
struct MergedResult {
    QJsonArray data;        // Paginated slice
    int total = 0;          // Total items across all agents
    int page = 1;
    int limit = 10;
    QJsonObject total_data; // Summary data (first agent that has it)
};

class UpstreamClient : public QObject {
    Q_OBJECT

public:
    using FetchCallback = std::function<void(const MergedResult& result)>;
    using SingleCallback = std::function<void(const AgentFetchResult& result)>;

    explicit UpstreamClient(ApiClient* api, QObject* parent = nullptr);

    // Load agent credentials từ Goserver (GET /api/agents/upstream-info).
    void load_credentials(std::function<void(bool ok)> callback = nullptr);

    // Fetch từ tất cả agents → merge + paginate.
    void fetch_all(const QString& path,
                   const QMap<QString, QString>& params,
                   int page, int limit,
                   FetchCallback callback);

    int agent_count() const;
    bool has_credentials() const;
    static QString default_base_url();

    // Xóa toàn bộ cache (khi user force refresh).
    void invalidate_cache();

private:
    void fetch_from_agent(const AgentCredential& agent,
                          const QString& path,
                          const QMap<QString, QString>& params,
                          SingleCallback callback);

    AgentFetchResult parse_response(int64_t agent_id, const QString& agent_name,
                                     const QByteArray& body, const QByteArray& aes_key,
                                     bool encrypted);

    // ── Per-agent cache ──
    struct AgentCacheEntry {
        QJsonArray data;
        int count = 0;
        QJsonObject total_data;
        QElapsedTimer timer;
        bool valid = false;
    };

    // ── Merged cache (all agents merged) — tránh merge lại mỗi lần đổi trang ──
    struct MergedCacheEntry {
        QJsonArray all_items;   // Toàn bộ data merged
        int total_count = 0;
        QJsonObject total_data;
        QElapsedTimer timer;
        bool valid = false;
    };

    // Cache key builders
    static QString make_agent_cache_key(int64_t agent_id, const QString& path,
                                         const QMap<QString, QString>& params);
    static QString make_merged_cache_key(const QString& path,
                                          const QMap<QString, QString>& params);

    // Paginate từ merged cache — O(limit), không merge lại.
    MergedResult paginate_from_merged(const MergedCacheEntry& merged, int page, int limit);

    // Background revalidate — fetch lại data mới, cập nhật cache.
    void revalidate_background(const QString& path,
                                const QMap<QString, QString>& params);

    void evict_expired_cache();

    // Fetch tất cả agents (internal) — dùng cho cả foreground và background.
    void fetch_all_internal(const QString& path,
                             const QMap<QString, QString>& params,
                             FetchCallback callback);

    ApiClient* m_api;
    QNetworkAccessManager m_nam;
    std::vector<AgentCredential> m_agents;

    // Per-agent cache
    QHash<QString, AgentCacheEntry> m_agent_cache;

    // Merged cache — key = path:sorted_params (không có agent_id)
    QHash<QString, MergedCacheEntry> m_merged_cache;

    // Track background revalidation in-flight (tránh duplicate)
    QSet<QString> m_revalidating;

    static constexpr int k_cache_ttl_ms = 30000;       // 30s — data còn fresh
    static constexpr int k_stale_ttl_ms = 120000;      // 2min — data stale nhưng vẫn serve
    static constexpr int k_max_cache_entries = 50;      // Giới hạn memory
};
