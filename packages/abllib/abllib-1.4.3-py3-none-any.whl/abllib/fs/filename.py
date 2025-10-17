"""A module containing file name-modification functions."""

from abllib.error import MissingRequiredModuleError, WrongTypeError
from abllib.general import try_import_module
from abllib.log import get_logger

pykakasi = try_import_module("pykakasi")

logger = get_logger("sanitize")

CHARS_TO_REMOVE = "',#^?!\"<>%$%°*"
CHARS_TO_REPLACE = " /\\|~+:;@\n"

def sanitize(filename: str) -> str:
    """
    Return a sanitized version of the file name, which replaces/removes all invalid symbols.

    Additionally, all spaces are replaced with underscores.
    """

    if not isinstance(filename, str):
        raise WrongTypeError.with_values(filename, str)

    filename = filename.strip(" ")

    # remove trailing chars
    filename = filename.strip(CHARS_TO_REPLACE)

    filename = _sanitize_letters(filename)

    filename = _sanitize_punctuations(filename)

    filename = _sanitize_symbols(filename)

    return filename

def _sanitize_letters(filename: str) -> str:
    """convert invalid letters"""

    # german Umlaute
    # https://en.wikipedia.org/wiki/Umlaut_(diacritic)
    filename = filename.replace("ä", "a")
    filename = filename.replace("Ä", "A")
    filename = filename.replace("ö", "o")
    filename = filename.replace("Ö", "O")
    filename = filename.replace("ü", "u")
    filename = filename.replace("Ü", "U")
    filename = filename.replace("ß", "ss")

    # japanese characters
    if _contains_japanese_char(filename):
        if pykakasi is not None:
            filename = _replace_japanese_chars(filename)
        else:
            logger.warning("to properly transliterate japanese text to rōmaji, "
                           "you need to install the optional dependency 'pykakasi'")

    return filename

def _sanitize_punctuations(filename: str) -> str:
    """make punctuation marks readable"""

    # to make sentences seem reasonable
    filename = filename.replace(", ", "_")
    filename = filename.replace(". ", "_")
    filename = filename.replace("! ", "_")
    filename = filename.replace("? ", "_")
    filename = filename.replace("; ", "_")
    filename = filename.replace(": ", "_")
    filename = filename.replace(" \n", "_")

    # fix sentences ending in a dot
    filename = filename.replace("..", ".")

    return filename

def _sanitize_symbols(filename: str) -> str:
    """remove/replace invalid symbols"""

    for char in CHARS_TO_REMOVE:
        filename = filename.replace(char, "")

    for char in CHARS_TO_REPLACE:
        filename = filename.replace(char, "_")

    # remove leftover non-ascii characters
    filename = filename.encode('ascii', 'ignore').decode()

    return filename

# original code from here:
# https://stackoverflow.com/a/30070664/15436169
japanese_char_ranges = [
    {"from": ord("\u3300"), "to": ord("\u33ff")},         # compatibility ideographs
    {"from": ord("\ufe30"), "to": ord("\ufe4f")},         # compatibility ideographs
    {"from": ord("\uf900"), "to": ord("\ufaff")},         # compatibility ideographs
    {"from": ord("\U0002F800"), "to": ord("\U0002fa1f")}, # compatibility ideographs
    {"from": ord("\u3040"), "to": ord("\u309f")},         # Japanese Hiragana
    {"from": ord("\u30a0"), "to": ord("\u30ff")},         # Japanese Katakana
    {"from": ord("\u2e80"), "to": ord("\u2eff")},         # cjk radicals supplement
    {"from": ord("\u4e00"), "to": ord("\u9fff")},
    {"from": ord("\u3400"), "to": ord("\u4dbf")},
    {"from": ord("\U00020000"), "to": ord("\U0002a6df")},
    {"from": ord("\U0002a700"), "to": ord("\U0002b73f")},
    {"from": ord("\U0002b740"), "to": ord("\U0002b81f")},
    {"from": ord("\U0002b820"), "to": ord("\U0002ceaf")}  # included as of Unicode 8.0
]

def _contains_japanese_char(text) -> bool:
    for char in text:
        if _is_japanese_letter(char):
            return True

    return False

def _is_japanese_letter(char: str) -> bool:
    if char == " ":
        return False

    for char_range in japanese_char_ranges:
        if char_range["from"] <= ord(char) <= char_range["to"]:
            return True

    return False

def _replace_japanese_chars(text: str) -> str:
    if pykakasi is None:
        raise MissingRequiredModuleError.with_values("pykakasi")

    # replace japanese Full stop (https://en.wikipedia.org/wiki/Japanese_punctuation#Full_stop)
    text = text.replace("。", ". ")

    i = 0
    while i < len(text):
        if _is_japanese_letter(text[i]):
            start = i

            # the current character is known to be japanese
            i += 1

            while i < len(text) and _is_japanese_letter(text[i]):
                i += 1

            converted_text = " ".join([item["hepburn"] for item in pykakasi.kakasi().convert(text[start:i])])

            text = text[:start] + converted_text + text[i:]
        i += 1

    return text
