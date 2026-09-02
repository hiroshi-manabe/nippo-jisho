#!/usr/bin/env python3
"""Build scan-first Level 1 bootstrap candidates for previously unprocessed pages.

The script deliberately writes a candidate package, not canonical Level 1
files. Raw Kraken/Calamari drafts are completed before the target page is
interpreted. A language model trained on earlier pages may then infer
roman/italic spans, while scan geometry supplies rows, indentation, zones, and
review crops. Held-out benchmark pages are opened only after every candidate
has been serialized.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import subprocess
import sys
import unicodedata

from build_ocr_dataset import load_json, write_json
from build_ocr_page_data import character_alignment
from prepare_calamari_page_drafts import position_alignment


ROOT = Path(__file__).resolve().parents[1]
SCANS = ROOT / "build" / "nippo-jisho-images" / "scans" / "native"
LEVEL1 = ROOT / "pilot" / "format-v1-trial" / "level1"
GEOMETRY = ROOT / "pilot" / "human-review" / "line-geometry.json"
DEFAULT_OUTPUT = ROOT / ".cache" / "ocr-model" / "scan-bootstrap-v1"
DEFAULT_PAGES = tuple(range(238, 248))
DEFAULT_BENCHMARK_PAGES = (14, 18, 47, 68, 103, 115, 135, 149, 160, 230, 237)
WORD_RE = re.compile(r"\w+", re.UNICODE)
MAIN_LETTER_ORDER = "ABCDFGIMNPQRSTVXZ"


def page_id(number: int) -> str:
    return f"bnf-f{number:04d}"


def page_number(identifier: str) -> int:
    return int(identifier.removeprefix("bnf-f"))


def line_text(line: dict) -> str:
    return unicodedata.normalize("NFC", "".join(run["text"] for run in line["runs"]))


def line_labels(line: dict) -> list[str]:
    return [
        run["typeface"]
        for run in line["runs"]
        for _ in run["text"]
    ]


def body_lines(page: dict) -> dict[str, dict]:
    return {
        line["id"]: line
        for zone in page["zones"]
        if zone.get("kind") == "column"
        for line in zone.get("lines", [])
    }


def scan_digest(number: int) -> str:
    return hashlib.sha256((SCANS / f"f{number:04d}.jpg").read_bytes()).hexdigest()


@dataclass
class TypefaceModel:
    words: dict[str, Counter]
    grams: dict[str, Counter]
    word_totals: dict[str, int]
    gram_totals: dict[str, int]
    vocabulary_size: int
    gram_vocabulary: dict[str, int]

    @classmethod
    def train(cls, pages: list[dict]) -> "TypefaceModel":
        states = ("roman", "italic")
        words = {state: Counter() for state in states}
        grams = {state: Counter() for state in states}
        vocabulary: set[str] = set()
        for page in pages:
            for line in body_lines(page).values():
                text = line_text(line)
                labels = line_labels(line)
                for match in WORD_RE.finditer(text):
                    labelled = [
                        label
                        for character, label in zip(
                            match.group(), labels[match.start() : match.end()]
                        )
                        if character.isalpha() and label in states
                    ]
                    if not labelled:
                        continue
                    state = Counter(labelled).most_common(1)[0][0]
                    token = match.group().casefold()
                    vocabulary.add(token)
                    words[state][token] += 1
                    wrapped = f"^{token}$"
                    for size in range(2, 6):
                        for index in range(len(wrapped) - size + 1):
                            grams[state][wrapped[index : index + size]] += 1
        return cls(
            words=words,
            grams=grams,
            word_totals={state: sum(words[state].values()) for state in states},
            gram_totals={state: sum(grams[state].values()) for state in states},
            vocabulary_size=max(1, len(vocabulary)),
            gram_vocabulary={state: max(1, len(grams[state])) for state in states},
        )

    def score(self, token: str, state: str) -> float:
        token = token.casefold()
        exact = math.log(
            (self.words[state][token] + 0.3)
            / (self.word_totals[state] + 0.3 * self.vocabulary_size)
        )
        wrapped = f"^{token}$"
        gram_scores = []
        for size in range(2, 6):
            for index in range(len(wrapped) - size + 1):
                gram = wrapped[index : index + size]
                gram_scores.append(
                    math.log(
                        (self.grams[state][gram] + 0.1)
                        / (
                            self.gram_totals[state]
                            + 0.1 * self.gram_vocabulary[state]
                        )
                    )
                )
        return exact * 2 + 1.3 * sum(gram_scores) / max(1, len(gram_scores))

    def word_states(self, text: str, *, indent: int) -> list[tuple[re.Match, str, float]]:
        matches = [match for match in WORD_RE.finditer(text) if match.group()]
        if not matches:
            return []
        states = ("roman", "italic")
        scores: list[dict[str, float]] = []
        back: list[dict[str, str]] = []
        for index, match in enumerate(matches):
            row: dict[str, float] = {}
            previous: dict[str, str] = {}
            emissions = {state: self.score(match.group(), state) for state in states}
            for state in states:
                if index == 0:
                    prior = 1.5 if not indent and state == "roman" else 0.0
                    if indent and state == "italic":
                        prior += 0.5
                    row[state] = emissions[state] + prior
                    continue
                source = max(
                    states,
                    key=lambda candidate: scores[-1][candidate]
                    + (0.0 if candidate == state else -2.5),
                )
                row[state] = (
                    scores[-1][source]
                    + (0.0 if source == state else -2.5)
                    + emissions[state]
                )
                previous[state] = source
            scores.append(row)
            back.append(previous)
        state = max(states, key=lambda candidate: scores[-1][candidate])
        sequence = [state]
        for index in range(len(matches) - 1, 0, -1):
            state = back[index][state]
            sequence.append(state)
        sequence.reverse()
        output = []
        for match, state in zip(matches, sequence):
            margin = abs(self.score(match.group(), "roman") - self.score(match.group(), "italic"))
            output.append((match, state, margin))
        return output

    def runs(self, text: str, *, indent: int) -> tuple[list[dict], list[str]]:
        predictions = self.word_states(text, indent=indent)
        if not predictions:
            return ([{"typeface": "roman", "text": text}], [])
        labels: list[str | None] = [None] * len(text)
        low_margin = []
        for match, state, margin in predictions:
            for index in range(match.start(), match.end()):
                labels[index] = state
            if margin < 0.75:
                low_margin.append(match.group())
        for index, label in enumerate(labels):
            if label is not None:
                continue
            next_label = next(
                (candidate for candidate in labels[index + 1 :] if candidate is not None),
                None,
            )
            previous_label = next(
                (
                    candidate
                    for candidate in reversed(labels[:index])
                    if candidate is not None
                ),
                None,
            )
            if text[index].isspace():
                labels[index] = next_label or previous_label or "roman"
            else:
                labels[index] = previous_label or next_label or "roman"
        runs = []
        for character, state in zip(text, labels):
            assert state is not None
            if runs and runs[-1]["typeface"] == state:
                runs[-1]["text"] += character
            else:
                runs.append({"typeface": state, "text": character})
        return runs, low_margin


def training_pages(*, through: int, excluded: set[int]) -> list[dict]:
    pages = []
    for path in sorted(LEVEL1.glob("bnf-f*.json")):
        number = page_number(path.stem)
        if number > through or number in excluded:
            continue
        pages.append(load_json(path))
    if not pages:
        raise RuntimeError("no eligible typeface-training pages")
    return pages


def normalized_text(text: str) -> str:
    return unicodedata.normalize("NFC", text.strip())


def edit_distance(left: str, right: str) -> int:
    previous = list(range(len(right) + 1))
    for left_index, left_character in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_character in enumerate(right, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[right_index] + 1,
                    previous[right_index - 1]
                    + int(left_character != right_character),
                )
            )
        previous = current
    return previous[-1]


def cluster_rows(lines: list[dict], *, tolerance: float = 20.0) -> list[dict]:
    """Collapse duplicate or fragmented Kraken baselines into physical rows.

    Scan-band recognition sees the complete column at each baseline. Multiple
    Kraken fragments at nearly the same height therefore produce duplicate
    whole-row readings; concatenating those candidates would duplicate text.
    The longest reading is retained and every source detection remains listed.
    """
    groups: list[list[dict]] = []
    for candidate in sorted(
        (line for line in lines if normalized_text(line.get("text", ""))),
        key=lambda line: line["centre"][1],
    ):
        if groups and abs(
            candidate["centre"][1]
            - statistics.mean(item["centre"][1] for item in groups[-1])
        ) <= tolerance:
            groups[-1].append(candidate)
        else:
            groups.append([candidate])
    rows = []
    for group in groups:
        chosen = max(
            group,
            key=lambda candidate: (
                len(normalized_text(candidate["text"])),
                candidate["crop"][2],
            ),
        )
        rows.append(
            {
                "centre_y": chosen["centre"][1],
                "text": normalized_text(chosen["text"]),
                "chosen_candidate": chosen,
                "source_candidate_ids": [item["id"] for item in group],
                "duplicate_candidates": len(group) - 1,
            }
        )
    return rows


def uppercase_ratio(text: str) -> float:
    letters = [character for character in text if character.isalpha()]
    return sum(character.isupper() for character in letters) / max(1, len(letters))


def display_heading(text: str) -> bool:
    letters = [character for character in text if character.isalpha()]
    if len(letters) < 4:
        return False
    compact = "".join(character for character in text.upper() if character.isalpha())
    ratio = uppercase_ratio(text)
    specific = (
        "VOCABV" in compact
        or "ANTESD" in compact
        or "POLLALETRA" in compact
        or compact.startswith("TRA")
    )
    return ratio >= 0.88 or (ratio >= 0.45 and specific)


def header_row(rows: list[dict], page_height: int) -> dict:
    candidates = [
        row
        for row in rows
        if page_height * 0.065 <= row["centre_y"] <= page_height * 0.14
    ]
    if not candidates:
        raise RuntimeError("no top-of-page row suitable for a running header")
    display = [row for row in candidates if display_heading(row["text"])]
    return min(display or candidates, key=lambda row: row["centre_y"])


def median_spacing(rows: list[dict]) -> float:
    differences = [
        right["centre_y"] - left["centre_y"]
        for left, right in zip(rows, rows[1:])
        if 38 <= right["centre_y"] - left["centre_y"] <= 85
    ]
    return statistics.median(differences) if differences else 62.0


def row_left_offset(row: dict) -> float:
    candidate = row["chosen_candidate"]
    band_left = candidate["ocr_crop"][0]
    return min(point[0] for point in candidate["baseline"]) - band_left


def indent_threshold(rows: list[dict]) -> float:
    # Kraken occasionally assigns a decorated heading fragment or marginal
    # noise to a row's baseline. Those detections can begin several hundred
    # pixels into the column and must not become a third "indent" class. In
    # these native scans, the two real body-text starts consistently lie in
    # the first 180px of the OCR band (entries around 50--70px and
    # continuations around 90--130px).
    values = sorted(
        row_left_offset(row)
        for row in rows
        if 0 <= row_left_offset(row) <= 180
    )
    if len(values) < 4:
        return 90.0
    low, high = values[len(values) // 4], values[3 * len(values) // 4]
    for _ in range(12):
        first = [value for value in values if abs(value - low) <= abs(value - high)]
        second = [value for value in values if abs(value - low) > abs(value - high)]
        if not first or not second:
            break
        low, high = statistics.mean(first), statistics.mean(second)
    if high - low < 24:
        return 90.0
    return (low + high) / 2


def heading_letter(text: str) -> str | None:
    compact = "".join(character for character in text.upper() if character.isalpha())
    if "ANTESD" in compact and compact[:1] in MAIN_LETTER_ORDER:
        return compact[0]
    match = re.match(r"([A-Z])ANTESD", compact)
    if match:
        return match.group(1)
    match = re.search(r"TRA([A-Z])$", compact)
    return match.group(1) if match else None


def resolve_heading_letter(reading: str | None, previous: str | None) -> str | None:
    """Resolve only strongly evidenced decorated-initial confusions.

    The large G used in running and internal headings is repeatedly read as C
    by both segmentation and recognition. If the preceding section is G, a C
    reading cannot represent the next alphabetic section and is retained as G.
    Other changes are left to visual review.
    """
    if previous == "G" and reading == "C":
        return "G"
    return reading


def choose_page_letter(headers: list[str], previous: str | None) -> str | None:
    readings = [letter for text in headers if (letter := heading_letter(text))]
    readings = [resolve_heading_letter(reading, previous) for reading in readings]
    if previous and (not readings or previous in readings):
        return previous
    if len(set(readings)) == 1:
        return readings[0]
    if previous:
        # OCR often confuses the decorated G with C. Preserve plausible
        # sequential context instead of allowing one noisy header to change the
        # entire page's entry initials.
        return previous
    return Counter(readings).most_common(1)[0][0] if readings else None


def repair_entry_initial(text: str, expected: str | None, indent: int) -> tuple[str, str | None]:
    if indent or not expected or not text or not text[0].isalpha():
        return text, None
    if text[0] == expected:
        return text, None
    if text[0].upper() not in MAIN_LETTER_ORDER:
        return text, None
    repaired = expected + text[1:]
    return repaired, f"{text[0]}→{expected}"


def crop_for_row(row: dict, source_size: list[int]) -> tuple[list[int], list[int]]:
    page_width, page_height = source_size
    candidate = row["chosen_candidate"]
    left, _, width, _ = candidate["ocr_crop"]
    left = max(0, left - 16)
    right = min(page_width, left + width + 32)
    centre = round(row["centre_y"])
    top = max(0, centre - 52)
    bottom = min(page_height, centre + 52)
    context_top = max(0, centre - 125)
    context_bottom = min(page_height, centre + 125)
    return (
        [left, top, right - left, bottom - top],
        [left, context_top, right - left, context_bottom - context_top],
    )


def infer_column(
    draft: dict,
    column: str,
    model: TypefaceModel,
    expected_letter: str | None,
) -> dict:
    start_expected_letter = expected_letter
    source_size = draft["source"]["source_size"]
    page_height = source_size[1]
    rows = cluster_rows(draft["columns"][column]["lines"])
    header = header_row(rows, page_height)
    following = [
        row
        for row in rows
        if header["centre_y"] + 25 < row["centre_y"] < page_height * 0.92
    ]
    spacing = median_spacing(following)
    first_y = following[0]["centre_y"]
    cutoff = min(page_height * 0.895, first_y + 47.45 * spacing)
    flow = [row for row in following if row["centre_y"] <= cutoff]
    bottom = [row for row in following if row["centre_y"] > cutoff]
    headings = {id(row) for row in flow if display_heading(row["text"])}
    ordinary = [row for row in flow if id(row) not in headings]
    threshold = indent_threshold(ordinary)

    # A short, far-right final row can be either a catchword or a physically
    # displaced continuation. Preserve it, but do not force its semantic role.
    uncertain_bottom = []
    if column == "column-2" and ordinary:
        last = ordinary[-1]
        band_width = last["chosen_candidate"]["ocr_crop"][2]
        suspicious = (
            len(last["text"]) <= 24
            and row_left_offset(last) > band_width * 0.30
            and len(flow) >= 46
        )
        if suspicious:
            ordinary.remove(last)
            flow.remove(last)
            bottom.insert(0, last)
            uncertain_bottom.append(last)

    row_records = {}
    repairs = []
    low_margin = []
    counter = 0
    active_letter = expected_letter
    for row in flow:
        if id(row) in headings:
            discovered = resolve_heading_letter(heading_letter(row["text"]), active_letter)
            if discovered:
                active_letter = discovered
            continue
        counter += 1
        identifier = f"c{1 if column == 'column-1' else 2}-l{counter:03d}"
        indent = int(row_left_offset(row) >= threshold)
        text, repair = repair_entry_initial(row["text"], active_letter, indent)
        if repair:
            repairs.append({"line_id": identifier, "change": repair, "ocr": row["text"], "text": text})
        runs, uncertain_words = model.runs(text, indent=indent)
        if uncertain_words:
            low_margin.append({"line_id": identifier, "tokens": uncertain_words})
        line = {"id": identifier, "runs": runs}
        if indent:
            line["indent"] = 1
        crop, context_crop = crop_for_row(row, source_size)
        row_records[id(row)] = {
            "line": line,
            "evidence": {
                "centre_y": row["centre_y"],
                "crop": crop,
                "context_crop": context_crop,
                "source_candidate_ids": row["source_candidate_ids"],
                "duplicate_candidates": row["duplicate_candidates"],
                "raw_ocr": row["text"],
            },
        }

    zones = []
    heading_index = body_part = 0
    active_lines = []
    post_heading_initial_candidates = []
    pending_heading_letter = None

    def flush_body() -> None:
        nonlocal body_part, active_lines
        if not active_lines:
            return
        body_part += 1
        suffix = "" if body_part == 1 and not headings else f"-part-{body_part}"
        zones.append(
            {
                "id": f"{column}{suffix}",
                "kind": "column",
                "label": f"Column {1 if column == 'column-1' else 2}"
                + (f", part {body_part}" if headings else ""),
                "lines": active_lines,
            }
        )
        active_lines = []

    for row in flow:
        if id(row) not in headings:
            if pending_heading_letter:
                post_heading_initial_candidates.append(
                    {
                        "line_id": row_records[id(row)]["line"]["id"],
                        "expected_letter": pending_heading_letter,
                        "raw_ocr": row["text"],
                        "note": "Assess a possible enlarged initial directly from the scan.",
                    }
                )
                pending_heading_letter = None
            active_lines.append(row_records[id(row)]["line"])
            continue
        flush_body()
        heading_index += 1
        raw_heading_letter = heading_letter(row["text"])
        resolved_heading_letter = resolve_heading_letter(
            raw_heading_letter, expected_letter
        )
        heading_text = row["text"]
        if (
            resolved_heading_letter
            and raw_heading_letter
            and resolved_heading_letter != raw_heading_letter
        ):
            heading_text = resolved_heading_letter + heading_text[1:]
        zones.append(
            {
                "id": f"section-{1 if column == 'column-1' else 2}-{heading_index}",
                "kind": "section_heading",
                "label": f"Column {1 if column == 'column-1' else 2} internal heading",
                "lines": [
                    {
                        "id": f"s{1 if column == 'column-1' else 2}-{heading_index:02d}-l001",
                        "runs": [
                            {
                                "typeface": "display",
                                "text": heading_text,
                            }
                        ],
                    }
                ],
            }
        )
        if resolved_heading_letter:
            expected_letter = resolved_heading_letter
            pending_heading_letter = resolved_heading_letter
    flush_body()

    geometry_lines = {
        record["line"]["id"]: {
            "centre_y": record["evidence"]["centre_y"],
            "crop": record["evidence"]["crop"],
            "context_crop": record["evidence"]["context_crop"],
        }
        for record in row_records.values()
    }
    crop_values = list(geometry_lines.values())
    if crop_values:
        left = min(value["crop"][0] for value in crop_values)
        right = max(value["crop"][0] + value["crop"][2] for value in crop_values)
        top = min(value["crop"][1] for value in crop_values)
        bottom_edge = max(value["crop"][1] + value["crop"][3] for value in crop_values)
        box = [left, top, right, bottom_edge]
    else:
        box = [0, 0, 0, 0]
    return {
        "header": header,
        "zones": zones,
        "geometry": {
            "box": box,
            "visual_review": "ocr_bootstrap_unreviewed",
            "lines": geometry_lines,
        },
        "row_records": row_records,
        "heading_rows": [row for row in flow if id(row) in headings],
        "top_rows": [row for row in rows if row["centre_y"] < header["centre_y"] - 20],
        "bottom_rows": bottom,
        "uncertain_bottom_rows": uncertain_bottom,
        "start_expected_letter": start_expected_letter,
        "final_expected_letter": expected_letter,
        "audit": {
            "raw_candidates": len(draft["columns"][column]["lines"]),
            "grouped_rows": len(rows),
            "duplicate_candidates_collapsed": sum(row["duplicate_candidates"] for row in rows),
            "body_lines": len(geometry_lines),
            "internal_heading_lines": len(headings),
            "line_spacing": round(spacing, 2),
            "body_cutoff_y": round(cutoff, 2),
            "indent_threshold": round(threshold, 2),
            "initial_repairs": repairs,
            "low_margin_typeface_tokens": low_margin,
            "uncertain_bottom_rows": [row["text"] for row in uncertain_bottom],
            "post_heading_initial_candidates": post_heading_initial_candidates,
        },
    }


def furniture_zone(column_number: int, position: str, rows: list[dict]) -> dict | None:
    if not rows:
        return None
    return {
        "id": f"{position}-furniture-column-{column_number}",
        "kind": "unclassified_furniture",
        "label": f"Provisional {position} furniture, column {column_number}",
        "note": "OCR bootstrap retained this material without assigning a final page role.",
        "lines": [
            {
                "id": f"u{column_number}{position[0]}-l{index:03d}",
                "runs": [{"typeface": "display", "text": row["text"]}],
            }
            for index, row in enumerate(rows, start=1)
        ],
    }


def previous_section_letter(first_page: int) -> str | None:
    for number in range(first_page - 1, 0, -1):
        path = LEVEL1 / f"{page_id(number)}.json"
        if not path.exists():
            continue
        page = load_json(path)
        readings = [
            heading_letter(line_text(line))
            for zone in page["zones"]
            if zone.get("kind") in {"running_header", "section_heading", "internal_heading"}
            for line in zone.get("lines", [])
        ]
        readings = [reading for reading in readings if reading]
        if readings:
            return readings[-1]
    return None


def infer_page(draft: dict, model: TypefaceModel, previous_letter: str | None) -> tuple[dict, dict, dict, str | None]:
    identifier = draft["id"]
    number = page_number(identifier)
    clustered = {
        column: cluster_rows(draft["columns"][column]["lines"])
        for column in ("column-1", "column-2")
    }
    headers = {
        column: header_row(
            clustered[column], draft["source"]["source_size"][1]
        )
        for column in clustered
    }
    expected = choose_page_letter([headers["column-1"]["text"]], previous_letter)
    column_1 = infer_column(draft, "column-1", model, expected)
    column_2_expected = choose_page_letter(
        [headers["column-2"]["text"]], column_1["final_expected_letter"]
    )
    columns = {
        "column-1": column_1,
        "column-2": infer_column(draft, "column-2", model, column_2_expected),
    }
    page_zones = []
    for column_number, column in enumerate(("column-1", "column-2"), start=1):
        result = columns[column]
        top_zone = furniture_zone(column_number, "top", result["top_rows"])
        if top_zone:
            page_zones.append(top_zone)
        header_text = result["header"]["text"]
        raw_header_letter = heading_letter(header_text)
        resolved_header_letter = resolve_heading_letter(
            raw_header_letter, result["start_expected_letter"]
        )
        if (
            resolved_header_letter
            and raw_header_letter
            and resolved_header_letter != raw_header_letter
        ):
            header_text = resolved_header_letter + header_text[1:]
        page_zones.append(
            {
                "id": f"header-column-{column_number}",
                "kind": "running_header",
                "label": f"Column {column_number} running header",
                "lines": [
                    {
                        "id": f"h{column_number}-l001",
                        "runs": [{"typeface": "display", "text": header_text}],
                    }
                ],
            }
        )
        page_zones.extend(result["zones"])
        bottom_zone = furniture_zone(column_number, "bottom", result["bottom_rows"])
        if bottom_zone:
            page_zones.append(bottom_zone)
    page = {
        "format": "nippo-level1-page",
        "format_version": 1,
        "id": identifier,
        "source": {
            "repository": "BnF Gallica",
            "view": f"f{number}",
            "url": f"https://gallica.bnf.fr/ark:/12148/bpt6k852354j/f{number}.item",
            "master_sha256": scan_digest(number),
        },
        "scope": "full_dictionary_text_and_furniture",
        "review": {
            "origin": "independent_ocr_scan_bootstrap",
            "wikisource_used_for_this_trial": False,
            "physical_lineation_checked": False,
            "status": "visual_draft",
        },
        "zones": page_zones,
    }
    geometry = {
        "id": identifier,
        "source_size": draft["source"]["source_size"],
        "columns": {
            column: columns[column]["geometry"]
            for column in ("column-1", "column-2")
        },
    }
    evidence = {
        "format": "nippo-ocr-level1-bootstrap-candidate",
        "format_version": 1,
        "id": identifier,
        "page": page,
        "geometry": geometry,
        "audit": {
            "expected_main_letter": expected,
            "columns": {column: columns[column]["audit"] for column in columns},
            "lineation": "machine_provisional",
            "canonical_application": "blocked_pending_visual_lineation_and_geometry_review",
        },
    }
    final_expected = columns["column-2"]["final_expected_letter"]
    return page, geometry, evidence, final_expected or expected


def canonical_heading_counts(page: dict) -> dict[str, int]:
    counts = {"column-1": 0, "column-2": 0}
    active = "column-1"
    for zone in page["zones"]:
        if zone["id"] == "header-column-2":
            active = "column-2"
            continue
        if zone.get("kind") in {"section_heading", "internal_heading"}:
            counts[active] += len(zone.get("lines", []))
    return counts


def typeface_at(line: dict) -> list[str]:
    return [run["typeface"] for run in line["runs"] for _ in run["text"]]


def benchmark_page(candidate: dict, canonical: dict, canonical_geometry: dict) -> dict:
    predicted_lines = body_lines(candidate["page"])
    canonical_lines = body_lines(canonical)
    predicted_geometry = candidate["geometry"]["columns"]
    metrics = {
        "page_id": canonical["id"],
        "columns": {},
        "matched": 0,
        "missing": 0,
        "extra": 0,
        "indent_correct": 0,
        "typeface_characters": 0,
        "typeface_correct": 0,
        "matching_text_characters": 0,
        "reference_text_characters": 0,
        "text_edit_distance": 0,
    }
    for column in ("column-1", "column-2"):
        references = [
            {"id": line_id, "centre_y": value["centre_y"]}
            for line_id, value in sorted(
                canonical_geometry["columns"][column]["lines"].items(),
                key=lambda item: item[1]["centre_y"],
            )
        ]
        predictions = [
            {"id": line_id, "centre_y": value["centre_y"]}
            for line_id, value in sorted(
                predicted_geometry[column]["lines"].items(),
                key=lambda item: item[1]["centre_y"],
            )
        ]
        if len(references) == len(predictions):
            # Equal physical-row counts make order the strongest signal. A
            # nearest-y alignment can slip by exactly one line when manually
            # reviewed geometry has accumulated skew relative to Kraken.
            alignment = list(zip(range(len(references)), range(len(predictions))))
            offsets = [
                prediction["centre_y"] - reference["centre_y"]
                for reference, prediction in zip(references, predictions)
            ]
            offset = statistics.median(offsets) if offsets else 0.0
        else:
            # Search a bounded translation before the monotonic positional
            # alignment. This is evaluation-only and is run after inference.
            best = None
            for candidate_offset in range(-100, 101):
                adjusted = [
                    {
                        **prediction,
                        "centre_y": prediction["centre_y"] - candidate_offset,
                    }
                    for prediction in predictions
                ]
                candidate_alignment = position_alignment(
                    references, adjusted, maximum_distance=40
                )
                matched_count = sum(
                    reference_index is not None and prediction_index is not None
                    for reference_index, prediction_index in candidate_alignment
                )
                position_error = sum(
                    abs(
                        references[reference_index]["centre_y"]
                        - adjusted[prediction_index]["centre_y"]
                    )
                    for reference_index, prediction_index in candidate_alignment
                    if reference_index is not None and prediction_index is not None
                )
                score = (matched_count, -position_error, -abs(candidate_offset))
                if best is None or score > best[0]:
                    best = (score, candidate_offset, candidate_alignment)
            assert best is not None
            _, offset, alignment = best
        matched = missing = extra = 0
        for reference_index, prediction_index in alignment:
            if reference_index is None:
                extra += 1
                prediction = predictions[prediction_index]
                metrics["text_edit_distance"] += len(
                    line_text(predicted_lines[prediction["id"]])
                )
                continue
            if prediction_index is None:
                missing += 1
                reference = references[reference_index]
                reference_text = line_text(canonical_lines[reference["id"]])
                metrics["reference_text_characters"] += len(reference_text)
                metrics["text_edit_distance"] += len(reference_text)
                continue
            matched += 1
            reference = references[reference_index]
            prediction = predictions[prediction_index]
            reference_line = canonical_lines[reference["id"]]
            prediction_line = predicted_lines[prediction["id"]]
            metrics["indent_correct"] += int(
                reference_line.get("indent", 0) == prediction_line.get("indent", 0)
            )
            reference_text = line_text(reference_line)
            prediction_text = line_text(prediction_line)
            metrics["reference_text_characters"] += len(reference_text)
            metrics["text_edit_distance"] += edit_distance(
                reference_text, prediction_text
            )
            reference_faces = typeface_at(reference_line)
            prediction_faces = typeface_at(prediction_line)
            for prediction_character, reference_character in character_alignment(
                prediction_text, reference_text
            ):
                if prediction_character is None or reference_character is None:
                    continue
                if prediction_text[prediction_character] != reference_text[reference_character]:
                    continue
                if prediction_text[prediction_character].isspace():
                    continue
                metrics["matching_text_characters"] += 1
                if (
                    prediction_faces[prediction_character] in {"roman", "italic"}
                    and reference_faces[reference_character] in {"roman", "italic"}
                ):
                    metrics["typeface_characters"] += 1
                    metrics["typeface_correct"] += int(
                        prediction_faces[prediction_character]
                        == reference_faces[reference_character]
                    )
        metrics["matched"] += matched
        metrics["missing"] += missing
        metrics["extra"] += extra
        metrics["columns"][column] = {
            "canonical_body_lines": len(references),
            "predicted_body_lines": len(predictions),
            "matched": matched,
            "missing": missing,
            "extra": extra,
            "centre_offset": round(offset, 2),
        }
    canonical_headings = canonical_heading_counts(canonical)
    predicted_headings = {
        column: candidate["audit"]["columns"][column]["internal_heading_lines"]
        for column in ("column-1", "column-2")
    }
    metrics["canonical_heading_lines"] = canonical_headings
    metrics["predicted_heading_lines"] = predicted_headings
    metrics["indent_accuracy"] = metrics["indent_correct"] / max(1, metrics["matched"])
    metrics["typeface_accuracy_on_matching_characters"] = (
        metrics["typeface_correct"] / max(1, metrics["typeface_characters"])
    )
    metrics["character_error_rate"] = metrics["text_edit_distance"] / max(
        1, metrics["reference_text_characters"]
    )
    metrics["character_accuracy"] = max(0.0, 1.0 - metrics["character_error_rate"])
    return metrics


def aggregate_benchmarks(pages: list[dict]) -> dict:
    totals = Counter()
    heading_exact = 0
    for page in pages:
        for key in (
            "matched",
            "missing",
            "extra",
            "indent_correct",
            "typeface_characters",
            "typeface_correct",
            "matching_text_characters",
            "reference_text_characters",
            "text_edit_distance",
        ):
            totals[key] += page[key]
        heading_exact += sum(
            page["canonical_heading_lines"][column]
            == page["predicted_heading_lines"][column]
            for column in ("column-1", "column-2")
        )
    canonical = totals["matched"] + totals["missing"]
    predicted = totals["matched"] + totals["extra"]
    return {
        "pages": len(pages),
        "canonical_body_lines": canonical,
        "predicted_body_lines": predicted,
        "matched_body_lines": totals["matched"],
        "body_line_recall": totals["matched"] / max(1, canonical),
        "body_line_precision": totals["matched"] / max(1, predicted),
        "missing_body_lines": totals["missing"],
        "extra_body_lines": totals["extra"],
        "indent_accuracy": totals["indent_correct"] / max(1, totals["matched"]),
        "typeface_characters": totals["typeface_characters"],
        "typeface_accuracy_on_matching_characters": totals["typeface_correct"]
        / max(1, totals["typeface_characters"]),
        "character_error_rate": totals["text_edit_distance"]
        / max(1, totals["reference_text_characters"]),
        "character_accuracy": max(
            0.0,
            1.0
            - totals["text_edit_distance"]
            / max(1, totals["reference_text_characters"]),
        ),
        "heading_count_exact_columns": heading_exact,
        "heading_count_columns": len(pages) * 2,
    }


def prepare_raw(pages: list[int], args: argparse.Namespace) -> None:
    command = [
        sys.executable,
        str(ROOT / "scripts" / "prepare_calamari_page_drafts.py"),
        "--output",
        str(args.output / "raw"),
        "--pages",
        *map(str, pages),
        "--benchmark-pages",
        "--segmentation-workers",
        str(args.segmentation_workers),
    ]
    if args.fresh_segmentation:
        command.append("--fresh-segmentation")
    if args.fresh_recognition:
        command.append("--fresh-recognition")
    subprocess.run(command, cwd=ROOT, check=True)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--pages", nargs="+", type=int, default=DEFAULT_PAGES)
    result.add_argument(
        "--benchmark-pages", nargs="*", type=int, default=DEFAULT_BENCHMARK_PAGES
    )
    result.add_argument("--train-through", type=int, default=160)
    result.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    result.add_argument("--skip-ocr", action="store_true")
    result.add_argument("--fresh-segmentation", action="store_true")
    result.add_argument("--fresh-recognition", action="store_true")
    result.add_argument("--segmentation-workers", type=int, default=3)
    return result


def main() -> int:
    args = parser().parse_args()
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    targets = sorted(set(args.pages))
    benchmarks = sorted(set(args.benchmark_pages))
    all_pages = sorted(set(targets) | set(benchmarks))
    if not args.skip_ocr:
        prepare_raw(all_pages, args)
    raw_drafts = args.output / "raw" / "drafts"
    missing = [number for number in all_pages if not (raw_drafts / f"{page_id(number)}.json").exists()]
    if missing:
        raise SystemExit(f"missing raw page drafts: {missing}")

    model = TypefaceModel.train(
        training_pages(through=args.train_through, excluded=set(benchmarks) | set(targets))
    )
    candidate_dir = args.output / "candidates"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    inferred: dict[int, dict] = {}
    for number in benchmarks:
        draft = load_json(raw_drafts / f"{page_id(number)}.json")
        _, _, package, _ = infer_page(
            draft, model, previous_section_letter(number)
        )
        write_json(candidate_dir / f"{page_id(number)}.json", package)
        inferred[number] = package
    previous_letter = previous_section_letter(min(targets))
    for number in targets:
        draft = load_json(raw_drafts / f"{page_id(number)}.json")
        _, _, package, previous_letter = infer_page(draft, model, previous_letter)
        write_json(candidate_dir / f"{page_id(number)}.json", package)
        inferred[number] = package

    # Independence checkpoint: canonical benchmark pages and geometry are not
    # opened until every target and benchmark candidate exists on disk.
    geometry_by_id = {
        page["id"]: page for page in load_json(GEOMETRY)["pages"]
    }
    benchmark_results = []
    for number in benchmarks:
        identifier = page_id(number)
        canonical_path = LEVEL1 / f"{identifier}.json"
        if not canonical_path.exists() or identifier not in geometry_by_id:
            continue
        benchmark_results.append(
            benchmark_page(
                inferred[number], load_json(canonical_path), geometry_by_id[identifier]
            )
        )
    aggregate = aggregate_benchmarks(benchmark_results)
    gate = {
        "minimum_body_line_recall": 0.985,
        "minimum_body_line_precision": 0.975,
        "minimum_indent_accuracy": 0.90,
        "minimum_typeface_accuracy": 0.95,
        "minimum_character_accuracy": 0.94,
    }
    passed = (
        aggregate["body_line_recall"] >= gate["minimum_body_line_recall"]
        and aggregate["body_line_precision"] >= gate["minimum_body_line_precision"]
        and aggregate["indent_accuracy"] >= gate["minimum_indent_accuracy"]
        and aggregate["typeface_accuracy_on_matching_characters"]
        >= gate["minimum_typeface_accuracy"]
        and aggregate["character_accuracy"] >= gate["minimum_character_accuracy"]
    )
    target_summary = []
    for number in targets:
        package = inferred[number]
        columns = package["audit"]["columns"]
        target_summary.append(
            {
                "page": number,
                "body_lines": sum(value["body_lines"] for value in columns.values()),
                "heading_lines": sum(
                    value["internal_heading_lines"] for value in columns.values()
                ),
                "uncertain_bottom_rows": sum(
                    len(value["uncertain_bottom_rows"]) for value in columns.values()
                ),
                "initial_repairs": sum(
                    len(value["initial_repairs"]) for value in columns.values()
                ),
            }
        )
    report = {
        "format": "nippo-ocr-level1-bootstrap-report",
        "format_version": 1,
        "method": {
            "target_inference_inputs": [
                "native scan",
                "independent Kraken row detections",
                "independent Calamari text",
                f"roman/italic language model trained on structured pages through f{args.train_through}",
                "preceding page's main alphabet section as sequential context",
            ],
            "target_inference_excludes": [
                "target page transcription",
                "target page canonical geometry",
                "target page review state",
            ],
            "benchmark_opened": "only after all candidate packages were serialized",
            "canonical_application": "blocked pending visual lineation and geometry review",
        },
        "gate": {**gate, "passed": passed},
        "benchmark": {"aggregate": aggregate, "pages": benchmark_results},
        "targets": target_summary,
    }
    write_json(args.output / "report.json", report)
    print(
        f"Wrote {len(all_pages)} scan-first candidate packages; benchmark body-row "
        f"recall {aggregate['body_line_recall']:.2%}, precision "
        f"{aggregate['body_line_precision']:.2%}, indent "
        f"{aggregate['indent_accuracy']:.2%}, typeface "
        f"{aggregate['typeface_accuracy_on_matching_characters']:.2%}, text "
        f"{aggregate['character_accuracy']:.2%}."
    )
    print(f"Safety gate: {'passed' if passed else 'failed'}; canonical files unchanged.")
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
