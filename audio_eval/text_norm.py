"""Turn written text into the words a speaker would say, so the script and
the Whisper transcript can be compared word by word.

"$20" -> "twenty dollars", "15 - pound" -> "fifteen pound", "847" -> either
"eight hundred forty seven" or "eight four seven" (both are valid readings,
so numbers expand to several candidate spellings — see ``spoken_variants``).
"""

from __future__ import annotations

import itertools
import re

_ONES = ("zero one two three four five six seven eight nine ten eleven twelve "
         "thirteen fourteen fifteen sixteen seventeen eighteen nineteen").split()
_TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()
_SCALES = ((10**9, "billion"), (10**6, "million"), (1000, "thousand"), (100, "hundred"))
_ORDINAL_FIX = {"one": "first", "two": "second", "three": "third", "five": "fifth",
                "eight": "eighth", "nine": "ninth", "twelve": "twelfth"}
_SYMBOLS = {"%": "percent", "&": "and", "+": "plus", "@": "at", "=": "equals"}
_CURRENCY = {"$": ("dollar", "dollars", "cent", "cents"),
             "£": ("pound", "pounds", "penny", "pence"),
             "€": ("euro", "euros", "cent", "cents")}

# Common spoken contractions; Whisper and the script may disagree on these.
_CONTRACTIONS = {"you'll": "you will", "i'm": "i am", "don't": "do not",
                 "can't": "can not", "cannot": "can not", "won't": "will not",
                 "it's": "it is", "that's": "that is", "there's": "there is",
                 "we're": "we are", "they're": "they are", "you're": "you are",
                 "i'll": "i will", "we'll": "we will", "i've": "i have",
                 "you've": "you have", "isn't": "is not", "aren't": "are not",
                 "doesn't": "does not", "didn't": "did not", "let's": "let us",
                 "ok": "okay"}


def int_to_words(n: int) -> str:
    if n < 0:
        return "minus " + int_to_words(-n)
    if n < 20:
        return _ONES[n]
    if n < 100:
        tens, ones = divmod(n, 10)
        return _TENS[tens] + ("" if ones == 0 else " " + _ONES[ones])
    for value, name in _SCALES:
        if n >= value:
            head, rest = divmod(n, value)
            return f"{int_to_words(head)} {name}" + ("" if rest == 0 else " " + int_to_words(rest))
    raise AssertionError("unreachable")


def ordinal_words(n: int) -> str:
    words = int_to_words(n).split()
    last = words[-1]
    if last in _ORDINAL_FIX:
        words[-1] = _ORDINAL_FIX[last]
    elif last.endswith("y"):
        words[-1] = last[:-1] + "ieth"
    else:
        words[-1] = last + "th"
    return " ".join(words)


def _digit_by_digit(digits: str) -> str:
    return " ".join("oh" if d == "0" and i else _ONES[int(d)] for i, d in enumerate(digits))


def number_variants(token: str) -> list[str]:
    """All reasonable spoken forms of a bare number string like '847' or '3.5'."""
    token = token.replace(",", "")
    if "." in token:
        whole, frac = token.split(".", 1)
        head = int_to_words(int(whole or 0))
        return [f"{head} point {' '.join(_ONES[int(d)] for d in frac)}"]
    n = int(token)
    variants = [int_to_words(n)]
    if 1000 <= n <= 9999 and n % 100 >= 10 and n // 100 % 10:
        # year-style: 1985 -> "nineteen eighty five"
        variants.append(f"{int_to_words(n // 100)} {int_to_words(n % 100)}")
    if 1100 <= n <= 9900 and n % 100 == 0 and n % 1000:
        # 1500 -> "fifteen hundred"
        variants.append(f"{int_to_words(n // 100)} hundred")
    if 100 <= n <= 9999 and n % 100 >= 10:
        # "847" -> "eight forty seven"
        variants.append(f"{int_to_words(n // 100)} {int_to_words(n % 100)}")
    if len(token) >= 3:
        variants.append(_digit_by_digit(token))
        variants.append(" ".join(_ONES[int(d)] for d in token))
    return list(dict.fromkeys(variants))


def _expand_currency(match: re.Match) -> str:
    sym, amount = match.group(1), match.group(2).replace(",", "")
    unit, units, sub, subs = _CURRENCY[sym]
    whole, _, frac = amount.partition(".")
    out = f"{whole} {unit if whole == '1' else units}"
    if frac and int(frac):
        out += f" and {int(frac)} {sub if int(frac) == 1 else subs}"
    return out


_TOKEN_RE = re.compile(r"\d+(?:[.,]\d+)*|[a-z]+(?:'[a-z]+)?")


def spoken_variants(text: str, max_variants: int = 64) -> list[list[str]]:
    """Every plausible spoken word sequence for ``text`` (numbers can be read
    several ways). The first entry is the canonical reading."""
    t = text.lower().replace("’", "'")
    t = re.sub(r"([$£€])\s?(\d[\d,]*(?:\.\d+)?)", _expand_currency, t)
    t = re.sub(r"(\d+)(st|nd|rd|th)\b", lambda m: "\x00" + m.group(1) + "\x00", t)
    for sym, word in _SYMBOLS.items():
        t = t.replace(sym, f" {word} ")

    slots: list[list[list[str]]] = []  # each slot: list of alternative word lists
    for piece in re.split(r"(\x00\d+\x00)", t):
        if piece.startswith("\x00"):
            slots.append([ordinal_words(int(piece.strip("\x00"))).split()])
            continue
        for tok in _TOKEN_RE.findall(piece):
            if tok[0].isdigit():
                slots.append([v.split() for v in number_variants(tok)])
            else:
                slots.append([_CONTRACTIONS.get(tok, tok).split()])

    out: list[list[str]] = []
    for combo in itertools.product(*slots):
        out.append([w for part in combo for w in part])
        if len(out) >= max_variants:
            break
    return out


def spoken_words(text: str) -> list[str]:
    """Canonical spoken reading of ``text``."""
    return spoken_variants(text)[0]


def normalize_hypothesis_word(word: str) -> list[str]:
    """Normalise one Whisper word token (may be '$20,' or '847.') into spoken words."""
    return spoken_words(word)
