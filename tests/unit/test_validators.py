"""
Unit tests cho utils/validators.py
Mỗi validator function có: happy path, edge cases, error cases.
"""
import pytest


@pytest.fixture(autouse=True)
def _init_i18n():
    """Auto-init i18n cho mọi test trong module."""
    from core.i18n import init
    init()


# ══════════════════════════════════════════════════════════════
#  required()
# ══════════════════════════════════════════════════════════════

class TestRequired:
    def test_valid_string_returns_none(self):
        from utils.validators import required
        assert required("Name", "Alice") is None

    def test_valid_number_returns_none(self):
        from utils.validators import required
        assert required("Age", 25) is None

    def test_empty_string_returns_error(self):
        from utils.validators import required
        result = required("Name", "")
        assert result is not None
        assert isinstance(result, str)

    def test_whitespace_only_returns_error(self):
        from utils.validators import required
        assert required("Name", "   ") is not None

    def test_none_returns_error(self):
        from utils.validators import required
        assert required("Name", None) is not None

    def test_zero_is_valid(self):
        from utils.validators import required
        assert required("Count", 0) is None

    def test_false_is_valid(self):
        from utils.validators import required
        assert required("Flag", False) is None


# ══════════════════════════════════════════════════════════════
#  min_length()
# ══════════════════════════════════════════════════════════════

class TestMinLength:
    def test_string_meets_min_returns_none(self):
        from utils.validators import min_length
        assert min_length("Password", "123456", 6) is None

    def test_string_exceeds_min_returns_none(self):
        from utils.validators import min_length
        assert min_length("Password", "1234567890", 6) is None

    def test_string_below_min_returns_error(self):
        from utils.validators import min_length
        assert min_length("Password", "123", 6) is not None

    def test_empty_string_returns_error(self):
        from utils.validators import min_length
        assert min_length("Password", "", 1) is not None

    def test_whitespace_trimmed(self):
        from utils.validators import min_length
        # "  ab  " stripped = "ab" = length 2
        assert min_length("Code", "  ab  ", 3) is not None

    def test_exact_min_length_returns_none(self):
        from utils.validators import min_length
        assert min_length("Pin", "1234", 4) is None


# ══════════════════════════════════════════════════════════════
#  max_length()
# ══════════════════════════════════════════════════════════════

class TestMaxLength:
    def test_string_within_max_returns_none(self):
        from utils.validators import max_length
        assert max_length("Name", "Alice", 100) is None

    def test_string_exceeds_max_returns_error(self):
        from utils.validators import max_length
        assert max_length("Name", "A" * 101, 100) is not None

    def test_exact_max_length_returns_none(self):
        from utils.validators import max_length
        assert max_length("Name", "A" * 100, 100) is None

    def test_empty_string_returns_none(self):
        from utils.validators import max_length
        assert max_length("Name", "", 100) is None


# ══════════════════════════════════════════════════════════════
#  email()
# ══════════════════════════════════════════════════════════════

class TestEmail:
    @pytest.mark.parametrize("addr", [
        "user@example.com",
        "user.name@example.co.uk",
        "user123@test.org",
    ])
    def test_valid_emails(self, addr):
        from utils.validators import email
        assert email("Email", addr) is None

    @pytest.mark.parametrize("addr", [
        "not-an-email",
        "@example.com",
        "user@",
        "user@.com",
        "",
        "user@com",
    ])
    def test_invalid_emails(self, addr):
        from utils.validators import email
        assert email("Email", addr) is not None


# ══════════════════════════════════════════════════════════════
#  phone()
# ══════════════════════════════════════════════════════════════

class TestPhone:
    @pytest.mark.parametrize("num", [
        "0912345678",
        "0123456789",
        "0912 345 678",  # dấu cách — digits được tách ra
    ])
    def test_valid_phones(self, num):
        from utils.validators import phone
        assert phone("SĐT", num) is None

    @pytest.mark.parametrize("num", [
        "1234567890",    # không bắt đầu bằng 0
        "091234567",     # thiếu 1 số
        "09123456789",   # thừa 1 số
        "",
        "abc",
    ])
    def test_invalid_phones(self, num):
        from utils.validators import phone
        assert phone("SĐT", num) is not None


# ══════════════════════════════════════════════════════════════
#  positive()
# ══════════════════════════════════════════════════════════════

class TestPositive:
    def test_positive_number_returns_none(self):
        from utils.validators import positive
        assert positive("Price", 100) is None

    def test_float_positive_returns_none(self):
        from utils.validators import positive
        assert positive("Price", 0.01) is None

    def test_zero_returns_error(self):
        from utils.validators import positive
        assert positive("Price", 0) is not None

    def test_negative_returns_error(self):
        from utils.validators import positive
        assert positive("Price", -5) is not None

    def test_non_numeric_returns_error(self):
        from utils.validators import positive
        assert positive("Price", "abc") is not None

    def test_none_returns_error(self):
        from utils.validators import positive
        assert positive("Price", None) is not None


# ══════════════════════════════════════════════════════════════
#  non_negative()
# ══════════════════════════════════════════════════════════════

class TestNonNegative:
    def test_positive_returns_none(self):
        from utils.validators import non_negative
        assert non_negative("Qty", 10) is None

    def test_zero_returns_none(self):
        from utils.validators import non_negative
        assert non_negative("Qty", 0) is None

    def test_negative_returns_error(self):
        from utils.validators import non_negative
        assert non_negative("Qty", -1) is not None


# ══════════════════════════════════════════════════════════════
#  in_range()
# ══════════════════════════════════════════════════════════════

class TestInRange:
    def test_value_in_range_returns_none(self):
        from utils.validators import in_range
        assert in_range("Age", 25, 0, 150) is None

    def test_value_at_min_boundary_returns_none(self):
        from utils.validators import in_range
        assert in_range("Age", 0, 0, 150) is None

    def test_value_at_max_boundary_returns_none(self):
        from utils.validators import in_range
        assert in_range("Age", 150, 0, 150) is None

    def test_value_below_min_returns_error(self):
        from utils.validators import in_range
        assert in_range("Age", -1, 0, 150) is not None

    def test_value_above_max_returns_error(self):
        from utils.validators import in_range
        assert in_range("Age", 151, 0, 150) is not None

    def test_non_numeric_returns_error(self):
        from utils.validators import in_range
        assert in_range("Age", "abc", 0, 150) is not None


# ══════════════════════════════════════════════════════════════
#  numeric()
# ══════════════════════════════════════════════════════════════

class TestNumeric:
    @pytest.mark.parametrize("val", ["123", "0.5", "3,14", "-10"])
    def test_valid_numeric(self, val):
        from utils.validators import numeric
        assert numeric("Val", val) is None

    @pytest.mark.parametrize("val", ["abc", "12.34.56", ""])
    def test_invalid_numeric(self, val):
        from utils.validators import numeric
        assert numeric("Val", val) is not None


# ══════════════════════════════════════════════════════════════
#  validate_all()
# ══════════════════════════════════════════════════════════════

class TestValidateAll:
    def test_all_none_returns_empty_list(self):
        from utils.validators import validate_all
        assert validate_all([None, None, None]) == []

    def test_mixed_returns_only_errors(self):
        from utils.validators import validate_all
        result = validate_all([None, "Error 1", None, "Error 2"])
        assert result == ["Error 1", "Error 2"]

    def test_empty_input_returns_empty_list(self):
        from utils.validators import validate_all
        assert validate_all([]) == []

    def test_all_errors_returns_all(self):
        from utils.validators import validate_all
        result = validate_all(["E1", "E2", "E3"])
        assert len(result) == 3
