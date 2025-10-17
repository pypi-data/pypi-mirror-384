"""Test plural rules for all locale defaults with non-trivial pluralization"""
import pytest
from gloser import Gloser


class TestSlavicPlurals:
    """Test Slavic languages with complex plural rules"""

    def test_polish_plurals(self):
        """Test Polish one/few/many plurals"""
        g = Gloser(default_locale="pl")
        g.add_translations("pl", {
            "items": {
                "one": "{count} przedmiot",
                "few": "{count} przedmioty",
                "many": "{count} przedmiotów",
                "other": "{count} przedmiotów"
            }
        })

        # one: n=1
        assert g.translate("items", count=1, locale="pl") == "1 przedmiot"

        # few: n%10=2..4 and n%100!=12..14
        assert g.translate("items", count=2, locale="pl") == "2 przedmioty"
        assert g.translate("items", count=3, locale="pl") == "3 przedmioty"
        assert g.translate("items", count=4, locale="pl") == "4 przedmioty"
        assert g.translate("items", count=22, locale="pl") == "22 przedmioty"
        assert g.translate("items", count=23, locale="pl") == "23 przedmioty"
        assert g.translate("items", count=24, locale="pl") == "24 przedmioty"

        # many: others including 12-14
        assert g.translate("items", count=5, locale="pl") == "5 przedmiotów"
        assert g.translate("items", count=12, locale="pl") == "12 przedmiotów"
        assert g.translate("items", count=13, locale="pl") == "13 przedmiotów"
        assert g.translate("items", count=14, locale="pl") == "14 przedmiotów"
        assert g.translate("items", count=100, locale="pl") == "100 przedmiotów"

    def test_russian_plurals(self):
        """Test Russian one/few/many plurals"""
        g = Gloser(default_locale="ru")
        g.add_translations("ru", {
            "items": {
                "one": "{count} предмет",
                "few": "{count} предмета",
                "many": "{count} предметов",
                "other": "{count} предметов"
            }
        })

        # one: n%10=1 and n%100!=11
        assert g.translate("items", count=1, locale="ru") == "1 предмет"
        assert g.translate("items", count=21, locale="ru") == "21 предмет"
        assert g.translate("items", count=31, locale="ru") == "31 предмет"
        assert g.translate("items", count=101, locale="ru") == "101 предмет"

        # few: n%10=2..4 and n%100!=12..14
        assert g.translate("items", count=2, locale="ru") == "2 предмета"
        assert g.translate("items", count=3, locale="ru") == "3 предмета"
        assert g.translate("items", count=4, locale="ru") == "4 предмета"
        assert g.translate("items", count=22, locale="ru") == "22 предмета"
        assert g.translate("items", count=23, locale="ru") == "23 предмета"

        # many: others including 11-19
        assert g.translate("items", count=11, locale="ru") == "11 предметов"
        assert g.translate("items", count=12, locale="ru") == "12 предметов"
        assert g.translate("items", count=13, locale="ru") == "13 предметов"
        assert g.translate("items", count=5, locale="ru") == "5 предметов"
        assert g.translate("items", count=100, locale="ru") == "100 предметов"

    def test_ukrainian_plurals(self):
        """Test Ukrainian one/few/many plurals (same as Russian)"""
        g = Gloser(default_locale="uk")
        g.add_translations("uk", {
            "items": {
                "one": "{count} предмет",
                "few": "{count} предмети",
                "many": "{count} предметів",
                "other": "{count} предметів"
            }
        })

        # one: n%10=1 and n%100!=11
        assert g.translate("items", count=1, locale="uk") == "1 предмет"
        assert g.translate("items", count=21, locale="uk") == "21 предмет"

        # few: n%10=2..4 and n%100!=12..14
        assert g.translate("items", count=2, locale="uk") == "2 предмети"
        assert g.translate("items", count=3, locale="uk") == "3 предмети"
        assert g.translate("items", count=4, locale="uk") == "4 предмети"

        # many: others
        assert g.translate("items", count=5, locale="uk") == "5 предметів"
        assert g.translate("items", count=11, locale="uk") == "11 предметів"

    def test_czech_slovak_plurals(self):
        """Test Czech/Slovak one/few/other plurals"""
        g = Gloser(default_locale="cs")
        g.add_translations("cs", {
            "items": {
                "one": "{count} položka",
                "few": "{count} položky",
                "other": "{count} položek"
            }
        })

        # one: n=1
        assert g.translate("items", count=1, locale="cs") == "1 položka"

        # few: n=2..4
        assert g.translate("items", count=2, locale="cs") == "2 položky"
        assert g.translate("items", count=3, locale="cs") == "3 položky"
        assert g.translate("items", count=4, locale="cs") == "4 položky"

        # other: n>=5
        assert g.translate("items", count=5, locale="cs") == "5 položek"
        assert g.translate("items", count=10, locale="cs") == "10 položek"

    def test_croatian_serbian_bosnian_plurals(self):
        """Test Croatian/Serbian/Bosnian one/few/other plurals"""
        g = Gloser(default_locale="hr")
        g.add_translations("hr", {
            "items": {
                "one": "{count} predmet",
                "few": "{count} predmeta",
                "other": "{count} predmeta"
            }
        })

        # one: n%10=1 and n%100!=11
        assert g.translate("items", count=1, locale="hr") == "1 predmet"
        assert g.translate("items", count=21, locale="hr") == "21 predmet"

        # few: n%10=2..4 and n%100!=12..14
        assert g.translate("items", count=2, locale="hr") == "2 predmeta"
        assert g.translate("items", count=3, locale="hr") == "3 predmeta"
        assert g.translate("items", count=4, locale="hr") == "4 predmeta"

        # other: everything else
        assert g.translate("items", count=11, locale="hr") == "11 predmeta"
        assert g.translate("items", count=5, locale="hr") == "5 predmeta"

    def test_slovenian_plurals(self):
        """Test Slovenian one/two/few/other plurals"""
        g = Gloser(default_locale="sl")
        g.add_translations("sl", {
            "items": {
                "one": "{count} predmet",
                "two": "{count} predmeta",
                "few": "{count} predmeti",
                "other": "{count} predmetov"
            }
        })

        # one: n%100=1 (ending in 01)
        assert g.translate("items", count=1, locale="sl") == "1 predmet"
        assert g.translate("items", count=101, locale="sl") == "101 predmet"

        # two: n%100=2 (ending in 02)
        assert g.translate("items", count=2, locale="sl") == "2 predmeta"
        assert g.translate("items", count=102, locale="sl") == "102 predmeta"

        # few: n%100=3..4 (ending in 03 or 04)
        assert g.translate("items", count=3, locale="sl") == "3 predmeti"
        assert g.translate("items", count=4, locale="sl") == "4 predmeti"
        assert g.translate("items", count=103, locale="sl") == "103 predmeti"
        assert g.translate("items", count=104, locale="sl") == "104 predmeti"

        # other: everything else
        assert g.translate("items", count=5, locale="sl") == "5 predmetov"
        assert g.translate("items", count=100, locale="sl") == "100 predmetov"


