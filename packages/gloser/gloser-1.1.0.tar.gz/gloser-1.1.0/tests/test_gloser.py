"""Unit tests for Gloser class"""

import pytest
from pathlib import Path
import tempfile
import yaml
import threading
import time

from gloser.gloser import Gloser, LocaleGloser, translate


class TestGloserBasics:
    """Test basic Gloser functionality"""

    def test_initialization(self):
        """Test Gloser initialization with default and custom locale"""
        g = Gloser(load_defaults=False)  # Disable defaults for this test
        assert g.default_locale == "en"
        assert g.current_locale == "en"
        assert g.translations == {}

        g_custom = Gloser(default_locale="no", load_defaults=False)
        assert g_custom.default_locale == "no"
        assert g_custom.current_locale == "no"

    def test_add_translations(self):
        """Test adding translations for a locale"""
        g = Gloser()
        g.add_translations("en", {"hello": "Hello", "world": "World"})

        assert "en" in g.translations
        assert g.translations["en"]["hello"] == "Hello"
        assert g.translations["en"]["world"] == "World"

    def test_add_translations_multiple_locales(self):
        """Test adding translations for multiple locales"""
        g = Gloser(load_defaults=False)
        g.add_translations("en", {"hello": "Hello"})
        g.add_translations("no", {"hello": "Hei"})
        g.add_translations("es", {"hello": "Hola"})

        assert len(g.translations) == 3
        assert g.translations["en"]["hello"] == "Hello"
        assert g.translations["no"]["hello"] == "Hei"
        assert g.translations["es"]["hello"] == "Hola"

    def test_add_translations_update_existing(self):
        """Test that adding translations updates existing ones"""
        g = Gloser()
        g.add_translations("en", {"hello": "Hello", "world": "World"})
        g.add_translations("en", {"hello": "Hi", "goodbye": "Bye"})

        assert g.translations["en"]["hello"] == "Hi"
        assert g.translations["en"]["world"] == "World"
        assert g.translations["en"]["goodbye"] == "Bye"

    def test_set_locale(self):
        """Test setting the current locale"""
        g = Gloser()
        assert g.current_locale == "en"

        g.set_locale("no")
        assert g.current_locale == "no"

    def test_translate_basic(self):
        """Test basic translation"""
        g = Gloser()
        g.add_translations("en", {"hello": "Hello"})
        g.add_translations("no", {"hello": "Hei"})

        assert g.translate("hello") == "Hello"

        g.set_locale("no")
        assert g.translate("hello") == "Hei"

    def test_translate_with_locale_override(self):
        """Test translation with locale override"""
        g = Gloser()
        g.add_translations("en", {"hello": "Hello"})
        g.add_translations("no", {"hello": "Hei"})
        g.set_locale("en")

        assert g.translate("hello", locale="no") == "Hei"
        # Current locale should remain unchanged
        assert g.current_locale == "en"

    def test_translate_missing_key(self):
        """Test translation with missing key returns the key"""
        g = Gloser()
        g.add_translations("en", {"hello": "Hello"})

        assert g.translate("missing_key") == "missing_key"

    def test_translate_fallback_to_default(self):
        """Test translation falls back to default locale"""
        g = Gloser(default_locale="en")
        g.add_translations("en", {"hello": "Hello"})
        g.set_locale("no")

        # Key exists in default locale but not in current locale
        assert g.translate("hello") == "Hello"

    def test_translate_with_format_args(self):
        """Test translation with format arguments"""
        g = Gloser()
        g.add_translations("en", {"greeting": "Hello, {name}!"})
        g.add_translations("no", {"greeting": "Hei, {name}!"})

        assert g.translate("greeting", name="World") == "Hello, World!"

        g.set_locale("no")
        assert g.translate("greeting", name="Verden") == "Hei, Verden!"

    def test_global_translate_function(self):
        """Test the global translate convenience function"""
        # This test uses the global _default_gloser instance
        # Note: This might have state from other tests, so we add new keys
        from gloser.gloser import _default_gloser

        _default_gloser.add_translations("en", {"test_key": "Test Value"})
        result = translate("test_key")
        assert result == "Test Value"

    def test_t_shorthand(self):
        """Test the t() shorthand for translate()"""
        g = Gloser()
        g.add_translations("en", {
            "hello": "Hello",
            "greeting": "Hello, {name}!"
        })
        g.add_translations("es", {
            "hello": "Hola",
            "greeting": "¡Hola, {name}!"
        })

        # Basic usage
        assert g.t("hello") == "Hello"

        # With parameters
        assert g.t("greeting", name="World") == "Hello, World!"

        # With locale
        assert g.t("hello", locale="es") == "Hola"
        assert g.t("greeting", name="Mundo", locale="es") == "¡Hola, Mundo!"


class TestGloserYAML:
    """Test YAML file loading functionality"""

    def test_load_yaml_basic(self):
        """Test loading basic YAML file with explicit keys"""
        g = Gloser(default_locale="en")

        # Create a temporary YAML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""hello:
  en: Hello
  no: Hei
  es: Hola
world:
  en: World
  no: Verden
  es: Mundo
""")
            temp_path = f.name

        try:
            g.load_yaml(temp_path)

            # Check that translations were loaded
            assert g.translate("hello", locale="en") == "Hello"
            assert g.translate("hello", locale="no") == "Hei"
            assert g.translate("hello", locale="es") == "Hola"

            assert g.translate("world", locale="en") == "World"
            assert g.translate("world", locale="no") == "Verden"
            assert g.translate("world", locale="es") == "Mundo"
        finally:
            Path(temp_path).unlink()

    def test_load_yaml_multiple_single_locale_documents(self):
        """Test loading YAML with multiple single-locale documents"""
        g = Gloser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""---
.locale: no
hello: Hei
goodbye: Ha det
---
.locale: en
hello: Hello
goodbye: Goodbye
""")
            temp_path = f.name

        try:
            g.load_yaml(temp_path)
            assert g.translate("hello", locale="no") == "Hei"
            assert g.translate("goodbye", locale="no") == "Ha det"
            assert g.translate("hello", locale="en") == "Hello"
            assert g.translate("goodbye", locale="en") == "Goodbye"
        finally:
            Path(temp_path).unlink()

    def test_load_yaml_mixed_document_types(self):
        """Test mixing single-locale and multi-locale documents in same file"""
        g = Gloser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""---
.locale: no
hello: Hei
---
goodbye:
  en: Goodbye
  es: Adiós
---
.locale: fr
hello: Bonjour
""")
            temp_path = f.name

        try:
            g.load_yaml(temp_path)
            # From first document (single-locale .locale: no)
            assert g.translate("hello", locale="no") == "Hei"
            # From second document (multi-locale)
            assert g.translate("goodbye", locale="en") == "Goodbye"
            assert g.translate("goodbye", locale="es") == "Adiós"
            # From third document (single-locale .locale: fr)
            assert g.translate("hello", locale="fr") == "Bonjour"
        finally:
            Path(temp_path).unlink()

    def test_load_yaml_file_not_found(self):
        """Test loading non-existent YAML file raises error"""
        g = Gloser()

        with pytest.raises(FileNotFoundError):
            g.load_yaml("nonexistent_file.yaml")

    def test_load_yaml_non_dict_values_skipped(self):
        """Test that non-dict values in multi-locale format are skipped"""
        g = Gloser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""hello:
  en: Hello
  no: Hei
some_string: "This is not a translation"
world:
  en: World
  no: Verden
""")
            temp_path = f.name

        try:
            g.load_yaml(temp_path)

            # Should only load the dict values (translations)
            assert g.translate("hello", locale="en") == "Hello"
            assert g.translate("world", locale="en") == "World"
            # some_string should be skipped
            assert g.translate("some_string", locale="en") == "some_string"
        finally:
            Path(temp_path).unlink()

    def test_load_yaml_multiple_files(self):
        """Test loading multiple YAML files"""
        g = Gloser()

        # Create two temporary YAML files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f1:
            f1.write("""hello:
  en: Hello
  no: Hei
""")
            temp_path1 = f1.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f2:
            f2.write("""goodbye:
  en: Goodbye
  no: Ha det
""")
            temp_path2 = f2.name

        try:
            g.load_yaml_files(temp_path1, temp_path2)

            assert g.translate("hello", locale="en") == "Hello"
            assert g.translate("hello", locale="no") == "Hei"
            assert g.translate("goodbye", locale="en") == "Goodbye"
            assert g.translate("goodbye", locale="no") == "Ha det"
        finally:
            Path(temp_path1).unlink()
            Path(temp_path2).unlink()

    def test_load_yaml_with_pathlib(self):
        """Test loading YAML using pathlib.Path"""
        g = Gloser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""hello:
  en: Hello
  no: Hei
