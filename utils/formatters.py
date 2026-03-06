"""
utils/formatters.py
Hàm format dữ liệu hiển thị dùng chung.

Dùng:
    from utils.formatters import currency, number, date_str, phone_fmt, truncate
    currency(9200000)          → "9.200.000 đ"
    number(1234567.5, dec=1)   → "1.234.567,5"
    date_str("2026-03-05")     → "05/03/2026"
    phone_fmt("0912345678")    → "0912 345 678"
    truncate("Tên rất dài...", 20) → "Tên rất dài..."
"""
from datetime import datetime, date


def currency(value: int | float,
             suffix: str = " đ",
             sep: str = ".") -> str:
    """Format số tiền: 9200000 → '9.200.000 đ'"""
    try:
        return f"{int(value):,}".replace(",", sep) + suffix
    except (TypeError, ValueError):
        return str(value)


def number(value: int | float,
           decimals: int = 0,
           sep: str = ".") -> str:
    """Format số có dấu phân cách hàng nghìn."""
    try:
        if decimals == 0:
            return f"{int(value):,}".replace(",", sep)
        formatted = f"{float(value):,.{decimals}f}"
        # Đổi sang định dạng VN: dấu . ngàn, dấu , thập phân
        parts = formatted.split(".")
        integer_part = parts[0].replace(",", sep)
        decimal_part = parts[1] if len(parts) > 1 else ""
        return f"{integer_part},{decimal_part}" if decimal_part else integer_part
    except (TypeError, ValueError):
        return str(value)


def percent(value: float, decimals: int = 1) -> str:
    """Format phần trăm: 0.856 → '85.6%'"""
    return f"{value * 100:.{decimals}f}%"


def date_str(value, fmt_in: str = "%Y-%m-%d",
             fmt_out: str = "%d/%m/%Y") -> str:
    """Chuyển chuỗi ngày từ định dạng ISO sang DD/MM/YYYY."""
    if isinstance(value, (datetime, date)):
        return value.strftime(fmt_out)
    try:
        return datetime.strptime(str(value), fmt_in).strftime(fmt_out)
    except ValueError:
        return str(value)


def datetime_str(value, fmt_out: str = "%d/%m/%Y %H:%M") -> str:
    if isinstance(value, datetime):
        return value.strftime(fmt_out)
    try:
        return datetime.fromisoformat(str(value)).strftime(fmt_out)
    except ValueError:
        return str(value)


def phone_fmt(value: str) -> str:
    """Format SĐT: '0912345678' → '0912 345 678'"""
    digits = "".join(filter(str.isdigit, str(value)))
    if len(digits) == 10:
        return f"{digits[:4]} {digits[4:7]} {digits[7:]}"
    return value


def truncate(text: str, max_len: int = 30, suffix: str = "...") -> str:
    """Cắt chuỗi dài và thêm '...'"""
    if len(text) <= max_len:
        return text
    return text[:max_len - len(suffix)] + suffix


def yesno(value: bool) -> str:
    return "Có" if value else "Không"


def active_text(value: bool) -> str:
    return "Hoạt động" if value else "Không hoạt động"
