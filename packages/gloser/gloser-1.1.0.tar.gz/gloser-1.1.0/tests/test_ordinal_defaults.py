"""Test ordinal rules for locale defaults"""
import pytest
from gloser import Gloser


class TestEnglishOrdinals:
    """Test English ordinal patterns (1st, 2nd, 3rd, 4th, etc.)"""

    def test_english_basic_ordinals(self):
        """Test English 1st, 2nd, 3rd ordinals"""
        g = Gloser(default_locale="en")
        g.add_translations("en", {
            "place": {
                "first": "{count}st place",
                "second": "{count}nd place",
                "third": "{count}rd place",
                "other": "{count}th place"
            }
        })

        # Special cases: 1st, 2nd, 3rd
        assert g.translate("place", count=1, locale="en") == "1st place"
        assert g.translate("place", count=2, locale="en") == "2nd place"
        assert g.translate("place", count=3, locale="en") == "3rd place"

        # Regular: 4th-10th
        assert g.translate("place", count=4, locale="en") == "4th place"
        assert g.translate("place", count=5, locale="en") == "5th place"
        assert g.translate("place", count=10, locale="en") == "10th place"

    def test_english_teen_ordinals(self):
        """Test English teen ordinals (11th, 12th, 13th) - all use 'th'"""
        g = Gloser(default_locale="en")
        g.add_translations("en", {
            "place": {
                "first": "{count}st place",
                "second": "{count}nd place",
                "third": "{count}rd place",
                "other": "{count}th place"
            }
        })

        # Teens are exceptions: 11th, 12th, 13th (not 11st, 12nd, 13rd)
        assert g.translate("place", count=11, locale="en") == "11th place"
        assert g.translate("place", count=12, locale="en") == "12th place"
        assert g.translate("place", count=13, locale="en") == "13th place"
        assert g.translate("place", count=14, locale="en") == "14th place"

    def test_english_twenties_ordinals(self):
        """Test English ordinals in twenties (21st, 22nd, 23rd, 24th...)"""
        g = Gloser(default_locale="en")
        g.add_translations("en", {
            "place": {
                "first": "{count}st place",
                "second": "{count}nd place",
                "third": "{count}rd place",
                "other": "{count}th place"
            }
        })

        # Pattern repeats: 21st, 22nd, 23rd, 24th...
        assert g.translate("place", count=21, locale="en") == "21st place"
        assert g.translate("place", count=22, locale="en") == "22nd place"
        assert g.translate("place", count=23, locale="en") == "23rd place"
        assert g.translate("place", count=24, locale="en") == "24th place"

        # 31st, 32nd, 33rd...
        assert g.translate("place", count=31, locale="en") == "31st place"
        assert g.translate("place", count=32, locale="en") == "32nd place"
        assert g.translate("place", count=33, locale="en") == "33rd place"

        # 101st, 102nd, 103rd...
        assert g.translate("place", count=101, locale="en") == "101st place"
        assert g.translate("place", count=102, locale="en") == "102nd place"
        assert g.translate("place", count=103, locale="en") == "103rd place"

    def test_english_mixed_ordinals_and_cardinals(self):
        """Test using both ordinals and cardinals with same plural rules"""
        g = Gloser(default_locale="en")
        g.add_translations("en", {
            "items": {
                "one": "one item",
                "other": "{count} items"
            },
            "place": {
                "first": "{count}st place",
                "second": "{count}nd place",
                "third": "{count}rd place",
                "other": "{count}th place"
            }
        })

        # Cardinals use 'one'
        assert g.translate("items", count=1, locale="en") == "one item"
        assert g.translate("items", count=2, locale="en") == "2 items"

        # Ordinals use 'first', 'second', 'third'
        assert g.translate("place", count=1, locale="en") == "1st place"
        assert g.translate("place", count=2, locale="en") == "2nd place"
        assert g.translate("place", count=3, locale="en") == "3rd place"


