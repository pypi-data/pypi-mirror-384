"""Main Gloser implementation"""

from pathlib import Path
from typing import Dict, Optional, Any, Union, List, Tuple
import yaml
import string
import re
import datetime


class LocaleFormatter(string.Formatter):
    """
    Custom string formatter that applies locale-specific number and date formatting.

    This formatter intercepts format specifications and applies locale-specific:
    - Number formatting: decimal and thousand separators
    - Date formatting: custom date formats and localized month/weekday names
    """

    def __init__(
        self,
        decimal_sep: str = ".",
        thousand_sep: str = ",",
        date_formats: Optional[Dict[str, str]] = None,
        time_formats: Optional[Dict[str, str]] = None,
        datetime_formats: Optional[Dict[str, str]] = None,
        month_names: Optional[Dict[str, Dict[int, str]]] = None,
        weekday_names: Optional[Dict[str, Dict[int, str]]] = None
    ):
        """
        Initialize the locale formatter.

        Args:
            decimal_sep: Decimal separator for this locale (default: ".")
            thousand_sep: Thousand separator for this locale (default: ",")
            date_formats: Dict of date format styles (short, long, full, other)
            time_formats: Dict of time format styles (short, long, other)
            datetime_formats: Dict of datetime format styles (short, long, full, other)
            month_names: Dict with "full" and "short" dicts mapping month numbers to names
            weekday_names: Dict with "full" and "short" dicts mapping weekday numbers to names
        """
        super().__init__()
        self.decimal_sep = decimal_sep
        self.thousand_sep = thousand_sep
        self.date_formats = date_formats or {}
        self.time_formats = time_formats or {}
        self.datetime_formats = datetime_formats or {}
        self.month_names = month_names or {"full": {}, "short": {}}
        self.weekday_names = weekday_names or {"full": {}, "short": {}}

    def format_field(self, value: Any, format_spec: str) -> str:
        """
        Format a field with locale-specific number and date/time formatting.

        Args:
            value: The value to format
            format_spec: The format specification string

        Returns:
            The formatted string with locale-specific formatting applied
        """
        # Handle date/datetime/time formatting
        if isinstance(value, (datetime.date, datetime.datetime, datetime.time)):
            return self._format_date(value, format_spec)

        # Apply standard Python formatting first for non-dates
        result = super().format_field(value, format_spec)

        # Check if this looks like number formatting
        # Numeric types: f, F, e, E, g, G, d, n, %
        # Also check for comma (thousand separator indicator)
        if format_spec and (
            ',' in format_spec or
            any(c in format_spec for c in 'fFegGdDn%')
        ):
            # Only apply locale formatting if value is numeric
            if isinstance(value, (int, float, complex)):
                # Replace separators only if they're different from defaults
                if self.decimal_sep != "." or self.thousand_sep != ",":
                    # Use temporary placeholders to avoid conflicts when swapping
                    # (e.g., when . → , and , → . like in Norwegian)
                    temp_thousand = "\x00"  # Null byte as temporary marker
                    temp_decimal = "\x01"   # SOH as temporary marker

                    # Step 1: Replace default separators with temporary markers
                    result = result.replace(",", temp_thousand)  # Save thousand separator
                    result = result.replace(".", temp_decimal)   # Save decimal separator

                    # Step 2: Replace temporary markers with locale-specific separators
                    result = result.replace(temp_thousand, self.thousand_sep)
                    result = result.replace(temp_decimal, self.decimal_sep)

        return result

    def _format_date(self, date_obj: Union[datetime.date, datetime.datetime, datetime.time], format_spec: str) -> str:
        """
        Format a date, datetime, or time object using {variable} syntax.

        Args:
            date_obj: The date, datetime, or time object to format
            format_spec: Format specification - can be:
                - Empty ("") or None: use other format
                - Named style ("short", "long", "full"): use configured format
                - Named style with capitalization ("Short", "Full"): capitalize result

        Returns:
            Formatted date/time string with localized month/weekday names

        Supported variables:
            Date: {YYYY}, {YY}, {MM}, {M}, {DD}, {D}
            Month names: {monthname}, {mnm}
            Weekday names: {dayname}, {dnm}
            Time: {hh}, {h}, {HH}, {H}, {mm}, {m}, {ss}, {s}
            Period: {ampm}, {AMPM}
        """
        capitalize_result = False

        # Determine which format configuration to use based on object type
        if isinstance(date_obj, datetime.datetime):
            # For datetime objects, try datetime formats first, fallback to date formats
            formats = self.datetime_formats if self.datetime_formats else self.date_formats
            default_format = "{YYYY}-{MM}-{DD} {hh}:{mm}"
        elif isinstance(date_obj, datetime.time):
            # For time objects, use time formats
            formats = self.time_formats
            default_format = "{hh}:{mm}"
        else:  # datetime.date
            # For date objects, use date formats
            formats = self.date_formats
            default_format = "{YYYY}-{MM}-{DD}"

        # Determine the format string to use
        if not format_spec:
            # Use default format
            format_string = formats.get("other", default_format)
        else:
            # Named style (short, long, full, etc.)
            # Check if first letter is uppercase (indicates capitalization)
            if format_spec and format_spec[0].isupper():
                capitalize_result = True
                format_spec_lower = format_spec.lower()
            else:
                format_spec_lower = format_spec

            # Look up the named format
            format_string = formats.get(
                format_spec_lower,
                formats.get("other", default_format)
            )

        # Build format variables dictionary
        format_vars = {}

        # Date components (for date and datetime objects)
        if hasattr(date_obj, 'year'):
            format_vars.update({
                'YYYY': date_obj.year,
                'YY': str(date_obj.year)[-2:].zfill(2),
                'MM': f'{date_obj.month:02d}',
                'M': str(date_obj.month),
                'DD': f'{date_obj.day:02d}',
                'D': str(date_obj.day),
                'monthname': self.month_names.get('full', {}).get(date_obj.month, ''),
                'mnm': self.month_names.get('short', {}).get(date_obj.month, ''),
                'dayname': self.weekday_names.get('full', {}).get(date_obj.isoweekday(), ''),
                'dnm': self.weekday_names.get('short', {}).get(date_obj.isoweekday(), ''),
            })

        # Time components (for time and datetime objects)
        if hasattr(date_obj, 'hour'):
            hour_12 = date_obj.hour % 12 or 12
            format_vars.update({
                'hh': f'{date_obj.hour:02d}',
                'h': str(date_obj.hour),
                'HH': f'{hour_12:02d}',
                'H': str(hour_12),
                'mm': f'{date_obj.minute:02d}',
                'm': str(date_obj.minute),
                'ss': f'{date_obj.second:02d}',
                's': str(date_obj.second),
                'ampm': 'am' if date_obj.hour < 12 else 'pm',
                'AMPM': 'AM' if date_obj.hour < 12 else 'PM',
            })

        # Format using Python's native mechanism
        result = format_string.format(**format_vars)

        # Apply capitalization if requested
        if capitalize_result and result:
            result = result[0].upper() + result[1:] if len(result) > 1 else result.upper()

        return result



