"""Google Play Store constants for categories and collections.

Based on google-play-scraper constants:
https://github.com/facundoolano/google-play-scraper/blob/main/lib/constants.js
"""

from enum import Enum


class Category(str, Enum):
    """App categories on Google Play Store."""

    def __str__(self) -> str:
        """Return the enum value as string for string formatting."""
        return self.value

    # Games
    GAME = "GAME"
    GAME_ACTION = "GAME_ACTION"
    GAME_ADVENTURE = "GAME_ADVENTURE"
    GAME_ARCADE = "GAME_ARCADE"
    GAME_BOARD = "GAME_BOARD"
    GAME_CARD = "GAME_CARD"
    GAME_CASINO = "GAME_CASINO"
    GAME_CASUAL = "GAME_CASUAL"
    GAME_EDUCATIONAL = "GAME_EDUCATIONAL"
    GAME_MUSIC = "GAME_MUSIC"
    GAME_PUZZLE = "GAME_PUZZLE"
    GAME_RACING = "GAME_RACING"
    GAME_ROLE_PLAYING = "GAME_ROLE_PLAYING"
    GAME_SIMULATION = "GAME_SIMULATION"
    GAME_SPORTS = "GAME_SPORTS"
    GAME_STRATEGY = "GAME_STRATEGY"
    GAME_TRIVIA = "GAME_TRIVIA"
    GAME_WORD = "GAME_WORD"

    # Family
    FAMILY = "FAMILY"
    FAMILY_ACTION = "FAMILY_ACTION"
    FAMILY_BRAINGAMES = "FAMILY_BRAINGAMES"
    FAMILY_CREATE = "FAMILY_CREATE"
    FAMILY_EDUCATION = "FAMILY_EDUCATION"
    FAMILY_MUSICVIDEO = "FAMILY_MUSICVIDEO"
    FAMILY_PRETEND = "FAMILY_PRETEND"

    # Apps
    APPLICATION = "APPLICATION"
    ART_AND_DESIGN = "ART_AND_DESIGN"
    AUTO_AND_VEHICLES = "AUTO_AND_VEHICLES"
    BEAUTY = "BEAUTY"
    BOOKS_AND_REFERENCE = "BOOKS_AND_REFERENCE"
    BUSINESS = "BUSINESS"
    COMICS = "COMICS"
    COMMUNICATION = "COMMUNICATION"
    DATING = "DATING"
    EDUCATION = "EDUCATION"
    ENTERTAINMENT = "ENTERTAINMENT"
    EVENTS = "EVENTS"
    FINANCE = "FINANCE"
    FOOD_AND_DRINK = "FOOD_AND_DRINK"
    HEALTH_AND_FITNESS = "HEALTH_AND_FITNESS"
    HOUSE_AND_HOME = "HOUSE_AND_HOME"
    LIBRARIES_AND_DEMO = "LIBRARIES_AND_DEMO"
    LIFESTYLE = "LIFESTYLE"
    MAPS_AND_NAVIGATION = "MAPS_AND_NAVIGATION"
    MEDICAL = "MEDICAL"
    MUSIC_AND_AUDIO = "MUSIC_AND_AUDIO"
    NEWS_AND_MAGAZINES = "NEWS_AND_MAGAZINES"
    PARENTING = "PARENTING"
    PERSONALIZATION = "PERSONALIZATION"
    PHOTOGRAPHY = "PHOTOGRAPHY"
    PRODUCTIVITY = "PRODUCTIVITY"
    SHOPPING = "SHOPPING"
    SOCIAL = "SOCIAL"
    SPORTS = "SPORTS"
    TOOLS = "TOOLS"
    TRAVEL_AND_LOCAL = "TRAVEL_AND_LOCAL"
    VIDEO_PLAYERS = "VIDEO_PLAYERS"
    WEATHER = "WEATHER"


