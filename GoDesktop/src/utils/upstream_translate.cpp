#include "utils/upstream_translate.h"

#include <QHash>

namespace UpstreamTranslate {

// Helper: tạo QString từ UTF-8 literal an toàn
static inline QString u(const char* s) { return QString::fromUtf8(s); }

QString zh_to_vi(const QString& text)
{
    static const QHash<QString, QString> map = {
        // === Loại hình hội viên (type_format) ===
        {u("\xE6\xAD\xA3\xE5\xBC\x8F"), u("Ch\xC3\xADnh th\xE1\xBB\xA9""c")},     // 正式 → Chính thức
        {u("\xE8\xAF\x95\xE7\x8E\xA9"), u("Th\xE1\xBB\xAD nghi\xE1\xBB\x87m")},   // 试玩 → Thử nghiệm
        {u("\xE4\xBB\xA3\xE7\x90\x86"), u("\xC4\x90\xE1\xBA\xA1i l\xC3\xBD")},     // 代理 → Đại lý

        // === Trạng thái hội viên (status_format) ===
        {u("\xE6\xAD\xA3\xE5\xB8\xB8"), u("B\xC3\xACnh th\xC6\xB0\xE1\xBB\x9Dng")}, // 正常 → Bình thường
        {u("\xE5\x86\xBB\xE7\xBB\x93"), u("\xC4\x90\xC3\xB3ng b\xC4\x83ng")},       // 冻结 → Đóng băng
        {u("\xE9\x94\x81\xE5\xAE\x9A"), u("Kh\xC3\xB3""a")},                         // 锁定 → Khóa

        // === Trạng thái đơn cược (status_text) ===
        {u("\xE6\x9C\xAA\xE5\xBC\x80\xE5\xA5\x96"), u("Ch\xC6\xB0""a thanh to\xC3\xA1n")},       // 未开奖 → Chưa thanh toán
        {u("\xE4\xB8\xAD\xE5\xA5\x96"),               u("Tr\xC3\xBAng")},                           // 中奖 → Trúng
        {u("\xE6\x9C\xAA\xE4\xB8\xAD\xE5\xA5\x96"), u("Kh\xC3\xB4ng tr\xC3\xBAng")},             // 未中奖 → Không trúng
        {u("\xE5\x92\x8C"),                             u("Ho\xC3\xA0")},                             // 和 → Hoà
        {u("\xE7\x94\xA8\xE6\x88\xB7\xE6\x92\xA4\xE5\x8D\x95"), u("Kh\xC3\xA1""ch hu\xE1\xBB\xB7 \xC4\x91\xC6\xA1n")}, // 用户撤单 → Khách huỷ đơn
        {u("\xE7\xB3\xBB\xE7\xBB\x9F\xE6\x92\xA4\xE5\x8D\x95"), u("H\xE1\xBB\x87 th\xE1\xBB\x91ng hu\xE1\xBB\xB7 \xC4\x91\xC6\xA1n")}, // 系统撤单 → Hệ thống huỷ đơn
        {u("\xE5\xBC\x82\xE5\xB8\xB8\xE8\xAE\xA2\xE5\x8D\x95"), u("\xC4\x90\xC6\xA1n b\xE1\xBA\xA5t th\xC6\xB0\xE1\xBB\x9Dng")}, // 异常订单 → Đơn bất thường

        // === Trạng thái giao dịch nạp/rút (status) ===
        {u("\xE5\xBE\x85\xE5\xA4\x84\xE7\x90\x86"), u("Ch\xE1\xBB\x9D x\xE1\xBB\xAD l\xC3\xAD")},   // 待处理 → Chờ xử lí
        {u("\xE5\xB7\xB2\xE5\xAE\x8C\xE6\x88\x90"), u("Ho\xC3\xA0n t\xE1\xBA\xA5t")},                 // 已完成 → Hoàn tất
        {u("\xE5\xA4\x84\xE7\x90\x86\xE4\xB8\xAD"), u("\xC4\x90""ang x\xE1\xBB\xAD l\xC3\xAD")},     // 处理中 → Đang xử lí
        {u("\xE5\xA4\xB1\xE8\xB4\xA5"),               u("Th\xE1\xBA\xA5t b\xE1\xBA\xA1i")},           // 失败 → Thất bại
        {u("\xE6\x88\x90\xE5\x8A\x9F"),               u("Th\xC3\xA0nh c\xC3\xB4ng")},                   // 成功 → Thành công
        {u("\xE6\x8B\x92\xE7\xBB\x9D"),               u("T\xE1\xBB\xAB""" "ch\xE1\xBB\x91i")},         // 拒绝 → Từ chối

        // === Loại giao dịch (type) ===
        {u("\xE5\x85\x85\xE5\x80\xBC"), u("N\xE1\xBA\xA1p ti\xE1\xBB\x81n")},     // 充值 → Nạp tiền
        {u("\xE6\x8F\x90\xE7\x8E\xB0"), u("R\xC3\xBAt ti\xE1\xBB\x81n")},         // 提现 → Rút tiền
        {u("\xE4\xB8\x8A\xE5\x88\x86"), u("N\xE1\xBA\xA1p ti\xE1\xBB\x81n")},     // 上分 → Nạp tiền
        {u("\xE4\xB8\x8B\xE5\x88\x86"), u("R\xC3\xBAt ti\xE1\xBB\x81n")},         // 下分 → Rút tiền
    };

    auto it = map.find(text);
    return it != map.end() ? *it : text;
}

QColor status_color(const QString& status_text)
{
    // Bình thường / 正常 → green
    if (status_text == u("B\xC3\xACnh th\xC6\xB0\xE1\xBB\x9Dng")
        || status_text == u("\xE6\xAD\xA3\xE5\xB8\xB8"))
        return QColor("#16a34a");

    // Đóng băng / 冻结 → orange
    if (status_text == u("\xC4\x90\xC3\xB3ng b\xC4\x83ng")
        || status_text == u("\xE5\x86\xBB\xE7\xBB\x93"))
        return QColor("#ea580c");

    // Khóa / 锁定 → red
    if (status_text == u("Kh\xC3\xB3""a")
        || status_text == u("\xE9\x94\x81\xE5\xAE\x9A"))
        return QColor("#dc2626");

    // Chờ xử lí / 待处理 → orange
    if (status_text == u("Ch\xE1\xBB\x9D x\xE1\xBB\xAD l\xC3\xAD")
        || status_text == u("\xE5\xBE\x85\xE5\xA4\x84\xE7\x90\x86"))
        return QColor("#ea580c");

    // Hoàn tất / 已完成 / Thành công / 成功 → green
    if (status_text == u("Ho\xC3\xA0n t\xE1\xBA\xA5t")
        || status_text == u("\xE5\xB7\xB2\xE5\xAE\x8C\xE6\x88\x90")
        || status_text == u("Th\xC3\xA0nh c\xC3\xB4ng")
        || status_text == u("\xE6\x88\x90\xE5\x8A\x9F"))
        return QColor("#16a34a");

    // Đang xử lí / 处理中 → blue
    if (status_text == u("\xC4\x90""ang x\xE1\xBB\xAD l\xC3\xAD")
        || status_text == u("\xE5\xA4\x84\xE7\x90\x86\xE4\xB8\xAD"))
        return QColor("#2563eb");

    // Thất bại / 失败 / Từ chối / 拒绝 → red
    if (status_text == u("Th\xE1\xBA\xA5t b\xE1\xBA\xA1i")
        || status_text == u("\xE5\xA4\xB1\xE8\xB4\xA5")
        || status_text == u("T\xE1\xBB\xAB""" "ch\xE1\xBB\x91i")
        || status_text == u("\xE6\x8B\x92\xE7\xBB\x9D"))
        return QColor("#dc2626");

    // Trúng → green
    if (status_text == u("Tr\xC3\xBAng")
        || status_text == u("\xE4\xB8\xAD\xE5\xA5\x96"))
        return QColor("#16a34a");

    // Không trúng → red
    if (status_text == u("Kh\xC3\xB4ng tr\xC3\xBAng")
        || status_text == u("\xE6\x9C\xAA\xE4\xB8\xAD\xE5\xA5\x96"))
        return QColor("#dc2626");

    // Hoà → blue
    if (status_text == u("Ho\xC3\xA0")
        || status_text == u("\xE5\x92\x8C"))
        return QColor("#2563eb");

    // Default: no special color
    return QColor();
}

bool is_lose_status(const QString& status_text)
{
    return status_text == u("Kh\xC3\xB4ng tr\xC3\xBAng")
        || status_text == u("\xE6\x9C\xAA\xE4\xB8\xAD\xE5\xA5\x96");
}

} // namespace UpstreamTranslate