""")
            temp_path = Path(f.name)

        try:
            g.load_yaml(temp_path)

            assert g.translate("hello", locale="en") == "Hello"
            assert g.translate("hello", locale="no") == "Hei"
        finally:
            temp_path.unlink()

    def test_load_yaml_preserves_existing_translations(self):
        """Test that loading YAML preserves existing translations"""
        g = Gloser()
        g.add_translations("en", {"manual": "Manual Entry"})

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""hello:
  en: Hello
  no: Hei
""")
            temp_path = f.name

        try:
            g.load_yaml(temp_path)

            # Check both manual and YAML-loaded translations exist
            assert g.translate("manual", locale="en") == "Manual Entry"
            assert g.translate("hello", locale="en") == "Hello"
        finally:
            Path(temp_path).unlink()

    def test_load_yaml_with_special_characters(self):
        """Test loading YAML with special characters in translations"""
        g = Gloser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""greeting:
  en: "Hello, {name}!"
  no: "Hei, {name}!"
""")
            temp_path = f.name

        try:
            g.load_yaml(temp_path)

            assert g.translate("greeting", locale="en", name="World") == "Hello, World!"
            assert g.translate("greeting", locale="no", name="Verden") == "Hei, Verden!"
        finally:
            Path(temp_path).unlink()

    def test_load_yaml_with_multiple_keys(self):
        """Test loading YAML with multiple translation keys"""
        g = Gloser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""hello:
  en: Hello
  no: Hei
  es: Hola
world:
  en: World
  no: Verden
  es: Mundo
greeting:
  en: "Hello, {name}!"
  no: "Hei, {name}!"
""")
            temp_path = f.name

        try:
            g.load_yaml(temp_path)

            # Check that translations use the explicit keys
            assert g.translate("hello", locale="en") == "Hello"
            assert g.translate("hello", locale="no") == "Hei"
            assert g.translate("hello", locale="es") == "Hola"

            assert g.translate("world", locale="en") == "World"
            assert g.translate("world", locale="no") == "Verden"
            assert g.translate("world", locale="es") == "Mundo"

            assert g.translate("greeting", locale="en", name="Alice") == "Hello, Alice!"
            assert g.translate("greeting", locale="no", name="Alice") == "Hei, Alice!"
        finally:
            Path(temp_path).unlink()

    def test_load_yaml_empty_key(self):
        """Test that empty keys are loaded correctly"""
        g = Gloser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""hello:
  en: Hello
  no: Hei
"":
  en: Empty Key
  no: Tom nøkkel
""")
            temp_path = f.name

        try:
            g.load_yaml(temp_path)
            # Empty key should work
            assert g.translate("", locale="en") == "Empty Key"
            assert g.translate("", locale="no") == "Tom nøkkel"
        finally:
            Path(temp_path).unlink()

    def test_load_yaml_multi_document_with_nested_structures(self):
        """Test multi-document YAML with nested structures (plurals, number format)"""
        g = Gloser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(""".plurals:
  en:
    one: "^1$"
  no:
    one: "^1$"
    few: "^[2-7]$"
items:
  en:
    one: "one item"
    other: "{count} items"
  no:
    one: "én ting"
    few: "noen få ting"
    other: "{count} ting"
.number:
  no:
    .decimal-separator: ","
    .thousand-separator: " "
""")
            temp_path = f.name

        try:
            g.load_yaml(temp_path)

            # Test English plurals
            assert g.translate("items", count=1, locale="en") == "one item"
            assert g.translate("items", count=5, locale="en") == "5 items"

            # Test Norwegian plurals with custom rules
            assert g.translate("items", count=1, locale="no") == "én ting"
            assert g.translate("items", count=3, locale="no") == "noen få ting"
            assert g.translate("items", count=10, locale="no") == "10 ting"

            # Test Norwegian number formatting
            assert g.translate("{price:,.2f}", price=1234.56, locale="no") == "1 234,56"
        finally:
            Path(temp_path).unlink()


class TestSingleLocaleYAML:
    """Test single-locale YAML file format"""

    def test_single_locale_basic(self):
        """Test loading single-locale YAML with basic key-value pairs"""
        g = Gloser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(""".locale: no
hello: Hei
world: Verden
goodbye: Ha det
""")
            temp_path = f.name

        try:
            g.load_yaml(temp_path)

            assert g.translate("hello", locale="no") == "Hei"
            assert g.translate("world", locale="no") == "Verden"
            assert g.translate("goodbye", locale="no") == "Ha det"
        finally:
            Path(temp_path).unlink()

    def test_single_locale_with_plurals(self):
        """Test single-locale YAML with plural forms"""
        g = Gloser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(""".locale: no
.plurals:
  one: "^1$"
  few: "^[2-7]$"
items:
  one: "én ting"
  few: "noen få ting"
  other: "{count} ting"
""")
            temp_path = f.name

        try:
            g.load_yaml(temp_path)

            assert g.translate("items", count=1, locale="no") == "én ting"
            assert g.translate("items", count=3, locale="no") == "noen få ting"
            assert g.translate("items", count=10, locale="no") == "10 ting"
        finally:
            Path(temp_path).unlink()

    def test_single_locale_with_number_format(self):
        """Test single-locale YAML with number formatting"""
        g = Gloser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(""".locale: no
.number:
  .decimal-separator: ","
  .thousand-separator: " "
price: "Pris: {price:,.2f} kr"
""")
            temp_path = f.name

        try:
            g.load_yaml(temp_path)

            result = g.translate("price", price=1234.56, locale="no")
            assert result == "Pris: 1 234,56 kr"
        finally:
            Path(temp_path).unlink()

    def test_single_locale_with_date_format(self):
        """Test single-locale YAML with date formatting"""
        g = Gloser()
        import datetime

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(""".locale: no
.date:
  short: "{DD}.{MM}.{YY}"
  long: "{DD}. {monthname} {YYYY}"
.month:
  full:
    1: januar
    10: oktober
meeting: "Møte: {date:short}"
""")
            temp_path = f.name

        try:
            g.load_yaml(temp_path)

            date = datetime.date(2025, 10, 13)
            result = g.translate("meeting", date=date, locale="no")
            assert result == "Møte: 13.10.25"
        finally:
            Path(temp_path).unlink()

    def test_single_locale_combined(self):
        """Test single-locale YAML with all features combined"""
        g = Gloser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(""".locale: no
.plurals:
  one: "^1$"
.number:
  .decimal-separator: ","
  .thousand-separator: " "
hello: Hei
downloads:
  one: "{count:,} nedlasting"
  other: "{count:,} nedlastinger"
""")
            temp_path = f.name

        try:
            g.load_yaml(temp_path)

            assert g.translate("hello", locale="no") == "Hei"
            assert g.translate("downloads", count=1, locale="no") == "1 nedlasting"
            assert g.translate("downloads", count=1000, locale="no") == "1 000 nedlastinger"
        finally:
            Path(temp_path).unlink()

    def test_single_locale_missing_locale_field(self):
        """Test that single document without .locale field is treated as multi-locale"""
        g = Gloser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            # Single document WITHOUT .locale is treated as multi-locale format
            # But with strings instead of dicts, they should be skipped
            f.write("""hello: Hei
world: Verden
""")
            temp_path = f.name

        try:
            g.load_yaml(temp_path)
            # Since "Hei" and "Verden" are strings (not dicts), they should be skipped
            # So no translations should be loaded
            assert g.translate("hello", locale="no") == "hello"
            assert g.translate("world", locale="no") == "world"
        finally:
            Path(temp_path).unlink()

    def test_single_locale_invalid_locale_field(self):
        """Test that invalid .locale field raises error"""
        g = Gloser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(""".locale: ""
hello: Hei
""")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="invalid '.locale' field"):
                g.load_yaml(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_mixed_format_files(self):
        """Test loading both single-locale and multi-document files"""
        g = Gloser()

        # Create single-locale file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(""".locale: no
hello: Hei
""")
            temp_path_single = f.name

        # Create multi-document file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""world:
  en: World
  no: Verden
""")
            temp_path_multi = f.name

        try:
            g.load_yaml(temp_path_single)
            g.load_yaml(temp_path_multi)

            assert g.translate("hello", locale="no") == "Hei"
            assert g.translate("world", locale="en") == "World"
            assert g.translate("world", locale="no") == "Verden"
        finally:
            Path(temp_path_single).unlink()
            Path(temp_path_multi).unlink()

    def test_single_locale_with_interpolation(self):
        """Test single-locale YAML with string interpolation"""
        g = Gloser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(""".locale: no
greeting: "Hei, {name}!"
welcome: "Velkommen til {country}, {name}!"
""")
            temp_path = f.name

        try:
            g.load_yaml(temp_path)

            assert g.translate("greeting", name="Alice", locale="no") == "Hei, Alice!"
            assert g.translate("welcome", name="Bob", country="Norge", locale="no") == "Velkommen til Norge, Bob!"
        finally:
            Path(temp_path).unlink()