class LocaleGloser:
    """
    Lightweight, locale-specific translator.

    This class is designed for multi-user contexts (e.g., web applications)
    where each request needs its own locale without shared state.

    It holds a reference to the parent Gloser and delegates translation logic,
    avoiding code duplication.
    """

    def __init__(self, gloser: 'Gloser', locale: str):
        """
        Initialize a LocaleGloser.

        Args:
            gloser: Reference to the parent Gloser instance
            locale: The locale for this translator
        """
        self._gloser = gloser
        self._locale = locale

    def __call__(self, key: str, *args: Any, **kwargs: Any) -> str:
        """
        Translate a key to the configured locale.

        Delegates to the parent Gloser's translate method.
        Supports both positional and keyword arguments for string interpolation.

        Args:
            key: The translation key
            *args: Positional arguments for format placeholders
            **kwargs: Keyword arguments for format placeholders

        Returns:
            The translated string, or the key if translation not found

        Examples:
            t = gloser["en"]
            t("hello")  # → "Hello"
            t("greeting", "John", country="England")  # → "Hello John from England"
        """
        return self._gloser.translate(key, *args, locale=self._locale, **kwargs)

    @property
    def locale(self) -> str:
        """Get the current locale."""
        return self._locale

    def format_date(self, value: Union[datetime.date, datetime.datetime],
                    format_spec: str = "") -> str:
        """
        Format a date or datetime object using this locale's formatting.

        Args:
            value: The date or datetime object to format
            format_spec: Format specification - either a named style ("short", "long", "full")
                        or a custom format string using {YYYY}, {MM}, {DD}, etc.

        Returns:
            The formatted date string

        Examples:
            t = g["de"]
            t.format_date(date(2025, 1, 9), "long")  # → "9. Januar 2025"
        """
        return self._gloser.format_date(value, format_spec, locale=self._locale)

    def format_number(self, value: Union[int, float], format_spec: str = "") -> str:
        """
        Format a number using this locale's formatting.

        Args:
            value: The numeric value to format
            format_spec: Format specification using Python's format spec mini-language

        Returns:
            The formatted number string

        Examples:
            t = g["de"]
            t.format_number(1234.56, ",.2f")  # → "1.234,56"
        """
        return self._gloser.format_number(value, format_spec, locale=self._locale)


