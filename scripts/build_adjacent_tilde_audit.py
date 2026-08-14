#!/usr/bin/env python3
"""Inventory adjacent-vowel tildes and build scan-review contact sheets."""

from __future__ import annotations

import argparse
import csv
import difflib
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "pilot" / "format-v1-trial" / "level1-source"
GEOMETRY = ROOT / "pilot" / "human-review" / "line-geometry.json"
MASTER_DIR = ROOT / ".cache" / "sources" / "bnf-gallica" / "master"
OCR_DIR = ROOT / ".cache" / "adjacent-tilde-audit" / "ocr"
MARKED = set("ãõũẽĩÃÕŨẼĨ")
VOWELS = set("aeiouáéíóúàèìòùâêîôûãõũẽĩAEIOUÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕŨẼĨ")
WORD_RE = re.compile(r"[^\W\d_]+(?:[-'][^\W\d_]+)*", re.UNICODE)
LINE_RE = re.compile(r"^\[([^]]+)\]\s*(.*)$")


def plain_text(markdown: str) -> str:
    return re.sub(r"[*_`]", "", markdown)


def inventory(start_page: int) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(SOURCE_DIR.glob("bnf-f*.md")):
        page_number = int(re.search(r"f(\d+)", path.stem).group(1))
        if page_number < start_page:
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line_match = LINE_RE.match(raw_line)
            if not line_match:
                continue
            line_id, markdown = line_match.groups()
            text = unicodedata.normalize("NFC", plain_text(markdown))
            ordinal = 0
            for word_match in WORD_RE.finditer(text):
                token = word_match.group(0)
                lowered = token.lower()
                if "nhaã" in lowered or "nhãa" in lowered:
                    continue
                for index, character in enumerate(token):
                    if character not in MARKED:
                        continue
                    left_vowel = index > 0 and token[index - 1] in VOWELS
                    right_vowel = index + 1 < len(token) and token[index + 1] in VOWELS
                    if not (left_vowel or right_vowel):
                        continue
                    ordinal += 1
                    context_start = max(0, index - 1)
                    context_end = min(len(token), index + 2)
                    rows.append(
                        {
                            "page": path.stem,
                            "line": line_id.split()[0],
                            "occurrence": str(ordinal),
                            "token": token,
                            "token_start": str(word_match.start()),
                            "token_end": str(word_match.end()),
                            "marked_index": str(index),
                            "current_context": token[context_start:context_end],
                            "reviewed_token": token,
                            "mark_on": unicodedata.normalize("NFD", character)[0].lower(),
                            "status": "pending_scan_review",
                        }
                    )
    return rows