class TestMultiUserContext:
    """Test multi-user web context functionality"""

    def test_gloser_init_with_file_path(self):
        """Test Gloser initialization with file path"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""hello:
  en: Hello
  no: Hei
""")
            temp_path = f.name

        try:
            # Test initialization with single file
            g = Gloser(temp_path)
            assert g.translate("hello", locale="en") == "Hello"
            assert g.translate("hello", locale="no") == "Hei"
        finally:
            Path(temp_path).unlink()

    def test_gloser_init_with_multiple_files(self):
        """Test Gloser initialization with multiple file paths"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f1:
            f1.write("""hello:
  en: Hello
  no: Hei
""")
            temp_path1 = f1.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f2:
            f2.write("""goodbye:
  en: Goodbye
  no: Ha det
""")
            temp_path2 = f2.name

        try:
            g = Gloser([temp_path1, temp_path2])
            assert g.translate("hello", locale="en") == "Hello"
            assert g.translate("goodbye", locale="no") == "Ha det"
        finally:
            Path(temp_path1).unlink()
            Path(temp_path2).unlink()

    def test_getitem_returns_locale_gloser(self):
        """Test that [] operator returns LocaleGloser"""
        g = Gloser()
        g.add_translations("en", {"hello": "Hello"})
        g.add_translations("no", {"hello": "Hei"})

        t = g["no"]
        assert isinstance(t, LocaleGloser)
        assert t.locale == "no"

    def test_for_locale_returns_locale_gloser(self):
        """Test that for_locale() returns LocaleGloser"""
        g = Gloser()
        g.add_translations("en", {"hello": "Hello"})
        g.add_translations("no", {"hello": "Hei"})

        t = g.for_locale("no")
        assert isinstance(t, LocaleGloser)
        assert t.locale == "no"

    def test_locale_gloser_callable(self):
        """Test that LocaleGloser is callable for translation"""
        g = Gloser()
        g.add_translations("en", {"hello": "Hello", "greeting": "Hello, {name}!"})
        g.add_translations("no", {"hello": "Hei", "greeting": "Hei, {name}!"})

        # Test English
        t_en = g["en"]
        assert t_en("hello") == "Hello"
        assert t_en("greeting", name="World") == "Hello, World!"

        # Test Norwegian
        t_no = g["no"]
        assert t_no("hello") == "Hei"
        assert t_no("greeting", name="Verden") == "Hei, Verden!"

    def test_locale_gloser_shares_parent(self):
        """Test that LocaleGloser references parent Gloser"""
        g = Gloser()
        g.add_translations("en", {"hello": "Hello"})

        t1 = g["en"]
        t2 = g["en"]

        # Both should reference the same parent Gloser
        assert t1._gloser is g
        assert t2._gloser is g
        assert t1._gloser is t2._gloser

    def test_locale_gloser_fallback_to_default(self):
        """Test that LocaleGloser falls back to default locale"""
        g = Gloser(default_locale="en")
        g.add_translations("en", {"hello": "Hello", "world": "World"})
        g.add_translations("no", {"hello": "Hei"})  # Missing "world"

        t = g["no"]
        assert t("hello") == "Hei"  # From Norwegian
        assert t("world") == "World"  # Falls back to English

    def test_locale_gloser_missing_key(self):
        """Test that LocaleGloser returns key when translation not found"""
        g = Gloser()
        g.add_translations("en", {"hello": "Hello"})

        t = g["en"]
        assert t("missing_key") == "missing_key"

    def test_gloser_callable(self):
        """Test that Gloser itself is callable"""
        g = Gloser()
        g.add_translations("en", {"hello": "Hello"})
        g.add_translations("no", {"hello": "Hei"})
        g.set_locale("no")

        # Test callable shorthand
        assert g("hello") == "Hei"
        assert g("hello", locale="en") == "Hello"

    def test_multi_user_concurrent_access(self):
        """Test that multiple users can access different locales concurrently"""
        # Create shared Gloser instance
        g = Gloser()
        g.add_translations("en", {"message": "English"})
        g.add_translations("no", {"message": "Norwegian"})
        g.add_translations("es", {"message": "Spanish"})
        g.add_translations("fr", {"message": "French"})

        results = {}
        errors = []

        def user_request(user_id, locale, expected):
            """Simulate a user request"""
            try:
                t = g[locale]
                # Simulate some processing time
                time.sleep(0.01)
                result = t("message")
                results[user_id] = result
                # Verify it matches expected
                if result != expected:
                    errors.append(f"User {user_id}: expected {expected}, got {result}")
            except Exception as e:
                errors.append(f"User {user_id}: {e}")

        # Create threads simulating concurrent users
        threads = [
            threading.Thread(target=user_request, args=("user1", "en", "English")),
            threading.Thread(target=user_request, args=("user2", "no", "Norwegian")),
            threading.Thread(target=user_request, args=("user3", "es", "Spanish")),
            threading.Thread(target=user_request, args=("user4", "fr", "French")),
            threading.Thread(target=user_request, args=("user5", "en", "English")),
            threading.Thread(target=user_request, args=("user6", "no", "Norwegian")),
        ]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all to complete
        for thread in threads:
            thread.join()

        # Verify no errors
        assert not errors, f"Concurrent access errors: {errors}"

        # Verify all users got correct translations
        assert results["user1"] == "English"
        assert results["user2"] == "Norwegian"
        assert results["user3"] == "Spanish"
        assert results["user4"] == "French"
        assert results["user5"] == "English"
        assert results["user6"] == "Norwegian"

    def test_web_context_pattern(self):
        """Test the full web context usage pattern"""
        # Simulate global setup at application startup
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""welcome:
  en: "Welcome, {name}!"
  no: "Velkommen, {name}!"
  es: "¡Bienvenido, {name}!"
goodbye:
  en: Goodbye
  no: Ha det
  es: Adiós
""")
            temp_path = f.name

        try:
            # Global setup (once at startup)
            gloser = Gloser(temp_path, default_locale="en")

            # Simulate multiple user requests
            def handle_user_request(user_name, user_locale):
                """Simulate a user request handler"""
                t = gloser[user_locale]
                welcome = t("welcome", name=user_name)
                goodbye = t("goodbye")
                return welcome, goodbye

            # User 1: English
            welcome, goodbye = handle_user_request("Alice", "en")
            assert welcome == "Welcome, Alice!"
            assert goodbye == "Goodbye"

            # User 2: Norwegian
            welcome, goodbye = handle_user_request("Bob", "no")
            assert welcome == "Velkommen, Bob!"
            assert goodbye == "Ha det"

            # User 3: Spanish
            welcome, goodbye = handle_user_request("Carlos", "es")
            assert welcome == "¡Bienvenido, Carlos!"
            assert goodbye == "Adiós"

        finally:
            Path(temp_path).unlink()


class TestInterpolation:
    """Test string interpolation features"""

    def test_positional_arguments(self):
        """Test translation with positional arguments"""
        g = Gloser()
        g.add_translations("en", {"greeting": "Hello {} from {}"})
        g.add_translations("no", {"greeting": "Hei {} fra {}"})

        assert g.translate("greeting", "John", "England") == "Hello John from England"

        g.set_locale("no")
        assert g.translate("greeting", "John", "Norge") == "Hei John fra Norge"

    def test_positional_with_indices(self):
        """Test translation with indexed positional arguments"""
        g = Gloser()
        g.add_translations("en", {"message": "{0} and {1} and {0} again"})

        assert g.translate("message", "first", "second") == "first and second and first again"

    def test_keyword_arguments(self):
        """Test translation with keyword arguments (existing behavior)"""
        g = Gloser()
        g.add_translations("en", {"greeting": "Hello {name} from {country}"})

        assert g.translate("greeting", name="John", country="England") == "Hello John from England"

    def test_mixed_positional_and_keyword(self):
        """Test translation with both positional and keyword arguments"""
        g = Gloser()
        g.add_translations("en", {"message": "User {} is {age} years old"})

        assert g.translate("message", "John", age=30) == "User John is 30 years old"

    def test_interpolation_on_missing_key(self):
        """Test that interpolation works even when key is not found"""
        g = Gloser()
        g.add_translations("en", {"hello": "Hello"})

        # Key not found, but interpolation should still work
        assert g.translate("Hello {name}", name="John") == "Hello John"
        assert g.translate("User {} from {}", "John", "England") == "User John from England"

    def test_interpolation_on_missing_key_with_fallback(self):
        """Test interpolation on missing key with default locale fallback"""
        g = Gloser(default_locale="en")
        g.add_translations("en", {"known": "Known"})
        g.set_locale("no")

        # Key not in Norwegian or English, should interpolate
        assert g.translate("Welcome {name}!", name="Alice") == "Welcome Alice!"

    def test_interpolation_error_handling(self):
        """Test that interpolation errors don't break the translation"""
        g = Gloser()

        # Missing keyword argument - should return key as-is
        result = g.translate("Hello {name}")
        assert result == "Hello {name}"

        # Missing positional argument - should return key as-is
        result = g.translate("Hello {} from {}", "John")
        assert result == "Hello {} from {}"

    def test_locale_gloser_positional_arguments(self):
        """Test LocaleGloser with positional arguments"""
        g = Gloser()
        g.add_translations("en", {"greeting": "Hello {} from {}"})
        g.add_translations("no", {"greeting": "Hei {} fra {}"})

        t_en = g["en"]
        assert t_en("greeting", "John", "England") == "Hello John from England"

        t_no = g["no"]
        assert t_no("greeting", "John", "Norge") == "Hei John fra Norge"

    def test_locale_gloser_interpolation_on_missing_key(self):
        """Test LocaleGloser interpolation when key is not found"""
        g = Gloser()
        g.add_translations("en", {"hello": "Hello"})

        t = g["en"]
        # Key not found, but interpolation should work
        assert t("Welcome {name}!", name="Alice") == "Welcome Alice!"
        assert t("Hello {} from {}", "John", "England") == "Hello John from England"

    def test_callable_syntax_with_positional_args(self):
        """Test callable syntax g() with positional arguments"""
        g = Gloser()
        g.add_translations("en", {"message": "User {} is {age} years old"})

        assert g("message", "John", age=30) == "User John is 30 years old"

    def test_empty_translation_with_args(self):
        """Test that args work correctly with empty/whitespace translations"""
        g = Gloser()
        g.add_translations("en", {"template": "{} + {} = {}"})

        assert g.translate("template", "1", "2", "3") == "1 + 2 = 3"