class TestRomancePlurals:
    """Test Romance languages with special plural rules"""

    def test_french_plurals(self):
        """Test French one (n=0,1) / other plurals"""
        g = Gloser(default_locale="fr")
        g.add_translations("fr", {
            "items": {
                "one": "{count} article",
                "other": "{count} articles"
            }
        })

        # one: n=0 or n=1
        assert g.translate("items", count=0, locale="fr") == "0 article"
        assert g.translate("items", count=1, locale="fr") == "1 article"

        # other: n>=2
        assert g.translate("items", count=2, locale="fr") == "2 articles"
        assert g.translate("items", count=10, locale="fr") == "10 articles"

    def test_romanian_plurals(self):
        """Test Romanian one/few/other plurals"""
        g = Gloser(default_locale="ro")
        g.add_translations("ro", {
            "items": {
                "one": "{count} articol",
                "few": "{count} articole",
                "other": "{count} de articole"
            }
        })

        # one: n=1
        assert g.translate("items", count=1, locale="ro") == "1 articol"

        # few: n=0 or n%100=1..19 (0-19, 100-119)
        assert g.translate("items", count=0, locale="ro") == "0 articole"
        assert g.translate("items", count=2, locale="ro") == "2 articole"
        assert g.translate("items", count=5, locale="ro") == "5 articole"
        assert g.translate("items", count=19, locale="ro") == "19 articole"
        assert g.translate("items", count=101, locale="ro") == "101 articole"
        assert g.translate("items", count=119, locale="ro") == "119 articole"

        # other: n>=20 and n%100!=01..19
        assert g.translate("items", count=20, locale="ro") == "20 de articole"
        assert g.translate("items", count=100, locale="ro") == "100 de articole"