class Collection(str, Enum):
    """App collections/rankings on Google Play Store."""

    def __str__(self) -> str:
        """Return the enum value as string for string formatting."""
        return self.value

    TOP_FREE = "topselling_free"
    TOP_PAID = "topselling_paid"
    TOP_GROSSING = "topgrossing"
    TOP_NEW_FREE = "topselling_new_free"
    TOP_NEW_PAID = "topselling_new_paid"
    MOVERS_SHAKERS = "movers_shakers"


class Age(str, Enum):
    """Age ranges for family apps."""

    FIVE_UNDER = "AGE_RANGE1"
    SIX_EIGHT = "AGE_RANGE2"
    NINE_UP = "AGE_RANGE3"


class Country:
    """Country information for Google Play Store.

    Attributes:
        code: Two-letter country code (e.g., "us", "kr")
        name: Full country name
        currency: Currency code (e.g., "USD", "KRW")

    """

    def __init__(self, code: str, name: str, currency: str) -> None:
        self.code = code
        self.name = name
        self.currency = currency

    def __repr__(self) -> str:
        return f"Country(code='{self.code}', name='{self.name}', currency='{self.currency}')"

    def __str__(self) -> str:
        return f"{self.name} ({self.code}) - {self.currency}"


# List of countries supported by Google Play Store
# Based on comprehensive verification (247 verified countries)
# Verified on: 2025-10-13
# Excluded: North Korea (KP), Syria (SY) - restricted access
COUNTRIES = [
    # North America
    Country("us", "United States", "USD"),
    Country("ca", "Canada", "CAD"),
    Country("mx", "Mexico", "MXN"),
    # Central America
    Country("gt", "Guatemala", "GTQ"),
    Country("hn", "Honduras", "HNL"),
    Country("sv", "El Salvador", "USD"),
    Country("ni", "Nicaragua", "NIO"),
    Country("cr", "Costa Rica", "CRC"),
    Country("pa", "Panama", "PAB"),
    Country("bz", "Belize", "BZD"),
    # Caribbean
    Country("cu", "Cuba", "CUP"),
    Country("jm", "Jamaica", "JMD"),
    Country("do", "Dominican Republic", "DOP"),
    Country("ht", "Haiti", "HTG"),
    Country("tt", "Trinidad and Tobago", "TTD"),
    Country("bb", "Barbados", "BBD"),
    Country("bs", "Bahamas", "BSD"),
    Country("pr", "Puerto Rico", "USD"),
    Country("ai", "Anguilla", "XCD"),
    Country("ag", "Antigua and Barbuda", "XCD"),
    Country("aw", "Aruba", "AWG"),
    Country("bm", "Bermuda", "BMD"),
    Country("bq", "Caribbean Netherlands", "USD"),
    Country("ky", "Cayman Islands", "KYD"),
    Country("cw", "Curaçao", "ANG"),
    Country("dm", "Dominica", "XCD"),
    Country("gd", "Grenada", "XCD"),
    Country("gp", "Guadeloupe", "EUR"),
    Country("mq", "Martinique", "EUR"),
    Country("ms", "Montserrat", "XCD"),
    Country("bl", "Saint Barthélemy", "EUR"),
    Country("kn", "Saint Kitts and Nevis", "XCD"),
    Country("lc", "Saint Lucia", "XCD"),
    Country("mf", "Saint Martin", "EUR"),
    Country("pm", "Saint Pierre and Miquelon", "EUR"),
    Country("vc", "Saint Vincent and the Grenadines", "XCD"),
    Country("sx", "Sint Maarten", "ANG"),
    Country("tc", "Turks and Caicos Islands", "USD"),
    Country("vg", "British Virgin Islands", "USD"),
    Country("vi", "U.S. Virgin Islands", "USD"),
    # South America
    Country("br", "Brazil", "BRL"),
    Country("ar", "Argentina", "ARS"),
    Country("cl", "Chile", "CLP"),
    Country("co", "Colombia", "COP"),
    Country("pe", "Peru", "PEN"),
    Country("ve", "Venezuela", "VES"),
    Country("ec", "Ecuador", "USD"),
    Country("bo", "Bolivia", "BOB"),
    Country("py", "Paraguay", "PYG"),
    Country("uy", "Uruguay", "UYU"),
    Country("gy", "Guyana", "GYD"),
    Country("sr", "Suriname", "SRD"),
    Country("gf", "French Guiana", "EUR"),
    Country("fk", "Falkland Islands", "FKP"),
    # Western Europe
    Country("gb", "United Kingdom", "GBP"),
    Country("de", "Germany", "EUR"),
    Country("fr", "France", "EUR"),
    Country("es", "Spain", "EUR"),
    Country("it", "Italy", "EUR"),
    Country("nl", "Netherlands", "EUR"),
    Country("be", "Belgium", "EUR"),
    Country("at", "Austria", "EUR"),
    Country("ch", "Switzerland", "CHF"),
    Country("ie", "Ireland", "EUR"),
    Country("pt", "Portugal", "EUR"),
    Country("lu", "Luxembourg", "EUR"),
    Country("mc", "Monaco", "EUR"),
    Country("li", "Liechtenstein", "CHF"),
    Country("ad", "Andorra", "EUR"),
    Country("sm", "San Marino", "EUR"),
    Country("va", "Vatican City", "EUR"),
    Country("gi", "Gibraltar", "GIP"),
    # Northern Europe
    Country("se", "Sweden", "SEK"),
    Country("no", "Norway", "NOK"),
    Country("dk", "Denmark", "DKK"),
    Country("fi", "Finland", "EUR"),
    Country("is", "Iceland", "ISK"),
    Country("fo", "Faroe Islands", "DKK"),
    Country("ax", "Åland Islands", "EUR"),
    # Eastern Europe
    Country("pl", "Poland", "PLN"),
    Country("cz", "Czech Republic", "CZK"),
    Country("hu", "Hungary", "HUF"),
    Country("ro", "Romania", "RON"),
    Country("bg", "Bulgaria", "BGN"),
    Country("sk", "Slovakia", "EUR"),
    Country("si", "Slovenia", "EUR"),
    Country("hr", "Croatia", "EUR"),
    Country("ee", "Estonia", "EUR"),
    Country("lv", "Latvia", "EUR"),
    Country("lt", "Lithuania", "EUR"),
    Country("rs", "Serbia", "RSD"),
    Country("ua", "Ukraine", "UAH"),
    Country("by", "Belarus", "BYN"),
    Country("md", "Moldova", "MDL"),
    # Southern Europe
    Country("gr", "Greece", "EUR"),
    Country("cy", "Cyprus", "EUR"),
    Country("mt", "Malta", "EUR"),
    Country("al", "Albania", "ALL"),
    Country("mk", "North Macedonia", "MKD"),
    Country("ba", "Bosnia and Herzegovina", "BAM"),
    Country("me", "Montenegro", "EUR"),
    Country("xk", "Kosovo", "EUR"),
    # British Isles
    Country("im", "Isle of Man", "GBP"),
    Country("je", "Jersey", "GBP"),
    Country("gg", "Guernsey", "GBP"),
    # East Asia
    Country("jp", "Japan", "JPY"),
    Country("kr", "South Korea", "KRW"),
    Country("cn", "China", "CNY"),
    Country("hk", "Hong Kong", "HKD"),
    Country("tw", "Taiwan", "TWD"),
    Country("mo", "Macao", "MOP"),
    Country("mn", "Mongolia", "MNT"),
    # Southeast Asia
    Country("sg", "Singapore", "SGD"),
    Country("my", "Malaysia", "MYR"),
    Country("th", "Thailand", "THB"),
    Country("id", "Indonesia", "IDR"),
    Country("ph", "Philippines", "PHP"),
    Country("vn", "Vietnam", "VND"),
    Country("mm", "Myanmar", "MMK"),
    Country("kh", "Cambodia", "KHR"),
    Country("la", "Laos", "LAK"),
    Country("bn", "Brunei", "BND"),
    Country("tl", "Timor-Leste", "USD"),
    # South Asia
    Country("in", "India", "INR"),
    Country("pk", "Pakistan", "PKR"),
    Country("bd", "Bangladesh", "BDT"),
    Country("lk", "Sri Lanka", "LKR"),
    Country("np", "Nepal", "NPR"),
    Country("bt", "Bhutan", "BTN"),
    Country("mv", "Maldives", "MVR"),
    # Central Asia
    Country("kz", "Kazakhstan", "KZT"),
    Country("uz", "Uzbekistan", "UZS"),
    Country("kg", "Kyrgyzstan", "KGS"),
    Country("tj", "Tajikistan", "TJS"),
    Country("tm", "Turkmenistan", "TMT"),
    # Middle East
    Country("af", "Afghanistan", "AFN"),
    Country("tr", "Turkey", "TRY"),
    Country("il", "Israel", "ILS"),
    Country("sa", "Saudi Arabia", "SAR"),
    Country("ae", "United Arab Emirates", "AED"),
    Country("qa", "Qatar", "QAR"),
    Country("kw", "Kuwait", "KWD"),
    Country("bh", "Bahrain", "BHD"),
    Country("om", "Oman", "OMR"),
    Country("jo", "Jordan", "JOD"),
    Country("lb", "Lebanon", "LBP"),
    Country("iq", "Iraq", "IQD"),
    Country("ye", "Yemen", "YER"),
    Country("ps", "Palestine", "ILS"),
    Country("ir", "Iran", "IRR"),
    # Caucasus
    Country("ge", "Georgia", "GEL"),
    Country("am", "Armenia", "AMD"),
    Country("az", "Azerbaijan", "AZN"),
    # Russia
    Country("ru", "Russia", "RUB"),
    # North Africa
    Country("eg", "Egypt", "EGP"),
    Country("ma", "Morocco", "MAD"),
    Country("dz", "Algeria", "DZD"),
    Country("tn", "Tunisia", "TND"),
    Country("ly", "Libya", "LYD"),
    Country("sd", "Sudan", "SDG"),
    Country("ss", "South Sudan", "SSP"),
    # West Africa
    Country("ng", "Nigeria", "NGN"),
    Country("gh", "Ghana", "GHS"),
    Country("ci", "Côte d'Ivoire", "XOF"),
    Country("sn", "Senegal", "XOF"),
    Country("ml", "Mali", "XOF"),
    Country("bf", "Burkina Faso", "XOF"),
    Country("ne", "Niger", "XOF"),
    Country("gn", "Guinea", "GNF"),
    Country("sl", "Sierra Leone", "SLE"),
    Country("lr", "Liberia", "LRD"),
    Country("gm", "Gambia", "GMD"),
    Country("bj", "Benin", "XOF"),
    Country("tg", "Togo", "XOF"),
    Country("mr", "Mauritania", "MRU"),
    Country("gw", "Guinea-Bissau", "XOF"),
    Country("cv", "Cape Verde", "CVE"),
    Country("st", "São Tomé and Príncipe", "STN"),
    Country("gq", "Equatorial Guinea", "XAF"),
    # East Africa
    Country("ke", "Kenya", "KES"),
    Country("tz", "Tanzania", "TZS"),
    Country("ug", "Uganda", "UGX"),
    Country("et", "Ethiopia", "ETB"),
    Country("so", "Somalia", "SOS"),
    Country("rw", "Rwanda", "RWF"),
    Country("bi", "Burundi", "BIF"),
    Country("dj", "Djibouti", "DJF"),
    Country("er", "Eritrea", "ERN"),
    # Southern Africa
    Country("za", "South Africa", "ZAR"),
    Country("zw", "Zimbabwe", "ZWL"),
    Country("bw", "Botswana", "BWP"),
    Country("na", "Namibia", "NAD"),
    Country("mz", "Mozambique", "MZN"),
    Country("zm", "Zambia", "ZMW"),
    Country("mw", "Malawi", "MWK"),
    Country("ls", "Lesotho", "LSL"),
    Country("sz", "Eswatini", "SZL"),
    Country("ao", "Angola", "AOA"),
    # Central Africa
    Country("cm", "Cameroon", "XAF"),
    Country("cd", "DR Congo", "CDF"),
    Country("cg", "Congo", "XAF"),
    Country("ga", "Gabon", "XAF"),
    Country("cf", "Central African Republic", "XAF"),
    Country("td", "Chad", "XAF"),
    # Indian Ocean
    Country("mu", "Mauritius", "MUR"),
    Country("sc", "Seychelles", "SCR"),
    Country("yt", "Mayotte", "EUR"),
    Country("re", "Réunion", "EUR"),
    Country("km", "Comoros", "KMF"),
    Country("mg", "Madagascar", "MGA"),
    # Australia & New Zealand
    Country("au", "Australia", "AUD"),
    Country("nz", "New Zealand", "NZD"),
    # Pacific Islands
    Country("fj", "Fiji", "FJD"),
    Country("pg", "Papua New Guinea", "PGK"),
    Country("nc", "New Caledonia", "XPF"),
    Country("pf", "French Polynesia", "XPF"),
    Country("vu", "Vanuatu", "VUV"),
    Country("ws", "Samoa", "WST"),
    Country("to", "Tonga", "TOP"),
    Country("sb", "Solomon Islands", "SBD"),
    Country("gu", "Guam", "USD"),
    Country("as", "American Samoa", "USD"),
    Country("mp", "Northern Mariana Islands", "USD"),
    Country("pw", "Palau", "USD"),
    Country("fm", "Micronesia", "USD"),
    Country("mh", "Marshall Islands", "USD"),
    Country("ki", "Kiribati", "AUD"),
    Country("nr", "Nauru", "AUD"),
    Country("tv", "Tuvalu", "AUD"),
    Country("ck", "Cook Islands", "NZD"),
    Country("nu", "Niue", "NZD"),
    Country("tk", "Tokelau", "NZD"),
    Country("pn", "Pitcairn Islands", "NZD"),
    Country("nf", "Norfolk Island", "AUD"),
    Country("wf", "Wallis and Futuna", "XPF"),
    Country("um", "U.S. Minor Outlying Islands", "USD"),
    # Greenland
    Country("gl", "Greenland", "DKK"),
    # Antarctica
    Country("aq", "Antarctica", "USD"),
    # Remote Territories
    Country("bv", "Bouvet Island", "NOK"),
    Country("tf", "French Southern Territories", "EUR"),
    Country("hm", "Heard Island and McDonald Islands", "AUD"),
    Country("gs", "South Georgia and South Sandwich Islands", "GBP"),
    Country("io", "British Indian Ocean Territory", "USD"),
    Country("cc", "Cocos Islands", "AUD"),
    Country("cx", "Christmas Island", "AUD"),
    Country("sh", "Saint Helena", "SHP"),
    Country("ta", "Tristan da Cunha", "GBP"),
]

