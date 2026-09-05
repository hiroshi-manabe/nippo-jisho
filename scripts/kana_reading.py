"""Derived katakana hints for reviewing Nippo Jisho romanized Japanese."""

from __future__ import annotations

import re
import unicodedata


LABELS = {"ad", "adu", "aduer", "aduerb", "alicubi", "bup", "fab", "fei", "feiq", "fox", "i", "item", "l", "lib", "melius", "mon", "nome", "p", "permet", "s", "tac", "taif", "ut", "vt", "voi", "x", "xix"}
VOWELS = {"a": "ア", "i": "イ", "u": "ウ", "e": "エ", "o": "オ"}
LABELS.add("yax")  # Citation label, not Japanese running text (f169).
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
# Attested Japanese lexical forms with consonantal I/J, not a global Ie rule.
# f20/f165: 膳; f41: 前後; f111: 銭; f169: 全体.
# Include the separately attested Ien/Ienno, but do not infer arbitrary suffixes.
CONSONANTAL_I_FORMS = {"ien", "ienno", "ienuo", "iengo", "ieni", "ienino", "ientai"}


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
    if text in CONSONANTAL_I_FORMS:
        text = "j" + text[1:]
    output: list[str] = []
    index = 0
    while index < len(text):
        orthographic_u_after_g = False
        doubled_z = False
        if (text[index] == "y" and not vowel_at(text, index + 1)
                and text[index + 1:index + 2] != "y"):
            # Vocalic y: taguy, ytçucuximi; retain consonantal ya/yu/yo.
            output.append("イ"); index += 1; continue
        if (text[index] == "j" and index > 0 and vowel_at(text, index - 1)
                and not vowel_at(text, index + 1) and text[index + 1:index + 2] != "j"):
            # Long i/j is also used internally: ijta, qijta, Chijſai.
            output.append("イ"); index += 1; continue
        if text[index] == "m" and text[index + 1:index + 2] in ("b", "p"):
            output.append("ン"); index += 1; continue
        if text.startswith("qua", index):
            output.append("クヮ")
            index += 3
            continue
        if text.startswith("gua", index):
            output.append("グヮ")
            index += 3
            continue
        if text[index] == "u" and (following := vowel_at(text, index + 1)):
            output.extend((ROWS["w"][INDEX[following[0]]], following[1]))
            index += 2
            continue
        if (text.startswith("nu", index) and vowel_at(text, index + 2)
                and not (text.startswith("nuu", index) and vowel_at(text, index + 3))):
            # In forms such as ``Quǒguenuo``, the n closes the preceding
            # Japanese word and ``uo`` is the following particle: -n-uo,
            # not the syllables nu-o. But nu + ua/uo keeps its own vowel:
            # Inuuo = inu-uo, not in-u-uo.
            output.append("ン")
            index += 1
            continue
        if text.startswith(("cq", "cc", "xx"), index):
            # cc/cq double k; xx doubles sh (Bexxo = ベッショ).
            output.append("ッ")
            index += 1
            continue
        if text[index] == "n" and not text.startswith("nh", index) and (index + 1 == len(text) or not vowel_at(text, index + 1)):
            output.append("ン")
            index += 1
            continue
        consonant = ""
        if text.startswith("tç", index): consonant, index = "t", index + 2
        elif text[index] == "t" and (not vowel_at(text, index + 1) or text.startswith("tuo", index)):
            # Sino-Japanese checked -t is written as a bare coda in Jesuit
            # romanization. Small ッ is an editorial display convention for
            # that closed syllable, not a claim of ordinary modern gemination.
            # Before object-particle uo, retain the coda boundary as well:
            # facufat-uo, not facufa-tu-o. The following loop reads uo as ヲ.
            output.append("ッ"); index += 1; continue
        elif text.startswith("zz", index):
            consonant, index = "z", index + 2
            doubled_z = True
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
            if index == 0 and (following := vowel_at(text, index + 1)):
                # Initial ``v`` is not uniform in the Jesuit spelling. Before
                # ``a`` it represents the surviving /w/ of forms such as
                # ``vare`` and ``vaqete``; before ``o`` it normally belongs to
                # forms such as ``vonaji`` and is not rendered as /w/.
                if following[0] == "a":
                    consonant, index = "w", index + 1
                else:
                    index += 1
                    continue
            else:
                if index == 0 or not vowel_at(text, index + 1):
                    output.append("ウ"); index += 1; continue
                consonant, index = "w", index + 1
        elif text[index] in ROWS:
            consonant, index = text[index], index + 1
            # As in contemporary Portuguese spelling, the u in Japanese
            # ``gue``/``gui`` is normally orthographic rather than a separate
            # vowel: Xiraſagui is *shirasagi*, not *shirasagui*.
            if consonant == "g" and index + 1 < len(text) and text[index] == "u" and text[index + 1] in "ie":
                index += 1
                orthographic_u_after_g = True
        elif (vowel := vowel_at(text, index)):
            output.extend((VOWELS[vowel[0]], vowel[1])); index += 1; continue
        else:
            return None
        if index < len(text) and text[index] == consonant and len(consonant) == 1:
            output.append("ッ"); index += 1
        if (index < len(text) and consonant in "kgnhbpmr"
                and (text[index] == "i" or
                     (text[index] == "e" and text[index + 1:index + 2] in ("ǒ", "ô")))):
            # eǒ/eô also mark palatalized long-o syllables (Reǒginno).
            # Hints intentionally merge the open/closed long-o distinction.
            following = vowel_at(text, index + 1)
            # In sequences such as niua and biuo, the following u begins a
            # separate ua/uo spelling; it is not the palatalizing vowel of
            # nia/niu/nio.
            if following and vowel_at(text, index + 2):
                following = None
            small = {"a": "ャ", "u": "ュ", "o": "ョ"}.get(following[0] if following else "")
            if small:
                # Jesuit ``gi`` before another vowel represents the
                # historical voiced palatal series, as in ``cotogia``
                # (ことぢゃ), rather than modern Hepburn-style gi + a/u/o.
                # Plain ``gio`` belongs to the historical voiced palatal
                # series represented here as ヂョ, but Portuguese-style
                # ``guio`` has an orthographic silent u and represents ギョ.
                base = "ヂ" if consonant == "g" and not orthographic_u_after_g else ROWS[consonant][1]
                output.extend((base, small, following[1])); index += 2; continue
        vowel = vowel_at(text, index)
        if not vowel:
            return None
        special = {
            "sh": {"a": "シャ", "i": "シ", "u": "シュ", "e": "セ", "o": "ショ"},
            "ch": {"a": "チャ", "i": "チ", "u": "チュ", "e": "チェ", "o": "チョ"},
            "j": {"a": "ジャ", "i": "ジ", "u": "ジュ", "e": "ゼ", "o": "ジョ"},
            "ny": {"a": "ニャ", "i": "ニ", "u": "ニュ", "e": "ニェ", "o": "ニョ"},
        }
        rendered = special.get(consonant, {}).get(vowel[0])
        if doubled_z and vowel[0] == "u":
            # Preserve the printed yotsugana distinction: zzu = ヅ, zu = ズ.
            rendered = "ヅ"
        if consonant == "g" and vowel[0] == "i" and not orthographic_u_after_g:
            # Bare gi belongs to the voiced palatal series (Fagi = はぢ).
            # Portuguese-style gui retains hard g (Fagui = はぎ).
            rendered = "ヂ"
        if rendered is None:
            rendered = ROWS[consonant][INDEX[vowel[0]]]
        output.append(rendered)
        output.append(vowel[1]); index += 1
    return "".join(output) or None