class Gloser:
    """
    Simple internationalization manager for Python applications.

    Supports both traditional single-locale usage and modern multi-user contexts.

    Usage patterns:
        # Traditional (single locale, stateful)
        g = Gloser()
        g.load_yaml("translations.yaml")
        g.set_locale("no")
        print(g.translate("hello"))

        # Multi-user web context (stateless, thread-safe)
        gloser = Gloser("translations.yaml")  # Load once at startup
        t = gloser["no"]  # Or: gloser.for_locale("no")
        print(t("hello"))  # Translate
    """

    def __init__(self, file_path: Union[str, Path, List[Union[str, Path]], None] = None,
                 default_locale: str = "en",
                 load_defaults: Union[bool, List[str]] = True):
        """
        Initialize Gloser with optional translation files.

        Args:
            file_path: Optional YAML file(s) to load on initialization.
                      Can be a single path or list of paths.
            default_locale: The default locale to use (default: "en")
            load_defaults: Control loading of built-in locale defaults.
                          - True: Auto-load defaults as locales are used (default)
                          - False or []: Don't load any defaults
                          - List of locale codes: Load specific defaults immediately
                          Examples:
                              load_defaults=True              # Auto-load on demand
                              load_defaults=False             # No defaults
                              load_defaults=[]                # No defaults
                              load_defaults=["en", "es"]      # Load English and Spanish
        """
        self.default_locale = default_locale
        self.current_locale = default_locale
        self.translations: Dict[str, Dict[str, str]] = {}
        self._plural_regex_cache: Dict[str, Dict[str, re.Pattern]] = {}
        self._loaded_default_locales: set = set()

        # Determine auto-load behavior
        if isinstance(load_defaults, bool):
            self._auto_load_defaults = load_defaults
            locales_to_load = [default_locale] if load_defaults else []
        elif isinstance(load_defaults, list):
            self._auto_load_defaults = False  # Explicit list means no auto-loading
            locales_to_load = load_defaults
        else:
            raise ValueError("load_defaults must be bool or list of locale codes")

        # Load specified default locale configurations
        for locale in locales_to_load:
            self._load_default_locale(locale)

        # Load translations if file_path provided
        if file_path is not None:
            if isinstance(file_path, (list, tuple)):
                self.load_yaml_files(*file_path)
            else:
                self.load_yaml(file_path)

    def add_translations(self, locale: str, translations: Dict[str, str]) -> None:
        """
        Add translations for a specific locale.

        Args:
            locale: The locale code (e.g., "en", "es", "fr")
            translations: Dictionary mapping keys to translated strings
        """
        # Auto-load default locale configuration if not yet loaded and auto-loading is enabled
        if self._auto_load_defaults and locale not in self._loaded_default_locales:
            self._load_default_locale(locale)

        if locale not in self.translations:
            self.translations[locale] = {}
        self._deep_merge(self.translations[locale], translations)

    def load_defaults(self, *locales: str) -> None:
        """
        Load built-in locale defaults for specific locales or all available locales.

        Args:
            *locales: Locale codes to load. If no arguments provided, loads all
                     available locale defaults (72 languages).

        Examples:
            g.load_defaults()              # Load all 72 locale defaults
            g.load_defaults("de", "fr")    # Load German and French defaults
        """
        if not locales:
            # Load all available locale defaults
            locale_dir = Path(__file__).parent / "locale-defaults"
            if locale_dir.exists():
                for yaml_file in locale_dir.glob("*.yaml"):
                    locale = yaml_file.stem
                    if locale not in self._loaded_default_locales:
                        self._load_default_locale(locale)
        else:
            # Load specific locale defaults
            for locale in locales:
                if locale not in self._loaded_default_locales:
                    self._load_default_locale(locale)

    def set_locale(self, locale: str) -> None:
        """
        Set the current locale.

        Args:
            locale: The locale code to set as current
        """
        self.current_locale = locale

    def _load_default_locale(self, locale: str) -> None:
        """
        Load default configuration for a locale from the locale-defaults directory.

        Attempts to load locale-specific defaults (e.g., "en-US.yaml") or falls back
        to language-only defaults (e.g., "en.yaml" for "en-US").

        After loading, aliases the locale so both "no" and "no-NO" work.

        Args:
            locale: The locale code (e.g., "en", "en-US", "no-NO")
        """
        # Don't load the same locale defaults twice
        if locale in self._loaded_default_locales:
            return

        # Mark as being loaded before loading to prevent recursion
        self._loaded_default_locales.add(locale)

        # Get the directory where gloser.py is located
        gloser_dir = Path(__file__).parent
        defaults_dir = gloser_dir / "locale-defaults"

        # Try loading exact locale match first (e.g., "en-US.yaml")
        locale_file = defaults_dir / f"{locale}.yaml"
        loaded_from_key = None

        if locale_file.exists():
            self.load_yaml(locale_file)
            loaded_from_key = self._get_loaded_locale_key(locale)
            # Alias the locale if needed
            self._alias_locale(locale, loaded_from_key)
            return

        # Try loading language-only version (e.g., "en.yaml" for "en-US")
        if "-" in locale or "_" in locale:
            # Extract language code (before - or _)
            lang = locale.split("-")[0].split("_")[0]
            lang_file = defaults_dir / f"{lang}.yaml"
            if lang_file.exists():
                self._loaded_default_locales.add(lang)  # Mark lang as loaded too
                self.load_yaml(lang_file)
                loaded_from_key = self._get_loaded_locale_key(lang)
                # Alias the locale if needed
                self._alias_locale(locale, loaded_from_key)

    def _get_loaded_locale_key(self, requested_locale: str) -> Optional[str]:
        """Get the actual locale key that was loaded (might differ from requested)"""
        # Check for more specific locale codes first (e.g., "no-NO" for "no")
        # This allows proper aliasing when both exist
        for key in self.translations.keys():
            if key.startswith(requested_locale + "-") or key.startswith(requested_locale + "_"):
                return key

        # Check if the requested locale exists
        if requested_locale in self.translations:
            return requested_locale

        # Also check reverse: "no" for "no-NO"
        for key in self.translations.keys():
            lang_part = key.split("-")[0].split("_")[0]
            if lang_part == requested_locale:
                return key

        return None

    def _alias_locale(self, requested_locale: str, actual_locale_key: Optional[str]) -> None:
        """Create an alias so both locale codes work, merging if locale already exists"""
        if actual_locale_key and actual_locale_key != requested_locale:
            if actual_locale_key in self.translations:
                # If requested_locale already has content, merge defaults into it
                if requested_locale in self.translations:
                    # Deep merge: defaults first, then user translations (so user overrides defaults)
                    merged = self.translations[actual_locale_key].copy()
                    self._deep_merge(merged, self.translations[requested_locale])
                    self.translations[requested_locale] = merged
                else:
                    # No existing content, just alias
                    self.translations[requested_locale] = self.translations[actual_locale_key]

    def _deep_merge(self, base: Dict, updates: Dict) -> None:
        """
        Deep merge updates dict into base dict.

        For configuration keys like .plurals, .number, .date, etc., merges nested
        dictionaries recursively so user can add to defaults rather than replace them.

        Args:
            base: The base dictionary to merge into (modified in place)
            updates: The updates to apply
        """
        CONFIG_KEYS = {'.plurals', '.number', '.date', '.time', '.datetime', '.month', '.dayofweek'}

        for key, value in updates.items():
            if key in CONFIG_KEYS and isinstance(value, dict) and key in base and isinstance(base[key], dict):
                # Recursively merge configuration sections
                self._deep_merge(base[key], value)
            elif isinstance(value, dict) and key in base and isinstance(base[key], dict) and not key.startswith('.'):
                # For regular translation keys with plural forms, also merge recursively
                # This allows adding new plural categories without replacing existing ones
                self._deep_merge(base[key], value)
            else:
                # For simple values, just update
                base[key] = value

    def _get_number_format(self, locale: str) -> Tuple[str, str]:
        """
        Get number formatting configuration for a locale.

        Expects hierarchical structure:
        `.number` dict with `.decimal-separator` and `.thousand-separator` keys

        Args:
            locale: The locale code

        Returns:
            Tuple of (decimal_separator, thousand_separator)
        """
        decimal_sep = "."
        thousand_sep = ","

        # Check if locale has custom number format settings
        if locale in self.translations:
            if ".number" in self.translations[locale]:
                number_config = self.translations[locale][".number"]
                if isinstance(number_config, dict):
                    if ".decimal-separator" in number_config:
                        decimal_sep = number_config[".decimal-separator"]
                    if ".thousand-separator" in number_config:
                        thousand_sep = number_config[".thousand-separator"]

        return (decimal_sep, thousand_sep)

    def _get_date_format(self, locale: str) -> Dict[str, str]:
        """
        Get date formatting configuration for a locale.

        Expects hierarchical structure:
        `.date` dict with format style keys (short, long, full, other)

        Args:
            locale: The locale code

        Returns:
            Dict mapping format style names to strftime format strings.
            Always includes an "other" key.
        """
        default_formats = {
            "short": "{YYYY}-{MM}-{DD}",
            "long": "{monthname} {DD}, {YYYY}",
            "full": "{dayname}, {monthname} {DD}, {YYYY}",
            "other": "{YYYY}-{MM}-{DD}"
        }

        # Check if locale has custom date format settings
        if locale in self.translations:
            if ".date" in self.translations[locale]:
                date_config = self.translations[locale][".date"]

                # If it's a dict, use it (may have multiple styles)
                if isinstance(date_config, dict):
                    # Ensure there's always an "other"
                    if "other" not in date_config:
                        # Use "short" as default if available, otherwise first available
                        if "short" in date_config:
                            date_config["other"] = date_config["short"]
                        elif date_config:
                            date_config["other"] = next(iter(date_config.values()))
                    return date_config

                # If it's a string, use it for all styles
                elif isinstance(date_config, str):
                    return {
                        "short": date_config,
                        "long": date_config,
                        "full": date_config,
                        "other": date_config
                    }

        return default_formats

    def _get_time_format(self, locale: str) -> Dict[str, str]:
        """
        Get time formatting configuration for a locale.

        Expects hierarchical structure:
        `.time` dict with format style keys (short, long, with-period, other)

        Args:
            locale: The locale code

        Returns:
            Dict mapping format style names to strftime format strings.
            Always includes an "other" key.
        """
        default_formats = {
            "short": "{hh}:{mm}",
            "long": "{hh}:{mm}:{ss}",
            "with-period": "{HH}:{mm} {AMPM}",
            "other": "{hh}:{mm}"
        }

        # Check if locale has custom time format settings
        if locale in self.translations:
            if ".time" in self.translations[locale]:
                time_config = self.translations[locale][".time"]

                # If it's a dict, use it (may have multiple styles)
                if isinstance(time_config, dict):
                    # Ensure there's always an "other"
                    if "other" not in time_config:
                        if "short" in time_config:
                            time_config["other"] = time_config["short"]
                        elif time_config:
                            time_config["other"] = next(iter(time_config.values()))
                    return time_config

                # If it's a string, use it for all styles
                elif isinstance(time_config, str):
                    return {
                        "short": time_config,
                        "long": time_config,
                        "with-period": time_config,
                        "other": time_config
                    }

        return default_formats

    def _get_datetime_format(self, locale: str) -> Dict[str, str]:
        """
        Get datetime formatting configuration for a locale.

        Expects hierarchical structure:
        `.datetime` dict with format style keys (short, long, full, other)

        If not found, returns None to trigger fallback to .date format.

        Args:
            locale: The locale code

        Returns:
            Dict mapping format style names to strftime format strings,
            or None if no datetime-specific configuration exists.
        """
        # Check if locale has custom datetime format settings
        if locale in self.translations:
            if ".datetime" in self.translations[locale]:
                datetime_config = self.translations[locale][".datetime"]

                # If it's a dict, use it (may have multiple styles)
                if isinstance(datetime_config, dict):
                    # Ensure there's always an "other"
                    if "other" not in datetime_config:
                        if "short" in datetime_config:
                            datetime_config["other"] = datetime_config["short"]
                        elif datetime_config:
                            datetime_config["other"] = next(iter(datetime_config.values()))
                    return datetime_config

                # If it's a string, use it for all styles
                elif isinstance(datetime_config, str):
                    return {
                        "short": datetime_config,
                        "long": datetime_config,
                        "full": datetime_config,
                        "other": datetime_config
                    }

        # No datetime-specific format, will fallback to date format
        return None

    def _get_month_names(self, locale: str) -> Dict[str, Dict[int, str]]:
        """
        Get localized month names for a locale.

        Expects hierarchical structure:
        `.month` dict with `full` and `short` subdicts containing numeric keys (1-12)

        Args:
            locale: The locale code

        Returns:
            Dict with "full" and "short" keys, each mapping month numbers (1-12)
            to localized names. Returns empty dicts if not configured.
        """
        months_full = {}
        months_short = {}

        if locale in self.translations:
            if ".month" in self.translations[locale]:
                month_config = self.translations[locale][".month"]
                if isinstance(month_config, dict):
                    if "full" in month_config:
                        month_full_dict = month_config["full"]
                        if isinstance(month_full_dict, dict):
                            months_full = {int(k): v for k, v in month_full_dict.items()}

                    if "short" in month_config:
                        month_short_dict = month_config["short"]
                        if isinstance(month_short_dict, dict):
                            months_short = {int(k): v for k, v in month_short_dict.items()}

        return {"full": months_full, "short": months_short}

    def _get_weekday_names(self, locale: str) -> Dict[str, Dict[int, str]]:
        """
        Get localized weekday names for a locale.

        Expects hierarchical structure:
        `.dayofweek` dict with `full` and `short` subdicts containing numeric keys (1=Monday, 7=Sunday)

        Note: Uses ISO 8601 weekday numbering where 1=Monday, 7=Sunday
        (matching Python's datetime.isoweekday())

        Args:
            locale: The locale code

        Returns:
            Dict with "full" and "short" keys, each mapping weekday numbers (1-7)
            to localized names (1=Monday, 7=Sunday). Returns empty dicts if not configured.
        """
        weekdays_full = {}
        weekdays_short = {}

        if locale in self.translations:
            if ".dayofweek" in self.translations[locale]:
                weekday_config = self.translations[locale][".dayofweek"]
                if isinstance(weekday_config, dict):
                    if "full" in weekday_config:
                        weekday_full_dict = weekday_config["full"]
                        if isinstance(weekday_full_dict, dict):
                            weekdays_full = {int(k): v for k, v in weekday_full_dict.items()}

                    if "short" in weekday_config:
                        weekday_short_dict = weekday_config["short"]
                        if isinstance(weekday_short_dict, dict):
                            weekdays_short = {int(k): v for k, v in weekday_short_dict.items()}

        return {"full": weekdays_full, "short": weekdays_short}

    def _get_plural_rules(self, locale: str) -> Dict[str, str]:
        """
        Get plural rules for a locale.

        Looks up the special key `.plurals` which contains regex patterns
        for matching count values to plural categories.

        Args:
            locale: The locale code

        Returns:
            Dict mapping category names to regex patterns.

        Example:
            {
                "zero": "^0$",
                "one": "^1$",
                "few": "^[2-7]$",
            }
        """
        # Check if locale has custom plural rules
        if locale in self.translations:
            if ".plurals" in self.translations[locale]:
                rules = self.translations[locale][".plurals"]
                if isinstance(rules, dict):
                    return rules

        # Default English rules: singular (1) and plural (everything else)
        return {
            "one": "^1$"
        }

    def _get_compiled_plural_rules(self, locale: str) -> Dict[str, re.Pattern]:
        """
        Get compiled regex patterns for plural rules of a locale.

        Uses caching to avoid recompiling regexes on every translation.

        Args:
            locale: The locale code

        Returns:
            Dict mapping category names to compiled regex patterns
        """
        if locale not in self._plural_regex_cache:
            rules = self._get_plural_rules(locale)
            self._plural_regex_cache[locale] = {
                category: re.compile(pattern)
                for category, pattern in rules.items()
            }
        return self._plural_regex_cache[locale]

    def _select_plural_form(self, count_value: Any, locale: str, available_categories: Optional[set] = None) -> str:
        """
        Select appropriate plural category for a count value.

        First checks for direct key match (for array-style lookups), then falls back
        to regex pattern matching for plural rules.

        Args:
            count_value: The count value (can be int, str, or other types)
            locale: The locale (used to get rules)
            available_categories: Optional set of categories to check. If provided,
                                 only these categories will be considered. This allows
                                 different translation keys to use different subsets of
                                 plural rules (e.g., ordinals vs cardinals), or
                                 array-style lookups with numeric keys.

        Returns:
            Category name that matches (e.g., "one", "few", "many", "other", or a direct key)

        Example:
            _select_plural_form(1, "en")   # → "one"
            _select_plural_form(3, "en")   # → "other"
            _select_plural_form(5, "ru")   # → "many" (if Russian rules configured)
            _select_plural_form(1, "en", {"first", "second", "third"})  # → "first"
            _select_plural_form(2, "no", {1, 2, 3})  # → 2 (direct match for array)
        """
        # First, check for direct key match (array-style lookup)
        # Try both the original value and string representation
        if available_categories is not None:
            if count_value in available_categories:
                return count_value
            count_str = str(count_value)
            if count_str in available_categories:
                return count_str

        # Fall back to regex-based plural matching
        count_str = str(count_value)
        rules = self._get_plural_rules(locale)
        compiled_rules = self._get_compiled_plural_rules(locale)

        # Try each category in the order they're defined
        # This preserves user-specified order from YAML
        for category in rules.keys():
            # If available_categories is specified, only check those categories
            if available_categories is not None and category not in available_categories:
                continue

            if category in compiled_rules:
                pattern = compiled_rules[category]
                if pattern.match(count_str):
                    return category

        # Fall back to "other"
        return "other"

    def __getitem__(self, locale: str) -> LocaleGloser:
        """
        Get a locale-specific translator (for multi-user contexts).

        This is the preferred way to handle translations in multi-user
        environments like web applications, where different users may
        need different locales simultaneously.

        Args:
            locale: The locale code for the translator

        Returns:
            A LocaleGloser instance configured for the specified locale

        Example:
            gloser = Gloser("translations.yaml")
            t = gloser["no"]
            message = t("welcome", name="Alice")
        """
        return LocaleGloser(self, locale)

    def for_locale(self, locale: str) -> LocaleGloser:
        """
        Get a locale-specific translator (explicit method form).

        This is an alternative to the bracket notation for getting a
        locale-specific translator. Both are equivalent:
            gloser[locale] == gloser.for_locale(locale)

        Args:
            locale: The locale code for the translator

        Returns:
            A LocaleGloser instance configured for the specified locale

        Example:
            gloser = Gloser("translations.yaml")
            t = gloser.for_locale("no")
            message = t("welcome", name="Alice")
        """
        return self[locale]

    def __call__(self, key: str, *args: Any, locale: Optional[str] = None, **kwargs: Any) -> str:
        """
        Shorthand for translate() - allows callable syntax.

        Supports both positional and keyword arguments for string interpolation.

        Args:
            key: The translation key
            *args: Positional arguments for format placeholders
            locale: Optional locale to use (defaults to current_locale)
            **kwargs: Keyword arguments for format placeholders

        Returns:
            The translated string

        Examples:
            g = Gloser("translations.yaml")
            g.set_locale("no")
            print(g("hello"))  # Same as g.translate("hello")
            print(g("greeting", "John", country="England"))  # With args
        """
        return self.translate(key, *args, locale=locale, **kwargs)

    def _convert_yaml_values(self, value: Any) -> Any:
        """
        Recursively convert YAML values, ensuring string keys in nested dicts.

        This is needed because YAML BaseLoader may parse locale codes like 'no'
        as False, or numbers as integers. We need to ensure all dict keys are strings.

        Args:
            value: The value to convert

        Returns:
            Converted value with string keys if it's a dict
        """
        if isinstance(value, dict):
            return {str(k): self._convert_yaml_values(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._convert_yaml_values(item) for item in value]
        else:
            return value

    def load_yaml(self, file_path: Union[str, Path]) -> None:
        """
        Load translations from a YAML file.

        Supports multiple flexible formats that can be mixed:

        1. Single-locale format (document with .locale field):
            .locale: no
            .plurals:
              one: "^1$"
              other: ".*"
            hello: Hei
            items:
              one: "én ting"
              other: "{count} ting"

        2. Multi-locale format (keys with nested locale translations):
            hello:
              no: Hei
              en: Hello
            world:
              no: Verden
              en: World

        3. Mixed documents (any combination):
            ---
            .locale: no
            hello: Hei
            goodbye: Ha det
            ---
            welcome:
              en: Welcome
              no: Velkommen
            ---
            .locale: es
            hello: Hola

        Args:
            file_path: Path to the YAML file containing translations

        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If format is invalid or required fields are missing
            yaml.YAMLError: If the file is not valid YAML
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Translation file not found: {file_path}")

        with path.open("r", encoding="utf-8") as f:
            # Use yaml.BaseLoader to prevent boolean conversion of 'no', 'yes', etc.
            documents = list(yaml.load_all(f, Loader=yaml.BaseLoader))

            # Filter out None/empty documents
            documents = [doc for doc in documents if doc and isinstance(doc, dict)]

            if not documents:
                return  # Empty file, nothing to load

            # Check if this is a single document
            if len(documents) == 1:
                doc = documents[0]
                # Convert all keys to strings
                doc = {str(k): self._convert_yaml_values(v) for k, v in doc.items()}

                # Single-locale format: document has .locale field
                if ".locale" in doc:
                    locale = doc[".locale"]

                    # Validate locale field
                    if not locale or not isinstance(locale, str):
                        raise ValueError(
                            f"File {file_path} has invalid '.locale' field: must be a non-empty string"
                        )

                    # Remove .locale from the document
                    translations = {k: v for k, v in doc.items() if k != ".locale"}

                    # Use add_translations which already handles nested structures
                    self.add_translations(locale, translations)
                    return

                # Multi-locale format: each key contains locale translations
                # Example: hello: {no: Hei, en: Hello}
                for key, value in doc.items():
                    if isinstance(value, dict):
                        # This is a multi-locale entry: key -> {locale: translation}
                        for locale, translation in value.items():
                            self.add_translations(locale, {key: translation})
                    # If value is not a dict, skip it (could be a comment or other data)

                return

            # Multiple documents: process each one
            # They can be either single-locale (with .locale) or multi-locale (nested)
            for doc_index, doc in enumerate(documents, start=1):
                doc = {str(k): self._convert_yaml_values(v) for k, v in doc.items()}

                if ".locale" in doc:
                    # Single-locale document
                    locale = doc[".locale"]

                    # Validate locale field
                    if not locale or not isinstance(locale, str):
                        raise ValueError(
                            f"Document {doc_index} in {file_path} has invalid '.locale' field: must be a non-empty string"
                        )

                    # Remove .locale from the document
                    translations = {k: v for k, v in doc.items() if k != ".locale"}

                    # Use add_translations which already handles nested structures
                    self.add_translations(locale, translations)
                else:
                    # Multi-locale document: each key contains locale translations
                    # Example: hello: {no: Hei, en: Hello}
                    for key, value in doc.items():
                        if isinstance(value, dict):
                            # This is a multi-locale entry: key -> {locale: translation}
                            for locale, translation in value.items():
                                self.add_translations(locale, {key: translation})
                        # If value is not a dict, skip it (could be a comment or other data)

    def load_yaml_files(self, *file_paths: Union[str, Path]) -> None:
        """
        Load translations from multiple YAML files.

        Args:
            *file_paths: Variable number of paths to YAML files containing translations

        Raises:
            FileNotFoundError: If any file does not exist
            yaml.YAMLError: If any file is not valid YAML

        Examples:
            g.load_yaml_files("en.yaml", "es.yaml", "fr.yaml")
        """
        for file_path in file_paths:
            self.load_yaml(file_path)

    def translate(self, key: str, *args: Any, locale: Optional[str] = None, **kwargs: Any) -> str:
        """
        Translate a key to the current or specified locale.

        Supports both positional and keyword arguments for string interpolation.
        If the key is not found, it will still perform interpolation on the key itself.

        Args:
            key: The translation key (can contain format placeholders)
            *args: Positional arguments for format placeholders (e.g., {}, {0}, {1})
            locale: Optional locale to use (defaults to current_locale)
            **kwargs: Keyword arguments for format placeholders (e.g., {name}, {country})

        Returns:
            The translated and formatted string, or the formatted key if translation not found

        Examples:
            # Basic translation
            g.translate("hello")  # → "Hello"

            # With keyword arguments
            g.translate("welcome", name="John")  # → "Welcome, John!"

            # With positional arguments
            g.translate("greeting", "John", country="England")  # → "Hello John from England"

            # Mixed positional and keyword
            g.translate("message", "John", age=30)  # → "User John is 30 years old"

            # Fallback with interpolation (key not found)
            g.translate("Hello {name}", name="John")  # → "Hello John"
        """
        target_locale = locale or self.current_locale

        # Auto-load default locale configuration if not yet loaded and auto-loading is enabled
        # This handles the case where translate() is called with a locale that hasn't been used yet
        if self._auto_load_defaults and target_locale not in self._loaded_default_locales:
            self._load_default_locale(target_locale)

        # Determine count value for plural selection
        # Priority: 1) count kwarg, 2) first positional arg, 3) single kwarg value
        count_value = kwargs.get("count")
        if count_value is None:
            if args:
                count_value = args[0]
            elif len(kwargs) == 1:
                # If there's exactly one kwarg and it's not "count" or "locale", use its value
                count_value = next(iter(kwargs.values()))

        # Try to find translation in target locale
        if target_locale in self.translations and key in self.translations[target_locale]:
            translation = self.translations[target_locale][key]

            # Check if translation is a dict (plural forms)
            if isinstance(translation, dict):
                if count_value is not None:
                    # Select appropriate plural form based on count
                    # Only consider categories that exist in this translation
                    available_categories = set(translation.keys())
                    category = self._select_plural_form(count_value, target_locale, available_categories)
                    # Try selected category, fallback to "other"
                    translation = translation.get(category, translation.get("other", ""))
                else:
                    # No count provided, use "other"
                    translation = translation.get("other", "")

            # Get formatting configuration from target locale
            decimal_sep, thousand_sep = self._get_number_format(target_locale)
            date_formats = self._get_date_format(target_locale)
            time_formats = self._get_time_format(target_locale)
            datetime_formats = self._get_datetime_format(target_locale)
            month_names = self._get_month_names(target_locale)
            weekday_names = self._get_weekday_names(target_locale)
            formatter = LocaleFormatter(decimal_sep, thousand_sep, date_formats, time_formats, datetime_formats, month_names, weekday_names)

            # Ensure count is available for formatting if it was used for plural selection
            format_kwargs = kwargs.copy()
            if count_value is not None and "count" not in format_kwargs:
                format_kwargs["count"] = count_value

            if args or format_kwargs:
                return formatter.vformat(translation, args, format_kwargs)
            return translation

        # Fallback to default locale
        if target_locale != self.default_locale:
            if self.default_locale in self.translations and key in self.translations[self.default_locale]:
                translation = self.translations[self.default_locale][key]

                # Check if translation is a dict (plural forms)
                if isinstance(translation, dict):
                    if count_value is not None:
                        # Select appropriate plural form based on count
                        # Only consider categories that exist in this translation
                        available_categories = set(translation.keys())
                        category = self._select_plural_form(count_value, self.default_locale, available_categories)
                        # Try selected category, fallback to "other"
                        translation = translation.get(category, translation.get("other", ""))
                    else:
                        # No count provided, use "other"
                        translation = translation.get("other", "")

                # Use formatting from default locale when falling back
                decimal_sep, thousand_sep = self._get_number_format(self.default_locale)
                date_formats = self._get_date_format(self.default_locale)
                time_formats = self._get_time_format(self.default_locale)
                datetime_formats = self._get_datetime_format(self.default_locale)
                month_names = self._get_month_names(self.default_locale)
                weekday_names = self._get_weekday_names(self.default_locale)
                formatter = LocaleFormatter(decimal_sep, thousand_sep, date_formats, time_formats, datetime_formats, month_names, weekday_names)

                # Ensure count is available for formatting if it was used for plural selection
                format_kwargs = kwargs.copy()
                if count_value is not None and "count" not in format_kwargs:
                    format_kwargs["count"] = count_value

                if args or format_kwargs:
                    return formatter.vformat(translation, args, format_kwargs)
                return translation

        # Key not found - return key with interpolation applied
        # Use formatting from target locale for missing keys
        decimal_sep, thousand_sep = self._get_number_format(target_locale)
        date_formats = self._get_date_format(target_locale)
        time_formats = self._get_time_format(target_locale)
        datetime_formats = self._get_datetime_format(target_locale)
        month_names = self._get_month_names(target_locale)
        weekday_names = self._get_weekday_names(target_locale)
        formatter = LocaleFormatter(decimal_sep, thousand_sep, date_formats, time_formats, datetime_formats, month_names, weekday_names)

        # Ensure count is available for formatting
        format_kwargs = kwargs.copy()
        if count_value is not None and "count" not in format_kwargs:
            format_kwargs["count"] = count_value

        if args or format_kwargs:
            try:
                return formatter.vformat(key, args, format_kwargs)
            except (KeyError, IndexError, ValueError):
                # If formatting fails, return the key as-is
                return key
        return key

    def format_date(self, value: Union[datetime.date, datetime.datetime],
                    format_spec: str = "", locale: Optional[str] = None) -> str:
        """
        Format a date or datetime object using locale-specific formatting.

        This is a standalone formatting method that doesn't require translation keys.
        Use this when you need direct date formatting without going through the translation system.

        Args:
            value: The date or datetime object to format
            format_spec: Format specification - either a named style ("short", "long", "full")
                        or a custom format string using {YYYY}, {MM}, {DD}, etc.
            locale: Optional locale to use (defaults to current_locale)

        Returns:
            The formatted date string

        Examples:
            # Using named styles
            g.format_date(date(2025, 1, 9), "long", locale="en")  # → "January 9, 2025"
            g.format_date(date(2025, 1, 9), "long", locale="de")  # → "9. Januar 2025"

            # Using custom format strings
            g.format_date(date(2025, 1, 9), "{YYYY}-{MM}-{DD}", locale="en")  # → "2025-01-09"
            g.format_date(date(2025, 1, 9), "{monthname} {DD}", locale="fr")  # → "janvier 9"
        """
        target_locale = locale or self.current_locale

        # Auto-load defaults if needed
        if self._auto_load_defaults and target_locale not in self._loaded_default_locales:
            self._load_default_locale(target_locale)

        # Get locale-specific formatting configuration
        date_formats = self._get_date_format(target_locale)
        time_formats = self._get_time_format(target_locale)
        datetime_formats = self._get_datetime_format(target_locale)
        month_names = self._get_month_names(target_locale)
        weekday_names = self._get_weekday_names(target_locale)

        formatter = LocaleFormatter(".", ",", date_formats, time_formats, datetime_formats, month_names, weekday_names)
        return formatter._format_date(value, format_spec)

    def format_number(self, value: Union[int, float],
                      format_spec: str = "", locale: Optional[str] = None) -> str:
        """
        Format a number using locale-specific formatting.

        This is a standalone formatting method that doesn't require translation keys.
        Use this when you need direct number formatting without going through the translation system.

        Args:
            value: The numeric value to format
            format_spec: Format specification using Python's format spec mini-language
                        (e.g., ",.2f" for comma-separated with 2 decimal places)
            locale: Optional locale to use (defaults to current_locale)

        Returns:
            The formatted number string

        Examples:
            g.format_number(1234.56, ",.2f", locale="en")  # → "1,234.56"
            g.format_number(1234.56, ",.2f", locale="de")  # → "1.234,56"
            g.format_number(1234.56, ",.2f", locale="fr")  # → "1 234,56"
        """
        target_locale = locale or self.current_locale

        # Auto-load defaults if needed
        if self._auto_load_defaults and target_locale not in self._loaded_default_locales:
            self._load_default_locale(target_locale)

        # Get locale-specific number formatting
        decimal_sep, thousand_sep = self._get_number_format(target_locale)
        formatter = LocaleFormatter(decimal_sep, thousand_sep, {}, {}, {}, {}, {})

        return formatter.format_field(value, format_spec)

    def t(self, key: str, *args: Any, locale: Optional[str] = None, **kwargs: Any) -> str:
        """
        Shorthand for translate().

        Args:
            key: The translation key
            *args: Positional arguments for format placeholders
            locale: Optional locale to use
            **kwargs: Keyword arguments for format placeholders

        Returns:
            The translated string

        Examples:
            g.t("hello")  # → "Hello"
            g.t("welcome", name="Alice")  # → "Welcome, Alice!"
        """
        return self.translate(key, *args, locale=locale, **kwargs)


# Global instance for convenience
_default_gloser = Gloser()


def translate(key: str, *args: Any, locale: Optional[str] = None, **kwargs: Any) -> str:
    """
    Convenience function to translate using the default Gloser instance.

    Supports both positional and keyword arguments for string interpolation.

    Args:
        key: The translation key
        *args: Positional arguments for format placeholders
        locale: Optional locale to use
        **kwargs: Keyword arguments for format placeholders

    Returns:
        The translated string
    """
    return _default_gloser.translate(key, *args, locale=locale, **kwargs)