# Unique regions for optimized scraping
# Based on store uniqueness verification (2025-10-13)
# These 93 regions represent all unique Google Play Stores
# Countries with identical scores share the same regional store
UNIQUE_REGION_CODES = [
    "vu",
    "cf",
    "sz",
    "fm",
    "gr",
    "dz",
    "ma",
    "by",
    "eg",
    "ua",
    "ru",
    "cr",
    "rs",
    "az",
    "nz",
    "ni",
    "au",
    "ge",
    "sv",
    "ir",
    "ps",
    "ye",
    "bg",
    "iq",
    "ro",
    "lb",
    "hu",
    "jo",
    "cz",
    "om",
    "pl",
    "ae",
    "sa",
    "il",
    "no",
    "tr",
    "se",
    "kg",
    "uz",
    "pa",
    "kz",
    "za",
    "us",
    "pt",
    "np",
    "ie",
    "lk",
    "ch",
    "bd",
    "at",
    "do",
    "pk",
    "be",
    "in",
    "nl",
    "it",
    "es",
    "la",
    "fr",
    "ke",
    "kh",
    "de",
    "mx",
    "mm",
    "gb",
    "vn",
    "ph",
    "ca",
    "id",
    "th",
    "my",
    "uy",
    "sg",
    "py",
    "bo",
    "ec",
    "tw",
    "ve",
    "hk",
    "pe",
    "co",
    "kr",
    "cl",
    "jp",
    "ar",
    "br",
    "sn",
    "gh",
    "hn",
    "ng",
    "ly",
    "gt",
    "tn",
]

