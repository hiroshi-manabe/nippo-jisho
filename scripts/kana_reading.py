"""Derived katakana hints for reviewing Nippo Jisho romanized Japanese."""

from __future__ import annotations

import re
import unicodedata


LABELS = {"ad", "adu", "aduer", "aduerb", "alicubi", "bup", "fab", "fei", "feiq", "fox", "i", "item", "lib", "melius", "mon", "nome", "p", "permet", "s", "tac", "taif", "ut", "vt", "voi", "x", "xix"}
VOWELS = {"a": "ア", "i": "イ", "u": "ウ", "e": "エ", "o": "オ"}
ROWS = {
    "k": "カキクケコ", "g": "ガギグゲゴ", "s": "サシスセソ", "z": "ザジズゼゾ",
    "t": "タチツテト", "d": "ダヂヅデド", "n": "ナニヌネノ", "h": "ハヒフヘホ",
    "b": "バビブベボ", "p": "パピプペポ", "m": "マミムメモ", "r": "ラリルレロ",
    "y": "ヤイユエヨ", "w": "ワヰウヱヲ",
}
INDEX = {letter: index for index, letter in enumerate("aiueo")}
MARKED = {
    "à": ("a", "ァ"), "á": ("a", "ァ"), "â": ("a", "ァ"), "ǎ": ("a", "ァ"),
    "ì": ("i", "ィ"), "í": ("i", "ィ"), "î": ("i", "ィ"), "ǐ": ("i", "ィ"),
    "ù": ("u", "ゥ"), "ú": ("u", "ゥ"), "û": ("u", "ゥ"), "ǔ": ("u", "ゥ"),
    "è": ("e", "ェ"), "é": ("e", "ェ"), "ê": ("e", "ェ"), "ě": ("e", "ェ"),
    "ò": ("o", "ォ"), "ó": ("o", "ォ"), "ô": ("o", "ゥ"), "ǒ": ("o", "ゥ"),
}
NASAL = {"ã": "a", "ĩ": "i", "ũ": "u", "ẽ": "e", "õ": "o"}
TOKEN_RE = re.compile(r"[A-Za-zÀ-žǍ-ǔſç]+")


def normalized(value: str) -> str:
    return unicodedata.normalize("NFC", value).lower()


def vowel_at(text: str, index: int) -> tuple[str, str] | None:
    if index >= len(text):
        return None
    character = text[index]
    if character in VOWELS:
        return character, ""
    if character in MARKED:
        return MARKED[character]
    if character in NASAL:
        return NASAL[character], "ン"
    return None


def transliterate_token(token: str) -> str | None:
    key = re.sub(r"[^a-z]", "", normalized(token))
    if not token or key in LABELS:
        return None
    text = normalized(token).replace("ſ", "s")
    output: list[str] = []
    index = 0
    while index < len(text):
        if text[index] == "u" and (following := vowel_at(text, index + 1)):
            output.extend((ROWS["w"][INDEX[following[0]]], following[1]))
            index += 2
            continue
        if text[index] == "n" and (index + 1 == len(text) or not vowel_at(text, index + 1)):
            output.append("ン")
            index += 1
            continue
        consonant = ""
        if text.startswith("tç", index): consonant, index = "t", index + 2
        elif text.startswith("zz", index): consonant, index = "z", index + 2
        elif text.startswith("nh", index): consonant, index = "ny", index + 2
        elif text.startswith("ch", index): consonant, index = "ch", index + 2
        elif text[index] == "x": consonant, index = "sh", index + 1
        elif text[index] == "q":
            consonant, index = "k", index + 1
            if index + 1 < len(text) and text[index] == "u" and text[index + 1] in "ie": index += 1
        elif text[index] == "c": consonant, index = "k", index + 1
        elif text[index] == "ç": consonant, index = "s", index + 1
        elif text[index] == "f": consonant, index = "h", index + 1
        elif text[index] == "j":
            if index + 1 == len(text): output.append("イ"); index += 1; continue
            consonant, index = "j", index + 1
        elif text[index] == "v":
            if index == 0 and vowel_at(text, index + 1): index += 1; continue
            if index == 0: output.append("ウ"); index += 1; continue
            consonant, index = "w", index + 1
        elif text[index] in ROWS:
            consonant, index = text[index], index + 1
            # As in contemporary Portuguese spelling, the u in Japanese
            # ``gue``/``gui`` is normally orthographic rather than a separate
            # vowel: Xiraſagui is *shirasagi*, not *shirasagui*.
            if consonant == "g" and index + 1 < len(text) and text[index] == "u" and text[index + 1] in "ie":
                index += 1
        elif (vowel := vowel_at(text, index)):
            output.extend((VOWELS[vowel[0]], vowel[1])); index += 1; continue
        else:
            return None
        if index < len(text) and text[index] == consonant and len(consonant) == 1:
            output.append("ッ"); index += 1
        if index < len(text) and text[index] == "i" and consonant in "kgnhbpmr":
            following = vowel_at(text, index + 1)
            # In sequences such as niua and biuo, the following u begins a
            # separate ua/uo spelling; it is not the palatalizing vowel of
            # nia/niu/nio.
            if following and vowel_at(text, index + 2):
                following = None
            small = {"a": "ャ", "u": "ュ", "o": "ョ"}.get(following[0] if following else "")
            if small:
                output.extend((ROWS[consonant][1], small, following[1])); index += 2; continue
        vowel = vowel_at(text, index)
        if not vowel:
            return None
        special = {
            "sh": {"a": "シャ", "i": "シ", "u": "シュ", "e": "セ", "o": "ショ"},
            "ch": {"a": "チャ", "i": "チ", "u": "チュ", "e": "チェ", "o": "チョ"},
            "j": {"a": "ジャ", "i": "ジ", "u": "ジュ", "e": "ジェ", "o": "ジョ"},
            "ny": {"a": "ニャ", "i": "ニ", "u": "ニュ", "e": "ニェ", "o": "ニョ"},
        }
        rendered = special.get(consonant, {}).get(vowel[0])
        if rendered is None:
            rendered = ROWS[consonant][INDEX[vowel[0]]]
        output.append(rendered)
        output.append(vowel[1]); index += 1
    return "".join(output) or None


def phrase_hint(text: str) -> str | None:
    tokens = TOKEN_RE.findall(text)
    tokens = [
        token for token in tokens
        if re.sub(r"[^a-z]", "", normalized(token)) not in LABELS
    ]
    readings = [transliterate_token(token) for token in tokens]
    if not tokens or any(reading is None for reading in readings):
        return None
    phrase = " ".join(tokens)
    return f"{phrase}/{' '.join(readings)}"


def reading_hint(runs: list[dict]) -> str | None:
    hints: list[str] = []
    for run in runs:
        if run.get("typeface") != "roman":
            continue
        for phrase in re.split(r"[.¶]+", run.get("text", "")):
            phrase = phrase.strip(" ,;:-")
            if phrase and (hint := phrase_hint(phrase)):
                hints.append(hint)
    return ", ".join(hints) or None
