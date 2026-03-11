#pragma once

#include <QSize>

/**
 * Quy chuẩn kích thước icon + spacing cho toàn app.
 * Mọi file dùng icon PHẢI include header này thay vì hardcode số.
 */
namespace IconDefs {

// ── Icon Sizes ──
constexpr int k_toolbar_icon     = 18;   // Toolbar nav buttons
constexpr int k_menu_icon        = 16;   // Dropdown menu items
constexpr int k_search_icon      = 16;   // Search/Reset buttons
constexpr int k_header_icon      = 14;   // Dialog header buttons
constexpr int k_table_icon       = 12;   // Table row action buttons

inline QSize toolbar_icon()  { return {k_toolbar_icon, k_toolbar_icon}; }
inline QSize menu_icon()     { return {k_menu_icon, k_menu_icon}; }
inline QSize search_icon()   { return {k_search_icon, k_search_icon}; }
inline QSize header_icon()   { return {k_header_icon, k_header_icon}; }
inline QSize table_icon()    { return {k_table_icon, k_table_icon}; }

// ── Widget Heights ──
constexpr int k_input_height         = 32;   // QLineEdit, QComboBox, DateRangePicker
constexpr int k_search_btn_height    = 32;   // Search/Reset buttons
constexpr int k_dialog_btn_height    = 34;   // Dialog action buttons (Huỷ, Lưu, etc.)
constexpr int k_header_btn_height    = 30;   // Dialog header buttons (Thêm, Xoá tất cả)
constexpr int k_table_btn_height     = 22;   // Table row action buttons
constexpr int k_toolbar_btn_height   = 26;   // Toolbar mini buttons (Thêm hội viên)
constexpr int k_page_combo_height    = 28;   // Pagination combo
constexpr int k_status_tag_height    = 22;   // Status tag labels
constexpr int k_separator_height     = 1;    // Divider lines
constexpr int k_table_row_height     = 36;   // Settings table row height
constexpr int k_toggle_width         = 50;   // Toggle switch width
constexpr int k_toggle_height        = 22;   // Toggle switch height

// ── Spacing ──
constexpr int k_toolbar_spacing      = 0;    // QToolBar spacing
constexpr int k_search_spacing       = 8;    // Search form spacing
constexpr int k_btn_spacing          = 4;    // Action buttons spacing in table
constexpr int k_dialog_spacing       = 14;   // Dialog form row spacing

// ── Colors ──
static constexpr const char* k_color_primary = "#16baaa";
static constexpr const char* k_color_muted   = "#cccccc";

// ── Font Sizes (px) ──
constexpr int k_font_table_btn       = 11;   // Table row button text
constexpr int k_font_search_btn      = 12;   // Search/header button text
constexpr int k_font_dialog          = 13;   // Dialog label/input text
constexpr int k_font_table           = 12;   // Table cell text
constexpr int k_font_title           = 14;   // Page/dialog titles
constexpr int k_font_toggle          = 9;    // Toggle switch text

} // namespace IconDefs
