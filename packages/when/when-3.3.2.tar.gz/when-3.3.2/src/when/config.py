"""
Format Specifiers:
+------+--------------------------------------------------------------------------+--------------------------+------+
| Spec | Replacement                                                              | Example                  | Note |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %a  | Abbreviated weekday name                                                 | Thu                      |  *   |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %A  | Full weekday name                                                        | Thursday                 |  *   |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %b  | Abbreviated month name                                                   | Aug                      |  *   |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %B  | Full month name                                                          | August                   |  *   |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %c  | Date and time representation                                             | Thu Aug 23 14:55:02 2001 |  *   |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %C  | Year divided by 100 and truncated to integer (00-99)                     | 20                       |  +   |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %d  | Day of the month, zero-padded (01-31)                                    | 23                       |      |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %D  | Short MM/DD/YY date, equivalent to %m/%d/%y                              | 08/23/01                 |  +   |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %e  | Day of the month, space-padded ( 1-31)                                   | 23                       |  +   |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %F  | Short YYYY-MM-DD date, equivalent to %Y-%m-%d                            | 2001-08-23               |  +   |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %g  | Week-based year, last two digits (00-99)                                 | 01                       |  +   |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %G  | Week-based year                                                          | 2001                     |  +   |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %h  | Abbreviated month name   (same as %b)                                    | Aug                      |  +*  |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %H  | Hour in 24h format (00-23)                                               | 14                       |      |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %I  | Hour in 12h format (01-12)                                               | 02                       |      |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %j  | Day of the year (001-366)                                                | 235                      |      |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %m  | Month as a decimal number (01-12)                                        | 08                       |      |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %M  | Minute (00-59)                                                           | 55                       |      |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %n  | New-line character                                                       | '\\n'                     |  +   |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %p  | AM or PM designation                                                     | PM                       |      |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %r  | 12-hour clock time                                                       | 02:55:02 pm              |  +*  |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %R  | 24-hour HH:MM time, equivalent to %H:%M                                  | 14:55                    |  +   |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %S  | Second (00-61)                                                           | 02                       |      |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %t  | Horizontal-tab character                                                 | '\\t'                     |  +   |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %T  | ISO 8601 time format (HH:MM:SS), equivalent to %H:%M:%S                  | 14:55:02                 |  +   |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %u  | ISO 8601 weekday as number with Monday as 1 (1-7)                        | 4                        |  +   |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %U  | Week number with the first Sunday as the first day of week one (00-53)   | 33                       |      |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %V  | ISO 8601 week number (01-53)                                             | 34                       |  +   |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %w  | Weekday as a decimal number with Sunday as 0 (0-6)                       | 4                        |      |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %W  | Week number with the first Monday as the first day of week one (00-53)   | 34                       |      |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %x  | Date representation                                                      | 08/23/01                 |  *   |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %X  | Time representation                                                      | 14:55:02                 |  *   |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %y  | Year, last two digits (00-99)                                            | 01                       |      |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %Y  | Year                                                                     | 2001                     |      |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %z  | ISO 8601 offset from UTC in timezone (1 minute=1, 1 hour=100). If        | +100                     |      |
|      | timezone cannot be determined, no characters                             |                          |      |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %Z  | Locale timezone name or abbreviation. If timezone cannot be determined,  | CDT                      |  *   |
|      | no characters                                                            |                          |      |
+------+--------------------------------------------------------------------------+--------------------------+------+
|  %%  | A % sign                                                                 | %                        |      |
+------+--------------------------------------------------------------------------+--------------------------+------+
| %!z  | When timezone name                                                       | US/New_York              |  !   |
+------+--------------------------------------------------------------------------+--------------------------+------+
| %!Z  | When timezone name, using conditional format in settings                 | US/New_York              |  !!  |
+------+--------------------------------------------------------------------------+--------------------------+------+
| %!c  | City name                                                                | Honolulu, Hawaii, US     |  !   |
+------+--------------------------------------------------------------------------+--------------------------+------+
| %!C  | City name, using conditional format in settings                          | Honolulu, Hawaii, US     |  !!  |
+------+--------------------------------------------------------------------------+--------------------------+------+
| %!l  | Lunar phase emoji                                                        | 🌖                       |  !   |
+------+--------------------------------------------------------------------------+--------------------------+------+

Notes:
* - Locale-dependent
+ - C99 extension
! - when extension
"""

import os
import sys
from pathlib import Path

import toml

