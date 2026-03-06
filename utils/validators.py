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
from core.i18n import t


# ── Kiểu trả về ───────────────────────────────────────────
# Mỗi hàm trả về None (hợp lệ) hoặc str (thông báo lỗi)

def required(field: str, value) -> str | None:
    """Không được để trống."""
    if value is None or str(value).strip() == "":
        return t("validator.required", field=field)
    return None


def min_length(field: str, value: str, min_len: int) -> str | None:
    if len(str(value).strip()) < min_len:
        return t("validator.min_length", field=field, min=min_len)
    return None


def max_length(field: str, value: str, max_len: int) -> str | None:
    if len(str(value).strip()) > max_len:
        return t("validator.max_length", field=field, max=max_len)
    return None


def email(field: str, value: str) -> str | None:
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"
    if not re.match(pattern, str(value).strip()):
        return t("validator.email", field=field)
    return None


def phone(field: str, value: str) -> str | None:
    """Số điện thoại Việt Nam: 10 số, bắt đầu bằng 0."""
    digits = re.sub(r"\D", "", str(value))
    if not re.match(r"^0\d{9}$", digits):
        return t("validator.phone", field=field)
    return None


def positive(field: str, value) -> str | None:
    """Phải là số dương."""
    try:
        if float(value) <= 0:
            return t("validator.positive", field=field)
    except (TypeError, ValueError):
        return t("validator.numeric", field=field)
    return None


def non_negative(field: str, value) -> str | None:
    """Phải >= 0."""
    try:
        if float(value) < 0:
            return t("validator.non_negative", field=field)
    except (TypeError, ValueError):
        return t("validator.numeric", field=field)
    return None


def in_range(field: str, value, min_val, max_val) -> str | None:
    try:
        v = float(value)
        if not (min_val <= v <= max_val):
            return t("validator.in_range", field=field, min=min_val, max=max_val)
    except (TypeError, ValueError):
        return t("validator.numeric", field=field)
    return None


def numeric(field: str, value: str) -> str | None:
    try:
        float(str(value).replace(",", "."))
    except ValueError:
        return t("validator.numeric", field=field)
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