# Region mapping: country_code -> representative_country
# Countries mapped to the same representative share the same Play Store
REGION_MAPPING = {
    # Largest group (138 countries) - mapped to 'vu'
    "vu": "vu",
    "md": "vu",
    "mq": "vu",
    "gp": "vu",
    "bm": "vu",
    "nc": "vu",
    "gd": "vu",
    "pg": "vu",
    "dm": "vu",
    "fj": "vu",
    "lt": "vu",
    "cw": "vu",
    "am": "vu",
    "lv": "vu",
    "ms": "vu",
    "ee": "vu",
    "ky": "vu",
    "mg": "vu",
    "hr": "vu",
    "pm": "vu",
    "tt": "vu",
    "km": "vu",
    "si": "vu",
    "bq": "vu",
    "re": "vu",
    "sk": "vu",
    "yt": "vu",
    "sc": "vu",
    "mu": "vu",
    "td": "vu",
    "bh": "vu",
    "ax": "vu",
    "cg": "vu",
    "kw": "vu",
    "fo": "vu",
    "cd": "vu",
    "qa": "vu",
    "is": "vu",
    "cm": "vu",
    "fi": "vu",
    "ao": "vu",
    "dk": "vu",
    "ls": "vu",
    "af": "vu",
    "gi": "vu",
    "bz": "vu",
    "mw": "vu",
    "tm": "vu",
    "va": "vu",
    "zm": "vu",
    "tj": "vu",
    "sm": "vu",
    "mz": "vu",
    "na": "vu",
    "jm": "vu",
    "bw": "vu",
    "mc": "vu",
    "zw": "vu",
    "lu": "vu",
    "bt": "vu",
    "er": "vu",
    "dj": "vu",
    "bi": "vu",
    "rw": "vu",
    "tl": "vu",
    "ug": "vu",
    "tz": "vu",
    "gq": "vu",
    "st": "vu",
    "fk": "vu",
    "tf": "vu",
    "cv": "vu",
    "gf": "vu",
    "gw": "vu",
    "sr": "vu",
    "mr": "vu",
    "gy": "vu",
    "gl": "vu",
    "tg": "vu",
    "bj": "vu",
    "mn": "vu",
    "bs": "vu",
    "nf": "vu",
    "gm": "vu",
    "lr": "vu",
    "bb": "vu",
    "nu": "vu",
    "sl": "vu",
    "cn": "vu",
    "ck": "vu",
    "gn": "vu",
    "nr": "vu",
    "bf": "vu",
    "ml": "vu",
    "je": "vu",
    "vi": "vu",
    "mh": "vu",
    "im": "vu",
    "ci": "vu",
    "me": "vu",
    "sx": "vu",
    "ba": "vu",
    "ai": "vu",
    "aw": "vu",
    "mf": "vu",
    "as": "vu",
    "mk": "vu",
    "sd": "vu",
    "al": "vu",
    "lc": "vu",
    "pr": "vu",
    "ag": "vu",
    "mt": "vu",
    "kn": "vu",
    "bl": "vu",
    "to": "vu",
    "cy": "vu",
    "pf": "vu",
    "ga": "vu",
    "tv": "vu",
    "ws": "vu",
    "mp": "vu",
    "pw": "vu",
    "sb": "vu",
    "aq": "vu",
    "um": "vu",
    "io": "vu",
    "cx": "vu",
    "wf": "vu",
    "gs": "vu",
    "tk": "vu",
    "bv": "vu",
    "sh": "vu",
    "ta": "vu",
    "gu": "vu",
    "cc": "vu",
    "hm": "vu",
    "pn": "vu",
    # Second group (12 countries) - mapped to 'cf'
    "cf": "cf",
    "li": "cf",
    "cu": "cf",
    "so": "cf",
    "et": "cf",
    "bn": "cf",
    "mo": "cf",
    "gg": "cf",
    "xk": "cf",
    "tc": "cf",
    "vc": "cf",
    "ss": "cf",
    # Third group (6 countries) - mapped to 'sz'
    "sz": "sz",
    "ad": "sz",
    "mv": "sz",
    "ht": "sz",
    "ne": "sz",
    "vg": "sz",
    # Fourth group (2 countries) - mapped to 'fm'
    "fm": "fm",
    "ki": "fm",
    # Unique regions (89 countries) - map to themselves
    "gr": "gr",
    "dz": "dz",
    "ma": "ma",
    "by": "by",
    "eg": "eg",
    "ua": "ua",
    "ru": "ru",
    "cr": "cr",
    "rs": "rs",
    "az": "az",
    "nz": "nz",
    "ni": "ni",
    "au": "au",
    "ge": "ge",
    "sv": "sv",
    "ir": "ir",
    "ps": "ps",
    "ye": "ye",
    "bg": "bg",
    "iq": "iq",
    "ro": "ro",
    "lb": "lb",
    "hu": "hu",
    "jo": "jo",
    "cz": "cz",
    "om": "om",
    "pl": "pl",
    "ae": "ae",
    "sa": "sa",
    "il": "il",
    "no": "no",
    "tr": "tr",
    "se": "se",
    "kg": "kg",
    "uz": "uz",
    "pa": "pa",
    "kz": "kz",
    "za": "za",
    "us": "us",
    "pt": "pt",
    "np": "np",
    "ie": "ie",
    "lk": "lk",
    "ch": "ch",
    "bd": "bd",
    "at": "at",
    "do": "do",
    "pk": "pk",
    "be": "be",
    "in": "in",
    "nl": "nl",
    "it": "it",
    "es": "es",
    "la": "la",
    "fr": "fr",
    "ke": "ke",
    "kh": "kh",
    "de": "de",
    "mx": "mx",
    "mm": "mm",
    "gb": "gb",
    "vn": "vn",
    "ph": "ph",
    "ca": "ca",
    "id": "id",
    "th": "th",
    "my": "my",
    "uy": "uy",
    "sg": "sg",
    "py": "py",
    "bo": "bo",
    "ec": "ec",
    "tw": "tw",
    "ve": "ve",
    "hk": "hk",
    "pe": "pe",
    "co": "co",
    "kr": "kr",
    "cl": "cl",
    "jp": "jp",
    "ar": "ar",
    "br": "br",
    "sn": "sn",
    "gh": "gh",
    "hn": "hn",
    "ng": "ng",
    "ly": "ly",
    "gt": "gt",
    "tn": "tn",
}


