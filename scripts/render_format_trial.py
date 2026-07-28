#!/usr/bin/env python3
"""Validate and render the candidate Nippo Jisho transcription trial."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import unicodedata


ALLOWED_TYPEFACES = {"roman", "italic", "display"}
ALLOWED_PLACEMENTS = {"normal", "far-right"}
ALLOWED_JOINS = {"space", "none", "word", "newline"}


class TrialFormatError(Exception):
    pass


def load_json(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as error:
        raise TrialFormatError(f"cannot read {path}: {error}") from error


def validate_page(page: dict, path: Path) -> dict[str, dict]:
    if page.get("format") != "nippo-level1-page" or page.get("format_version") != 1:
        raise TrialFormatError(f"{path}: unsupported page format")
    page_id = page.get("id")
    if not isinstance(page_id, str) or not page_id:
        raise TrialFormatError(f"{path}: missing page id")
    source = page.get("source", {})
    digest = source.get("master_sha256")
    if not isinstance(digest, str) or len(digest) != 64 or any(
        character not in "0123456789abcdef" for character in digest
    ):
        raise TrialFormatError(f"{path}: invalid or missing source master SHA-256")

    zone_ids: set[str] = set()
    line_ids: set[str] = set()
    lines: dict[str, dict] = {}
    for zone in page.get("zones", []):
        zone_id = zone.get("id")
        if not isinstance(zone_id, str) or not zone_id or zone_id in zone_ids:
            raise TrialFormatError(f"{path}: invalid or duplicate zone id {zone_id!r}")
        zone_ids.add(zone_id)
        for line in zone.get("lines", []):
            line_id = line.get("id")
            if not isinstance(line_id, str) or not line_id or line_id in line_ids:
                raise TrialFormatError(f"{path}: invalid or duplicate line id {line_id!r}")
            line_ids.add(line_id)
            indent = line.get("indent", 0)
            if not isinstance(indent, int) or indent < 0:
                raise TrialFormatError(f"{path}:{line_id}: indent must be a nonnegative integer")
            runs = line.get("runs")
            if not isinstance(runs, list) or not runs:
                raise TrialFormatError(f"{path}:{line_id}: at least one run is required")
            for index, run in enumerate(runs):
                typeface = run.get("typeface")
                text = run.get("text")
                placement = run.get("placement", "normal")
                if typeface not in ALLOWED_TYPEFACES:
                    raise TrialFormatError(
                        f"{path}:{line_id}: run {index} has invalid typeface {typeface!r}"
                    )
                if not isinstance(text, str) or not text:
                    raise TrialFormatError(f"{path}:{line_id}: run {index} has no text")
                if unicodedata.normalize("NFC", text) != text:
                    raise TrialFormatError(f"{path}:{line_id}: run {index} is not NFC")
                if placement not in ALLOWED_PLACEMENTS:
                    raise TrialFormatError(
                        f"{path}:{line_id}: run {index} has invalid placement {placement!r}"
                    )
            span_ids = [run["span_id"] for run in runs if "span_id" in run]
            if any(not isinstance(span_id, str) or not span_id for span_id in span_ids):
                raise TrialFormatError(f"{path}:{line_id}: invalid named span")
            if len(span_ids) != len(set(span_ids)):
                raise TrialFormatError(f"{path}:{line_id}: invalid or duplicate named span")
            ref = f"{page_id}:{line_id}"
            lines[ref] = line
    if not lines:
        raise TrialFormatError(f"{path}: page contains no transcribed lines")
    return lines


def line_text(
    line: dict,
    selected_runs: list[int] | None = None,
    selected_span: str | None = None,
) -> str:
    runs = line["runs"]
    if selected_runs is not None and selected_span is not None:
        raise TrialFormatError(f"{line['id']}: cannot select both runs and a named span")
    if selected_span is not None:
        matches = [run for run in runs if run.get("span_id") == selected_span]
        if len(matches) != 1:
            raise TrialFormatError(
                f"{line['id']}: named span {selected_span!r} does not resolve uniquely"
            )
        return matches[0]["text"]
    if selected_runs is None:
        return "".join(run["text"] for run in runs)
    pieces: list[str] = []
    for index in selected_runs:
        if not isinstance(index, int) or not 0 <= index < len(runs):
            raise TrialFormatError(f"invalid run selector {index!r} for {line['id']}")
        pieces.append(runs[index]["text"])
    return "".join(pieces)


def markdown_run(run: dict) -> str:
    text = run["text"]
    leading = text[: len(text) - len(text.lstrip())]
    trailing = text[len(text.rstrip()) :]
    core_end = len(text) - len(trailing) if trailing else len(text)
    core = text[len(leading) : core_end]
    if not core:
        return text
    if run["typeface"] == "italic":
        return f"{leading}*{core}*{trailing}"
    if run["typeface"] == "display":
        return f"{leading}**{core}**{trailing}"
    return text


def markdown_runs(runs: list[dict]) -> str:
    grouped: list[dict] = []
    for run in runs:
        if grouped and grouped[-1]["typeface"] == run["typeface"]:
            grouped[-1]["text"] += run["text"]
        else:
            grouped.append({"typeface": run["typeface"], "text": run["text"]})
    return "".join(markdown_run(run) for run in grouped)


def render_page(page: dict) -> str:
    output = [f"# Page view: {page['id']}", ""]
    output.append(f"Source: {page['source']['url']}")
    output.extend(["", f"Scope: `{page['scope']}`", ""])
    for zone in page["zones"]:
        output.extend([f"## {zone.get('label', zone['id'])}", ""])
        if "note" in zone:
            output.extend([zone["note"], ""])
        if not zone.get("lines"):
            continue
        output.extend(["| Physical line | Main position | Far right |", "| --- | --- | --- |"])
        for line in zone["lines"]:
            main: list[dict] = []
            far_right: list[dict] = []
            for run in line["runs"]:
                target = far_right if run.get("placement") == "far-right" else main
                target.append(run)
            indentation = "&emsp;" * line.get("indent", 0)
            output.append(
                f"| `{line['id']}` | {indentation}{markdown_runs(main)} | "
                f"{markdown_runs(far_right)} |"
            )
        output.append("")
    return "\n".join(output).rstrip() + "\n"


def validate_structure(structure: dict, registry: dict[str, dict], path: Path) -> None:
    if structure.get("format") != "nippo-level2-trial" or structure.get("format_version") != 1:
        raise TrialFormatError(f"{path}: unsupported structure format")
    ids: set[str] = set()
    for collection in ("assertions", "reading_sequences"):
        for item in structure.get(collection, []):
            item_id = item.get("id")
            if not isinstance(item_id, str) or not item_id or item_id in ids:
                raise TrialFormatError(f"{path}: invalid or duplicate item id {item_id!r}")
            ids.add(item_id)
            refs: list[dict]
            if collection == "assertions":
                refs = item.get("targets", [])
            else:
                refs = item.get("segments", [])
            if not refs:
                raise TrialFormatError(f"{path}:{item_id}: no source references")
            for selector in refs:
                ref = selector.get("line")
                if ref not in registry:
                    raise TrialFormatError(f"{path}:{item_id}: unknown line reference {ref!r}")
                line_text(registry[ref], selector.get("runs"), selector.get("span"))
                if collection == "reading_sequences" and selector.get("join", "space") not in ALLOWED_JOINS:
                    raise TrialFormatError(f"{path}:{item_id}: invalid join operation")


def render_sequences(structure: dict, registry: dict[str, dict]) -> str:
    output = ["# Selected Level 2 reading views", ""]
    output.extend(
        [
            "These views are generated from Level 1 source strings through linked structural assertions.",
            "They are not independent transcriptions.",
            "",
        ]
    )
    for sequence in structure.get("reading_sequences", []):
        assembled = ""
        for index, selector in enumerate(sequence["segments"]):
            text = line_text(
                registry[selector["line"]], selector.get("runs"), selector.get("span")
            )
            if index == 0:
                assembled = text
                continue
            join = selector.get("join", "space")
            if join == "word":
                if not assembled.endswith(("-", "=")):
                    raise TrialFormatError(
                        f"{sequence['id']}: word join requires a preceding visible division mark"
                    )
                assembled = assembled[:-1] + text.lstrip()
            elif join == "none":
                assembled += text
            elif join == "newline":
                assembled += "\n" + text
            else:
                assembled += " " + text
        output.extend([f"## {sequence['label']}", "", assembled, ""])
    return "\n".join(output).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trial_dir", type=Path)
    parser.add_argument("--check", action="store_true", help="validate without writing views")
    args = parser.parse_args()
    trial_dir = args.trial_dir.resolve()
    try:
        registry: dict[str, dict] = {}
        pages: list[dict] = []
        for page_path in sorted((trial_dir / "level1").glob("*.json")):
            page = load_json(page_path)
            page_lines = validate_page(page, page_path)
            overlap = registry.keys() & page_lines.keys()
            if overlap:
                raise TrialFormatError(f"duplicate global line references: {sorted(overlap)}")
            registry.update(page_lines)
            pages.append(page)
        if not pages:
            raise TrialFormatError("no Level 1 page files found")

        structure_path = trial_dir / "level2" / "selected-structure.json"
        structure = load_json(structure_path)
        validate_structure(structure, registry, structure_path)

        if not args.check:
            output_dir = trial_dir / "generated"
            output_dir.mkdir(parents=True, exist_ok=True)
            for page in pages:
                (output_dir / f"{page['id']}-page.md").write_text(
                    render_page(page), encoding="utf-8"
                )
            (output_dir / "selected-reading-views.md").write_text(
                render_sequences(structure, registry), encoding="utf-8"
            )
        print(
            f"Validated {len(pages)} page records, {len(registry)} physical lines, "
            f"{len(structure.get('assertions', []))} assertions, and "
            f"{len(structure.get('reading_sequences', []))} reading sequences."
        )
        return 0
    except TrialFormatError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