class TestNumberFormatting:
    """Test locale-aware number formatting"""

    def test_basic_number_formatting_english(self):
        """Test basic number formatting with English locale (default)"""
        g = Gloser(default_locale="en")
        g.add_translations("en", {"price": "Price: ${:,.2f}"})

        assert g.translate("price", 1234.567) == "Price: $1,234.57"

    def test_basic_number_formatting_norwegian(self):
        """Test basic number formatting with Norwegian locale"""
        g = Gloser(default_locale="en")
        g.add_translations("no", {
            "price": "Pris: {:,.2f} kr",
            ".number": {
                ".decimal-separator": ",",
                ".thousand-separator": "."
            }
        })

        assert g.translate("price", 1234.567, locale="no") == "Pris: 1.234,57 kr"

    def test_thousand_separator_norwegian(self):
        """Test thousand separator with Norwegian locale"""
        g = Gloser()
        g.add_translations("no", {
            "amount": "{:,.2f}",
            ".number": {
                ".decimal-separator": ",",
                ".thousand-separator": "."
            }
        })

        assert g.translate("amount", 1234567.89, locale="no") == "1.234.567,89"

    def test_number_formatting_with_different_specs(self):
        """Test various Python format specifications with locale formatting"""
        g = Gloser()
        g.add_translations("no", {
            ".number": {
                ".decimal-separator": ",",
                ".thousand-separator": "."
            }
        })

        # Floating point with 2 decimals
        assert g.translate("{:.2f}", 1234.567, locale="no") == "1234,57"

        # Floating point with 3 decimals
        assert g.translate("{:.3f}", 1234.567, locale="no") == "1234,567"

        # With thousand separator
        assert g.translate("{:,.2f}", 1234567.89, locale="no") == "1.234.567,89"

        # Integer (no decimals expected)
        assert g.translate("{:d}", 1234, locale="no") == "1234"

    def test_number_formatting_scientific_notation(self):
        """Test scientific notation with locale formatting"""
        g = Gloser()
        g.add_translations("no", {
            ".number": {
                ".decimal-separator": ",",
                ".thousand-separator": "."
            }
        })

        result = g.translate("{:.2e}", 1234.567, locale="no")
        assert "," in result  # Should have comma as decimal separator
        assert result == "1,23e+03"

    def test_number_formatting_percentage(self):
        """Test percentage formatting with locale"""
        g = Gloser()
        g.add_translations("no", {
            ".number": {
                ".decimal-separator": ",",
                ".thousand-separator": "."
            }
        })

        assert g.translate("{:.1%}", 0.1234, locale="no") == "12,3%"

    def test_mixed_text_and_numbers(self):
        """Test formatting with both text and numbers"""
        g = Gloser()
        g.add_translations("no", {
            "report": "Totalt: {total:,.2f} kr for {items} varer",
            ".number": {
                ".decimal-separator": ",",
                ".thousand-separator": "."
            }
        })

        result = g.translate("report", total=1234.56, items=10, locale="no")
        assert result == "Totalt: 1.234,56 kr for 10 varer"

    def test_negative_numbers(self):
        """Test formatting negative numbers with locale"""
        g = Gloser()
        g.add_translations("no", {
            ".number": {
                ".decimal-separator": ",",
                ".thousand-separator": "."
            }
        })

        assert g.translate("{:,.2f}", -1234.56, locale="no") == "-1.234,56"

    def test_zero_and_small_numbers(self):
        """Test formatting zero and small numbers"""
        g = Gloser()
        g.add_translations("no", {
            ".number": {
                ".decimal-separator": ",",
                ".thousand-separator": "."
            }
        })

        assert g.translate("{:.2f}", 0, locale="no") == "0,00"
        assert g.translate("{:.4f}", 0.0001, locale="no") == "0,0001"

    def test_very_large_numbers(self):
        """Test formatting very large numbers"""
        g = Gloser()
        g.add_translations("no", {
            ".number": {
                ".decimal-separator": ",",
                ".thousand-separator": "."
            }
        })

        assert g.translate("{:,.0f}", 1234567890, locale="no") == "1.234.567.890"

    def test_default_separators_when_not_configured(self):
        """Test that default separators are used when not configured"""
        g = Gloser()
        g.add_translations("en", {
            "price": "{:,.2f}"
        })

        # English should use default . and ,
        assert g.translate("price", 1234.56, locale="en") == "1,234.56"

    def test_only_decimal_separator_configured(self):
        """Test when only decimal separator is configured"""
        g = Gloser()
        g.add_translations("custom", {
            ".number": {
                ".decimal-separator": ","
            }
            # thousand-separator not configured, should default to ","
        })

        # With only decimal separator changed
        assert g.translate("{:.2f}", 1234.56, locale="custom") == "1234,56"

    def test_only_thousand_separator_configured(self):
        """Test when only thousand separator is configured"""
        g = Gloser()
        g.add_translations("custom", {
            ".number": {
                ".thousand-separator": " "
            }
            # decimal-separator not configured, should default to "."
        })

        # With only thousand separator changed
        assert g.translate("{:,.2f}", 1234.56, locale="custom") == "1 234.56"

    def test_string_values_not_affected(self):
        """Test that non-numeric values are not affected by locale formatting"""
        g = Gloser()
        g.add_translations("no", {
            "message": "Hello {name}",
            ".number": {
                ".decimal-separator": ",",
                ".thousand-separator": "."
            }
        })

        assert g.translate("message", name="John", locale="no") == "Hello John"

    def test_locale_gloser_number_formatting(self):
        """Test number formatting with LocaleGloser"""
        g = Gloser()
        g.add_translations("no", {
            "price": "Pris: {:.2f} kr",
            ".number": {
                ".decimal-separator": ",",
                ".thousand-separator": "."
            }
        })

        t = g["no"]
        assert t("price", 1234.56) == "Pris: 1234,56 kr"

    def test_multiple_numbers_in_one_string(self):
        """Test formatting multiple numbers in one string"""
        g = Gloser()
        g.add_translations("no", {
            "range": "Fra {:.2f} til {:.2f}",
            ".number": {
                ".decimal-separator": ",",
                ".thousand-separator": "."
            }
        })

        assert g.translate("range", 10.5, 99.9, locale="no") == "Fra 10,50 til 99,90"

    def test_positional_and_keyword_numbers(self):
        """Test mixing positional and keyword number arguments"""
        g = Gloser()
        g.add_translations("no", {
            "report": "{} items cost {price:,.2f} kr",
            ".number": {
                ".decimal-separator": ",",
                ".thousand-separator": "."
            }
        })

        assert g.translate("report", 5, price=1234.56, locale="no") == "5 items cost 1.234,56 kr"

    def test_number_formatting_fallback_locale(self):
        """Test that number formatting works with fallback to default locale"""
        g = Gloser(default_locale="no")
        g.add_translations("no", {
            "price": "Pris: {:.2f} kr",
            ".number": {
                ".decimal-separator": ",",
                ".thousand-separator": "."
            }
        })

        # Request Swedish locale, should fall back to Norwegian
        assert g.translate("price", 1234.56, locale="sv") == "Pris: 1234,56 kr"

    def test_number_formatting_on_missing_key(self):
        """Test number formatting when key is not found"""
        g = Gloser()
        g.add_translations("no", {
            ".number": {
                ".decimal-separator": ",",
                ".thousand-separator": "."
            }
        })

        # Key not found, but number formatting should still work
        assert g.translate("Price: {:.2f}", 1234.56, locale="no") == "Price: 1234,56"

    def test_integer_formatting(self):
        """Test formatting integers with thousand separators"""
        g = Gloser()
        g.add_translations("no", {
            ".number": {
                ".decimal-separator": ",",
                ".thousand-separator": "."
            }
        })

        # Integer with thousand separator
        assert g.translate("{:,d}", 1234567, locale="no") == "1.234.567"

    def test_complex_numbers(self):
        """Test that complex numbers are handled correctly"""
        g = Gloser()
        g.add_translations("no", {
            ".number": {
                ".decimal-separator": ",",
                ".thousand-separator": "."
            }
        })

        # Complex number formatting (Python supports this)
        result = g.translate("{:.2f}", 3.14+2.71j, locale="no")
        # Should have comma as decimal separator
        assert "," in result

    def test_no_format_spec_no_conversion(self):
        """Test that numbers without format specs are not converted"""
        g = Gloser()
        g.add_translations("no", {
            "message": "Value: {}",
            ".number": {
                ".decimal-separator": ",",
                ".thousand-separator": "."
            }
        })

        # Without format spec, should use default Python str() conversion
        result = g.translate("message", 1234.56, locale="no")
        # Python's default str() for numbers uses "." for decimals
        assert result == "Value: 1234.56"

    def test_g_format_spec(self):
        """Test 'g' format specification (general format)"""
        g = Gloser()
        g.add_translations("no", {
            ".number": {
                ".decimal-separator": ",",
                ".thousand-separator": "."
            }
        })

        # 'g' format uses exponential for large numbers, fixed for small
        assert g.translate("{:.3g}", 1234.5, locale="no") == "1,23e+03"
        assert g.translate("{:.5g}", 123.45, locale="no") == "123,45"