def get_countries() -> list[Country]:
    """Get list of all supported countries.

    Returns:
        list[Country]: List of Country objects with code, name, and currency

    Examples:
        >>> from playfast.constants import get_countries
        >>> countries = get_countries()
        >>> len(countries)
        247
        >>> countries[0].code
        'us'
        >>> countries[0].name
        'United States'

    """
    return COUNTRIES.copy()


def get_country_by_code(code: str) -> Country | None:
    """Get country information by country code.

    Args:
        code: Two-letter country code (e.g., "us", "kr")

    Returns:
        Country | None: Country object if found, None otherwise

    Examples:
        >>> from playfast.constants import get_country_by_code
        >>> country = get_country_by_code("kr")
        >>> print(country)
        South Korea (kr) - KRW

    """
    code_lower = code.lower()
    for country in COUNTRIES:
        if country.code == code_lower:
            return country
    return None


def get_unique_countries() -> list[Country]:
    """Get list of unique region countries for optimized scraping.

    Returns only the 93 representative countries that have unique Play Store data.
    Use this instead of get_countries() when you want to scrape efficiently without
    redundant API calls.

    Returns:
        list[Country]: List of 93 Country objects representing unique regions

    Examples:
        >>> from playfast.constants import get_unique_countries
        >>> unique_countries = get_unique_countries()
        >>> len(unique_countries)
        93
        >>> # All returned countries should have code in UNIQUE_REGION_CODES
        >>> from playfast.constants import UNIQUE_REGION_CODES
        >>> all(c.code in UNIQUE_REGION_CODES for c in unique_countries)
        True

    """
    return [c for c in COUNTRIES if c.code in UNIQUE_REGION_CODES]


