"""Tests for load_defaults functionality"""
import pytest
from gloser import Gloser


class TestLoadDefaultsParameter:
    """Test load_defaults parameter in __init__"""

    def test_load_defaults_true_autoloads(self):
        """Test that load_defaults=True enables auto-loading"""
        g = Gloser(load_defaults=True)

        # Should auto-load on translate
        result = g.translate("{:long}", count=1, locale="pl")

        # Should have plural rules loaded
        assert g._loaded_default_locales == {"en", "pl"}

    def test_load_defaults_false_no_autoload(self):
        """Test that load_defaults=False disables auto-loading"""
        g = Gloser(load_defaults=False)

        # Should not have any defaults loaded
        assert len(g._loaded_default_locales) == 0

        # Should not auto-load on translate
        g.translate("test", locale="pl")
        assert "pl" not in g._loaded_default_locales

    def test_load_defaults_empty_list_no_autoload(self):
        """Test that load_defaults=[] disables auto-loading"""
        g = Gloser(load_defaults=[])

        # Should not have any defaults loaded
        assert len(g._loaded_default_locales) == 0

        # Should not auto-load on translate
        g.translate("test", locale="de")
        assert "de" not in g._loaded_default_locales

    def test_load_defaults_specific_locales(self):
        """Test loading specific locales at initialization"""
        g = Gloser(load_defaults=["de", "fr", "es"])

        # Should have loaded the specified locales
        assert "de" in g._loaded_default_locales
        assert "fr" in g._loaded_default_locales
        assert "es" in g._loaded_default_locales

        # Should not auto-load additional locales
        g.translate("test", locale="pl")
        assert "pl" not in g._loaded_default_locales

    def test_load_defaults_with_default_locale(self):
        """Test that default_locale is loaded when load_defaults=True"""
        g = Gloser(default_locale="es", load_defaults=True)

        # Spanish should be loaded automatically
        assert "es" in g._loaded_default_locales

    def test_load_defaults_invalid_type(self):
        """Test that invalid load_defaults type raises error"""
        with pytest.raises(ValueError, match="load_defaults must be bool or list"):
            Gloser(load_defaults="invalid")


class TestLoadDefaultsMethod:
    """Test the load_defaults() method"""

    def test_load_defaults_specific_locales(self):
        """Test loading specific locales with load_defaults()"""
        g = Gloser(load_defaults=False)

        # Load specific locales
        g.load_defaults("de", "fr")

        assert "de" in g._loaded_default_locales
        assert "fr" in g._loaded_default_locales
        assert "es" not in g._loaded_default_locales

    def test_load_defaults_all_locales(self):
        """Test loading all available locales"""
        g = Gloser(load_defaults=False)

        # Load all defaults
        g.load_defaults()

        # Should have loaded many locales (at least 70+)
        assert len(g._loaded_default_locales) >= 70

        # Check a few specific ones
        assert "en" in g._loaded_default_locales
        assert "de" in g._loaded_default_locales
        assert "fr" in g._loaded_default_locales
        assert "pl" in g._loaded_default_locales
        assert "ja" in g._loaded_default_locales

    def test_load_defaults_idempotent(self):
        """Test that loading the same locale twice is safe"""
        g = Gloser(load_defaults=False)

        # Load same locale twice
        g.load_defaults("de")
        g.load_defaults("de")

        # Should only be in the set once
        assert "de" in g._loaded_default_locales

    def test_load_defaults_after_init_with_list(self):
        """Test that load_defaults() works after init with locale list"""
        g = Gloser(load_defaults=["en", "de"])

        # Load additional locales
        g.load_defaults("fr", "es")

        assert "en" in g._loaded_default_locales
        assert "de" in g._loaded_default_locales
        assert "fr" in g._loaded_default_locales
        assert "es" in g._loaded_default_locales


class TestLoadDefaultsIntegration:
    """Integration tests for load_defaults functionality"""

    def test_preload_improves_performance(self):
        """Test that preloading defaults works correctly"""
        # Preload specific locales
        g = Gloser(load_defaults=["en", "de", "fr"])
        g.add_translations("en", {"test": "Test"})
        g.add_translations("de", {"test": "Test"})
        g.add_translations("fr", {"test": "Test"})

        # Should not trigger additional loading
        assert g.translate("test", locale="en") == "Test"
        assert g.translate("test", locale="de") == "Test"
        assert g.translate("test", locale="fr") == "Test"

        # Only the preloaded locales should be present
        assert g._loaded_default_locales == {"en", "de", "fr"}

    def test_mixed_preload_and_autoload(self):
        """Test mixing preloaded and auto-loaded defaults"""
        # Preload some, but enable auto-load
        g = Gloser(load_defaults=["en", "de"])

        # These are already loaded
        assert "en" in g._loaded_default_locales
        assert "de" in g._loaded_default_locales

        # This should NOT auto-load (explicit list disables auto-loading)
        g.translate("test", locale="fr")
        assert "fr" not in g._loaded_default_locales

        # But we can manually load it
        g.load_defaults("fr")
        assert "fr" in g._loaded_default_locales

    def test_load_all_then_use(self):
        """Test loading all defaults upfront"""
        g = Gloser(load_defaults=False)

        # Load all defaults
        g.load_defaults()

        # Add translations for various locales
        g.add_translations("en", {"items": {"one": "1 item", "other": "{count} items"}})
        g.add_translations("pl", {"items": {"one": "{count} plik", "few": "{count} pliki", "many": "{count} plików"}})

        # Use plural rules (should already be loaded)
        assert g.translate("items", count=1, locale="en") == "1 item"
        assert g.translate("items", count=5, locale="en") == "5 items"

        assert g.translate("items", count=1, locale="pl") == "1 plik"
        assert g.translate("items", count=2, locale="pl") == "2 pliki"
        assert g.translate("items", count=5, locale="pl") == "5 plików"