FORMAT_SPECIFIERS = [
    ["%a", "Abbreviated weekday name", "Thu", "*"],
    ["%A", "Full weekday name", "Thursday", "*"],
    ["%b", "Abbreviated month name", "Aug", "*"],
    ["%B", "Full month name", "August", "*"],
    ["%c", "Date and time representation", "Thu Aug 23 14:55:02 2001", "*"],
    ["%C", "Year divided by 100 and truncated to integer (00-99)", "20", "+"],
    ["%d", "Day of the month, zero-padded (01-31)", "23", ""],
    ["%D", "Short MM/DD/YY date, equivalent to %m/%d/%y", "08/23/01", "+"],
    ["%e", "Day of the month, space-padded ( 1-31)", "23", "+"],
    ["%F", "Short YYYY-MM-DD date, equivalent to %Y-%m-%d", "2001-08-23", "+"],
    ["%g", "Week-based year, last two digits (00-99)", "01", "+"],
    ["%G", "Week-based year", "2001", "+"],
    ["%h", "Abbreviated month name   (same as %b)", "Aug", "+*"],
    ["%H", "Hour in 24h format (00-23)", "14", ""],
    ["%I", "Hour in 12h format (01-12)", "02", ""],
    ["%j", "Day of the year (001-366)", "235", ""],
    ["%m", "Month as a decimal number (01-12)", "08", ""],
    ["%M", "Minute (00-59)", "55", ""],
    ["%n", "New-line character ('\\n')", "", "+"],
    ["%p", "AM or PM designation", "PM", ""],
    ["%r", "12-hour clock time", "02:55:02 pm", "+*"],
    ["%R", "24-hour HH:MM time, equivalent to %H:%M", "14:55", "+"],
    ["%S", "Second (00-61)", "02", ""],
    ["%t", "Horizontal-tab character ('\\t')", "", "+"],
    ["%T", "ISO 8601 time format (HH:MM:SS), equivalent to %H:%M:%S", "14:55:02", "+"],
    ["%u", "ISO 8601 weekday as number with Monday as 1 (1-7)", "4", "+"],
    ["%U", "Week number with the first Sunday as the first day of week one (00-53)", "33", ""],
    ["%V", "ISO 8601 week number (01-53)", "34", "+"],
    ["%w", "Weekday as a decimal number with Sunday as 0 (0-6)", "4", ""],
    ["%W", "Week number with the first Monday as the first day of week one (00-53)", "34", ""],
    ["%x", "Date representation", "08/23/01", "*"],
    ["%X", "Time representation", "14:55:02", "*"],
    ["%y", "Year, last two digits (00-99)", "01", ""],
    ["%Y", "Year", "2001", ""],
    [
        "%z",
        "ISO 8601 offset from UTC in timezone (1 minute=1, 1 hour=100). "
        "If timezone cannot be determined, no characters",
        "+100",
        "",
    ],
    [
        "%Z",
        "Locale timezone name or abbreviation. If timezone cannot be determined, no characters",
        "CDT",
        "*",
    ],
    ["%%", "A % sign", "%", ""],
    ["%!z", "When timezone name", "US/New_York", "!"],
    ["%!Z", "When timezone name, using conditional format in settings", "US/New_York", "!!"],
    ["%!c", "City name", "Honolulu, Hawaii, US", "!"],
    ["%!C", "City name, using conditional format in settings", "Honolulu, Hawaii, US", "!!"],
    ["%!l", "Lunar phase emoji", "🌖", "!"],
]

DEFAULT_FORMAT = os.getenv("WHENFORMAT", "%F %T%z (%Z%!Z) %jd%Ww %!C[%!l]")
DEFAULT_TOML = f"""[calendar]
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

[holidays]
format = "%a, %b %d %Y"

[holidays.US]
# Relative to Easter
"Easter" = "Easter +0"
"Ash Wednesday" = "Easter -46"
"Mardi Gras" = "Easter -47"
"Palm Sunday" = "Easter -7"
"Good Friday" = "Easter -2"

# Floating holidays
"Memorial Day" = "Last Mon in May"
"MLK Day" = "3rd Mon in Jan"
"Presidents' Day" = "3rd Mon in Feb"
"Mother's Day" = "2nd Sun in May"
"Father's Day" = "3rd Sun in Jun"
"Labor" = "1st Mon in Sep"
"Columbus Day" = "2nd Mon in Oct"
"Thanksgiving" = "4th Thu in Nov"

# Fixed holidays
"New Year's Day" = "Jan 1"
"Valentine's Day" = "Feb 14"
"St. Patrick's Day" = "Mar 17"
"Juneteenth" = "Jun 19"
"Independence Day" = "Jul 4"
"Halloween" = "Oct 31"
"Veterans Day" = "Nov 11"
"Christmas" = "Dec 25"

[lunar]
phases = [
    "New Moon",
    "Waxing Crescent",
    "First Quarter",
    "Waxing Gibbous",
    "Full Moon",
    "Waning Gibbous",
    "Last Quarter",
    "Waning Crescent"
]
emojis = "🌑🌒🌓🌔🌕🌖🌗🌘"
format = "%a, %b %d %Y"

[formats.named]
default = "{DEFAULT_FORMAT}"
rfc2822 = "%a, %d %b %Y %H:%M:%S %z"
iso = "%Y-%m-%dT%H:%M:%S%z"

[formats.conditional]
Z = ", {{}}"
C = "({{}})"

[formats.source]
grouped = " ↳ @"
"""


class Settings:
    NAME = ".whenrc.toml"
    DIRS = [Path.cwd(), Path.home()]

    def __init__(self, name=None, dirs=None):
        self.name = name or self.NAME
        self.dirs = dirs or self.DIRS
        self.defaults = toml.loads(DEFAULT_TOML)
        self.data = self.defaults.copy()
        self.read_from = []
        for path in self.paths:
            self.read_path(path)

    def __getitem__(self, key):
        return self.data[key]

    def read_path(self, path):
        try:
            data = toml.load(path)
        except FileNotFoundError:
            pass
        else:
            try:
                result = Settings.overlay(self.data, data)
            except Exception as why:
                print(f"Unable to import settings file {path}, skipping:", file=sys.stderr)
                print(f"{why}", file=sys.stderr)
            else:
                self.data = result
                self.read_from.append(path)

    @property
    def paths(self):
        return [pth / self.name for pth in self.dirs]

    def write_text(self):
        text = ""
        if self.read_from:
            text = "# Read from {}\n".format(",".join(str(s) for s in self.read_from))

        out = toml.dumps(self.data)
        return f"{text}{out}"

    @staticmethod
    def overlay(first, other):
        if not isinstance(other, dict):
            return first

        keys = set([*first.keys(), *other.keys()])
        result = {}
        for key in keys:
            if key not in other:
                result[key] = first[key]
                continue

            if key not in first:
                result[key] = other[key]
                continue

            if isinstance(first[key], dict):
                result[key] = Settings.overlay(first[key], other[key])
                continue

            result[key] = other[key]

        return result
