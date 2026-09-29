#!/usr/bin/env python3
"""Apply the provisional italic-S. convention to human-unreviewed pages.

Only standalone capital S followed by a period in roman type is changed. The
page-level human-review guard is intentionally conservative. Run without
--apply to inspect the proposed scope first.
"""

import argparse
from copy import deepcopy
import json
from pathlib import Path
import re
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compile_level1_markdown import export_markdown, parse_markdown
from refresh_unreviewed_ocr import ROOT, page_sources, protected_pages
from render_format_trial import render_page

LABEL = re.compile(r"(?<![A-Za-z])S\.(?![A-Za-z])")
TYPEFACE_CLAIM = re.compile(r"\b(?:upright|roman)\b.{0,55}\bS\b|\bS\b.{0,55}\b(?:upright|roman)\b", re.I)
SUPERSESSION = "Typeface update: S. is provisionally italicized under the bulk convention."


def rewrite(page):
    result = deepcopy(page)
    changes = []
    for zone in result["zones"]:
        for line in zone.get("lines", []):
            new_runs = []
            changed = False
            for run in line["runs"]:
                if run["typeface"] != "roman" or not LABEL.search(run["text"]):
                    new_runs.append(run)
                    continue
                text = run["text"]
                cursor = 0
                for match in LABEL.finditer(text):
                    if match.start() > cursor:
                        new_runs.append({**run, "text": text[cursor:match.start()]})
                    new_runs.append({**run, "typeface": "italic", "text": "S."})
                    cursor = match.end()
                    changed = True
                    changes.append(line["id"])
                if cursor < len(text):
                    new_runs.append({**run, "text": text[cursor:]})
            if changed:
                line["runs"] = new_runs
                note = line.get("note", "")
                if TYPEFACE_CLAIM.search(note) and SUPERSESSION not in note:
                    line["note"] = note.rstrip() + " " + SUPERSESSION
    return result, changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    protected = protected_pages()
    prepared = []
    for page_id, path in sorted(page_sources().items()):
        if page_id in protected:
            continue
        obj = json.loads(path.read_text(encoding="utf-8"))
        original = obj.get("page", obj)
        if original["review"]["status"] == "human_checked":
            continue
        page, changes = rewrite(original)
        if not changes:
            continue
        md_path = ROOT / "pilot/format-v1-trial/level1-source" / f"{page_id}.md"
        md = export_markdown(page) if path.parent.name == "level1" else None
        if md is not None:
            with tempfile.TemporaryDirectory() as temp:
                check_path = Path(temp) / f"{page_id}.md"
                check_path.write_text(md, encoding="utf-8")
                reparsed = parse_markdown(check_path)
            def line_texts(value):
                return [(line["id"], "".join(run["text"] for run in line["runs"]), line.get("note"))
                        for zone in value["zones"] for line in zone.get("lines", [])]
            if line_texts(reparsed) != line_texts(page):
                raise ValueError(f"Markdown round-trip changed text for {page_id}")
            # The compact parser merges adjacent italic runs and treats style
            # on whitespace as immaterial. Its representation is canonical.
            page = reparsed
            md = export_markdown(page)
            if not md_path.exists():
                raise ValueError(f"missing canonical Markdown: {md_path}")
        prepared.append((page_id, path, obj, page, md_path, md, changes))
    print(f"{len(prepared)} pages; {sum(len(item[-1]) for item in prepared)} labels")
    for page_id, *_, changes in prepared:
        print(f"{page_id}: {', '.join(changes)}")
    if not args.apply:
        return
    for page_id, path, obj, page, md_path, md, _ in prepared:
        if md is not None:
            md_path.write_text(md, encoding="utf-8")
            path.write_text(json.dumps(page, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            rendered = ROOT / "pilot/format-v1-trial/generated" / f"{page_id}-page.md"
            rendered.write_text(render_page(page), encoding="utf-8")
        else:
            if "page" in obj:
                obj["page"] = page
            else:
                obj = page
            path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