def get_representative_country(code: str) -> str:
    """Get the representative country code for a given country.

    Countries that share the same Play Store are mapped to a single representative.
    Use this to determine which country to scrape when you need data for a specific country.

    Args:
        code: Two-letter country code (e.g., "fi", "dk")

    Returns:
        str: Representative country code (e.g., "vu" for Finland and Denmark)

    Examples:
        >>> from playfast.constants import get_representative_country
        >>> get_representative_country("fi")
        'vu'
        >>> get_representative_country("us")
        'us'
        >>> # Finland (fi) and Denmark (dk) share the same store as Vanuatu (vu)
        >>> get_representative_country("dk")
        'vu'

    """
    code_lower = code.lower()
    return REGION_MAPPING.get(code_lower, code_lower)


def is_unique_region(code: str) -> bool:
    """Check if a country code represents a unique Play Store region.

    Args:
        code: Two-letter country code (e.g., "us", "kr")

    Returns:
        bool: True if the country has a unique Play Store, False if it shares with others

    Examples:
        >>> from playfast.constants import is_unique_region
        >>> is_unique_region("us")
        True
        >>> is_unique_region("fi")
        False
        >>> # US has a unique store, Finland shares with others

    """
    code_lower = code.lower()
    return code_lower in UNIQUE_REGION_CODES


