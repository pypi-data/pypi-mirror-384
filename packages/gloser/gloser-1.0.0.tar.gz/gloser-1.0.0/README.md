# Gloser

**The simplest way to add internationalization to your Python app**

```python
from gloser import Gloser

g = Gloser()
g.load_yaml("translations.yaml")

print(g.translate("welcome", name="Alice", locale="es"))  # → "¡Bienvenida, Alice!"
```

[![PyPI version](https://badge.fury.io/py/gloser.svg)](https://pypi.org/project/gloser/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**72 languages** • **Zero config** • **Simple yet powerful**

---

## Why Gloser?

- ✨ **5-minute setup** — No complex configuration. Load a YAML file and start translating.
- 🌍 **72 languages out of the box** — Built-in locale defaults with pluralization rules, date/time formatting, and number formatting for 72 languages.
- 🎯 **Developer-friendly** — Natural Python API, clean YAML syntax, full type hints, and intuitive conventions.
- 🚀 **Modern patterns** — Built for web apps with thread-safe, stateless per-request locale handling.

---

## Quick Start

**1. Install**

```bash
pip install gloser
```

**2. Create your translations** (`translations.yaml`)

```yaml
welcome:
  en: "Welcome, {name}!"
  es: "¡Bienvenida, {name}!"
  fr: "Bienvenue, {name}!"

items:
  en:
    one: "You have {count} item"
    other: "You have {count} items"
  es:
    one: "Tienes {count} artículo"
    other: "Tienes {count} artículos"
  fr:
    one: "Vous avez {count} article"
    other: "Vous avez {count} articles"
```

**3. Use in your code**

```python
from gloser import Gloser

g = Gloser("translations.yaml")

# Simple translation
print(g.translate("welcome", name="Alice", locale="en"))
# → "Welcome, Alice!"

# Automatic pluralization
print(g.translate("items", count=1, locale="fr"))
# → "Vous avez 1 article"
print(g.translate("items", count=5, locale="es"))
# → "Tienes 5 artículos"
```

**That's it! You're internationalized.**

---

## Feature Showcase

### Flexible YAML Structure

Gloser supports multiple YAML formats — use whatever works best for you:

**Option 1: Single file with all translations** (shown above)
```yaml
welcome:
  en: "Welcome!"
  es: "¡Bienvenida!"
```

**Option 2: One file per locale**
```yaml
# en.yaml
.locale: en
welcome: "Welcome!"
goodbye: "Goodbye!"
```
```yaml
# es.yaml
.locale: es
welcome: "¡Bienvenida!"
goodbye: "¡Adiós!"
```

**Option 3: Multi-document YAML**
```yaml
---
en:
  welcome: "Welcome!"
---
es:
  welcome: "¡Bienvenida!"
```

**Mix and match:** Load multiple files with different formats — Gloser merges them intelligently!

```python
g = Gloser()
g.load_yaml_files("common.yaml", "en.yaml", "es.yaml")
```

### 🔢 Smart Pluralization

Gloser handles pluralization automatically using built-in rules for 72 languages, including complex ones like Polish with three forms:

```python
from gloser import Gloser

g = Gloser("translations.yaml")  # Auto-loads locale defaults on demand

# English: simple (one/other)
g.translate("files", count=1, locale="en")  # → "You have 1 file"
g.translate("files", count=5, locale="en")  # → "You have 5 files"

# Polish: complex (one/few/many)
g.translate("files", count=1, locale="pl")   # → "Masz 1 plik"
g.translate("files", count=2, locale="pl")   # → "Masz 2 pliki"
g.translate("files", count=5, locale="pl")   # → "Masz 5 plików"
g.translate("files", count=22, locale="pl")  # → "Masz 22 pliki"
```

**No configuration needed** — rules for Arabic, Russian, Slovenian, and 69 other languages are built-in!

### 📅 Intelligent Date/Time Formatting

Locale-aware date formatting with natural, localized output.

```python
from datetime import date
from gloser import Gloser

g = Gloser()  # Auto-loads date formats on demand

# Different locales, different formats
g.format_date(date(2025, 1, 9), "long", locale="en")
# → "January 9, 2025"

g.format_date(date(2025, 1, 9), "long", locale="de")
# → "9. Januar 2025"

g.format_date(date(2025, 1, 9), "long", locale="fr")
# → "9 janvier 2025"

g.format_date(date(2025, 1, 9), "long", locale="es")
# → "9 de enero de 2025"
```

You can also use date formatting within translations:

```yaml
event_date:
  en: "Event on {date:long}"
  de: "Veranstaltung am {date:long}"
```

```python
g.translate("event_date", date=date(2025, 1, 9), locale="en")
# → "Event on January 9, 2025"
```

**Built-in format styles**: `short`, `medium`, `long`, `full` — all configured per locale.

**Supported variables**: `{YYYY}`, `{MM}`, `{DD}`, `{monthname}`, `{mnm}`, `{dayname}`, `{dnm}`, `{hh}`, `{mm}`, `{ss}`, `{AMPM}`, and more.

### 💰 Number Formatting

Automatic thousands and decimal separators for all locales.

```python
from gloser import Gloser

g = Gloser()  # Uses built-in number formats for all locales

# Different locales use different separators
g.translate("Price: {price:,.2f}", price=1234.56, locale="en")
# → "Price: 1,234.56"

g.translate("Price: {price:,.2f}", price=1234.56, locale="de")
# → "Price: 1.234,56"  (Germany uses . for thousands, , for decimal)

g.translate("Price: {price:,.2f}", price=1234.56, locale="fr")
# → "Price: 1 234,56"  (France uses space for thousands, , for decimal)
```

### 📋 Array-Style Lookups

Perfect for enums, weekdays, months, and fixed lists. In your YAML:

```yaml
planet:
  en:
    1: Mercury
    2: Venus
    3: Earth
    4: Mars
  es:
    1: Mercurio
    2: Venus
    3: Tierra
    4: Marte
```

Then use it in code:

```python
g = Gloser("translations.yaml")

g.translate("planet", 3, locale="en")  # → "Earth"
g.translate("planet", 3, locale="es")  # → "Tierra"
```

### 🌐 Web-Ready: Stateless Locale Handling

Perfect for Flask, FastAPI, Django, and other web frameworks.

```python
# Initialize once at app startup
gloser = Gloser("translations.yaml")

# Get locale-specific translator per request
@app.route("/")
def index():
    locale = request.headers.get("Accept-Language", "en")[:2]
    t = gloser[locale]  # Thread-safe, stateless
    return t("welcome", name=current_user.name)
```

### 🥇 Ordinals

"1st, 2nd, 3rd" formatting with built-in rules for English, French, Spanish, and more.

```python
from gloser import Gloser

g = Gloser("translations.yaml")  # Auto-loads ordinal rules on demand

g.translate("place", position=1, locale="en")   # → "1st place"
g.translate("place", position=2, locale="en")   # → "2nd place"
g.translate("place", position=3, locale="en")   # → "3rd place"
g.translate("place", position=11, locale="en")  # → "11th place"
g.translate("place", position=22, locale="en")  # → "22nd place"
```

### 🛡️ Graceful Fallback

Missing translations? Gloser falls back to your default locale automatically.

```yaml
# translations.yaml
hello:
  en: "Hello!"
  es: "¡Hola!"

welcome:
  en: "Welcome!"
  # Spanish translation missing
```

```python
from gloser import Gloser

g = Gloser("translations.yaml", default_locale="en")

# Spanish translation exists
g.translate("hello", locale="es")    # → "¡Hola!"

# Falls back to English when Spanish is missing
g.translate("welcome", locale="es")  # → "Welcome!"
```

---

## 72 Languages Ready to Go

Gloser includes built-in locale defaults for **72 languages** with pluralization rules, date/time formatting, number formatting, month names, and weekday names:

<details>
<summary><strong>View all supported languages</strong></summary>

| | | | | |
|---|---|---|---|---|
| **af** - Afrikaans | **am** - Amharic | **ar** - Arabic | **az** - Azerbaijani | **be** - Belarusian |
| **bg** - Bulgarian | **bn** - Bengali | **bs** - Bosnian | **ca** - Catalan | **cs** - Czech |
| **da** - Danish | **de** - German | **dz** - Dzongkha | **el** - Greek | **en** - English |
| **es** - Spanish | **et** - Estonian | **fa** - Persian | **fi** - Finnish | **fr** - French |
| **ha** - Hausa | **he** - Hebrew | **hi** - Hindi | **hr** - Croatian | **hu** - Hungarian |
| **hy** - Armenian | **id** - Indonesian | **ig** - Igbo | **is** - Icelandic | **it** - Italian |
| **ja** - Japanese | **ka** - Georgian | **kk** - Kazakh | **km** - Khmer | **ko** - Korean |
| **ku** - Kurdish | **ky** - Kyrgyz | **lo** - Lao | **lt** - Lithuanian | **lv** - Latvian |
| **mn** - Mongolian | **ms** - Malay | **my** - Burmese | **nb** - Norwegian Bokmål | **ne** - Nepali |
| **nl** - Dutch | **nn** - Norwegian Nynorsk | **no** - Norwegian | **pl** - Polish | **pt** - Portuguese |
| **ro** - Romanian | **ru** - Russian | **si** - Sinhala | **sk** - Slovak | **sl** - Slovenian |
| **sn** - Shona | **so** - Somali | **sq** - Albanian | **sr** - Serbian | **sv** - Swedish |
| **sw** - Swahili | **ta** - Tamil | **th** - Thai | **tl** - Tagalog | **tr** - Turkish |
| **uk** - Ukrainian | **uz** - Uzbek | **vi** - Vietnamese | **xh** - Xhosa | **yo** - Yoruba |
| **zh** - Chinese | **zu** - Zulu | | | |

</details>

**Automatic deep merge**: Your custom translations merge with built-in defaults, so you only need to specify what's different.

---

## Examples

Check out the [`examples/`](examples/) directory for complete working examples:

- **[example.py](examples/example.py)** — Basic usage with multiple locales
- **[example_web_context.py](examples/example_web_context.py)** — Web application pattern (Flask/FastAPI)
- **[example_plurals.py](examples/example_plurals.py)** — Complex pluralization rules
- **[example_date_formatting.py](examples/example_date_formatting.py)** — Date and time formatting
- **[example_number_formatting.py](examples/example_number_formatting.py)** — Number formatting with locale separators
- **[example_ordinals.py](examples/example_ordinals.py)** — Ordinal numbers ("1st, 2nd, 3rd")
- **[example_arrays.py](examples/example_arrays.py)** — Array-style lookups for enums and lists

---

## Installation & Requirements

```bash
pip install gloser
```

**Requirements:**
- Python 3.8 or higher
- PyYAML 6.0 or higher (automatically installed)

**Optional dependencies for development:**
```bash
pip install gloser[dev]  # Includes pytest, pytest-cov
```

---

## API Overview

### Basic Usage

```python
from gloser import Gloser

# Initialize with default locale
g = Gloser(default_locale="en")

# Load translations from YAML
g.load_yaml("translations.yaml")

# Or load multiple files
g.load_yaml_files("common.yaml", "app.yaml")

# Or pass file(s) to constructor
g = Gloser("translations.yaml", default_locale="en")

# Translate with explicit locale
g.translate("welcome", name="Alice", locale="en")

# Or set current locale
g.set_locale("es")
g.translate("welcome", name="Alice")  # Uses Spanish
```

### Web Application Pattern

```python
# Initialize once at startup
gloser = Gloser("translations.yaml")

# Get locale-specific translator per request (stateless, thread-safe)
t = gloser["es"]  # or gloser.for_locale("es")
message = t("welcome", name="Alice")
```

### Controlling Locale Defaults

By default, Gloser auto-loads built-in locale defaults as needed. You can control this behavior:

```python
# Auto-load defaults on demand (default behavior)
g = Gloser("translations.yaml")

# Don't load any built-in defaults
g = Gloser("translations.yaml", load_defaults=False)

# Load specific locales immediately
g = Gloser("translations.yaml", load_defaults=["en", "es", "de"])

# Load all 72 locale defaults at startup
g = Gloser("translations.yaml")
g.load_defaults()  # Loads all available locale defaults

# Load additional defaults at runtime
g.load_defaults("fr", "it")  # Load French and Italian defaults
```

---

## Testing & Quality

Gloser is thoroughly tested with **184 tests** covering:
- ✅ All pluralization rules (Slavic, Semitic, Romance, Baltic, Germanic languages)
- ✅ Date and time formatting (72 locales)
- ✅ Number formatting with locale separators
- ✅ Ordinal numbers
- ✅ Array-style lookups
- ✅ Web application patterns
- ✅ Fallback behavior
- ✅ Edge cases and error handling

**Run tests:**
```bash
pytest
pytest --cov=gloser  # With coverage report
```

---

## Contributing

Contributions are welcome! Whether it's:
- 🐛 Bug reports
- 💡 Feature requests
- 📝 Documentation improvements
- 🌍 New locale defaults
- ✨ Code contributions

Please open an issue or submit a pull request on [GitHub](https://github.com/aremeis/gloser).

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Why "Gloser"?

"Gloser" is Norwegian for "glossary" — a fitting name for a translation library! 📚🇳🇴

---

Made with ❤️ by developers who believe i18n should be simple.