class TestDateFormatting:
    """Test locale-aware date formatting"""

    def test_basic_date_formatting_default(self):
        """Test basic date formatting with default format"""
        import datetime
        g = Gloser(load_defaults=False)
        date = datetime.date(2025, 10, 13)

        # With no custom format and no defaults, should use ISO format
        assert g.translate("Date: {}", date) == "Date: 2025-10-13"

    def test_basic_date_formatting_norwegian(self):
        """Test basic date formatting with Norwegian locale and custom format"""
        import datetime
        g = Gloser()
        g.add_translations("no", {
            ".date": {
                "short": "{DD}.{MM}.{YY}",
                "long": "{DD}. {monthname} {YYYY}",
                "full": "{dayname}, {DD}. {monthname} {YYYY}",
                "other": "{DD}.{MM}.{YYYY}"
            }
        })

        date = datetime.date(2025, 10, 13)

        # Default format
        assert g.translate("{}", date, locale="no") == "13.10.2025"

        # Short format
        assert g.translate("{:short}", date, locale="no") == "13.10.25"

    def test_date_formatting_with_month_names(self):
        """Test date formatting with localized month names"""
        import datetime
        g = Gloser()
        g.add_translations("no", {
            ".date": {
                "long": "{DD}. {monthname} {YYYY}",
                "other": "{DD}. {monthname} {YYYY}"
            },
            ".month": {
                "full": {
                    "10": "oktober"
                }
            }
        })

        date = datetime.date(2025, 10, 13)
        assert g.translate("{}", date, locale="no") == "13. oktober 2025"

    def test_date_formatting_with_weekday_names(self):
        """Test date formatting with localized weekday names"""
        import datetime
        g = Gloser()
        g.add_translations("no", {
            ".date": {
                "full": "{dayname}, {DD}.{MM}.{YYYY}",
                "other": "{dayname}, {DD}.{MM}.{YYYY}"
            },
            ".dayofweek": {
                "full": {
                    "1": "mandag"
                }
            }
        })

        date = datetime.date(2025, 10, 13)  # This is a Monday
        assert g.translate("{}", date, locale="no") == "mandag, 13.10.2025"

    def test_date_formatting_multiple_months(self):
        """Test date formatting with multiple localized months"""
        import datetime
        g = Gloser()
        g.add_translations("no", {
            ".date": {
                "other": "{monthname} {YYYY}"
            },
            ".month": {
                "full": {
                    "1": "januar",
                    "2": "februar",
                    "3": "mars",
                    "12": "desember"
                }
            }
        })

        assert g.translate("{}", datetime.date(2025, 1, 15), locale="no") == "januar 2025"
        assert g.translate("{}", datetime.date(2025, 2, 15), locale="no") == "februar 2025"
        assert g.translate("{}", datetime.date(2025, 3, 15), locale="no") == "mars 2025"
        assert g.translate("{}", datetime.date(2025, 12, 15), locale="no") == "desember 2025"

    def test_date_formatting_short_month_names(self):
        """Test date formatting with short month names"""
        import datetime
        g = Gloser()
        g.add_translations("no", {
            ".date": {
                "other": "{DD} {mnm} {YYYY}"
            },
            ".month": {
                "short": {
                    "10": "okt"
                }
            }
        })

        date = datetime.date(2025, 10, 13)
        assert g.translate("{}", date, locale="no") == "13 okt 2025"

    def test_date_formatting_short_weekday_names(self):
        """Test date formatting with short weekday names"""
        import datetime
        g = Gloser()
        g.add_translations("no", {
            ".date": {
                "other": "{dnm} {DD}.{MM}.{YYYY}"
            },
            ".dayofweek": {
                "short": {
                    "1": "man"
                }
            }
        })

        date = datetime.date(2025, 10, 13)  # Monday
        assert g.translate("{}", date, locale="no") == "man 13.10.2025"

    def test_date_formatting_capitalization(self):
        """Test date formatting with capitalization"""
        import datetime
        g = Gloser()
        g.add_translations("no", {
            ".date": {
                "full": "{dayname}, {DD}. {monthname} {YYYY}",
                "other": "{DD}.{MM}.{YYYY}"
            },
            ".dayofweek": {
                "full": {
                    "1": "mandag"
                }
            },
            ".month": {
                "full": {
                    "10": "oktober"
                }
            }
        })

        date = datetime.date(2025, 10, 13)  # Monday

        # Normal case
        assert g.translate("{:full}", date, locale="no") == "mandag, 13. oktober 2025"

        # Capitalized
        assert g.translate("{:Full}", date, locale="no") == "Mandag, 13. oktober 2025"

    def test_date_formatting_named_styles(self):
        """Test different named date format styles"""
        import datetime
        g = Gloser()
        g.add_translations("no", {
            ".date": {
                "short": "{DD}.{MM}.{YY}",
                "long": "{DD}. {monthname} {YYYY}",
                "full": "{dayname}, {DD}. {monthname} {YYYY}",
                "other": "{DD}.{MM}.{YYYY}"
            },
            ".month": {
                "full": {
                    "10": "oktober"
                }
            },
            ".dayofweek": {
                "full": {
                    "1": "mandag"
                }
            }
        })

        date = datetime.date(2025, 10, 13)

        assert g.translate("{:short}", date, locale="no") == "13.10.25"
        assert g.translate("{:long}", date, locale="no") == "13. oktober 2025"
        assert g.translate("{:full}", date, locale="no") == "mandag, 13. oktober 2025"
        assert g.translate("{}", date, locale="no") == "13.10.2025"

    def test_datetime_formatting(self):
        """Test formatting datetime objects (not just dates)"""
        import datetime
        g = Gloser(load_defaults=False)
        g.add_translations("no", {
            ".date": {
                "other": "{DD}.{MM}.{YYYY} {hh}:{mm}"
            }
        })

        dt = datetime.datetime(2025, 10, 13, 14, 30, 0)
        assert g.translate("{}", dt, locale="no") == "13.10.2025 14:30"

    def test_date_formatting_in_translation_string(self):
        """Test date formatting within a translation string"""
        import datetime
        g = Gloser()
        g.add_translations("no", {
            "event": "Arrangementet er {date:long}",
            ".date": {
                "long": "{DD}. {monthname} {YYYY}",
                "other": "{DD}.{MM}.{YYYY}"
            },
            ".month": {
                "full": {
                    "10": "oktober"
                }
            }
        })

        date = datetime.date(2025, 10, 13)
        assert g.translate("event", date=date, locale="no") == "Arrangementet er 13. oktober 2025"

    def test_date_formatting_fallback_to_default_locale(self):
        """Test that date formatting falls back to default locale"""
        import datetime
        g = Gloser(default_locale="no")
        g.add_translations("no", {
            "date-msg": "Dato: {}",
            ".date": {
                "other": "{DD}.{MM}.{YYYY}"
            },
            ".month": {
                "full": {
                    "10": "oktober"
                }
            }
        })

        date = datetime.date(2025, 10, 13)

        # Request Swedish locale (doesn't exist), should fall back to Norwegian
        result = g.translate("date-msg", date, locale="sv")
        assert result == "Dato: 13.10.2025"

    def test_date_formatting_missing_format(self):
        """Test date formatting when format style doesn't exist"""
        import datetime
        g = Gloser()
        g.add_translations("no", {
            ".date": {
                "short": "{DD}.{MM}.{YY}",
                "other": "{DD}.{MM}.{YYYY}"
            }
        })

        date = datetime.date(2025, 10, 13)

        # Request non-existent style, should fall back to default
        assert g.translate("{:custom}", date, locale="no") == "13.10.2025"

    def test_date_formatting_string_format(self):
        """Test when .date is a simple string (not dict)"""
        import datetime
        g = Gloser()
        g.add_translations("de", {
            ".date": "{DD}.{MM}.{YYYY}"  # Simple string, not dict
        })

        date = datetime.date(2025, 10, 13)

        # Should work for all styles
        assert g.translate("{}", date, locale="de") == "13.10.2025"
        assert g.translate("{:short}", date, locale="de") == "13.10.2025"
        assert g.translate("{:long}", date, locale="de") == "13.10.2025"

    def test_locale_gloser_date_formatting(self):
        """Test date formatting with LocaleGloser"""
        import datetime
        g = Gloser()
        g.add_translations("no", {
            "today": "I dag er det {}",
            ".date": {
                "other": "{DD}.{MM}.{YYYY}"
            }
        })

        t = g["no"]
        date = datetime.date(2025, 10, 13)
        assert t("today", date) == "I dag er det 13.10.2025"

    def test_mixed_date_and_number_formatting(self):
        """Test formatting both dates and numbers in same string"""
        import datetime
        g = Gloser()
        g.add_translations("no", {
            "invoice": "Faktura {num} datert {date} - beløp: {amount:,.2f} kr",
            ".date": {
                "other": "{DD}.{MM}.{YYYY}"
            },
            ".number": {
                ".decimal-separator": ",",
                ".thousand-separator": "."
            }
        })

        date = datetime.date(2025, 10, 13)
        result = g.translate("invoice", num=1234, date=date, amount=9999.99, locale="no")
        assert result == "Faktura 1234 datert 13.10.2025 - beløp: 9.999,99 kr"

    def test_date_formatting_all_weekdays(self):
        """Test formatting with all weekdays localized"""
        import datetime
        g = Gloser()
        g.add_translations("no", {
            ".date": {
                "other": "{dayname}"
            },
            ".dayofweek": {
                "full": {
                    "1": "mandag",
                    "2": "tirsdag",
                    "3": "onsdag",
                    "4": "torsdag",
                    "5": "fredag",
                    "6": "lørdag",
                    "7": "søndag"
                }
            }
        })

        # 2025-10-13 is Monday, then increment to test all days
        dates = [datetime.date(2025, 10, 13 + i) for i in range(7)]
        expected = ["mandag", "tirsdag", "onsdag", "torsdag", "fredag", "lørdag", "søndag"]

        for date, expected_day in zip(dates, expected):
            assert g.translate("{}", date, locale="no") == expected_day

    def test_date_formatting_on_missing_key(self):
        """Test date formatting when translation key is not found"""
        import datetime
        g = Gloser()
        g.add_translations("no", {
            ".date": {
                "other": "{DD}.{MM}.{YYYY}"
            }
        })

        date = datetime.date(2025, 10, 13)

        # Key doesn't exist, but date formatting should still work
        assert g.translate("Date: {}", date, locale="no") == "Date: 13.10.2025"

    def test_date_formatting_no_configuration(self):
        """Test date formatting when no date configuration exists"""
        import datetime
        g = Gloser(load_defaults=False)
        g.add_translations("en", {
            "message": "Today is {}"
        })

        date = datetime.date(2025, 10, 13)

        # Should use default ISO format when no defaults loaded
        assert g.translate("message", date, locale="en") == "Today is 2025-10-13"


    def test_date_name_substitution(self):
        import datetime
        import locale
        current_locale = locale.getlocale(locale.LC_ALL)
        try:
            locale.setlocale(locale.LC_ALL , 'de_DE')
            g = Gloser()
            g.add_translations("no", {
                ".date": {
                    "other": "{dayname}"
                },
                ".dayofweek": {
                    "full": {
                        "1": "mandag"
                    }
                },
                "test": "Jeg heter Monday, i dag er det {date}"
            })

            date = datetime.date(2025, 10, 13)  # This is a Monday
            assert g.translate("test", date=date, locale="no") == "Jeg heter Monday, i dag er det mandag"
        finally:
            locale.setlocale(locale.LC_ALL, current_locale)


