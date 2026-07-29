#!/usr/bin/env python3
"""Generate a side-by-side human review interface for Level 1 pages."""

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
UNIT_DEFINITIONS = (
    ("column-1", "Column 1", ("header-column-1", "column-1"), "column-1"),
    ("column-2", "Column 2", ("header-column-2", "column-2"), "column-2"),
    (
        "furniture",
        "Page furniture",
        ("header-column-1", "header-column-2", "signature", "catchword"),
        None,
    ),
)
LINE_RE = re.compile(r"^\[([^\]]+)\]\s+(.*)$")


class HumanReviewError(Exception):
    pass


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise HumanReviewError(f"cannot read {path}: {error}") from error


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
        if not isinstance(units, dict) or set(units) != {
            definition[0] for definition in UNIT_DEFINITIONS
        }:
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


def raw_markdown_lines(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for physical_line in path.read_text(encoding="utf-8").splitlines():
        match = LINE_RE.match(physical_line)
        if not match:
            continue
        line_id = match.group(1).split()[0]
        result[line_id] = physical_line
    return result


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


def render_zone(zone: dict, raw_lines: dict[str, str]) -> str:
    lines = []
    for line in zone.get("lines", []):
        main, far_right = render_runs(line["runs"])
        indentation = line.get("indent", 0)
        line_id = html.escape(line["id"])
        raw = html.escape(raw_lines.get(line["id"], ""))
        far = f'<span class="far-right">{far_right}</span>' if far_right else ""
        lines.append(
            f'<div class="transcription-line" id="{line_id}">'
            f'<code class="line-id">{line_id}</code>'
            f'<span class="rendered-text indent-{indentation}">{main}{far}</span>'
            f'<code class="raw-text">{raw}</code></div>'
        )
    if not lines:
        return ""
    label = html.escape(zone.get("label", zone["id"]))
    return f'<section class="zone"><h3>{label}</h3>{"".join(lines)}</section>'


def relative_href(target: Path, output_dir: Path) -> str:
    return Path(os.path.relpath(target, output_dir)).as_posix()


def make_images(
    page_id: str,
    master_path: Path,
    boxes: dict[tuple[str, str], tuple[int, int, int, int]],
    assets_dir: Path,
) -> dict[str, str]:
    if not master_path.exists():
        raise HumanReviewError(f"missing master image: {master_path}")
    assets_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, str] = {}
    with Image.open(master_path) as master:
        master.load()
        for unit_id, _, _, image_zone in UNIT_DEFINITIONS:
            output_path = assets_dir / f"{page_id}-{unit_id}.jpg"
            if image_zone is None:
                image = master.copy()
                if image.width > 1800:
                    new_height = round(image.height * 1800 / image.width)
                    image.thumbnail((1800, new_height), Image.Resampling.LANCZOS)
            else:
                key = (page_id, image_zone)
                if key not in boxes:
                    raise HumanReviewError(f"no crop box for {page_id}/{image_zone}")
                left, top, right, bottom = boxes[key]
                if not (0 <= left < right <= master.width and 0 <= top < bottom <= master.height):
                    raise HumanReviewError(
                        f"crop for {page_id}/{image_zone} lies outside {master.width}x{master.height}"
                    )
                image = master.crop((left, top, right, bottom))
            image.save(output_path, "JPEG", quality=92, subsampling=0, optimize=True)
            result[unit_id] = f"assets/{output_path.name}"
    return result


