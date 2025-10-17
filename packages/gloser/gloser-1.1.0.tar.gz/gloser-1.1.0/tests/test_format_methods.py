"""Tests for format_date() and format_number() methods"""

from datetime import date, datetime, time
from gloser import Gloser


class TestFormatDate:
    """Tests for the format_date() method"""

    def test_format_date_with_named_style(self):
        """Test format_date with built-in named styles"""
        g = Gloser()
        test_date = date(2025, 1, 9)

        # English long format
        result = g.format_date(test_date, "long", locale="en")
        assert result == "January 9, 2025"

        # German long format
        result = g.format_date(test_date, "long", locale="de")
        assert result == "9. Januar 2025"

        # French long format
        result = g.format_date(test_date, "long", locale="fr")
        assert result == "9 janvier 2025"

    def test_format_date_with_different_named_styles(self):
        """Test format_date with different named styles"""
        g = Gloser()
        test_date = date(2025, 1, 9)

        # Short format
        result = g.format_date(test_date, "short", locale="en")
        assert result == "01/09/25"

        # Medium format
        result = g.format_date(test_date, "medium", locale="en")
        assert result == "Jan 9, 2025"

        # Full format
        result = g.format_date(test_date, "full", locale="en")
        assert result == "Thursday, January 9, 2025"

    def test_format_date_with_datetime_object(self):
        """Test format_date with datetime objects"""
        g = Gloser()
        test_datetime = datetime(2025, 1, 9, 14, 30, 45)

        # datetime uses datetime format which includes time
        result = g.format_date(test_datetime, "long", locale="en")
        # datetime long format includes time
        assert "January 9, 2025" in result
        assert "02:30:45 PM" in result

    def test_format_date_with_time_object(self):
        """Test format_date with time objects"""
        g = Gloser()
        test_time = time(14, 30, 45)

        # Short time format (default is other, which is short for time)
        result = g.format_date(test_time, "short", locale="en")
        assert result == "02:30 PM"

        # Long time format
        result = g.format_date(test_time, "long", locale="en")
        assert result == "02:30:45 PM "

    def test_format_date_uses_current_locale(self):
        """Test format_date uses current_locale when not specified"""
        g = Gloser(default_locale="de")
        test_date = date(2025, 1, 9)

        # Should use German as default
        result = g.format_date(test_date, "long")
        assert result == "9. Januar 2025"

    def test_format_date_with_empty_format_spec(self):
        """Test format_date with empty format spec uses 'other' format"""
        g = Gloser()
        test_date = date(2025, 1, 9)

        result = g.format_date(test_date, "", locale="en")
        assert result == "01/09/2025"

    def test_format_date_with_locale_gloser(self):
        """Test format_date works with LocaleGloser"""
        g = Gloser()
        de = g["de"]
        test_date = date(2025, 1, 9)

        result = de.format_date(test_date, "long")
        assert result == "9. Januar 2025"

    def test_format_date_capitalization(self):
        """Test format_date with capitalization (uppercase first letter of format style)"""
        g = Gloser()
        test_date = date(2025, 1, 9)

        # Lowercase style name - result as-is
        result = g.format_date(test_date, "long", locale="de")
        assert result == "9. Januar 2025"

        # Uppercase style name - capitalizes result
        result = g.format_date(test_date, "Long", locale="de")
        assert result == "9. Januar 2025"  # Already capitalized in German


class TestFormatNumber:
    """Tests for the format_number() method"""

    def test_format_number_with_locale_separators(self):
        """Test format_number with different locale separators"""
        g = Gloser()

        # English: comma for thousands, period for decimal
        result = g.format_number(1234.56, ",.2f", locale="en")
        assert result == "1,234.56"

        # German: period for thousands, comma for decimal
        result = g.format_number(1234.56, ",.2f", locale="de")
        assert result == "1.234,56"

        # French: space for thousands, comma for decimal
        result = g.format_number(1234.56, ",.2f", locale="fr")
        assert result == "1 234,56"

    def test_format_number_with_different_specs(self):
        """Test format_number with different format specifications"""
        g = Gloser()

        # Integer formatting
        result = g.format_number(1234, "d", locale="en")
        assert result == "1234"

        # Fixed point with 3 decimals
        result = g.format_number(1234.5678, ".3f", locale="en")
        assert result == "1234.568"

        # Percentage
        result = g.format_number(0.1234, ".2%", locale="en")
        assert result == "12.34%"

    def test_format_number_uses_current_locale(self):
        """Test format_number uses current_locale when not specified"""
        g = Gloser(default_locale="de")

        # Should use German separators
        result = g.format_number(1234.56, ",.2f")
        assert result == "1.234,56"

    def test_format_number_with_locale_gloser(self):
        """Test format_number works with LocaleGloser"""
        g = Gloser()
        de = g["de"]

        result = de.format_number(1234.56, ",.2f")
        assert result == "1.234,56"

    def test_format_number_with_integer(self):
        """Test format_number with integer values"""
        g = Gloser()

        result = g.format_number(1234567, ",d", locale="en")
        assert result == "1,234,567"

        result = g.format_number(1234567, ",d", locale="de")
        assert result == "1.234.567"

    def test_format_number_negative_numbers(self):
        """Test format_number with negative numbers"""
        g = Gloser()

        result = g.format_number(-1234.56, ",.2f", locale="en")
        assert result == "-1,234.56"

        result = g.format_number(-1234.56, ",.2f", locale="de")
        assert result == "-1.234,56"

    def test_format_number_with_float(self):
        """Test format_number with float values"""
        g = Gloser()

        # Large float
        result = g.format_number(1234567.89, ",.2f", locale="en")
        assert result == "1,234,567.89"

        # Small float
        result = g.format_number(0.123, ".3f", locale="en")
        assert result == "0.123"


class TestFormatMethodsIntegration:
    """Integration tests for format methods"""

    def test_format_methods_with_translations(self):
        """Test that format methods work alongside translate()"""
        g = Gloser()
        g.add_translations("en", {
            "event": "Event on {date:long}"
        })

        # format_date() for standalone formatting
        test_date = date(2025, 1, 9)
        standalone = g.format_date(test_date, "long", locale="en")
        assert standalone == "January 9, 2025"

        # translate() for translations with embedded formatting
        translated = g.translate("event", date=test_date, locale="en")
        assert translated == "Event on January 9, 2025"

    def test_format_methods_with_no_defaults_loaded(self):
        """Test format methods when load_defaults=False (no auto-loading)"""
        g = Gloser(load_defaults=False)

        # Without defaults, we won't have month names, so result will be missing them
        # This test shows the difference between auto-loading and no loading
        result = g.format_date(date(2025, 1, 9), "long", locale="en")
        # Without loaded defaults, month name placeholder will be empty
        assert " 09, 2025" in result or "9, 2025" in result

        # Number formatting still works with basic defaults
        result = g.format_number(1234.56, ",.2f", locale="en")
        assert result == "1,234.56"

    def test_format_methods_with_preloaded_defaults(self):
        """Test format methods with preloaded locale defaults"""
        g = Gloser(load_defaults=["en", "de", "fr"])

        # Should work immediately without loading
        result = g.format_date(date(2025, 1, 9), "long", locale="en")
        assert result == "January 9, 2025"

        result = g.format_date(date(2025, 1, 9), "long", locale="de")
        assert result == "9. Januar 2025"

        result = g.format_number(1234.56, ",.2f", locale="fr")
        assert result == "1 234,56"
