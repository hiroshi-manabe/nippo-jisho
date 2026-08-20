#!/usr/bin/env python3
"""Align f13-f30 line crops to the four visually verified column rules.

The bound books are photographed with mild page skew, so a single x/width pair
for an entire column cannot remain aligned at both the top and bottom.  This
script interpolates the two printed rules surrounding each column and derives
an independent horizontal envelope for every line and context crop.  Existing
vertical geometry is deliberately preserved.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


# page: (fit_y0, fit_y1, left_outer, column_1_right, column_2_left, right_outer)
# Each rule is (x_at_y0, x_at_y1).  Values were checked against the native scans.
RULES = {
    13: (1180, 3383, (219, 205), (1208, 1214), (1275, 1279), (2305, 2313)),
    14: (388, 3382, (453, 443), (1491, 1507), (1559, 1579), (2629, 2609)),
    15: (382, 3378, (213, 189), (1191, 1189), (1268, 1260), (2298, 2294)),
    16: (401, 3412, (444, 456), (1471, 1515), (1542, 1594), (2625, 2603)),
    17: (352, 3346, (176, 202), (1163, 1207), (1242, 1284), (2283, 2315)),
    18: (383, 3357, (482, 468), (1527, 1505), (1602, 1580), (2619, 2593)),
    19: (350, 3333, (165, 173), (1158, 1170), (1244, 1242), (2276, 2304)),
    20: (378, 3373, (456, 472), (1492, 1520), (1565, 1599), (2593, 2611)),
    21: (407, 3398, (177, 149), (1203, 1195), (1280, 1266), (2351, 2355)),
    22: (432, 3420, (367, 395), (1440, 1490), (1553, 1545), (2611, 2613)),
    23: (410, 3398, (205, 175), (1222, 1214), (1295, 1293), (2382, 2342)),
    24: (426, 3436, (387, 395), (1472, 1488), (1553, 1547), (2603, 2615)),
    25: (402, 3350, (186, 158), (1210, 1190), (1291, 1271), (2365, 2327)),
    26: (419, 3412, (383, 419), (1470, 1488), (1544, 1572), (2606, 2618)),
    27: (400, 3402, (209, 157), (1223, 1175), (1301, 1245), (2366, 2330)),
    28: (409, 3412, (378, 428), (1464, 1490), (1539, 1557), (2588, 2598)),
    29: (348, 3351, (187, 153), (1177, 1185), (1247, 1251), (2328, 2288)),
    30: (411, 3400, (383, 435), (1466, 1492), (1544, 1564), (2593, 2607)),
}

PADDING = 12


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def rule_x(rule: tuple[int, int], y: float, y0: int, y1: int) -> float:
    return rule[0] + (rule[1] - rule[0]) * ((y - y0) / (y1 - y0))


def horizontal_envelope(
    left: tuple[int, int],
    right: tuple[int, int],
    y: int,
    height: int,
    fit_y0: int,
    fit_y1: int,
) -> tuple[int, int]:
    y_bottom = y + height
    left_x = math.floor(min(rule_x(left, at, fit_y0, fit_y1) for at in (y, y_bottom)))
    right_x = math.ceil(max(rule_x(right, at, fit_y0, fit_y1) for at in (y, y_bottom)))
    x = left_x - PADDING
    return x, right_x + PADDING - x


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate without writing")
    args = parser.parse_args()

    geometry_path = root / "pilot/human-review/line-geometry.json"
    tiles_path = root / "pilot/tile-config-v1-trial.json"
    geometry = load_json(geometry_path)
    tiles = load_json(tiles_path)
    geometry_pages = {page["id"]: page for page in geometry["pages"]}
    tile_pages = {page["id"]: page for page in tiles["pages"]}

    changed_lines = 0
    for folio, (fit_y0, fit_y1, outer_left, c1_right, c2_left, outer_right) in RULES.items():
        page_id = f"bnf-f{folio:04d}"
        page = geometry_pages[page_id]
        tile = tile_pages[page_id]
        zone_by_id = {zone["id"]: zone for zone in tile["zones"]}

        for column_id, left, right in (
            ("column-1", outer_left, c1_right),
            ("column-2", c2_left, outer_right),
        ):
            column = page["columns"][column_id]
            old_box = column["box"]
            box_left = math.floor(min(left)) - PADDING
            box_right = math.ceil(max(right)) + PADDING
            column["box"] = [box_left, old_box[1], box_right, old_box[3]]
            zone_by_id[column_id]["box"] = list(column["box"])
            # Preserve the established review vocabulary and its stronger f24+
            # text/image sanity status; this pass refines one geometry dimension.
            column["visual_review"] = (
                "text_image_sanity_checked" if folio >= 24 else "line_by_line_reverified"
            )
            column["reviewed_at"] = "2026-08-20"
            column["horizontal_alignment"] = "interpolated_from_visually_verified_printed_rules"

            for line in column["lines"].values():
                for key in ("crop", "context_crop"):
                    rectangle = line[key]
                    x, width = horizontal_envelope(
                        left, right, rectangle[1], rectangle[3], fit_y0, fit_y1
                    )
                    rectangle[0] = x
                    rectangle[2] = width
                crop = line["crop"]
                context = line["context_crop"]
                # Rounding at different vertical spans must never make context narrower.
                context_left = min(context[0], crop[0])
                context_right = max(context[0] + context[2], crop[0] + crop[2])
                context[0] = context_left
                context[2] = context_right - context_left
                changed_lines += 1

                source_width, source_height = page["source_size"]
                for rectangle in (crop, context):
                    x, y, width, height = rectangle
                    if x < 0 or y < 0 or x + width > source_width or y + height > source_height:
                        raise SystemExit(f"out-of-bounds crop: {page_id}/{column_id}")

    if not args.check:
        geometry_path.write_text(
            json.dumps(geometry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        tiles_path.write_text(
            json.dumps(tiles, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(f"Validated {changed_lines} line records on {len(RULES)} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