class TestUniformOrdinals:
    """Test languages with uniform ordinal patterns (just add '.')"""

    def test_norwegian_uniform_ordinals(self):
        """Test Norwegian uniform ordinals (1., 2., 3., ...)"""
        g = Gloser(default_locale="no")
        g.add_translations("no", {
            "plass": {
                "other": "{count}. plass"
            }
        })

        # All use same pattern with '.'
        assert g.translate("plass", count=1, locale="no") == "1. plass"
        assert g.translate("plass", count=2, locale="no") == "2. plass"
        assert g.translate("plass", count=3, locale="no") == "3. plass"
        assert g.translate("plass", count=11, locale="no") == "11. plass"
        assert g.translate("plass", count=21, locale="no") == "21. plass"

    def test_german_uniform_ordinals(self):
        """Test German uniform ordinals (1., 2., 3., ...)"""
        g = Gloser(default_locale="de")
        g.add_translations("de", {
            "platz": {
                "other": "{count}. Platz"
            }
        })

        # All use same pattern with '.'
        assert g.translate("platz", count=1, locale="de") == "1. Platz"
        assert g.translate("platz", count=2, locale="de") == "2. Platz"
        assert g.translate("platz", count=3, locale="de") == "3. Platz"
        assert g.translate("platz", count=11, locale="de") == "11. Platz"

    def test_spanish_ordinals_with_first(self):
        """Test Spanish ordinals - 'first' allows different text for 1"""
        g = Gloser(default_locale="es")
        g.add_translations("es", {
            "lugar": {
                "first": "primer lugar",  # Can spell out "primer" for emphasis
                "other": "{count}.º lugar"
            }
        })

        # User can provide different text for 1 (e.g., spelled out)
        assert g.translate("lugar", count=1, locale="es") == "primer lugar"
        # All others use numeric ordinal
        assert g.translate("lugar", count=2, locale="es") == "2.º lugar"
        assert g.translate("lugar", count=3, locale="es") == "3.º lugar"
        assert g.translate("lugar", count=11, locale="es") == "11.º lugar"

    def test_french_ordinals_with_first(self):
        """Test French ordinals - 1er vs 2e, 3e, etc."""
        g = Gloser(default_locale="fr")
        g.add_translations("fr", {
            "place": {
                "first": "{count}er place",  # 1er uses 'er'
                "other": "{count}e place"  # All others use 'e'
            }
        })

        # 1er is different (premier/première)
        assert g.translate("place", count=1, locale="fr") == "1er place"
        # All others use 'e'
        assert g.translate("place", count=2, locale="fr") == "2e place"
        assert g.translate("place", count=3, locale="fr") == "3e place"
        assert g.translate("place", count=21, locale="fr") == "21e place"

    def test_italian_ordinals_with_first(self):
        """Test Italian ordinals - can spell out 'primo' vs numeric for others"""
        g = Gloser(default_locale="it")
        g.add_translations("it", {
            "posto": {
                "first": "primo posto",   # Can spell out "primo/prima"
                "other": "{count}º posto"
            }
        })

        # User can spell out "primo" for 1
        assert g.translate("posto", count=1, locale="it") == "primo posto"
        # All others use numeric ordinal
        assert g.translate("posto", count=2, locale="it") == "2º posto"
        assert g.translate("posto", count=3, locale="it") == "3º posto"

    def test_portuguese_ordinals_with_first(self):
        """Test Portuguese ordinals - can spell out 'primeiro' vs numeric"""
        g = Gloser(default_locale="pt")
        g.add_translations("pt", {
            "lugar": {
                "first": "primeiro lugar",  # Can spell out "primeiro/primeira"
                "other": "{count}.º lugar"
            }
        })

        # User can spell out "primeiro" for 1
        assert g.translate("lugar", count=1, locale="pt") == "primeiro lugar"
        # All others use numeric ordinal
        assert g.translate("lugar", count=2, locale="pt") == "2.º lugar"
        assert g.translate("lugar", count=3, locale="pt") == "3.º lugar"


class TestOrdinalsWithCardinals:
    """Test that ordinals and cardinals can coexist"""

    def test_english_date_ordinals(self):
        """Test using ordinals for dates in English"""
        g = Gloser(default_locale="en")
        g.add_translations("en", {
            "birthday": {
                "one": "You have {count} birthday this year",
                "other": "You have {count} birthdays this year"
            },
            "date_suffix": {
                "first": "{count}st",
                "second": "{count}nd",
                "third": "{count}rd",
                "other": "{count}th"
            }
        })

        # Cardinals for counting
        assert g.translate("birthday", count=1, locale="en") == "You have 1 birthday this year"
        assert g.translate("birthday", count=2, locale="en") == "You have 2 birthdays this year"

        # Ordinals for dates
        assert g.translate("date_suffix", count=1, locale="en") == "1st"
        assert g.translate("date_suffix", count=2, locale="en") == "2nd"
        assert g.translate("date_suffix", count=3, locale="en") == "3rd"
        assert g.translate("date_suffix", count=21, locale="en") == "21st"

    def test_mixed_usage_same_number(self):
        """Test using same number for both cardinal and ordinal"""
        g = Gloser(default_locale="en")
        g.add_translations("en", {
            "items": {
                "one": "one item",
                "other": "{count} items"
            },
            "position": {
                "first": "{count}st position",
                "second": "{count}nd position",
                "third": "{count}rd position",
                "other": "{count}th position"
            }
        })

        # Same count value, different meanings
        count_val = 1
        assert g.translate("items", count=count_val, locale="en") == "one item"
        assert g.translate("position", count=count_val, locale="en") == "1st position"

        count_val = 3
        assert g.translate("items", count=count_val, locale="en") == "3 items"
        assert g.translate("position", count=count_val, locale="en") == "3rd position"