class TestTimeAndDateTimeFormatting:
    """Test separate time and datetime formatting configurations"""

    def test_time_formatting_basic(self):
        """Test basic time formatting with time objects"""
        import datetime
        g = Gloser()
        g.add_translations("no", {
            ".time": {
                "short": "{hh}:{mm}",
                "long": "{hh}:{mm}:{ss}",
                "other": "{hh}:{mm}"
            }
        })

        time = datetime.time(14, 30, 45)

        # Default format
        assert g.translate("{}", time, locale="no") == "14:30"

        # Short format
        assert g.translate("{:short}", time, locale="no") == "14:30"

        # Long format
        assert g.translate("{:long}", time, locale="no") == "14:30:45"

    def test_datetime_uses_datetime_format(self):
        """Test that datetime objects use datetime-specific format when available"""
        import datetime
        g = Gloser()
        g.add_translations("no", {
            ".date": "%d.%m.%Y",
            ".datetime": {
                "short": "{DD}.{MM}.{YY} {hh}:{mm}",
                "long": "{DD}. {monthname} {YYYY} kl. {hh}:{mm}:{ss}",
                "other": "{DD}.{MM}.{YYYY} kl. {hh}:{mm}"
            },
            ".month": {
                "full": {
                    "10": "oktober"
                }
            }
        })

        dt = datetime.datetime(2025, 10, 13, 14, 30, 45)

        # Should use datetime, not date
        assert g.translate("{}", dt, locale="no") == "13.10.2025 kl. 14:30"
        assert g.translate("{:short}", dt, locale="no") == "13.10.25 14:30"
        assert g.translate("{:long}", dt, locale="no") == "13. oktober 2025 kl. 14:30:45"

    def test_datetime_fallback_to_date_format(self):
        """Test that datetime falls back to date format when datetime format not specified"""
        import datetime
        g = Gloser(load_defaults=False)
        g.add_translations("no", {
            ".date": "{DD}.{MM}.{YYYY}"
            # No .datetime specified
        })

        dt = datetime.datetime(2025, 10, 13, 14, 30, 0)

        # Should fallback to date format (ignoring time)
        assert g.translate("{}", dt, locale="no") == "13.10.2025"

    def test_time_format_with_period(self):
        """Test time formatting with AM/PM"""
        import datetime
        g = Gloser()
        g.add_translations("en", {
            ".time": {
                "short": "{hh}:{mm}",
                "with-period": "{HH}:{mm} {AMPM}",
                "other": "{hh}:{mm}"
            }
        })

        time = datetime.time(14, 30)

        assert g.translate("{:short}", time, locale="en") == "14:30"
        assert g.translate("{:with-period}", time, locale="en") == "02:30 PM"

    def test_mixed_date_time_and_number_formatting(self):
        """Test combining date, time, and number formatting"""
        import datetime
        g = Gloser()
        g.add_translations("no", {
            "appointment": "Møte {date:short} kl. {time:short} - varighet: {duration:.1f} timer",
            ".date": {
                "short": "{DD}.{MM}",
                "other": "{DD}.{MM}.{YYYY}"
            },
            ".month": {
                "full": {
                    "10": "oktober"
                }
            },
            ".time": {
                "short": "{hh}:{mm}",
                "other": "{hh}:{mm}"
            },
            ".number": {
                ".decimal-separator": ",",
                ".thousand-separator": "."
            }
        })

        date = datetime.date(2025, 10, 13)
        time = datetime.time(14, 30)
        duration = 2.5

        result = g.translate("appointment", date=date, time=time, duration=duration, locale="no")
        assert result == "Møte 13.10 kl. 14:30 - varighet: 2,5 timer"

    def test_datetime_with_date_time_formats_only(self):
        """Test datetime when only date and time formats exist (no datetime)"""
        import datetime
        g = Gloser(load_defaults=False)
        g.add_translations("no", {
            ".date": {
                "other": "{DD}.{MM}.{YYYY}"
            },
            ".time": {
                "other": "{hh}:{mm}"
            }
            # No datetime format - should fallback to date format
        })

        dt = datetime.datetime(2025, 10, 13, 14, 30)

        # Fallback to date format
        assert g.translate("{}", dt, locale="no") == "13.10.2025"

    def test_time_in_translation_string(self):
        """Test time formatting within a translation string"""
        import datetime
        g = Gloser()
        g.add_translations("no", {
            "meeting": "Møtet starter {time:short}",
            ".time": {
                "short": "kl. {hh}:{mm}",
                "other": "{hh}:{mm}"
            }
        })

        time = datetime.time(14, 30)
        assert g.translate("meeting", time=time, locale="no") == "Møtet starter kl. 14:30"

    def test_separate_date_and_time_in_same_string(self):
        """Test using separate date and time placeholders"""
        import datetime
        g = Gloser()
        g.add_translations("no", {
            "event": "Arrangement: {date:long} kl. {time}",
            ".date": {
                "long": "{DD}. {monthname} {YYYY}",
                "other": "{DD}.{MM}.{YYYY}"
            },
            ".time": {
                "other": "{hh}:{mm}"
            },
            ".month": {
                "full": {
                    "10": "oktober"
                }
            }
        })

        date = datetime.date(2025, 10, 13)
        time = datetime.time(14, 30)

        result = g.translate("event", date=date, time=time, locale="no")
        assert result == "Arrangement: 13. oktober 2025 kl. 14:30"

    def test_datetime_format_string_simple(self):
        """Test when datetime is a simple string (not dict)"""
        import datetime
        g = Gloser(load_defaults=False)
        g.add_translations("no", {
            ".datetime": "{DD}.{MM}.{YYYY} {hh}:{mm}"  # Simple string
        })

        dt = datetime.datetime(2025, 10, 13, 14, 30)

        assert g.translate("{}", dt, locale="no") == "13.10.2025 14:30"
        assert g.translate("{:short}", dt, locale="no") == "13.10.2025 14:30"
        assert g.translate("{:long}", dt, locale="no") == "13.10.2025 14:30"


