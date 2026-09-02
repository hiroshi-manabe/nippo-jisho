# Frozen f248–f250 reference

This directory freezes the pre-bootstrap state of `f248`–`f250` so those
near-range pages can be used as an independent comparison for the bulk
scan-first run.

The snapshot was taken from Git commit `ef7c5dd` and contains:

- the compact Level 1 Markdown sources;
- their compiled Level 1 JSON;
- the three corresponding records from `line-geometry.json`; and
- their human-review registry entries.

The bootstrap inference path does not read this directory. It may be opened
only after the new OCR-derived candidate files have been serialized.