def build_cards(
    record: dict,
    trial_dir: Path,
    master_dir: Path,
    tile_boxes: dict[tuple[str, str], tuple[int, int, int, int]],
    output_dir: Path,
) -> tuple[str, list[dict]]:
    cards: list[str] = []
    index: list[dict] = []
    assets_dir = output_dir / "assets"
    card_number = 0
    for page_record in record["pages"]:
        page_id = page_record["id"]
        json_path = trial_dir / "level1" / f"{page_id}.json"
        source_path = trial_dir / "level1-source" / f"{page_id}.md"
        page = load_json(json_path)
        if page.get("id") != page_id:
            raise HumanReviewError(f"{json_path}: page id does not match review record")
        raw_lines = raw_markdown_lines(source_path)
        master_name = f"f{int(page['source']['view'][1:]):04d}.jpg"
        master_path = master_dir / master_name
        images = make_images(page_id, master_path, tile_boxes, assets_dir)
        source_href = relative_href(source_path, output_dir)
        master_href = relative_href(master_path, output_dir)
        zones = {zone["id"]: zone for zone in page["zones"]}
        for unit_id, label, zone_ids, _ in UNIT_DEFINITIONS:
            state = page_record["units"][unit_id]
            missing = [zone_id for zone_id in zone_ids if zone_id not in zones]
            visible_zone_ids = [zone_id for zone_id in zone_ids if zone_id in zones]
            if unit_id != "furniture" and missing:
                raise HumanReviewError(f"{page_id}/{unit_id}: missing zones {missing}")
            rendered_zones = "".join(
                render_zone(zones[zone_id], raw_lines) for zone_id in visible_zone_ids
            )
            key = f"{page_id}:{unit_id}"
            status = state["status"]
            hidden = "" if card_number == 0 else " hidden"
            cards.append(
                f'<article class="review-card{hidden}" data-index="{card_number}" '
                f'data-key="{html.escape(key)}" data-page="{html.escape(page_id)}" '
                f'data-unit="{unit_id}">'
                '<div class="card-heading">'
                f'<div><p class="eyebrow">{html.escape(page_id)}</p><h2>{html.escape(label)}</h2></div>'
                f'<span class="canonical-status status-{status}">Canonical: {status.replace("_", " ")}</span>'
                '</div><div class="comparison">'
                '<section class="scan-pane"><div class="pane-toolbar">'
                '<span>Scan</span><label>Zoom <input class="zoom" type="range" min="100" max="320" value="100"></label>'
                f'<a href="{html.escape(master_href)}" target="_blank">Full-resolution page</a></div>'
                f'<div class="image-frame"><img src="{html.escape(images[unit_id])}" alt="{html.escape(page_id)} {html.escape(label)} scan"></div></section>'
                '<section class="text-pane"><div class="pane-toolbar"><span>Level 1 transcription</span>'
                '<button class="mode-toggle" type="button">Show Markdown</button>'
                f'<a href="{html.escape(source_href)}" target="_blank">Source Markdown</a></div>'
                f'<div class="transcription">{rendered_zones}</div></section></div>'
                '<section class="session-panel"><div><strong>This-browser review note</strong>'
                '<p>Convenience only; the committed review record remains canonical.</p></div>'
                '<label>Status <select class="session-status">'
                '<option value="pending">Pending</option><option value="needs_correction">Needs correction</option>'
                '<option value="checked">Checked</option></select></label>'
                '<label class="note-label">Note <textarea class="session-note" rows="2" placeholder="Line ID and correction, if any"></textarea></label>'
                '</section></article>'
            )
            index.append({"key": key, "page": page_id, "unit": unit_id, "label": label})
            card_number += 1
    return "".join(cards), index


def render_html(cards: str, index: list[dict], title: str) -> str:
    index_json = json.dumps(index, ensure_ascii=False).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
