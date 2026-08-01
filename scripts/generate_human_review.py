#!/usr/bin/env python3
"""Generate the dictionary-wide Nippo Jisho human review interface."""

from __future__ import annotations

import argparse
import html
import json
import os
from pathlib import Path
import re
import sys

from PIL import Image


ALLOWED_REVIEW_STATUSES = {"pending", "needs_correction", "checked"}
REVIEW_UNITS = ("column-1", "column-2", "furniture")
VIEW_LABELS = {
    "page": "Full page",
    "column-1": "Column 1",
    "column-2": "Column 2",
    "furniture": "Page furniture",
}
MASTER_RE = re.compile(r"^f(\d{4})\.jpg$")
LINE_RE = re.compile(r"^\[([^\]]+)\]\s+(.*)$")


class HumanReviewError(Exception):
    pass


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise HumanReviewError(f"cannot read {path}: {error}") from error


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def load_review_record(path: Path) -> dict:
    record = load_json(path)
    if (
        record.get("format") != "nippo-human-column-review"
        or record.get("format_version") != 1
    ):
        raise HumanReviewError(f"{path}: unsupported review-record format")
    pages = record.get("pages")
    if not isinstance(pages, list) or not pages:
        raise HumanReviewError(f"{path}: pages must be a nonempty list")
    seen_pages: set[str] = set()
    for page in pages:
        page_id = page.get("id")
        if not isinstance(page_id, str) or not page_id or page_id in seen_pages:
            raise HumanReviewError(f"{path}: invalid or duplicate page id {page_id!r}")
        seen_pages.add(page_id)
        units = page.get("units")
        if not isinstance(units, dict) or set(units) != set(REVIEW_UNITS):
            raise HumanReviewError(f"{path}:{page_id}: expected three review units")
        for unit_id, state in units.items():
            if not isinstance(state, dict) or state.get("status") not in ALLOWED_REVIEW_STATUSES:
                raise HumanReviewError(f"{path}:{page_id}/{unit_id}: invalid status")
            if state["status"] == "checked" and not (
                state.get("reviewer") and state.get("reviewed_at")
            ):
                raise HumanReviewError(
                    f"{path}:{page_id}/{unit_id}: checked review requires reviewer and reviewed_at"
                )
    return record


def review_registry(record: dict) -> dict[str, dict]:
    return {page["id"]: page["units"] for page in record["pages"]}


def load_tile_boxes(path: Path) -> dict[tuple[str, str], tuple[int, int, int, int]]:
    config = load_json(path)
    if config.get("format") != "nippo-tile-config":
        raise HumanReviewError(f"{path}: unsupported tile configuration")
    boxes: dict[tuple[str, str], tuple[int, int, int, int]] = {}
    for page in config.get("pages", []):
        page_id = page.get("id")
        for zone in page.get("zones", []):
            values = zone.get("box")
            if not (
                isinstance(values, list)
                and len(values) == 4
                and all(isinstance(value, int) for value in values)
            ):
                raise HumanReviewError(f"{path}:{page_id}/{zone.get('id')}: invalid box")
            boxes[(page_id, zone.get("id"))] = tuple(values)
    return boxes


def load_line_spans(path: Path) -> dict[tuple[str, str], tuple[float, float]]:
    config = load_json(path)
    spans: dict[tuple[str, str], tuple[float, float]] = {}
    for page in config.get("pages", []):
        page_id = page.get("id")
        for zone in page.get("zones", []):
            values = zone.get("line_span_percent")
            if values is None:
                continue
            if not (
                isinstance(values, list)
                and len(values) == 2
                and all(isinstance(value, (int, float)) for value in values)
                and 0 <= values[0] < values[1] <= 100
            ):
                raise HumanReviewError(
                    f"{path}:{page_id}/{zone.get('id')}: invalid line span"
                )
            spans[(page_id, zone.get("id"))] = (float(values[0]), float(values[1]))
    return spans


def discover_masters(master_dir: Path) -> list[tuple[int, Path]]:
    masters: list[tuple[int, Path]] = []
    for path in master_dir.glob("f*.jpg"):
        match = MASTER_RE.fullmatch(path.name)
        if match:
            masters.append((int(match.group(1)), path))
    masters.sort()
    if not masters:
        raise HumanReviewError(f"no Gallica masters found in {master_dir}")
    leaf_numbers = [leaf for leaf, _ in masters]
    expected = list(range(leaf_numbers[0], leaf_numbers[-1] + 1))
    if leaf_numbers != expected:
        missing = sorted(set(expected) - set(leaf_numbers))
        raise HumanReviewError(f"master sequence is not contiguous; missing {missing[:10]}")
    return masters