def get_countries_in_region(representative_code: str) -> list[Country]:
    """Get all countries that share the same Play Store region.

    Args:
        representative_code: Representative country code (e.g., "vu", "us")

    Returns:
        list[Country]: List of countries in the same region

    Examples:
        >>> from playfast.constants import get_countries_in_region
        >>> # Get all countries that share Vanuatu's store
        >>> vu_countries = get_countries_in_region("vu")
        >>> len(vu_countries)
        138
        >>> # US has its own unique store
        >>> us_countries = get_countries_in_region("us")
        >>> len(us_countries)
        1

    """
    rep_lower = representative_code.lower()
    country_codes = [code for code, rep in REGION_MAPPING.items() if rep == rep_lower]
    return [c for c in COUNTRIES if c.code in country_codes]


# For backward compatibility and convenience
category = Category
collection = Collection
age = Age


__all__ = [
    # Enums
    "Category",
    "Collection",
    "Age",
    # Classes
    "Country",
    # Constants
    "COUNTRIES",
    "UNIQUE_REGION_CODES",
    "REGION_MAPPING",
    # Functions - All countries
    "get_countries",
    "get_country_by_code",
    # Functions - Unique regions (optimized)
    "get_unique_countries",
    "get_representative_country",
    "is_unique_region",
    "get_countries_in_region",
    # Aliases
    "category",
    "collection",
    "age",
]
