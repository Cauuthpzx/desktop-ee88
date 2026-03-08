"""
Unit tests cho utils/formatters.py
"""
import pytest
from datetime import datetime, date


class TestCurrency:
    def test_basic_format(self):
        from utils.formatters import currency
        assert currency(9200000) == "9.200.000 đ"

    def test_zero(self):
        from utils.formatters import currency
        assert currency(0) == "0 đ"

    def test_negative(self):
        from utils.formatters import currency
        assert currency(-1500) == "-1.500 đ"

    def test_custom_suffix(self):
        from utils.formatters import currency
        assert currency(1000, suffix=" VND") == "1.000 VND"

    def test_custom_separator(self):
        from utils.formatters import currency
        assert currency(1000000, sep=",") == "1,000,000 đ"

    def test_float_truncates_to_int(self):
        from utils.formatters import currency
        assert currency(1234.56) == "1.234 đ"

    def test_non_numeric_returns_str(self):
        from utils.formatters import currency
        assert currency("abc") == "abc"


class TestNumber:
    def test_integer_format(self):
        from utils.formatters import number
        assert number(1234567) == "1.234.567"

    def test_with_decimals(self):
        from utils.formatters import number
        result = number(1234567.89, decimals=2)
        assert "1.234.567" in result
        assert "89" in result

    def test_zero(self):
        from utils.formatters import number
        assert number(0) == "0"

    def test_negative(self):
        from utils.formatters import number
        assert number(-1500) == "-1.500"

    def test_non_numeric_returns_str(self):
        from utils.formatters import number
        assert number("abc") == "abc"


class TestPercent:
    def test_basic(self):
        from utils.formatters import percent
        assert percent(0.856) == "85.6%"

    def test_zero(self):
        from utils.formatters import percent
        assert percent(0) == "0.0%"

    def test_full(self):
        from utils.formatters import percent
        assert percent(1.0) == "100.0%"

    def test_custom_decimals(self):
        from utils.formatters import percent
        assert percent(0.8567, decimals=2) == "85.67%"


class TestDateStr:
    def test_iso_to_display(self):
        from utils.formatters import date_str
        assert date_str("2026-03-05") == "05/03/2026"

    def test_date_object(self):
        from utils.formatters import date_str
        assert date_str(date(2026, 3, 5)) == "05/03/2026"

    def test_datetime_object(self):
        from utils.formatters import date_str
        assert date_str(datetime(2026, 3, 5, 14, 30)) == "05/03/2026"

    def test_invalid_returns_original(self):
        from utils.formatters import date_str
        assert date_str("not-a-date") == "not-a-date"

    def test_custom_format(self):
        from utils.formatters import date_str
        result = date_str("2026-03-05", fmt_out="%Y/%m/%d")
        assert result == "2026/03/05"


class TestDatetimeStr:
    def test_datetime_object(self):
        from utils.formatters import datetime_str
        dt = datetime(2026, 3, 5, 14, 30)
        assert datetime_str(dt) == "05/03/2026 14:30"

    def test_iso_string(self):
        from utils.formatters import datetime_str
        result = datetime_str("2026-03-05T14:30:00")
        assert "05/03/2026" in result
        assert "14:30" in result

    def test_invalid_returns_original(self):
        from utils.formatters import datetime_str
        assert datetime_str("invalid") == "invalid"


class TestPhoneFmt:
    def test_10_digit_format(self):
        from utils.formatters import phone_fmt
        assert phone_fmt("0912345678") == "0912 345 678"

    def test_already_formatted(self):
        from utils.formatters import phone_fmt
        assert phone_fmt("0912 345 678") == "0912 345 678"

    def test_short_number_returns_original(self):
        from utils.formatters import phone_fmt
        assert phone_fmt("12345") == "12345"

    def test_with_dashes(self):
        from utils.formatters import phone_fmt
        assert phone_fmt("091-234-5678") == "0912 345 678"


class TestTruncate:
    def test_short_string_unchanged(self):
        from utils.formatters import truncate
        assert truncate("Hello", 30) == "Hello"

    def test_exact_max_unchanged(self):
        from utils.formatters import truncate
        text = "A" * 30
        assert truncate(text, 30) == text

    def test_long_string_truncated(self):
        from utils.formatters import truncate
        result = truncate("A" * 50, 30)
        assert len(result) == 30
        assert result.endswith("...")

    def test_custom_suffix(self):
        from utils.formatters import truncate
        result = truncate("A" * 50, 30, suffix="…")
        assert result.endswith("…")

    def test_empty_string(self):
        from utils.formatters import truncate
        assert truncate("", 30) == ""


class TestYesNo:
    def test_true(self):
        from utils.formatters import yesno
        assert yesno(True) == "Có"

    def test_false(self):
        from utils.formatters import yesno
        assert yesno(False) == "Không"


class TestActiveText:
    def test_active(self):
        from utils.formatters import active_text
        assert active_text(True) == "Hoạt động"

    def test_inactive(self):
        from utils.formatters import active_text
        assert active_text(False) == "Không hoạt động"