def raw_markdown_lines(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for physical_line in path.read_text(encoding="utf-8").splitlines():
        match = LINE_RE.match(physical_line)
        if not match:
            continue
        line_id = match.group(1).split()[0]
        result[line_id] = physical_line
    return result


def plain_line_text(line: dict) -> str:
    return "".join(run["text"] for run in line["runs"])


def render_runs(runs: list[dict]) -> tuple[str, str]:
    main: list[str] = []
    far_right: list[str] = []
    for run in runs:
        text = html.escape(run["text"])
        if run["typeface"] == "italic":
            rendered = f"<em>{text}</em>"
        elif run["typeface"] == "display":
            rendered = f"<strong>{text}</strong>"
        else:
            rendered = text
        target = far_right if run.get("placement") == "far-right" else main
        target.append(rendered)
    return "".join(main), "".join(far_right)


def render_zone(
    zone: dict,
    raw_lines: dict[str, str],
    view: str,
    paired: bool = False,
    line_span: tuple[float, float] = (5.8, 95.8),
) -> str:
    rendered_lines: list[str] = []
    lines = zone.get("lines", [])
    for index, line in enumerate(lines):
        main, far_right = render_runs(line["runs"])
        indentation = line.get("indent", 0)
        line_id = html.escape(line["id"])
        raw = html.escape(raw_lines.get(line["id"], ""))
        current = html.escape(plain_line_text(line), quote=True)
        reference = html.escape(f"{view}/{line['id']}", quote=True)
        far = f'<span class="far-right">{far_right}</span>' if far_right else ""
        if paired and zone.get("kind") == "column":
            position = (
                50.0
                if len(lines) == 1
                else line_span[0]
                + index / (len(lines) - 1) * (line_span[1] - line_span[0])
            )
            rendered_lines.append(
                f'<article class="line-review" id="{line_id}">'
                f'<div class="line-review-meta"><code>{line_id}</code>'
                f'<span class="line-review-actions">'
                f'<button class="context-line" type="button" aria-expanded="false">Show context</button>'
                f'<button class="copy-line" type="button" data-reference="{reference}" '
                f'data-current="{current}" aria-label="Copy {reference}" title="Copy for chat">Copy</button>'
                f'</span></div>'
                f'<button class="line-scan" type="button" aria-label="Show more context for {reference}">'
                f'<img loading="lazy" alt="Scan strip for {reference}" '
                f'data-scan-unit="{html.escape(zone["id"])}" '
                f'style="--line-position:-{position:.3f}%"></button>'
                f'<div class="paired-transcription rendered-text indent-{indentation}">{main}{far}</div>'
                f'<code class="paired-raw raw-text">{raw}</code></article>'
            )
            continue
        rendered_lines.append(
            f'<div class="transcription-line" id="{line_id}">'
            f'<button class="copy-line" type="button" data-reference="{reference}" '
            f'data-current="{current}" aria-label="Copy {reference}" title="Copy for chat">Copy</button>'
            f'<code class="line-id">{line_id}</code>'
            f'<span class="rendered-text indent-{indentation}">{main}{far}</span>'
            f'<code class="raw-text">{raw}</code></div>'
        )
    if not rendered_lines:
        return ""
    label = html.escape(zone.get("label", zone["id"]))
    zone_class = "zone paired-zone" if paired and zone.get("kind") == "column" else "zone"
    return f'<section class="{zone_class}"><h3>{label}</h3>{"".join(rendered_lines)}</section>'


def zone_ids_for_unit(page: dict, unit: str) -> list[str]:
    if unit == "page":
        return [zone["id"] for zone in page["zones"]]
    if unit == "column-1":
        wanted = {"header-column-1", "column-1"}
        return [zone["id"] for zone in page["zones"] if zone["id"] in wanted]
    if unit == "column-2":
        wanted = {"header-column-2", "column-2"}
        return [zone["id"] for zone in page["zones"] if zone["id"] in wanted]
    return [
        zone["id"]
        for zone in page["zones"]
        if zone.get("kind") != "column"
    ]


def printed_page_number(page: dict) -> str | None:
    for zone in page.get("zones", []):
        if zone.get("kind") != "running_header":
            continue
        for line in zone.get("lines", []):
            for run in line.get("runs", []):
                candidate = run["text"].strip()
                if candidate.isdigit():
                    return candidate
    return None


def relative_href(target: Path, output_dir: Path) -> str:
    return Path(os.path.relpath(target, output_dir)).as_posix()


def estimated_column_box(
    image_size: tuple[int, int],
    unit: str,
) -> tuple[int, int, int, int]:
    width, height = image_size
    top = round(height * 0.07)
    bottom = round(height * 0.92)
    left_margin = round(width * 0.06)
    right_margin = round(width * 0.94)
    middle = (left_margin + right_margin) // 2
    overlap = round(width * 0.025)
    if unit == "column-1":
        return left_margin, top, middle + overlap, bottom
    return middle - overlap, top, right_margin, bottom


def make_processed_images(
    page_id: str,
    master_path: Path,
    boxes: dict[tuple[str, str], tuple[int, int, int, int]],
    assets_dir: Path,
) -> dict[str, str]:
    assets_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, str] = {}
    with Image.open(master_path) as master:
        master.load()
        page_path = assets_dir / f"{page_id}-page.jpg"
        page_image = master.copy()
        if page_image.width > 1800:
            target_height = round(page_image.height * 1800 / page_image.width)
            page_image.thumbnail((1800, target_height), Image.Resampling.LANCZOS)
        page_image.save(page_path, "JPEG", quality=92, subsampling=0, optimize=True)
        result["page"] = f"assets/{page_path.name}"
        result["furniture"] = result["page"]

        for unit in ("column-1", "column-2"):
            box = boxes.get((page_id, unit), estimated_column_box(master.size, unit))
            left, top, right, bottom = box
            if not (0 <= left < right <= master.width and 0 <= top < bottom <= master.height):
                raise HumanReviewError(
                    f"crop for {page_id}/{unit} lies outside {master.width}x{master.height}"
                )
            output_path = assets_dir / f"{page_id}-{unit}.jpg"
            master.crop(box).save(
                output_path, "JPEG", quality=92, subsampling=0, optimize=True
            )
            result[unit] = f"assets/{output_path.name}"
    return result