class TestBalticPlurals:
    """Test Baltic languages with special plural rules"""

    def test_lithuanian_plurals(self):
        """Test Lithuanian one/few/other plurals"""
        g = Gloser(default_locale="lt")
        g.add_translations("lt", {
            "items": {
                "one": "{count} daiktas",
                "few": "{count} daiktai",
                "other": "{count} daiktų"
            }
        })

        # one: n%10=1 and n%100!=11..19
        assert g.translate("items", count=1, locale="lt") == "1 daiktas"
        assert g.translate("items", count=21, locale="lt") == "21 daiktas"
        assert g.translate("items", count=31, locale="lt") == "31 daiktas"

        # few: n%10=2..9 and n%100!=11..19
        assert g.translate("items", count=2, locale="lt") == "2 daiktai"
        assert g.translate("items", count=3, locale="lt") == "3 daiktai"
        assert g.translate("items", count=9, locale="lt") == "9 daiktai"
        assert g.translate("items", count=22, locale="lt") == "22 daiktai"

        # other: includes 11-19
        assert g.translate("items", count=10, locale="lt") == "10 daiktų"
        assert g.translate("items", count=11, locale="lt") == "11 daiktų"
        assert g.translate("items", count=19, locale="lt") == "19 daiktų"
        assert g.translate("items", count=100, locale="lt") == "100 daiktų"

    def test_latvian_plurals(self):
        """Test Latvian zero/one/other plurals"""
        g = Gloser(default_locale="lv")
        g.add_translations("lv", {
            "items": {
                "zero": "{count} vienumu",
                "one": "{count} vienums",
                "other": "{count} vienumi"
            }
        })

        # zero: n=0
        assert g.translate("items", count=0, locale="lv") == "0 vienumu"

        # one: n%10=1 and n%100!=11
        assert g.translate("items", count=1, locale="lv") == "1 vienums"
        assert g.translate("items", count=21, locale="lv") == "21 vienums"
        assert g.translate("items", count=31, locale="lv") == "31 vienums"

        # other: everything else including 11
        assert g.translate("items", count=2, locale="lv") == "2 vienumi"
        assert g.translate("items", count=11, locale="lv") == "11 vienumi"
        assert g.translate("items", count=100, locale="lv") == "100 vienumi"


class TestGermanicPlurals:
    """Test Germanic languages with special plural rules"""

    def test_icelandic_plurals(self):
        """Test Icelandic one (n%10=1 and n%100!=11) / other plurals"""
        g = Gloser(default_locale="is")
        g.add_translations("is", {
            "items": {
                "one": "{count} hlutur",
                "other": "{count} hlutir"
            }
        })

        # one: n%10=1 and n%100!=11
        assert g.translate("items", count=1, locale="is") == "1 hlutur"
        assert g.translate("items", count=21, locale="is") == "21 hlutur"
        assert g.translate("items", count=31, locale="is") == "31 hlutur"

        # other: everything else including 11
        assert g.translate("items", count=2, locale="is") == "2 hlutir"
        assert g.translate("items", count=11, locale="is") == "11 hlutir"
        assert g.translate("items", count=100, locale="is") == "100 hlutir"


