#!/usr/bin/env python3
"""Compile or export the compact Level 1 Markdown authoring format."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import unicodedata


class Level1MarkdownError(Exception):
    pass


ZONE_RE = re.compile(r"^## ([a-z0-9-]+) \[([a-z0-9_-]+)\] (.+)$")
LINE_RE = re.compile(r"^\[([a-z0-9-]+)(?: (>|>>))?\] (.*)$")
SPAN_RE = re.compile(r"^\{([a-z0-9_-]+)\}(.*)$")

REQUIRED_METADATA = {
    "id",
    "source",
    "view",
    "url",
    "sha256",
    "scope",
    "origin",
    "wikisource",
    "lineation",
    "status",
}

ALLOWED_STATUSES = {
    "visual_draft",
    "context_reviewed",
    "scan_confirmed",
    "human_checked",
    "trial_reviewed",
}


def fail(path: Path, line_number: int, message: str) -> Level1MarkdownError:
    return Level1MarkdownError(f"{path}:{line_number}: {message}")


def parse_bool(value: str, path: Path, line_number: int) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    raise fail(path, line_number, f"expected true or false, found {value!r}")


def append_run(runs: list[dict], typeface: str, text: str) -> None:
    if not text:
        return
    if runs and runs[-1]["typeface"] == typeface and "span_id" not in runs[-1]:
        runs[-1]["text"] += text
    else:
        runs.append({"typeface": typeface, "text": text})


def parse_inline(text: str, path: Path, line_number: int) -> list[dict]:
    runs: list[dict] = []
    cursor = 0
    while cursor < len(text):
        if text.startswith("**", cursor):
            marker = "**"
            typeface = "display"
        elif text.startswith("*", cursor):
            marker = "*"
            typeface = "italic"
        else:
            next_marker = text.find("*", cursor)
            end = len(text) if next_marker < 0 else next_marker
            append_run(runs, "roman", text[cursor:end])
            cursor = end
            continue

        end = text.find(marker, cursor + len(marker))
        if end < 0:
            raise fail(path, line_number, f"unclosed {marker!r} emphasis marker")
        content = text[cursor + len(marker) : end]
        if not content:
            raise fail(path, line_number, "empty emphasized span")

        leading = ""
        if runs and runs[-1]["typeface"] == "roman":
            previous = runs[-1]["text"]
            stripped = previous.rstrip(" ")
            leading = previous[len(stripped) :]
            if leading:
                runs[-1]["text"] = stripped
                if not stripped:
                    runs.pop()
        append_run(runs, typeface, leading + content)
        cursor = end + len(marker)

    if not runs:
        raise fail(path, line_number, "line contains no text")
    return runs


def parse_cell(text: str, path: Path, line_number: int) -> list[dict]:
    span_id = None
    match = SPAN_RE.match(text)
    if match:
        span_id = match.group(1)
        text = match.group(2)
    runs = parse_inline(text, path, line_number)
    if span_id:
        if len(runs) != 1:
            raise fail(path, line_number, "a labelled cell must contain exactly one typeface run")
        runs[0]["span_id"] = span_id
    return runs


def parse_markdown(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if unicodedata.normalize("NFC", text) != text:
        raise Level1MarkdownError(f"{path}: source is not NFC-normalized")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise Level1MarkdownError(f"{path}: missing opening metadata delimiter")
    try:
        metadata_end = lines.index("---", 1)
    except ValueError as error:
        raise Level1MarkdownError(f"{path}: missing closing metadata delimiter") from error

    metadata: dict[str, str] = {}
    for index, line in enumerate(lines[1:metadata_end], start=2):
        if ": " not in line:
            raise fail(path, index, "metadata must use 'key: value'")
        key, value = line.split(": ", 1)
        if key in metadata:
            raise fail(path, index, f"duplicate metadata key {key!r}")
        metadata[key] = value
    if metadata.get("format") != "nippo-level1-markdown" or metadata.get("version") != "1":
        raise Level1MarkdownError(f"{path}: unsupported authoring format")
    missing = REQUIRED_METADATA - metadata.keys()
    if missing:
        raise Level1MarkdownError(f"{path}: missing metadata: {sorted(missing)}")

    digest = metadata["sha256"]
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise Level1MarkdownError(f"{path}: invalid source SHA-256")
    if metadata["lineation"] != "checked":
        raise Level1MarkdownError(f"{path}: lineation must be 'checked'")
    if metadata["status"] not in ALLOWED_STATUSES:
        raise Level1MarkdownError(
            f"{path}: unsupported review status {metadata['status']!r}"
        )

    page = {
        "format": "nippo-level1-page",
        "format_version": 1,
        "id": metadata["id"],
        "source": {
            "repository": metadata["source"],
            "view": metadata["view"],
            "url": metadata["url"],
            "master_sha256": digest,
        },
        "scope": metadata["scope"],
        "review": {
            "origin": metadata["origin"],
            "wikisource_used_for_this_trial": parse_bool(
                metadata["wikisource"], path, lines.index(f"wikisource: {metadata['wikisource']}") + 1
            ),
            "physical_lineation_checked": True,
            "status": metadata["status"],
        },
        "zones": [],
    }
    if "external-check" in metadata:
        page["review"]["external_check_scope"] = metadata["external-check"]

    current_zone = None
    line_ids: set[str] = set()
    span_ids: set[tuple[str, str]] = set()
    for line_number, line in enumerate(lines[metadata_end + 1 :], start=metadata_end + 2):
        if not line:
            continue
        zone_match = ZONE_RE.match(line)
        if zone_match:
            current_zone = {
                "id": zone_match.group(1),
                "kind": zone_match.group(2),
                "label": zone_match.group(3),
            }
            page["zones"].append(current_zone)
            continue
        if line.startswith("> "):
            if current_zone is None:
                raise fail(path, line_number, "zone note appears before a zone heading")
            if "note" in current_zone:
                raise fail(path, line_number, "a zone may contain only one note")
            current_zone["note"] = line[2:]
            continue
        match = LINE_RE.match(line)
        if not match:
            raise fail(path, line_number, "expected a zone heading, zone note, or physical line")
        if current_zone is None:
            raise fail(path, line_number, "physical line appears before a zone heading")
        line_id, flag, content = match.groups()
        if line_id in line_ids:
            raise fail(path, line_number, f"duplicate physical-line id {line_id!r}")
        line_ids.add(line_id)

        cells = content.split(" || ")
        if flag == ">>" and len(cells) != 1:
            raise fail(path, line_number, "a wholly far-right line cannot also use far-right cells")
        record: dict = {"id": line_id}
        if flag == ">":
            record["indent"] = 1
        runs = parse_cell(cells[0], path, line_number)
        if any("span_id" in run for run in runs):
            raise fail(path, line_number, "named spans are supported only in far-right cells")
        if flag == ">>":
            for run in runs:
                run["placement"] = "far-right"
        for cell in cells[1:]:
            cell_runs = parse_cell(cell, path, line_number)
            for run in cell_runs:
                run["placement"] = "far-right"
            runs.extend(cell_runs)
        for run in runs:
            if "span_id" in run:
                key = (line_id, run["span_id"])
                if key in span_ids:
                    raise fail(path, line_number, f"duplicate span id {run['span_id']!r}")
                span_ids.add(key)
        record["runs"] = runs
        current_zone.setdefault("lines", []).append(record)

    if not page["zones"] or not line_ids:
        raise Level1MarkdownError(f"{path}: no page zones or physical lines")
    return page


def styled_text(run: dict) -> str:
    text = run["text"]
    if run["typeface"] == "roman":
        return text
    marker = "*" if run["typeface"] == "italic" else "**"
    leading = text[: len(text) - len(text.lstrip(" "))]
    trailing = text[len(text.rstrip(" ")) :]
    core_end = len(text) - len(trailing) if trailing else len(text)
    core = text[len(leading) : core_end]
    return f"{leading}{marker}{core}{marker}{trailing}"


def export_markdown(page: dict) -> str:
    review = page["review"]
    metadata = [
        "---",
        "format: nippo-level1-markdown",
        "version: 1",
        f"id: {page['id']}",
        f"source: {page['source']['repository']}",
        f"view: {page['source']['view']}",
        f"url: {page['source']['url']}",
        f"sha256: {page['source']['master_sha256']}",
        f"scope: {page['scope']}",
        f"origin: {review['origin']}",
        f"wikisource: {str(review['wikisource_used_for_this_trial']).lower()}",
        "lineation: checked",
        f"status: {review['status']}",
    ]
    if "external_check_scope" in review:
        metadata.append(f"external-check: {review['external_check_scope']}")
    metadata.extend(["---", ""])

    output = metadata
    for zone in page["zones"]:
        output.extend([f"## {zone['id']} [{zone['kind']}] {zone.get('label', zone['id'])}", ""])
        if "note" in zone:
            output.extend([f"> {zone['note']}", ""])
        for line in zone.get("lines", []):
            normal = [run for run in line["runs"] if run.get("placement", "normal") == "normal"]
            far = [run for run in line["runs"] if run.get("placement") == "far-right"]
            flag = ""
            if line.get("indent") == 1:
                flag = " >"
            if far and not normal:
                flag = " >>"
                content = "".join(styled_text(run) for run in far)
            else:
                content = "".join(styled_text(run) for run in normal)
                for run in far:
                    label = f"{{{run['span_id']}}}" if "span_id" in run else ""
                    rendered = styled_text(run)
                    if not label:
                        rendered = rendered.lstrip(" ")
                    content += f" || {label}{rendered}"
            output.append(f"[{line['id']}{flag}] {content}")
        output.append("")
    return "\n".join(output).rstrip() + "\n"


def write_json(page: dict, path: Path) -> None:
    path.write_text(json.dumps(page, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def command_export(input_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for json_path in sorted(input_dir.glob("*.json")):
        page = json.loads(json_path.read_text(encoding="utf-8"))
        (output_dir / f"{page['id']}.md").write_text(export_markdown(page), encoding="utf-8")


def command_compile(input_dir: Path, output_dir: Path, check: bool) -> None:
    pages = [parse_markdown(path) for path in sorted(input_dir.glob("*.md"))]
    if not pages:
        raise Level1MarkdownError(f"{input_dir}: no Markdown page records")
    page_ids = {page["id"] for page in pages}
    if len(page_ids) != len(pages):
        raise Level1MarkdownError(f"{input_dir}: duplicate page id")
    if check:
        existing_ids = {path.stem for path in output_dir.glob("*.json")}
        if existing_ids != page_ids:
            raise Level1MarkdownError(
                f"{output_dir}: generated page set differs from compact source"
            )
    else:
        output_dir.mkdir(parents=True, exist_ok=True)
    for page in pages:
        output_path = output_dir / f"{page['id']}.json"
        if check:
            if not output_path.exists():
                raise Level1MarkdownError(f"{output_path}: generated JSON is missing")
            existing = json.loads(output_path.read_text(encoding="utf-8"))
            if existing != page:
                raise Level1MarkdownError(f"{output_path}: generated JSON is out of date")
        else:
            write_json(page, output_path)
    print(f"Validated {len(pages)} compact Level 1 page records.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    export_parser = subparsers.add_parser("export", help="export JSON pages to compact Markdown")
    export_parser.add_argument("input_dir", type=Path)
    export_parser.add_argument("output_dir", type=Path)
    compile_parser = subparsers.add_parser("compile", help="compile compact Markdown to JSON")
    compile_parser.add_argument("input_dir", type=Path)
    compile_parser.add_argument("output_dir", type=Path)
    compile_parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "export":
            command_export(args.input_dir, args.output_dir)
        else:
            command_compile(args.input_dir, args.output_dir, args.check)
        return 0
    except (OSError, json.JSONDecodeError, Level1MarkdownError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