def processed_page_data(
    page: dict,
    source_path: Path,
    master_path: Path,
    output_dir: Path,
    boxes: dict[tuple[str, str], tuple[int, int, int, int]],
    line_spans: dict[tuple[str, str], tuple[float, float]],
    review: dict[str, dict],
) -> dict:
    page_id = page["id"]
    view = page["source"]["view"]
    raw_lines = raw_markdown_lines(source_path)
    zones = {zone["id"]: zone for zone in page["zones"]}
    units: dict[str, dict] = {}
    for unit in ("page", *REVIEW_UNITS):
        zone_ids = zone_ids_for_unit(page, unit)
        unit_html = "".join(
            render_zone(
                zones[zone_id],
                raw_lines,
                view,
                paired=unit in {"column-1", "column-2"},
                line_span=line_spans.get((page_id, zone_id), (5.8, 95.8)),
            )
            for zone_id in zone_ids
            if zone_id in zones
        )
        units[unit] = {
            "label": VIEW_LABELS[unit],
            "html": unit_html,
            "review": review.get(unit, {}).get("status") if unit in REVIEW_UNITS else None,
        }
    images = make_processed_images(
        page_id, master_path, boxes, output_dir / "assets"
    )
    return {
        "processed": True,
        "page_id": page_id,
        "status": page["review"]["status"],
        "printed_page": printed_page_number(page),
        "source": relative_href(source_path, output_dir),
        "images": images,
        "units": units,
    }


def build_corpus(
    masters: list[tuple[int, Path]],
    trial_dir: Path,
    output_dir: Path,
    boxes: dict[tuple[str, str], tuple[int, int, int, int]],
    line_spans: dict[tuple[str, str], tuple[float, float]],
    reviews: dict[str, dict],
) -> list[dict]:
    level1_dir = trial_dir / "level1"
    source_dir = trial_dir / "level1-source"
    page_json = {path.stem: path for path in level1_dir.glob("bnf-f*.json")}
    corpus: list[dict] = []
    found_processed: set[str] = set()
    for leaf, master_path in masters:
        view = f"f{leaf}"
        page_id = f"bnf-f{leaf:04d}"
        base = {
            "leaf": leaf,
            "view": view,
            "page_id": page_id,
            "master": relative_href(master_path, output_dir),
            "gallica": f"https://gallica.bnf.fr/ark:/12148/bpt6k852354j/{view}.item",
        }
        if page_id not in page_json:
            corpus.append(
                {
                    **base,
                    "processed": False,
                    "status": "unprocessed",
                    "printed_page": None,
                    "source": None,
                    "images": {"page": base["master"]},
                    "units": {},
                }
            )
            continue
        page = load_json(page_json[page_id])
        source_path = source_dir / f"{page_id}.md"
        if page.get("id") != page_id or not source_path.exists():
            raise HumanReviewError(f"incomplete Level 1 pair for {page_id}")
        processed = processed_page_data(
            page,
            source_path,
            master_path,
            output_dir,
            boxes,
            line_spans,
            reviews.get(page_id, {}),
        )
        corpus.append({**base, **processed})
        found_processed.add(page_id)
    missing_masters = sorted(set(page_json) - found_processed)
    if missing_masters:
        raise HumanReviewError(f"Level 1 pages have no acquired master: {missing_masters}")
    unknown_reviews = sorted(set(reviews) - found_processed)
    if unknown_reviews:
        raise HumanReviewError(f"review records have no Level 1 page: {unknown_reviews}")
    return corpus


