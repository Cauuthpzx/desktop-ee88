#pragma once

#include <QString>
#include <QColor>

// Dịch text Chinese từ upstream EE88 → Vietnamese.
// Dùng chung cho customers_page, report_pages, v.v.
namespace UpstreamTranslate {

// Dịch Chinese → Vietnamese. Trả về text gốc nếu không có trong map.
QString zh_to_vi(const QString& text);

// Lấy màu cho status text (tương tự web lay-tag).
// normal → green, frozen → orange, locked → red.
QColor status_color(const QString& status_text);

// Kiểm tra status "Không trúng" / "未中奖" — chỉ hiển thị chữ, không nền.
bool is_lose_status(const QString& status_text);

} // namespace UpstreamTranslate