class TestSemiticPlurals:
    """Test Semitic languages with complex plural rules"""

    def test_arabic_plurals(self):
        """Test Arabic zero/one/two/few/many/other plurals"""
        g = Gloser(default_locale="ar")
        g.add_translations("ar", {
            "items": {
                "zero": "لا عناصر",
                "one": "عنصر واحد",
                "two": "عنصران",
                "few": "{count} عناصر",
                "many": "{count} عنصراً",
                "other": "{count} عنصر"
            }
        })

        # zero: n=0
        assert g.translate("items", count=0, locale="ar") == "لا عناصر"

        # one: n=1
        assert g.translate("items", count=1, locale="ar") == "عنصر واحد"

        # two: n=2
        assert g.translate("items", count=2, locale="ar") == "عنصران"

        # few: n%100=3..10 (3-10, 103-110, 203-210)
        assert g.translate("items", count=3, locale="ar") == "3 عناصر"
        assert g.translate("items", count=5, locale="ar") == "5 عناصر"
        assert g.translate("items", count=10, locale="ar") == "10 عناصر"
        assert g.translate("items", count=103, locale="ar") == "103 عناصر"
        assert g.translate("items", count=110, locale="ar") == "110 عناصر"

        # many: n%100=11..99 (11-99, 111-199)
        assert g.translate("items", count=11, locale="ar") == "11 عنصراً"
        assert g.translate("items", count=20, locale="ar") == "20 عنصراً"
        assert g.translate("items", count=99, locale="ar") == "99 عنصراً"
        assert g.translate("items", count=111, locale="ar") == "111 عنصراً"

        # other: n%100=0,1,2 (100, 101, 102, 200, 1000)
        assert g.translate("items", count=100, locale="ar") == "100 عنصر"
        assert g.translate("items", count=101, locale="ar") == "101 عنصر"
        assert g.translate("items", count=102, locale="ar") == "102 عنصر"
        assert g.translate("items", count=200, locale="ar") == "200 عنصر"
        assert g.translate("items", count=1000, locale="ar") == "1000 عنصر"

    def test_hebrew_plurals(self):
        """Test Hebrew one/two/many/other plurals"""
        g = Gloser(default_locale="he")
        g.add_translations("he", {
            "items": {
                "one": "פריט אחד",
                "two": "שני פריטים",
                "many": "{count} פריטים",
                "other": "{count} פריטים"
            }
        })

        # one: n=1
        assert g.translate("items", count=1, locale="he") == "פריט אחד"

        # two: n=2
        assert g.translate("items", count=2, locale="he") == "שני פריטים"

        # many: n%10=0 and n!=0 and n%100=0..10 (10, 20, 30...90, 100, 110...200, 210)
        assert g.translate("items", count=10, locale="he") == "10 פריטים"
        assert g.translate("items", count=20, locale="he") == "20 פריטים"
        assert g.translate("items", count=30, locale="he") == "30 פריטים"
        assert g.translate("items", count=100, locale="he") == "100 פריטים"
        assert g.translate("items", count=101, locale="he") == "101 פריטים"
        assert g.translate("items", count=110, locale="he") == "110 פריטים"
        assert g.translate("items", count=200, locale="he") == "200 פריטים"

        # other: everything else (3-9, 11-19, 21-29, etc.)
        assert g.translate("items", count=3, locale="he") == "3 פריטים"
        assert g.translate("items", count=11, locale="he") == "11 פריטים"
        assert g.translate("items", count=25, locale="he") == "25 פריטים"
        assert g.translate("items", count=99, locale="he") == "99 פריטים"