def render_html(corpus: list[dict], title: str) -> str:
    corpus_json = json.dumps(corpus, ensure_ascii=False, separators=(",", ":")).replace(
        "</", "<\\/"
    )
    processed_count = sum(page["processed"] for page in corpus)
    first_leaf = corpus[0]["leaf"]
    last_leaf = corpus[-1]["leaf"]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
:root {{ color-scheme:light; --paper:#f4efe4; --ink:#25231f; --muted:#716b61; --line:#d4cbbb; --accent:#745b32; --panel:#fffdf7; --ok:#37664c; --wait:#80621f; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; color:var(--ink); background:var(--paper); font-family:ui-sans-serif,system-ui,-apple-system,sans-serif; }}
button,select,input {{ font:inherit; }}
button,select,input[type=number] {{ border:1px solid var(--line); border-radius:.38rem; color:var(--ink); background:var(--panel); }}
button {{ padding:.45rem .7rem; cursor:pointer; }} button:hover:not(:disabled) {{ border-color:var(--accent); }}
button:disabled {{ cursor:not-allowed; opacity:.45; }}
.topbar {{ position:sticky; top:0; z-index:20; display:grid; grid-template-columns:minmax(13rem,1fr) auto auto; gap:1rem; align-items:center; padding:.7rem 1rem; border-bottom:1px solid var(--line); background:rgba(244,239,228,.97); backdrop-filter:blur(8px); }}
.brand h1 {{ margin:0; font:600 1.15rem Georgia,serif; }} .brand p {{ margin:.12rem 0 0; color:var(--muted); font-size:.72rem; }}
.leaf-nav,.utility-nav {{ display:flex; align-items:center; gap:.45rem; }}
.leaf-nav label {{ color:var(--muted); font-size:.78rem; }} #leaf-input {{ width:5.6rem; padding:.44rem .5rem; }}
.workspace {{ max-width:1900px; margin:auto; padding:.9rem 1rem 1.1rem; }}
.page-heading {{ display:flex; align-items:end; gap:1rem; margin:0 0 .65rem; }}
.page-heading h2 {{ margin:0; font:600 1.45rem Georgia,serif; }} .page-heading p {{ margin:.15rem 0 0; color:var(--muted); font-size:.8rem; }}
.badges {{ display:flex; gap:.45rem; margin-left:auto; flex-wrap:wrap; justify-content:end; }}
.badge {{ border:1px solid var(--line); border-radius:99px; padding:.33rem .62rem; color:var(--muted); background:var(--panel); font-size:.78rem; }}
.badge.processed,.badge.human-checked {{ color:var(--ok); border-color:#a9c5b5; }} .badge.unprocessed {{ color:var(--wait); }}
.view-tabs {{ display:flex; align-items:center; gap:.4rem; margin:0 0 .65rem; }}
.view-tabs button.active {{ color:white; border-color:var(--accent); background:var(--accent); }}
.comparison {{ display:grid; grid-template-columns:minmax(0,1fr) minmax(34rem,1fr); min-height:calc(100vh - 11.7rem); border:1px solid var(--line); border-radius:.55rem; overflow:hidden; background:var(--panel); box-shadow:0 8px 28px rgba(56,44,25,.08); }}
.comparison.line-paired-mode {{ display:block; }}
.line-paired-mode .scan-pane {{ display:none; }}
.line-paired-mode .text-pane {{ min-height:calc(100vh - 11.7rem); }}
.line-paired-mode .transcription {{ width:min(100%,88rem); height:calc(100vh - 14.8rem); margin:auto; padding:1rem 1.4rem 4rem; }}
.scan-pane,.text-pane {{ min-width:0; display:flex; flex-direction:column; }} .scan-pane {{ border-right:1px solid var(--line); background:#c9c0af; }}
.pane-toolbar {{ min-height:3rem; display:flex; align-items:center; gap:.8rem; padding:.5rem .75rem; border-bottom:1px solid var(--line); background:var(--panel); color:var(--muted); font-size:.8rem; }}
.pane-toolbar strong {{ color:var(--ink); }} .pane-toolbar a {{ color:var(--accent); }} .push {{ margin-left:auto; }}
.pane-toolbar label {{ display:flex; align-items:center; gap:.35rem; }} .zoom {{ width:7rem; }}
.image-frame,.transcription {{ height:calc(100vh - 14.8rem); overflow:auto; }}
.image-frame {{ padding:.7rem; text-align:center; }} .image-frame img {{ display:block; width:100%; max-width:none; height:auto; margin:auto; box-shadow:0 2px 12px rgba(0,0,0,.22); }}
.transcription {{ padding:1rem 1.05rem 3rem; background:#fffefa; }}
.zone {{ margin:0 0 1.25rem; }} .zone h3 {{ position:sticky; top:-1rem; z-index:2; margin:0 0 .5rem; padding:.45rem 0; color:var(--muted); background:#fffefa; font:600 .73rem ui-sans-serif,system-ui,sans-serif; letter-spacing:.06em; text-transform:uppercase; }}
.transcription-line {{ display:grid; grid-template-columns:3.4rem 5.4rem minmax(0,1fr); gap:.55rem; align-items:start; padding:.13rem .18rem; border-radius:.2rem; font:clamp(.94rem,1.05vw,1.12rem)/1.45 Georgia,'Times New Roman',serif; }}
.transcription-line:hover {{ background:#f4efe4; }} .copy-line {{ opacity:.28; padding:.18rem .35rem; font:10px ui-sans-serif,system-ui,sans-serif; }}
.transcription-line:hover .copy-line,.copy-line:focus {{ opacity:1; }} .line-id {{ padding-top:.16rem; color:#8a8173; font:11px/1.45 ui-monospace,SFMono-Regular,monospace; }}
.rendered-text {{ min-width:0; white-space:pre-wrap; }} .indent-1 {{ padding-left:1.5em; }} .indent-2 {{ padding-left:3em; }} .far-right {{ float:right; margin-left:1.5rem; }}
.raw-text {{ display:none; min-width:0; overflow-wrap:anywhere; white-space:pre-wrap; color:#463e31; font:13px/1.5 ui-monospace,SFMono-Regular,monospace; }}
.raw-mode .rendered-text,.raw-mode .line-id {{ display:none; }} .raw-mode .raw-text {{ display:block; }} .raw-mode .transcription-line {{ grid-template-columns:3.4rem minmax(0,1fr); }}
.paired-zone {{ margin-bottom:0; }}
.paired-zone > h3 {{ margin-bottom:.8rem; }}
.line-review {{ margin:0 0 1.15rem; overflow:hidden; border:1px solid var(--line); border-radius:.48rem; background:#fffdf8; box-shadow:0 2px 8px rgba(56,44,25,.06); }}
.line-review-meta {{ display:flex; align-items:center; min-height:2.15rem; padding:.25rem .45rem .25rem .75rem; border-bottom:1px solid var(--line); color:var(--muted); background:#f7f2e8; font:11px/1.3 ui-monospace,SFMono-Regular,monospace; }}
.line-review-actions {{ display:flex; gap:.35rem; margin-left:auto; }}
.line-review-actions button {{ padding:.22rem .45rem; color:var(--muted); background:#fffdf8; font:11px/1.2 ui-sans-serif,system-ui,sans-serif; }}
.line-review .copy-line {{ opacity:1; }}
.line-scan {{ position:relative; display:block; width:100%; height:clamp(3.8rem,5vw,4.5rem); overflow:hidden; padding:0; border:0; border-radius:0; background:#c9c0af; cursor:zoom-in; }}
.line-scan img {{ position:absolute; top:50%; left:0; display:block; width:100%; max-width:none; height:auto; transform:translateY(var(--line-position)); }}
.line-review.expanded .line-scan {{ height:clamp(12rem,18vw,18rem); cursor:zoom-out; }}
.paired-transcription {{ min-height:3.55rem; padding:.68rem 3.6% .72rem; border-top:1px solid #dfd5c4; white-space:pre-wrap; font:clamp(1.05rem,1.55vw,1.38rem)/1.5 Georgia,'Times New Roman',serif; }}
.paired-raw {{ padding:.7rem 3.6% .8rem; }}
.raw-mode .paired-transcription {{ display:none; }}
.raw-mode .paired-raw {{ display:block; }}
.empty-state {{ display:grid; place-content:center; min-height:100%; padding:2rem; text-align:center; color:var(--muted); }} .empty-state strong {{ display:block; margin-bottom:.35rem; color:var(--ink); font:600 1.35rem Georgia,serif; }}
#toast {{ position:fixed; right:1rem; bottom:1rem; z-index:30; padding:.55rem .8rem; border-radius:.4rem; color:white; background:#2f4939; box-shadow:0 5px 18px rgba(0,0,0,.2); }}
.hidden {{ display:none !important; }}
@media (max-width:1050px) {{
  .topbar {{ grid-template-columns:1fr; }} .brand p {{ display:none; }} .leaf-nav,.utility-nav {{ flex-wrap:wrap; }}
  .page-heading {{ align-items:start; }} .comparison {{ grid-template-columns:1fr; }} .scan-pane {{ border-right:0; border-bottom:1px solid var(--line); }}
  .image-frame,.transcription {{ height:56vh; }} .copy-line {{ opacity:.75; }}
  .line-paired-mode .transcription {{ height:56vh; padding:.7rem .55rem 3rem; }}
  .line-scan {{ height:clamp(3.8rem,8vw,4.5rem); }}
}}
</style>
</head>
<body>
<header class="topbar">
  <div class="brand"><h1>{html.escape(title)}</h1><p>{len(corpus)} acquired leaves · {processed_count} transcribed · {len(corpus)-processed_count} unprocessed</p></div>
  <nav class="leaf-nav" aria-label="Leaf navigation">
    <button id="previous" type="button">←</button>
    <label for="leaf-input">Gallica f</label><input id="leaf-input" type="number" min="{first_leaf}" max="{last_leaf}" value="{first_leaf}">
    <button id="go" type="button">Go</button><span id="leaf-total">of f{last_leaf}</span>
    <button id="next" type="button">→</button>
  </nav>
  <div class="utility-nav"><button id="reload" type="button">Reload latest</button></div>
</header>
<main class="workspace">
  <div class="page-heading">
    <div><h2 id="page-title"></h2><p id="page-subtitle"></p></div>
    <div class="badges"><span id="page-status" class="badge"></span><span id="review-status" class="badge"></span></div>
  </div>
  <nav class="view-tabs" aria-label="Page view">
    <button type="button" data-unit="page">Full page</button>
    <button type="button" data-unit="column-1">Column 1</button>
    <button type="button" data-unit="column-2">Column 2</button>
    <button type="button" data-unit="furniture">Page furniture</button>
  </nav>
  <div class="comparison">
    <section class="scan-pane">
      <div class="pane-toolbar"><strong>Scan</strong><label>Zoom <input id="zoom" class="zoom" type="range" min="100" max="320" value="100"></label><a id="gallica-link" class="push" target="_blank">Gallica</a><a id="master-link" target="_blank">Full resolution</a></div>
      <div class="image-frame"><img id="scan-image" alt=""></div>
    </section>
    <section class="text-pane">
      <div class="pane-toolbar"><strong id="text-heading">Level 1 transcription</strong><button id="mode-toggle" type="button">Show Markdown</button><a id="source-link" class="push" target="_blank">Source Markdown</a></div>
      <div id="transcription" class="transcription"></div>
    </section>
  </div>
</main>
<div id="toast" class="hidden" role="status">Copied for chat</div>
<script>
const corpus = {corpus_json};
const byLeaf = new Map(corpus.map(page => [page.leaf, page]));
const firstLeaf = {first_leaf};
const lastLeaf = {last_leaf};
const tabs = [...document.querySelectorAll('.view-tabs button')];
let currentLeaf = firstLeaf;
let currentUnit = 'page';
let rawMode = false;
let toastTimer;

function parseHash() {{
  const match = decodeURIComponent(location.hash).match(/^#f(\\d+)(?::(page|column-1|column-2|furniture))?$/);
  if (!match) return null;
  const leaf = Number(match[1]);
  return byLeaf.has(leaf) ? {{leaf,unit:match[2] || 'page'}} : null;
}}
function humanSummary(page) {{
  if (!page.processed) return 'Human review: unavailable';
  const states = ['column-1','column-2','furniture'].map(unit => page.units[unit].review || 'pending');
  const checked = states.filter(value => value === 'checked').length;
  const corrections = states.filter(value => value === 'needs_correction').length;
  return corrections ? `Human review: ${{corrections}} needs correction` : `Human review: ${{checked}} / 3 checked`;
}}
function emptyState(page) {{
  return `<div class="empty-state"><div><strong>Not yet processed</strong><span>${{page.view}} currently has only its acquired scan. Its transcription will appear here after generation.</span></div></div>`;
}}
function setLocation(leaf, unit, replace=false) {{
  const hash = `#f${{leaf}}:${{unit}}`;
  if (replace) history.replaceState(null, '', hash); else history.pushState(null, '', hash);
}}
function show(leaf, requestedUnit='page', updateLocation=true) {{
  const page = byLeaf.get(Math.max(firstLeaf, Math.min(lastLeaf, leaf)));
  if (!page) return;
  currentLeaf = page.leaf;
  currentUnit = page.processed ? requestedUnit : 'page';
  const pairedMode = page.processed && ['column-1','column-2'].includes(currentUnit);
  document.querySelector('.comparison').classList.toggle('line-paired-mode', pairedMode);
  document.getElementById('leaf-input').value = page.leaf;
  document.getElementById('previous').disabled = page.leaf === firstLeaf;
  document.getElementById('next').disabled = page.leaf === lastLeaf;
  document.getElementById('page-title').textContent = `${{page.view}} · ${{VIEW_LABELS[currentUnit] || 'Full page'}}`;
  document.getElementById('page-subtitle').textContent = page.printed_page ? `Printed page ${{page.printed_page}} · ${{page.page_id}}` : page.page_id;
  const pageStatus = document.getElementById('page-status');
  pageStatus.textContent = page.processed ? `Level 1: ${{page.status.replaceAll('_',' ')}}` : 'Unprocessed';
  pageStatus.className = `badge ${{page.processed ? 'processed' : 'unprocessed'}}`;
  const reviewStatus = document.getElementById('review-status');
  reviewStatus.textContent = humanSummary(page);
  reviewStatus.className = 'badge';
  tabs.forEach(tab => {{
    tab.classList.toggle('active', tab.dataset.unit === currentUnit);
    tab.disabled = !page.processed && tab.dataset.unit !== 'page';
  }});
  const image = document.getElementById('scan-image');
  image.src = page.processed ? page.images[currentUnit] : page.master;
  image.alt = `${{page.view}} ${{VIEW_LABELS[currentUnit] || 'Full page'}} scan`;
  image.style.width = `${{document.getElementById('zoom').value}}%`;
  document.querySelector('.image-frame').scrollTo(0,0);
  document.getElementById('gallica-link').href = page.gallica;
  document.getElementById('master-link').href = page.master;
  const source = document.getElementById('source-link');
  source.classList.toggle('hidden', !page.processed);
  if (page.processed) source.href = page.source;
  document.getElementById('mode-toggle').disabled = !page.processed;
  document.getElementById('text-heading').textContent = pairedMode ? 'Line-by-line comparison' : 'Level 1 transcription';
  const transcription = document.getElementById('transcription');
  transcription.innerHTML = page.processed ? page.units[currentUnit].html : emptyState(page);
  if (page.processed) {{
    transcription.querySelectorAll('.line-scan img').forEach(strip => {{
      strip.src = page.images[strip.dataset.scanUnit];
    }});
  }}
  transcription.classList.toggle('raw-mode', rawMode && page.processed);
  transcription.scrollTo(0,0);
  if (updateLocation) setLocation(page.leaf, currentUnit);
}}
const VIEW_LABELS = {json.dumps(VIEW_LABELS, ensure_ascii=False)};
tabs.forEach(tab => tab.addEventListener('click', () => show(currentLeaf, tab.dataset.unit)));
document.getElementById('previous').addEventListener('click', () => show(currentLeaf - 1, currentUnit));
document.getElementById('next').addEventListener('click', () => show(currentLeaf + 1, currentUnit));
function goToInput() {{
  const value = Number(document.getElementById('leaf-input').value);
  if (Number.isInteger(value) && byLeaf.has(value)) show(value, currentUnit);
}}
document.getElementById('go').addEventListener('click', goToInput);
document.getElementById('leaf-input').addEventListener('keydown', event => {{ if (event.key === 'Enter') goToInput(); }});
document.getElementById('reload').addEventListener('click', () => location.reload());
document.getElementById('zoom').addEventListener('input', event => {{ document.getElementById('scan-image').style.width = `${{event.target.value}}%`; }});
document.getElementById('mode-toggle').addEventListener('click', event => {{
  rawMode = !rawMode;
  document.getElementById('transcription').classList.toggle('raw-mode', rawMode);
  event.target.textContent = rawMode ? 'Show rendered text' : 'Show Markdown';
}});
async function copyText(text) {{
  const fallback = document.createElement('textarea');
  fallback.value = text;
  fallback.setAttribute('readonly', '');
  fallback.style.position = 'fixed';
  fallback.style.opacity = '0';
  document.body.appendChild(fallback);
  fallback.select();
  const copied = document.execCommand('copy');
  fallback.remove();
  if (copied) return true;
  if (navigator.clipboard && navigator.clipboard.writeText) {{
    try {{ await navigator.clipboard.writeText(text); return true; }} catch (_) {{}}
  }}
  return false;
}}
document.getElementById('transcription').addEventListener('click', async event => {{
  const contextButton = event.target.closest('.context-line');
  const stripButton = event.target.closest('.line-scan');
  if (contextButton || stripButton) {{
    const review = event.target.closest('.line-review');
    const expanded = review.classList.toggle('expanded');
    const control = review.querySelector('.context-line');
    control.textContent = expanded ? 'Hide context' : 'Show context';
    control.setAttribute('aria-expanded', String(expanded));
    return;
  }}
  const button = event.target.closest('.copy-line');
  if (!button) return;
  const text = `${{button.dataset.reference}}\\nCurrent: ${{button.dataset.current}}`;
  const copied = await copyText(text);
  const toast = document.getElementById('toast');
  toast.textContent = copied ? 'Copied for chat' : 'Copy unavailable in this browser';
  toast.classList.remove('hidden');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.add('hidden'), 1300);
}});
window.addEventListener('popstate', () => {{
  const target = parseHash();
  if (target) show(target.leaf, target.unit, false);
}});
document.addEventListener('keydown', event => {{
  if (event.altKey && event.key === 'ArrowLeft') show(currentLeaf - 1, currentUnit);
  if (event.altKey && event.key === 'ArrowRight') show(currentLeaf + 1, currentUnit);
}});
const initial = parseHash() || {{leaf:firstLeaf,unit:'page'}};
show(initial.leaf, initial.unit, false);
setLocation(initial.leaf, currentUnit, true);
</script>
</body>
</html>
"""


def generate(
    review_path: Path,
    trial_dir: Path,
    tile_config_path: Path,
    master_dir: Path,
    output_dir: Path,
) -> dict[str, int]:
    record = load_review_record(review_path)
    boxes = load_tile_boxes(tile_config_path)
    line_spans = load_line_spans(tile_config_path)
    masters = discover_masters(master_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    corpus = build_corpus(
        masters, trial_dir, output_dir, boxes, line_spans, review_registry(record)
    )
    title = record.get("title", "Nippo Jisho · Human review")
    atomic_write(
        output_dir / "corpus.json",
        json.dumps(
            {
                "format": "nippo-human-review-corpus",
                "format_version": 1,
                "pages": corpus,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    atomic_write(output_dir / "index.html", render_html(corpus, title))
    return {
        "pages": len(corpus),
        "processed": sum(page["processed"] for page in corpus),
        "unprocessed": sum(not page["processed"] for page in corpus),
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--review-record",
        type=Path,
        default=root / "pilot" / "human-review" / "review-status.json",
    )
    parser.add_argument(
        "--trial-dir", type=Path, default=root / "pilot" / "format-v1-trial"
    )
    parser.add_argument(
        "--tile-config",
        type=Path,
        default=root / "pilot" / "tile-config-v1-trial.json",
    )
    parser.add_argument(
        "--master-dir",
        type=Path,
        default=root / ".cache" / "sources" / "bnf-gallica" / "master",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=root / "build" / "human-review"
    )
    args = parser.parse_args()
    try:
        stats = generate(
            args.review_record.resolve(),
            args.trial_dir.resolve(),
            args.tile_config.resolve(),
            args.master_dir.resolve(),
            args.output_dir.resolve(),
        )
        print(
            f"Generated {stats['pages']} leaves: {stats['processed']} transcribed, "
            f"{stats['unprocessed']} unprocessed."
        )
        print(f"Interface: {args.output_dir.resolve() / 'index.html'}")
        return 0
    except (HumanReviewError, OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
