"""
utils/validators.py
Hàm validate dữ liệu dùng chung.

Dùng:
    from utils.validators import required, email, phone, min_length, positive
    from utils.validators import validate_all

    errors = validate_all([
        required("Tên", name),
        email("Email", email_str),
        phone("Điện thoại", phone_str),
        min_length("Mật khẩu", password, 6),
        positive("Giá", price),
    ])
    if errors:
        warn(self, "\n".join(errors))
        return
"""
import re


# ── Kiểu trả về ───────────────────────────────────────────
# Mỗi hàm trả về None (hợp lệ) hoặc str (thông báo lỗi)

def required(field: str, value) -> str | None:
    """Không được để trống."""
    if value is None or str(value).strip() == "":
        return f"{field} không được để trống."
    return None


def min_length(field: str, value: str, min_len: int) -> str | None:
    if len(str(value).strip()) < min_len:
        return f"{field} phải có ít nhất {min_len} ký tự."
    return None


def max_length(field: str, value: str, max_len: int) -> str | None:
    if len(str(value).strip()) > max_len:
        return f"{field} không được vượt quá {max_len} ký tự."
    return None


def email(field: str, value: str) -> str | None:
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"
    if not re.match(pattern, str(value).strip()):
        return f"{field} không đúng định dạng email."
    return None


def phone(field: str, value: str) -> str | None:
    """Số điện thoại Việt Nam: 10 số, bắt đầu bằng 0."""
    digits = re.sub(r"\D", "", str(value))
    if not re.match(r"^0\d{9}$", digits):
        return f"{field} không đúng định dạng (10 số, bắt đầu bằng 0)."
    return None


def positive(field: str, value) -> str | None:
    """Phải là số dương."""
    try:
        if float(value) <= 0:
            return f"{field} phải lớn hơn 0."
    except (TypeError, ValueError):
        return f"{field} phải là số."
    return None


def non_negative(field: str, value) -> str | None:
    """Phải >= 0."""
    try:
        if float(value) < 0:
            return f"{field} không được âm."
    except (TypeError, ValueError):
        return f"{field} phải là số."
    return None


def in_range(field: str, value, min_val, max_val) -> str | None:
    try:
        v = float(value)
        if not (min_val <= v <= max_val):
            return f"{field} phải trong khoảng {min_val} – {max_val}."
    except (TypeError, ValueError):
        return f"{field} phải là số."
    return None


def numeric(field: str, value: str) -> str | None:
    try:
        float(str(value).replace(",", "."))
    except ValueError:
        return f"{field} phải là số."
    return None


def validate_all(results: list[str | None]) -> list[str]:
    """
    Tổng hợp kết quả validate — lọc bỏ None, trả về list lỗi.

    Dùng:
        errors = validate_all([required(...), email(...), ...])
        if errors:
            warn(self, "\\n".join(errors))
            return
    """
    return [r for r in results if r is not None]