def reading_tokens(text: str) -> list[str]:
    tokens = TOKEN_RE.findall(text)
    result: list[str] = []
    for index, token in enumerate(tokens):
        key = re.sub(r"[^a-z]", "", normalized(token))
        # In the attested ``guio i. i.`` sequence, the first standalone i is
        # the final mora of Japanese *gyoi* (御衣); the second i. is the
        # dictionary abbreviation and falls in the next period-delimited
        # phrase.  Keep only the narrowly contextual Japanese occurrence.
        japanese_gyoi_i = (
            key == "i"
            and index > 0
            and normalized(tokens[index - 1]).endswith("guio")
        )
        if key not in LABELS or japanese_gyoi_i:
            result.append(token)
    return result


def phrase_hint(text: str) -> str | None:
    tokens = reading_tokens(text)
    readings = [
        "イ"
        if normalized(token) == "i"
        and index > 0
        and normalized(tokens[index - 1]).endswith("guio")
        else transliterate_token(token)
        for index, token in enumerate(tokens)
    ]
    if not tokens or all(reading is None for reading in readings):
        return None
    if any(reading is None for reading in readings):
        # A damaged token or a physical line-end fragment must not hide the
        # readable words beside it. Do not guess how the fragment continues.
        return ", ".join(
            f"{token}/{reading if reading is not None else '[unconverted]'}"
            for token, reading in zip(tokens, readings)
        )
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


def reading_hint_applicable(runs: list[dict]) -> bool:
    """Return whether roman runs contain anything other than known labels."""
    return any(
        reading_tokens(phrase.strip(" ,;:-"))
        for run in runs
        if run.get("typeface") == "roman"
        for phrase in re.split(r"[.¶]+", run.get("text", ""))
    )
