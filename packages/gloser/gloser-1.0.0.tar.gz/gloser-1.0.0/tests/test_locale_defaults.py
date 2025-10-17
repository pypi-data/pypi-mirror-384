"""Tests for default locale loading functionality"""

import pytest
from gloser import Gloser
import datetime


class TestDefaultLocaleLoading:
    """Test automatic loading of default locale configurations"""

    def test_en_defaults_loaded_automatically(self):
        """Test that English defaults are loaded automatically"""
        g = Gloser()  # load_defaults=True by default

        # Should have plural rules from defaults
        assert "en" in g.translations or "en-US" in g.translations

        # Test number formatting with US defaults
        result = g.translate("{price:,.2f}", price=1234.56, locale="en")
        assert result == "1,234.56"  # US format: comma for thousands, period for decimal

    def test_en_us_defaults(self):
        """Test US English specific defaults"""
        g = Gloser(default_locale="en-US")

        # Test date formatting (US uses MM/DD/YYYY)
        date = datetime.date(2025, 1, 15)
        result = g.translate("{date}", date=date, locale="en-US")
        assert result == "01/15/2025"  # US format

    def test_en_gb_defaults(self):
        """Test UK English defaults fall back to English"""
        g = Gloser(default_locale="en-GB")

        # en-GB should fall back to en (US format)
        date = datetime.date(2025, 1, 15)
        result = g.translate("{date}", date=date, locale="en-GB")
        assert result == "01/15/2025"  # US format (fallback from en)

    def test_no_defaults(self):
        """Test Norwegian defaults"""
        g = Gloser(default_locale="no")

        # Test number formatting with Norwegian defaults
        result = g.translate("{price:,.2f}", price=1234.56, locale="no")
        assert result == "1 234,56"  # Norwegian format: space for thousands, comma for decimal

    def test_es_defaults(self):
        """Test Spanish defaults"""
        g = Gloser(default_locale="es")

        # Test number formatting with Spanish defaults
        result = g.translate("{price:,.2f}", price=1234.56, locale="es")
        assert result == "1.234,56"  # Spanish format: period for thousands, comma for decimal

    def test_load_defaults_false(self):
        """Test that defaults are not loaded when load_defaults=False"""
        g = Gloser(load_defaults=False)

        # Should not have any translations loaded
        assert len(g.translations) == 0

    def test_fallback_from_specific_to_language(self):
        """Test that en-US falls back to en.yaml if en-US.yaml doesn't exist"""
        # This test verifies the fallback logic in _load_default_locale
        g = Gloser(default_locale="en-CA")  # en-CA.yaml doesn't exist

        # Should fall back to en.yaml (which is symlinked to en-US.yaml)
        result = g.translate("{price:,.2f}", price=1234.56, locale="en-CA")
        assert result == "1,234.56"  # Should get English defaults

    def test_plural_rules_from_defaults(self):
        """Test that plural rules are loaded from defaults"""
        g = Gloser()
        g.add_translations("en", {
            "items": {
                "one": "one item",
                "other": "{count} items"
            }
        })

        assert g.translate("items", count=1, locale="en") == "one item"
        assert g.translate("items", count=5, locale="en") == "5 items"

    def test_ordinal_rules_from_defaults(self):
        """Test that ordinal plural rules work from defaults"""
        g = Gloser()
        g.add_translations("en", {
            "place": {
                "first": "{pos}st",
                "second": "{pos}nd",
                "third": "{pos}rd",
                "other": "{pos}th"
            }
        })

        assert g.translate("place", pos=1, locale="en") == "1st"
        assert g.translate("place", pos=2, locale="en") == "2nd"
        assert g.translate("place", pos=3, locale="en") == "3rd"
        assert g.translate("place", pos=11, locale="en") == "11th"  # Teen handled correctly
        assert g.translate("place", pos=21, locale="en") == "21st"

    def test_month_names_from_defaults(self):
        """Test that month names are loaded from defaults"""
        g = Gloser()
        date = datetime.date(2025, 1, 15)

        # Test with English
        result = g.translate("{date:long}", date=date, locale="en")
        assert "January" in result

        # Test with Norwegian
        result = g.translate("{date:long}", date=date, locale="no")
        assert "januar" in result

    def test_weekday_names_from_defaults(self):
        """Test that weekday names are loaded from defaults"""
        g = Gloser()
        date = datetime.date(2025, 1, 13)  # Monday

        # Test with English
        result = g.translate("{date:full}", date=date, locale="en")
        assert "Monday" in result

        # Test with Norwegian
        result = g.translate("{date:full}", date=date, locale="no")
        assert "mandag" in result

    def test_user_translations_override_defaults(self):
        """Test that user translations override default configurations"""
        g = Gloser()

        # Override the default decimal separator
        g.add_translations("en", {
            ".number": {
                ".decimal-separator": "#",  # Custom separator
                ".thousand-separator": ","
            }
        })

        result = g.translate("{price:,.2f}", price=1234.56, locale="en")
        assert result == "1,234#56"  # User's custom separator

    def test_defaults_not_loaded_twice(self):
        """Test that defaults are only loaded once per locale"""
        g = Gloser(default_locale="en")

        # First translation loads defaults
        g.translate("test", locale="en")
        assert "en" in g._loaded_default_locales

        # Get initial translation count
        initial_count = len(g.translations.get("en", {}))

        # Second translation shouldn't reload defaults
        g.translate("test2", locale="en")

        # Count should be the same (no duplicate loading)
        assert len(g.translations.get("en", {})) == initial_count

    def test_auto_load_on_first_use(self):
        """Test that defaults are auto-loaded on first use of a locale"""
        g = Gloser(default_locale="en", load_defaults=True)

        # Norwegian defaults not loaded yet
        assert "no" not in g._loaded_default_locales

        # First use of Norwegian locale
        result = g.translate("{price:,.2f}", price=1234.56, locale="no")

        # Should have auto-loaded Norwegian defaults
        assert "no" in g._loaded_default_locales or "no-NO" in g._loaded_default_locales
        assert result == "1 234,56"  # Norwegian format

    def test_non_existent_locale(self):
        """Test behavior with a locale that has no defaults"""
        g = Gloser(default_locale="en")

        # Should not crash with non-existent locale, just mark as loaded
        result = g.translate("{price:,.2f}", price=1234.56, locale="xyz")

        # Should use default formatting (English-style) since xyz doesn't exist
        assert "," in result
        assert "." in result