class TestPlurals:
    """Test plural form selection and formatting"""

    def test_basic_plural_selection_english(self):
        """Test basic one vs other plural selection"""
        g = Gloser()
        g.add_translations("en", {
            ".plurals": {
                "one": "^1$",
            },
            "files": {
                "one": "One file",
                "other": "{count} files"
            }
        })

        assert g.translate("files", count=1, locale="en") == "One file"
        assert g.translate("files", count=0, locale="en") == "0 files"
        assert g.translate("files", count=2, locale="en") == "2 files"
        assert g.translate("files", count=100, locale="en") == "100 files"

    def test_custom_plural_rules(self):
        """Test custom plural rules with few and many"""
        g = Gloser()
        g.add_translations("no", {
            ".plurals": {
                "one": "^1$",
                "few": "^[2-7]$",
                "many": "^[89]$|^[1-9]\\d+$",
            },
            "items": {
                "one": "én ting",
                "few": "noen få ting",
                "many": "mange ting",
                "other": "ingen ting"
            }
        })

        assert g.translate("items", count=0, locale="no") == "ingen ting"
        assert g.translate("items", count=1, locale="no") == "én ting"
        assert g.translate("items", count=3, locale="no") == "noen få ting"
        assert g.translate("items", count=7, locale="no") == "noen få ting"
        assert g.translate("items", count=8, locale="no") == "mange ting"
        assert g.translate("items", count=10, locale="no") == "mange ting"
        assert g.translate("items", count=1000, locale="no") == "mange ting"

    def test_count_kwarg_vs_positional(self):
        """Test count can be provided as kwarg or first positional arg"""
        g = Gloser()
        g.add_translations("en", {
            ".plurals": {
                "one": "^1$",
            },
            "dogs": {
                "one": "one dog",
                "other": "{count} dogs"
            }
        })

        # Using count kwarg
        assert g.translate("dogs", count=1, locale="en") == "one dog"
        assert g.translate("dogs", count=5, locale="en") == "5 dogs"

        # Using first positional arg
        assert g.translate("dogs", 1, locale="en") == "one dog"
        assert g.translate("dogs", 5, locale="en") == "5 dogs"

        # Count kwarg takes precedence over positional
        assert g.translate("dogs", 99, count=1, locale="en") == "one dog"

    def test_count_in_format_string(self):
        """Test count is available for formatting even if not explicitly passed to format"""
        g = Gloser()
        g.add_translations("en", {
            ".plurals": {
                "one": "^1$",
            },
            "results": {
                "one": "Found {count} result",
                "other": "Found {count} results"
            }
        })

        assert g.translate("results", count=1, locale="en") == "Found 1 result"
        assert g.translate("results", count=42, locale="en") == "Found 42 results"

        # Count from positional arg
        assert g.translate("results", 1, locale="en") == "Found 1 result"
        assert g.translate("results", 42, locale="en") == "Found 42 results"

    def test_count_not_in_format_string(self):
        """Test plural forms work when count is not mentioned in the string"""
        g = Gloser()
        g.add_translations("en", {
            ".plurals": {
                "one": "^1$",
            },
            "status": {
                "one": "Processing one item",
                "other": "Processing multiple items"
            }
        })

        assert g.translate("status", count=1, locale="en") == "Processing one item"
        assert g.translate("status", count=5, locale="en") == "Processing multiple items"

    def test_missing_count_uses_default(self):
        """Test that missing count uses 'other' form"""
        g = Gloser()
        g.add_translations("en", {
            ".plurals": {
                "one": "^1$",
            },
            "message": {
                "one": "singular",
                "other": "plural or unknown"
            }
        })

        # No count provided
        assert g.translate("message", locale="en") == "plural or unknown"

    def test_zero_category(self):
        """Test special zero category"""
        g = Gloser()
        g.add_translations("en", {
            ".plurals": {
                "zero": "^0$",
                "one": "^1$",
            },
            "items": {
                "zero": "No items",
                "one": "One item",
                "other": "{count} items"
            }
        })

        assert g.translate("items", count=0, locale="en") == "No items"
        assert g.translate("items", count=1, locale="en") == "One item"
        assert g.translate("items", count=5, locale="en") == "5 items"

    def test_two_category(self):
        """Test special two category"""
        g = Gloser()
        g.add_translations("en", {
            ".plurals": {
                "one": "^1$",
                "two": "^2$",
            },
            "apples": {
                "one": "an apple",
                "two": "a pair of apples",
                "other": "{count} apples"
            }
        })

        assert g.translate("apples", count=1, locale="en") == "an apple"
        assert g.translate("apples", count=2, locale="en") == "a pair of apples"
        assert g.translate("apples", count=10, locale="en") == "10 apples"

    def test_complex_regex_patterns(self):
        """Test complex regex patterns for plural rules"""
        g = Gloser()
        g.add_translations("pl", {
            ".plurals": {
                "one": "^1$",
                "few": "^[2-4]$|^[2-4]\\d*[2-4]$",  # 2-4, 22-24, 32-34, etc
            },
            "books": {
                "one": "{count} książka",
                "few": "{count} książki",
                "other": "{count} książek"
            }
        })

        assert g.translate("books", count=1, locale="pl") == "1 książka"
        assert g.translate("books", count=2, locale="pl") == "2 książki"
        assert g.translate("books", count=4, locale="pl") == "4 książki"
        assert g.translate("books", count=5, locale="pl") == "5 książek"
        assert g.translate("books", count=22, locale="pl") == "22 książki"
        assert g.translate("books", count=25, locale="pl") == "25 książek"

    def test_multiple_locales_different_rules(self):
        """Test different plural rules for different locales"""
        g = Gloser()

        # English: one, other
        g.add_translations("en", {
            ".plurals": {
                "one": "^1$",
            },
            "cats": {
                "one": "one cat",
                "other": "{count} cats"
            }
        })

        # Norwegian with custom few category
        g.add_translations("no", {
            ".plurals": {
                "one": "^1$",
                "few": "^[2-5]$",
            },
            "cats": {
                "one": "én katt",
                "few": "noen katter",
                "other": "{count} katter"
            }
        })

        # English
        assert g.translate("cats", count=1, locale="en") == "one cat"
        assert g.translate("cats", count=3, locale="en") == "3 cats"
        assert g.translate("cats", count=10, locale="en") == "10 cats"

        # Norwegian
        assert g.translate("cats", count=1, locale="no") == "én katt"
        assert g.translate("cats", count=3, locale="no") == "noen katter"
        assert g.translate("cats", count=10, locale="no") == "10 katter"

    def test_fallback_locale_with_plurals(self):
        """Test fallback to default locale when translation missing"""
        g = Gloser(default_locale="en")
        g.add_translations("en", {
            ".plurals": {
                "one": "^1$",
            },
            "users": {
                "one": "one user",
                "other": "{count} users"
            }
        })

        # Request translation in Spanish (not defined), should fallback to English
        assert g.translate("users", count=1, locale="es") == "one user"
        assert g.translate("users", count=5, locale="es") == "5 users"

    def test_plural_with_number_formatting(self):
        """Test plurals work with number formatting"""
        g = Gloser()
        g.add_translations("en", {
            ".plurals": {
                "one": "^1$",
            },
            ".number.format": {
                "decimal": ".",
                "thousand": ","
            },
            "downloads": {
                "one": "{count:,} download",
                "other": "{count:,} downloads"
            }
        })

        assert g.translate("downloads", count=1, locale="en") == "1 download"
        assert g.translate("downloads", count=1000, locale="en") == "1,000 downloads"
        assert g.translate("downloads", count=1000000, locale="en") == "1,000,000 downloads"

    def test_plural_with_additional_parameters(self):
        """Test plurals work with additional format parameters"""
        g = Gloser()
        g.add_translations("en", {
            ".plurals": {
                "one": "^1$",
            },
            "notification": {
                "one": "{user} sent you {count} message",
                "other": "{user} sent you {count} messages"
            }
        })

        assert g.translate("notification", count=1, user="Alice", locale="en") == "Alice sent you 1 message"
        assert g.translate("notification", count=5, user="Bob", locale="en") == "Bob sent you 5 messages"

    def test_negative_count(self):
        """Test negative count values"""
        g = Gloser()
        g.add_translations("en", {
            ".plurals": {
                "one": "^1$",
            },
            "balance": {
                "one": "{count} dollar",
                "other": "{count} dollars"
            }
        })

        assert g.translate("balance", count=-1, locale="en") == "-1 dollars"
        assert g.translate("balance", count=-5, locale="en") == "-5 dollars"

    def test_missing_plural_rules_uses_default(self):
        """Test that missing .plurals key uses default English rules"""
        g = Gloser()
        g.add_translations("en", {
            # No .plurals key defined
            "items": {
                "one": "one item",
                "other": "{count} items"
            }
        })

        # Should use default rules: one = "^1$", other = ".*"
        assert g.translate("items", count=1, locale="en") == "one item"
        assert g.translate("items", count=0, locale="en") == "0 items"
        assert g.translate("items", count=5, locale="en") == "5 items"

    def test_missing_default_category(self):
        """Test that missing 'other' category is automatically added"""
        g = Gloser()
        g.add_translations("en", {
            ".plurals": {
                "one": "^1$"
                # No 'other' defined
            },
            "things": {
                "one": "one thing",
                "other": "{count} things"
            }
        })

        # Should work even without explicit 'other' in .plurals
        assert g.translate("things", count=1, locale="en") == "one thing"
        assert g.translate("things", count=5, locale="en") == "5 things"

    def test_non_numeric_count(self):
        """Test string representation of count values"""
        g = Gloser()
        g.add_translations("en", {
            ".plurals": {
                "one": "^1$",
            },
            "items": {
                "one": "one item",
                "other": "{count} items"
            }
        })

        # Count is converted to string for regex matching
        assert g.translate("items", count="1", locale="en") == "one item"
        assert g.translate("items", count="5", locale="en") == "5 items"

    def test_default_alternative_count_kwarg(self):
        """Test that the default alternative count kwarg is used"""
        g = Gloser()
        g.add_translations("en", {
            ".plurals": {
                "one": "^1$",
            },
            "items": {
                "one": "one item",
                "other": "{items} items"
            }
        })

        assert g.translate("items", items=1, locale="en") == "one item"
        assert g.translate("items", items=5, locale="en") == "5 items"

    def test_ordinals_and_cardinals(self):
        """Test that ordinals and cardinals work together"""
        g = Gloser()
        g.add_translations("en", {
            ".plurals": {
                "one": "^1$",
                # Ordinal patterns: ends with 1/2/3 but not 11/12/13
                "first": "^(?!11$).*1$",   # Ends with 1, excluding 11
                "second": "^(?!12$).*2$",  # Ends with 2, excluding 12
                "third": "^(?!13$).*3$",   # Ends with 3, excluding 13
            },
            "place": {
                "first": "{position}st place",
                "second": "{position}nd place",
                "third": "{position}rd place",
                "other": "{position}th place"
            },
            "elements": {
                "one": "one element",
                "other": "{count} elements"
            }
        })
        assert g.translate("place", position=1, locale="en") == "1st place"
        assert g.translate("place", position=2, locale="en") == "2nd place"
        assert g.translate("place", position=3, locale="en") == "3rd place"
        assert g.translate("place", position=11, locale="en") == "11th place"
        assert g.translate("place", position=12, locale="en") == "12th place"
        assert g.translate("place", position=13, locale="en") == "13th place"
        assert g.translate("place", position=21, locale="en") == "21st place"
        assert g.translate("place", position=22, locale="en") == "22nd place"
        assert g.translate("place", position=23, locale="en") == "23rd place"
        assert g.translate("elements", count=1, locale="en") == "one element"
        assert g.translate("elements", count=5, locale="en") == "5 elements"

    def test_array_style_lookups(self):
        """Test array-style lookups with numeric keys (direct key matching)"""
        g = Gloser()
        g.add_translations("no", {
            "planet": {
                1: "Merkur",
                2: "Venus",
                3: "Jorda",
                4: "Mars",
                5: "Jupiter",
                6: "Saturn",
                7: "Uranus",
                8: "Neptun"
            },
            "weekday_name": {
                1: "mandag",
                2: "tirsdag",
                3: "onsdag",
                4: "torsdag",
                5: "fredag",
                6: "lørdag",
                7: "søndag"
            }
        })

        # Test direct numeric key lookups
        assert g.translate("planet", 1, locale="no") == "Merkur"
        assert g.translate("planet", 2, locale="no") == "Venus"
        assert g.translate("planet", 3, locale="no") == "Jorda"
        assert g.translate("planet", 8, locale="no") == "Neptun"

        # Test with keyword argument
        assert g.translate("planet", count=4, locale="no") == "Mars"
        assert g.translate("planet", count=5, locale="no") == "Jupiter"

        # Test weekday names
        assert g.translate("weekday_name", 1, locale="no") == "mandag"
        assert g.translate("weekday_name", 7, locale="no") == "søndag"

    def test_array_style_with_string_keys(self):
        """Test array-style lookups with string keys"""
        g = Gloser()
        g.add_translations("en", {
            "grade": {
                "A": "Excellent",
                "B": "Good",
                "C": "Satisfactory",
                "D": "Poor",
                "F": "Fail"
            }
        })

        assert g.translate("grade", "A", locale="en") == "Excellent"
        assert g.translate("grade", "B", locale="en") == "Good"
        assert g.translate("grade", "F", locale="en") == "Fail"

    def test_array_style_fallback_to_other(self):
        """Test array-style lookups fall back to 'other' when key not found"""
        g = Gloser()
        g.add_translations("no", {
            "planet": {
                1: "Merkur",
                2: "Venus",
                3: "Jorda",
                "other": "Ukjent planet"
            }
        })

        # Known planets
        assert g.translate("planet", 1, locale="no") == "Merkur"
        assert g.translate("planet", 2, locale="no") == "Venus"

        # Unknown planet number - should fall back to "other"
        assert g.translate("planet", 9, locale="no") == "Ukjent planet"
        assert g.translate("planet", 100, locale="no") == "Ukjent planet"

    def test_array_style_mixed_with_plurals(self):
        """Test that array-style and plural rules can coexist"""
        g = Gloser()
        g.add_translations("en", {
            ".plurals": {
                "one": "^1$"
            },
            "month": {
                1: "January",
                2: "February",
                3: "March",
                4: "April",
                5: "May",
                6: "June",
                7: "July",
                8: "August",
                9: "September",
                10: "October",
                11: "November",
                12: "December"
            },
            "item": {
                "one": "{count} item",
                "other": "{count} items"
            }
        })

        # Array-style lookups (exact matches)
        assert g.translate("month", 1, locale="en") == "January"
        assert g.translate("month", 12, locale="en") == "December"

        # Plural rules still work
        assert g.translate("item", count=1, locale="en") == "1 item"
        assert g.translate("item", count=5, locale="en") == "5 items"


class TestLocaleDefaults():
    """Test locale defaults"""

    def test_custom_plural_rules(self):
        """Test that custom plural rules work in combination with default rules"""
        g = Gloser()
        g.add_translations("en", {
            ".plurals": {
                "few": "^[2-7]$", # Custom plural rule
            },
            "items": {
                "one": "one item",
                "few": "few items",
                "other": "{count} items"
            }
        })
        assert g.translate("items", count=1, locale="en") == "one item"
        assert g.translate("items", count=5, locale="en") == "few items"

    def test_temp(self):
        g = Gloser()
        g.add_translations("no", {
            ".plurals": {
                "0": "^0$",
                "1": "^1$"
            },
            "days": {
                "0": "False",
                "1": "True"
            }
        })
        assert g.translate("days", 0, locale="no") == "False"
        assert g.translate("days", 1, locale="no") == "True"
