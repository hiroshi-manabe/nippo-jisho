#!/usr/bin/env python3
"""Acquire the four Bodleian sides supplementing Paris folios 110–111.

Research cache only: this does not alter canonical text or public navigation.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

MANIFEST = "https://iiif.bodleian.ox.ac.uk/iiif/manifest/462146c4-dadb-4aa5-b324-2d45e30e5ddd.json"
PAGES = [("110r", "fol. Ee2r"), ("110v", "fol. Ee2v"),
         ("111r", "fol. Ee3r"), ("111v", "fol. Ee3v")]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--width", type=int, default=1800,
                        help="Image width; 0 requests native resolution")
    args = parser.parse_args()
    if args.width < 0:
        parser.error("width must be nonnegative")
    root = Path(__file__).resolve().parents[1]
    dest = root / ".cache/sources/bodleian/pilot-110-111"
    dest.mkdir(parents=True, exist_ok=True)
    with urlopen(MANIFEST, timeout=120) as response:
        raw = response.read()
    (dest / "manifest.json").write_bytes(raw)
    manifest = json.loads(raw)
    canvases = manifest["sequences"][0]["canvases"]
    size = f"{args.width}," if args.width else "full"
    variant = str(args.width) if args.width else "native"
    records = []
    for folio, label in PAGES:
        matches = [c for c in canvases if c["label"] == label]
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one canvas for {label}")
        canvas = matches[0]
        resource = canvas["images"][0]["resource"]
        url = resource["service"]["@id"] + f"/full/{size}/0/default.jpg"
        target = dest / f"{folio}-{variant}.jpg"
        print(f"Fetching {folio}: {url}", flush=True)
        with urlopen(url, timeout=180) as response:
            payload = response.read()
        if not payload.startswith(b"\xff\xd8") or not payload.endswith(b"\xff\xd9"):
            raise ValueError(f"Incomplete/non-JPEG response for {folio}")
        target.write_bytes(payload)
        records.append({"proposed_page_id": f"bodleian-f{folio.zfill(5)}",
                        "printed_folio_side": folio, "canvas_label": label,
                        "canvas": canvas["@id"], "url": url,
                        "file": str(target.relative_to(root)),
                        "native_width": resource["width"],
                        "native_height": resource["height"],
                        "sha256": hashlib.sha256(payload).hexdigest()})
    (dest / f"acquisition-{variant}.json").write_text(json.dumps({
        "manifest": MANIFEST, "attribution": manifest.get("attribution"),
        "insert_after": "bnf-f0226", "insert_before": "bnf-f0227",
        "pages": records}, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
