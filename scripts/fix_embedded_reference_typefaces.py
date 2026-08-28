#!/usr/bin/env python3
"""Correct systematic typeface boundaries in compact Level 1 Markdown."""

from __future__ import annotations

import argparse
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "pilot" / "format-v1-trial" / "level1-source"
REFERENCE_LABELS = (
    "Fab",
    "Feiq",
    "Fei",
    "Fox",
    "Mon",
    "Tac",
    "Taif",
    "Taiſ",
    "Taiſei",
    "Tai",
    "Tair",
    "Tait",
    "Faiq",
    "Xix",
)
REFERENCE_RE = re.compile(
    r"(?<![\wſ])(" + "|".join(map(re.escape, REFERENCE_LABELS)) + r")(?=\.)"
)
GRAMMATICAL_RE = re.compile(
    r"(?<![\wſ])(?:Aduerb|Aduer|Adu|Ad)\.|(?<![\wſ])Melius(?![\wſ])"
)
USAGE_LABEL_RE = re.compile(r"(?<![\wſ])(?:Bup|Voi|S|X)(?=\.)")
POETRY_LABEL_RE = re.compile(r"(?<![\wſ])P(?=\.)")
BOOK_RE = re.compile(r"(?<![\wſ])(?:Lib|lib|L|Li)\.")
CONTINUED_BOOK_RE = re.compile(r"^(?:Lib|lib)\.\s*(?:[ivxlcdm]+|\d+)\.", re.I)


def parse_styles(content: str) -> list[list[str | bool]]:
    characters: list[list[str | bool]] = []
    italic = False
    for character in content:
        if character == "*":
            italic = not italic
        else:
            characters.append([character, italic])
    if italic:
        raise ValueError(f"unclosed italic span: {content}")
    return characters


def visible_text(characters: list[list[str | bool]]) -> str:
    return "".join(str(character) for character, _ in characters)


def set_style(
    characters: list[list[str | bool]], match: re.Match[str], italic: bool
) -> None:
    for index in range(match.start(), match.end()):
        characters[index][1] = italic


def normalize_spaces(characters: list[list[str | bool]]) -> None:
    for index, item in enumerate(characters):
        if item[0] != " ":
            continue
        left = characters[index - 1][1] if index else False
        right = characters[index + 1][1] if index + 1 < len(characters) else False
        item[1] = left if left == right else False


def serialize(characters: list[list[str | bool]]) -> str:
    output: list[str] = []
    italic = False
    for character, target_italic in characters:
        if target_italic != italic:
            output.append("*")
            italic = bool(target_italic)
        output.append(str(character))
    if italic:
        output.append("*")
    return "".join(output)


def rewrite_content(content: str) -> str:
    characters = parse_styles(content)
    text = visible_text(characters)
    references = list(REFERENCE_RE.finditer(text))
    grammatical = list(GRAMMATICAL_RE.finditer(text))
    usage_labels = list(USAGE_LABEL_RE.finditer(text))
    poetry_labels = list(POETRY_LABEL_RE.finditer(text))
    continued_book = CONTINUED_BOOK_RE.match(text)
    if not grammatical and not references and not usage_labels and not poetry_labels and not continued_book:
        return content
    original_styles = [italic for _, italic in characters]

    for match in grammatical:
        set_style(characters, match, True)
    for match in references:
        set_style(characters, match, False)
    for match in usage_labels:
        set_style(characters, match, False)
    for match in poetry_labels:
        # `P.` is upright when it closes or qualifies material already in the
        # italic apparatus, but can itself be italic when it introduces the
        # following explanatory form. Preserve the latter case by changing
        # only a P that has alphabetic text before it in the same italic run.
        if not original_styles[match.start()]:
            continue
        run_start = match.start()
        while run_start and original_styles[run_start - 1]:
            run_start -= 1
        if re.search(r"[A-Za-zſ]", text[run_start : match.start()]):
            set_style(characters, match, False)
    if references or continued_book:
        for match in BOOK_RE.finditer(text):
            set_style(characters, match, True)
        if continued_book:
            set_style(characters, continued_book, True)

    if original_styles == [italic for _, italic in characters]:
        return content
    normalize_spaces(characters)
    return serialize(characters)


def page_number(path: Path) -> int:
    return int(path.stem.removeprefix("bnf-f"))


def process(path: Path, *, apply: bool) -> int:
    original = path.read_text(encoding="utf-8")
    output: list[str] = []
    changed = 0
    for line in original.splitlines(keepends=True):
        ending = "\n" if line.endswith("\n") else ""
        body = line.removesuffix("\n")
        if "] " not in body:
            output.append(line)
            continue
        prefix, content = body.split("] ", 1)
        rewritten = rewrite_content(content)
        new_line = f"{prefix}] {rewritten}{ending}"
        changed += new_line != line
        output.append(new_line)
    if changed and apply:
        path.write_text("".join(output), encoding="utf-8")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-page", type=int, default=105)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    changed_files = 0
    changed_lines = 0
    for path in sorted(SOURCE_ROOT.glob("bnf-f*.md")):
        if page_number(path) < args.from_page:
            continue
        count = process(path, apply=args.apply)
        if count:
            changed_files += 1
            changed_lines += count
            print(f"{path.relative_to(ROOT)}: {count}")
    action = "Updated" if args.apply else "Would update"
    print(f"{action} {changed_lines} lines in {changed_files} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