:root {{ color-scheme: light; --paper:#f4efe4; --ink:#25231f; --muted:#716b61; --line:#d4cbbb; --accent:#745b32; --panel:#fffdf7; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; color:var(--ink); background:var(--paper); font-family:ui-sans-serif,system-ui,-apple-system,sans-serif; }}
header {{ position:sticky; top:0; z-index:10; display:flex; align-items:center; gap:1rem; padding:.8rem 1.2rem; border-bottom:1px solid var(--line); background:rgba(244,239,228,.96); backdrop-filter:blur(8px); }}
header h1 {{ margin:0 auto 0 0; font-family:Georgia,serif; font-size:1.2rem; font-weight:600; }}
button, select, input, textarea {{ font:inherit; }}
button {{ border:1px solid var(--line); border-radius:.35rem; padding:.45rem .7rem; color:var(--ink); background:var(--panel); cursor:pointer; }}
button:hover {{ border-color:var(--accent); }}
#position {{ min-width:5rem; text-align:center; color:var(--muted); font-variant-numeric:tabular-nums; }}
main {{ padding:1rem; }}
.review-card {{ max-width:1800px; margin:0 auto; }}
.hidden {{ display:none !important; }}
.card-heading {{ display:flex; justify-content:space-between; align-items:end; gap:1rem; margin:.3rem 0 .8rem; }}
.eyebrow {{ margin:0 0 .15rem; color:var(--muted); font-size:.78rem; letter-spacing:.08em; text-transform:uppercase; }}
h2 {{ margin:0; font-family:Georgia,serif; font-size:1.45rem; }}
.canonical-status {{ border:1px solid var(--line); border-radius:99px; padding:.35rem .65rem; color:var(--muted); background:var(--panel); font-size:.82rem; }}
.comparison {{ display:grid; grid-template-columns:minmax(0,1fr) minmax(32rem,1fr); min-height:calc(100vh - 13rem); border:1px solid var(--line); border-radius:.55rem; overflow:hidden; background:var(--panel); box-shadow:0 8px 28px rgba(56,44,25,.08); }}
.scan-pane,.text-pane {{ min-width:0; display:flex; flex-direction:column; }}
.scan-pane {{ border-right:1px solid var(--line); background:#c9c0af; }}
.pane-toolbar {{ min-height:3rem; display:flex; align-items:center; gap:1rem; padding:.55rem .8rem; border-bottom:1px solid var(--line); background:var(--panel); color:var(--muted); font-size:.82rem; }}
.pane-toolbar > span:first-child {{ color:var(--ink); font-weight:650; }}
.pane-toolbar a {{ margin-left:auto; color:var(--accent); }}
.pane-toolbar label {{ display:flex; align-items:center; gap:.4rem; }}
.zoom {{ width:8rem; }}
.image-frame {{ height:calc(100vh - 16rem); overflow:auto; padding:.7rem; text-align:center; }}
.image-frame img {{ display:block; width:100%; max-width:none; height:auto; margin:0 auto; box-shadow:0 2px 12px rgba(0,0,0,.22); }}
.transcription {{ height:calc(100vh - 16rem); overflow:auto; padding:1rem 1.1rem 3rem; background:#fffefa; }}
.zone {{ margin:0 0 1.35rem; }}
.zone h3 {{ position:sticky; top:-1rem; z-index:2; margin:0 0 .55rem; padding:.5rem 0; color:var(--muted); background:#fffefa; font:600 .76rem ui-sans-serif,system-ui,sans-serif; letter-spacing:.06em; text-transform:uppercase; }}
.transcription-line {{ display:grid; grid-template-columns:5.6rem minmax(0,1fr); gap:.65rem; padding:.14rem .2rem; border-radius:.2rem; font:clamp(.95rem,1.1vw,1.15rem)/1.45 Georgia,'Times New Roman',serif; }}
.transcription-line:hover {{ background:#f4efe4; }}
.line-id {{ padding-top:.16rem; color:#8a8173; font:11px/1.45 ui-monospace,SFMono-Regular,monospace; }}
.rendered-text {{ min-width:0; white-space:pre-wrap; }}
.indent-1 {{ padding-left:1.5em; }} .indent-2 {{ padding-left:3em; }}
.far-right {{ float:right; margin-left:1.5rem; }}
.raw-text {{ display:none; min-width:0; overflow-wrap:anywhere; white-space:pre-wrap; color:#463e31; font:13px/1.5 ui-monospace,SFMono-Regular,monospace; }}
.raw-mode .rendered-text,.raw-mode .line-id {{ display:none; }} .raw-mode .raw-text {{ display:block; }}
.raw-mode .transcription-line {{ grid-template-columns:minmax(0,1fr); }}
.session-panel {{ display:grid; grid-template-columns:auto auto minmax(18rem,1fr); gap:1rem; align-items:center; margin:.8rem 0 0; padding:.75rem .9rem; border:1px solid var(--line); border-radius:.5rem; background:var(--panel); }}
.session-panel p {{ margin:.15rem 0 0; color:var(--muted); font-size:.75rem; }}
.session-panel label {{ display:flex; align-items:center; gap:.5rem; color:var(--muted); font-size:.8rem; }}
.note-label textarea {{ width:100%; resize:vertical; }}
@media (max-width:950px) {{
  header {{ flex-wrap:wrap; }} header h1 {{ width:100%; }}
  .comparison {{ grid-template-columns:1fr; }} .scan-pane {{ border-right:0; border-bottom:1px solid var(--line); }}
  .image-frame,.transcription {{ height:55vh; }} .session-panel {{ grid-template-columns:1fr; }}
}}
</style>
</head>
<body>
<header><h1>{html.escape(title)}</h1><button id="previous" type="button">← Previous</button><span id="position"></span><button id="next" type="button">Next →</button><button id="download" type="button">Download session summary</button></header>
<main>{cards}</main>
<script>
const reviewIndex = {index_json};
const cards = [...document.querySelectorAll('.review-card')];
let current = 0;
function storageKey(key) {{ return `nippo-review:${{key}}`; }}
function readSession(card) {{
  try {{ return JSON.parse(localStorage.getItem(storageKey(card.dataset.key))) || {{}}; }} catch (_) {{ return {{}}; }}
}}
function saveSession(card) {{
  const data = {{status:card.querySelector('.session-status').value,note:card.querySelector('.session-note').value}};
  localStorage.setItem(storageKey(card.dataset.key), JSON.stringify(data));
}}
function show(index) {{
  current = Math.max(0, Math.min(cards.length - 1, index));
  cards.forEach((card, i) => card.classList.toggle('hidden', i !== current));
  document.getElementById('position').textContent = `${{current + 1}} / ${{cards.length}}`;
  document.getElementById('previous').disabled = current === 0;
  document.getElementById('next').disabled = current === cards.length - 1;
  history.replaceState(null, '', `#${{cards[current].dataset.key}}`);
}}
cards.forEach(card => {{
  const saved = readSession(card);
  card.querySelector('.session-status').value = saved.status || 'pending';
  card.querySelector('.session-note').value = saved.note || '';
  card.querySelectorAll('.session-status,.session-note').forEach(control => control.addEventListener('input', () => saveSession(card)));
  card.querySelector('.zoom').addEventListener('input', event => {{ card.querySelector('.image-frame img').style.width = `${{event.target.value}}%`; }});
  card.querySelector('.mode-toggle').addEventListener('click', event => {{
    const raw = card.classList.toggle('raw-mode');
    event.target.textContent = raw ? 'Show rendered text' : 'Show Markdown';
  }});
}});
document.getElementById('previous').addEventListener('click', () => show(current - 1));
document.getElementById('next').addEventListener('click', () => show(current + 1));
document.addEventListener('keydown', event => {{ if (event.altKey && event.key === 'ArrowLeft') show(current - 1); if (event.altKey && event.key === 'ArrowRight') show(current + 1); }});
window.addEventListener('hashchange', () => {{
  const requested = cards.findIndex(card => `#${{card.dataset.key}}` === decodeURIComponent(location.hash));
  if (requested >= 0 && requested !== current) show(requested);
}});
document.getElementById('download').addEventListener('click', () => {{
  const summary = {{format:'nippo-human-review-session',format_version:1,exported_at:new Date().toISOString(),reviews:cards.map(card => ({{page:card.dataset.page,unit:card.dataset.unit,...readSession(card)}}))}};
  const link = document.createElement('a');
  link.href = URL.createObjectURL(new Blob([JSON.stringify(summary, null, 2) + '\\n'], {{type:'application/json'}}));
  link.download = 'nippo-human-review-session.json'; link.click(); URL.revokeObjectURL(link.href);
}});
const hashIndex = cards.findIndex(card => `#${{card.dataset.key}}` === decodeURIComponent(location.hash));
show(hashIndex >= 0 ? hashIndex : 0);
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
) -> int:
    record = load_review_record(review_path)
    boxes = load_tile_boxes(tile_config_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    cards, index = build_cards(record, trial_dir, master_dir, boxes, output_dir)
    document = render_html(cards, index, record.get("title", "Nippo Jisho human review"))
    (output_dir / "index.html").write_text(document, encoding="utf-8")
    return len(index)


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
        count = generate(
            args.review_record.resolve(),
            args.trial_dir.resolve(),
            args.tile_config.resolve(),
            args.master_dir.resolve(),
            args.output_dir.resolve(),
        )
        print(f"Generated {count} review units at {args.output_dir.resolve() / 'index.html'}")
        return 0
    except (HumanReviewError, OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