def write_inventory(rows: list[dict[str, str]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def load_geometry() -> dict[tuple[str, str], list[int]]:
    data = json.loads(GEOMETRY.read_text(encoding="utf-8"))
    result: dict[tuple[str, str], list[int]] = {}
    for page in data["pages"]:
        for column in page["columns"].values():
            for line_id, line in column["lines"].items():
                result[(page["id"], line_id)] = line["crop"]
    return result


def source_lines() -> dict[tuple[str, str], str]:
    result = {}
    for path in SOURCE_DIR.glob("bnf-f*.md"):
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            match = LINE_RE.match(raw_line)
            if match:
                result[(path.stem, match.group(1).split()[0])] = unicodedata.normalize(
                    "NFC", plain_text(match.group(2))
                )
    return result


def ink_bounds(image: Image.Image) -> tuple[int, int]:
    gray = np.asarray(image.convert("L"))
    occupied = np.flatnonzero((gray < 115).sum(axis=0) >= 3)
    return (int(occupied[0]), int(occupied[-1])) if occupied.size else (0, image.width - 1)


def normalized_word(value: str) -> str:
    value = unicodedata.normalize("NFD", value.replace("ſ", "s").lower())
    return "".join(character for character in value if character.isalpha() and not unicodedata.combining(character))


def page_ocr(page: str) -> list[dict[str, int | str]]:
    path = OCR_DIR / f"f{int(page[-4:]):04d}.tsv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = []
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["level"] != "5" or not normalized_word(row["text"]):
                continue
            rows.append(
                {
                    "text": row["text"],
                    "left": int(row["left"]),
                    "top": int(row["top"]),
                    "width": int(row["width"]),
                    "height": int(row["height"]),
                }
            )
    return rows


def locate_with_ocr(
    row: dict[str, str], text: str, line_crop: list[int], words: list[dict[str, int | str]]
) -> tuple[int | None, str]:
    x, y, width, height = line_crop
    line_words = [
        word
        for word in words
        if x <= int(word["left"]) + int(word["width"]) / 2 <= x + width
        and abs(int(word["top"]) + int(word["height"]) / 2 - (y + height / 2)) <= height * 0.7
    ]
    line_words.sort(key=lambda word: int(word["left"]))
    transcript_words = list(re.finditer(r"\S+", text))
    token_start = int(row["token_start"])
    target_index = next(
        (index for index, match in enumerate(transcript_words) if match.start() <= token_start < match.end()),
        0,
    )
    target = normalized_word(row["token"])

    # Establish monotonic anchors between the transcription and the OCR word
    # boxes.  OCR is deliberately used only to locate ink: the audit decision
    # still comes from the scan crop.  Neighbour anchors are much safer than
    # asking OCR to recognize the (often poorly recognized) marked word itself.
    canonical = [normalized_word(match.group(0)) for match in transcript_words]
    observed = [normalized_word(str(word["text"])) for word in line_words]
    candidates: list[tuple[float, int, int]] = []
    for canonical_index, canonical_word in enumerate(canonical):
        if not canonical_word:
            continue
        for observed_index, observed_word in enumerate(observed):
            if not observed_word:
                continue
            similarity = difflib.SequenceMatcher(None, canonical_word, observed_word).ratio()
            if canonical_word in observed_word or observed_word in canonical_word:
                similarity = max(similarity, 0.82)
            expected = canonical_index / max(len(canonical) - 1, 1)
            actual = observed_index / max(len(observed) - 1, 1)
            score = similarity - abs(expected - actual) * 0.18
            if similarity >= 0.52:
                candidates.append((score, canonical_index, observed_index))
    candidates.sort(reverse=True)
    anchors: list[tuple[int, int]] = []
    used_canonical: set[int] = set()
    used_observed: set[int] = set()
    for _score, canonical_index, observed_index in candidates:
        if canonical_index in used_canonical or observed_index in used_observed:
            continue
        if any(
            (canonical_index < previous_canonical and observed_index > previous_observed)
            or (canonical_index > previous_canonical and observed_index < previous_observed)
            for previous_canonical, previous_observed in anchors
        ):
            continue
        anchors.append((canonical_index, observed_index))
        used_canonical.add(canonical_index)
        used_observed.add(observed_index)
    anchors.sort()

    direct_anchor = next(
        ((ci, oi) for ci, oi in anchors if ci == target_index), None
    )
    if direct_anchor is not None:
        word = line_words[direct_anchor[1]]
        return int(word["left"]) - x + int(word["width"]) // 2, f"anchor:{word['text']}"

    target_character = (int(row["token_start"]) + int(row["token_end"])) / 2
    positioned_anchors: list[tuple[float, float, str]] = []
    for canonical_index, observed_index in anchors:
        match = transcript_words[canonical_index]
        word = line_words[observed_index]
        positioned_anchors.append(
            (
                (match.start() + match.end()) / 2,
                int(word["left"]) - x + int(word["width"]) / 2,
                str(word["text"]),
            )
        )
    before = [anchor for anchor in positioned_anchors if anchor[0] < target_character]
    after = [anchor for anchor in positioned_anchors if anchor[0] > target_character]
    if before and after:
        left_anchor = max(before)
        right_anchor = min(after)
        fraction = (target_character - left_anchor[0]) / (right_anchor[0] - left_anchor[0])
        centre = left_anchor[1] + (right_anchor[1] - left_anchor[1]) * fraction
        return int(centre), f"between:{left_anchor[2]}|{right_anchor[2]}"
    same_target_rank = sum(
        normalized_word(match.group(0)) == target for match in transcript_words[: target_index + 1]
    ) - 1
    close_matches = [
        word
        for word in line_words
        if difflib.SequenceMatcher(None, target, normalized_word(str(word["text"]))).ratio() >= 0.55
        or target in normalized_word(str(word["text"]))
    ]
    if same_target_rank < len(close_matches):
        word = close_matches[same_target_rank]
        word_text = normalized_word(str(word["text"]))
        offset = word_text.find(target)
        if offset >= 0 and word_text:
            fraction = (offset + len(target) / 2) / len(word_text)
            centre = int(word["left"]) - x + int(int(word["width"]) * fraction)
        else:
            centre = int(word["left"]) - x + int(word["width"]) // 2
        return centre, str(word["text"])
    if line_words:
        repeated_targets = sum(normalized_word(match.group(0)) == target for match in transcript_words)
        if repeated_targets > len(close_matches):
            left = min(int(word["left"]) for word in line_words)
            right = max(int(word["left"]) + int(word["width"]) for word in line_words)
            fraction = (token_start + len(row["token"]) / 2) / max(len(text), 1)
            return int(left + (right - left) * fraction) - x, "rank fallback"
    best: tuple[float, dict[str, int | str]] | None = None
    for index, word in enumerate(line_words):
        word_text = normalized_word(str(word["text"]))
        similarity = difflib.SequenceMatcher(None, target, word_text).ratio()
        if target in word_text:
            similarity = max(similarity, 0.95)
        expected = target_index / max(len(transcript_words) - 1, 1)
        observed = index / max(len(line_words) - 1, 1)
        score = similarity * 0.8 + (1 - abs(expected - observed)) * 0.2
        if best is None or score > best[0]:
            best = (score, word)
    if best is None or best[0] < 0.42:
        return None, ""
    word = best[1]
    word_text = normalized_word(str(word["text"]))
    offset = word_text.find(target)
    if offset >= 0 and word_text:
        fraction = (offset + len(target) / 2) / len(word_text)
        centre = int(word["left"]) - x + int(int(word["width"]) * fraction)
    else:
        centre = int(word["left"]) - x + int(word["width"]) // 2
    return centre, str(word["text"])


def make_sheets(rows: list[dict[str, str]], output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    geometry = load_geometry()
    lines = source_lines()
    label_font = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 17)
    measure_font = ImageFont.truetype("/System/Library/Fonts/Times.ttc", 48)
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    masters: dict[str, Image.Image] = {}
    ocr_cache: dict[str, list[dict[str, int | str]]] = {}
    for row in rows:
        grouped[row["current_context"].lower()].append(row)

    for group, members in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0])):
        for sheet_index in range(0, len(members), 32):
            subset = members[sheet_index : sheet_index + 32]
            sheet = Image.new("RGB", (1920, 1240), "white")
            for tile_index, row in enumerate(subset):
                page, line_id = row["page"], row["line"]
                crop = geometry.get((page, line_id))
                if crop is None and line_id.startswith(("catch-", "cw-")):
                    crop = [1445, 3380, 1206, 360]
                if crop is None:
                    raise KeyError(f"No scan crop for {page}:{line_id}")
                x, y, width, height = crop
                master = masters.get(page)
                if master is None:
                    master = Image.open(MASTER_DIR / f"f{int(page[-4:]):04d}.jpg").convert("RGB")
                    masters[page] = master
                line_image = master.crop((x, y, x + width, y + height))
                text = lines[(page, line_id)]
                start = int(row["token_start"])
                end = int(row["token_end"])
                repeated_target = sum(
                    normalized_word(match.group(0)) == normalized_word(row["token"])
                    for match in re.finditer(r"\S+", text)
                ) > 1
                words = ocr_cache.setdefault(page, page_ocr(page))
                centre, ocr_match = (None, "") if repeated_target else locate_with_ocr(row, text, crop, words)
                if centre is None:
                    left_ink, right_ink = ink_bounds(line_image)
                    total_width = max(measure_font.getlength(text), 1)
                    target_left = left_ink + (right_ink - left_ink) * measure_font.getlength(text[:start]) / total_width
                    target_right = left_ink + (right_ink - left_ink) * measure_font.getlength(text[:end]) / total_width
                    centre = int((target_left + target_right) / 2)
                    ocr_match = "repeat fallback" if repeated_target else "fallback"
                crop_left = max(0, centre - 120)
                crop_right = min(line_image.width, centre + 120)
                word_image = line_image.crop((crop_left, 0, crop_right, height)).resize(
                    ((crop_right - crop_left) * 2, height * 2), Image.Resampling.LANCZOS
                )
                tile_x = (tile_index % 4) * 480
                tile_y = (tile_index // 4) * 155
                draw = ImageDraw.Draw(sheet)
                label = f"{page[4:]}/{line_id} #{row['occurrence']}  {row['token']}  [{ocr_match}]"
                draw.text((tile_x + 5, tile_y + 3), label, font=label_font, fill="navy")
                paste_y = tile_y + 31
                sheet.paste(word_image.crop((0, 0, min(480, word_image.width), 124)), (tile_x, paste_y))
            number = sheet_index // 32 + 1
            sheet.save(output / f"{group}-{number:03d}.jpg", quality=95)


def make_full_line_sheets(rows: list[dict[str, str]], output: Path) -> None:
    """Make a second-pass packet for targets that OCR did not anchor securely.

    These sheets deliberately retain the complete printed line.  They are for
    visual review of carrier placement; OCR merely decides which rows need the
    less compact presentation.
    """
    output.mkdir(parents=True, exist_ok=True)
    geometry = load_geometry()
    lines = source_lines()
    label_font = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 18)
    masters: dict[str, Image.Image] = {}
    ocr_cache: dict[str, list[dict[str, int | str]]] = {}
    selected: list[tuple[dict[str, str], list[int], str]] = []

    for row in rows:
        page, line_id = row["page"], row["line"]
        crop = geometry.get((page, line_id))
        if crop is None and line_id.startswith(("catch-", "cw-")):
            crop = [1445, 3380, 1206, 360]
        if crop is None:
            continue
        text = lines[(page, line_id)]
        repeated_target = sum(
            normalized_word(match.group(0)) == normalized_word(row["token"])
            for match in re.finditer(r"\S+", text)
        ) > 1
        words = ocr_cache.setdefault(page, page_ocr(page))
        _centre, method = (None, "repeat") if repeated_target else locate_with_ocr(row, text, crop, words)
        if not (method.startswith("anchor:") or method.startswith("between:")):
            selected.append((row, crop, method or "no OCR location"))

    for sheet_index in range(0, len(selected), 16):
        subset = selected[sheet_index : sheet_index + 16]
        sheet = Image.new("RGB", (1920, 1920), "white")
        draw = ImageDraw.Draw(sheet)
        for tile_index, (row, crop, method) in enumerate(subset):
            page, line_id = row["page"], row["line"]
            x, y, width, height = crop
            master = masters.get(page)
            if master is None:
                master = Image.open(MASTER_DIR / f"f{int(page[-4:]):04d}.jpg").convert("RGB")
                masters[page] = master
            line_image = master.crop((x, y, x + width, y + height))
            scale = min(1880 / max(line_image.width, 1), 2.0)
            rendered = line_image.resize(
                (int(line_image.width * scale), min(82, int(line_image.height * scale))),
                Image.Resampling.LANCZOS,
            )
            tile_y = tile_index * 120
            label = (
                f"{page[4:]}/{line_id} #{row['occurrence']}  TARGET {row['token']}  "
                f"[{method}]"
            )
            draw.text((12, tile_y + 3), label, font=label_font, fill="navy")
            sheet.paste(rendered, (12, tile_y + 32))
        sheet.save(output / f"low-confidence-{sheet_index // 16 + 1:03d}.jpg", quality=95)
    print(f"Wrote {len(selected)} low-confidence full-line targets.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-page", type=int, default=39)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--sheets", type=Path)
    parser.add_argument("--full-line-sheets", type=Path)
    args = parser.parse_args()
    rows = inventory(args.start_page)
    if args.ledger:
        write_inventory(rows, args.ledger)
    if args.sheets:
        make_sheets(rows, args.sheets)
    if args.full_line_sheets:
        make_full_line_sheets(rows, args.full_line_sheets)
    print(f"Inventoried {len(rows)} adjacent-vowel tilde occurrences.")


if __name__ == "__main__":
    main()
