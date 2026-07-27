#!/usr/bin/env python3
"""Download and verify the Gallica/BnF page-image sequence.

The downloader uses only the Python standard library. Files are written through a
temporary ``.part`` path and atomically renamed only after JPEG validation. A
JSON Lines manifest and a compact status file make interrupted runs resumable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import signal
import sys
import time
from datetime import datetime, timezone
from typing import BinaryIO, Dict, Iterable, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ARK = "bpt6k852354j"
FIRST_VIEW = 1
LAST_VIEW = 651
USER_AGENT = "nippo-jisho-source-acquisition/0.1 (+local scholarly project)"
DEFAULT_DELAY_SECONDS = 0.75
DEFAULT_RETRIES = 5
DEFAULT_TIMEOUT_SECONDS = 180
CHUNK_SIZE = 1024 * 1024


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def page_id(number: int) -> str:
    return f"bnf-f{number:04d}"


def gallica_view(number: int) -> str:
    return f"f{number}"


def image_url(number: int) -> str:
    return (
        f"https://gallica.bnf.fr/iiif/ark:/12148/{ARK}/"
        f"{gallica_view(number)}/full/full/0/native.jpg"
    )


def item_url(number: int) -> str:
    return f"https://gallica.bnf.fr/ark:/12148/{ARK}/{gallica_view(number)}.item"


class DownloadInterrupted(Exception):
    pass


class ValidationError(Exception):
    pass


class RunLogger:
    def __init__(self, log_path: Path) -> None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = log_path.open("a", encoding="utf-8", buffering=1)

    def log(self, message: str) -> None:
        line = f"{utc_now()} {message}"
        print(line, flush=True)
        self._handle.write(line + "\n")

    def close(self) -> None:
        self._handle.close()


def jpeg_dimensions(path: Path) -> Tuple[int, int]:
    """Return JPEG width and height without requiring an imaging library."""

    with path.open("rb") as handle:
        if handle.read(2) != b"\xff\xd8":
            raise ValidationError("missing JPEG start marker")

        while True:
            marker_start = handle.read(1)
            if not marker_start:
                break
            if marker_start != b"\xff":
                continue

            marker = handle.read(1)
            while marker == b"\xff":
                marker = handle.read(1)
            if not marker:
                break

            marker_value = marker[0]
            if marker_value in (0xD8, 0xD9) or 0xD0 <= marker_value <= 0xD7:
                continue

            length_bytes = handle.read(2)
            if len(length_bytes) != 2:
                break
            segment_length = int.from_bytes(length_bytes, "big")
            if segment_length < 2:
                raise ValidationError("invalid JPEG segment length")

            if marker_value in {
                0xC0,
                0xC1,
                0xC2,
                0xC3,
                0xC5,
                0xC6,
                0xC7,
                0xC9,
                0xCA,
                0xCB,
                0xCD,
                0xCE,
                0xCF,
            }:
                payload = handle.read(5)
                if len(payload) != 5:
                    break
                height = int.from_bytes(payload[1:3], "big")
                width = int.from_bytes(payload[3:5], "big")
                if width <= 0 or height <= 0:
                    raise ValidationError("non-positive JPEG dimensions")
                return width, height

            handle.seek(segment_length - 2, os.SEEK_CUR)

    raise ValidationError("JPEG dimensions not found")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def validate_image(path: Path) -> Tuple[int, int, int]:
    size = path.stat().st_size
    if size < 10_000:
        raise ValidationError(f"file is unexpectedly small ({size} bytes)")
    width, height = jpeg_dimensions(path)
    return width, height, size


def load_manifest(path: Path) -> Dict[str, dict]:
    records: Dict[str, dict] = {}
    if not path.exists():
        return records

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValidationError(
                    f"invalid JSON in {path} at line {line_number}: {error}"
                ) from error
            record_id = record.get("id")
            if record_id:
                records[record_id] = record
    return records


def append_manifest(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def make_record(
    number: int,
    path: Path,
    output_dir: Path,
    width: int,
    height: int,
    size: int,
    sha256: str,
    disposition: str,
) -> dict:
    return {
        "id": page_id(number),
        "source": "bnf-gallica",
        "gallica_view": gallica_view(number),
        "gallica_item_url": item_url(number),
        "iiif_image_url": image_url(number),
        "local_path": str(path.relative_to(output_dir.parent)),
        "width": width,
        "height": height,
        "bytes": size,
        "sha256": sha256,
        "media_type": "image/jpeg",
        "resolution": "native",
        "disposition": disposition,
        "recorded_at": utc_now(),
    }


def existing_image_record(
    number: int,
    destination: Path,
    output_dir: Path,
    manifest_records: Dict[str, dict],
) -> Tuple[dict, bool]:
    width, height, size = validate_image(destination)
    existing = manifest_records.get(page_id(number))
    if (
        existing
        and existing.get("bytes") == size
        and existing.get("width") == width
        and existing.get("height") == height
        and existing.get("sha256")
    ):
        return existing, False

    record = make_record(
        number,
        destination,
        output_dir,
        width,
        height,
        size,
        sha256_file(destination),
        "recovered_existing_file",
    )
    return record, True


def download_once(number: int, destination: Path, timeout: int) -> Tuple[int, int, int, str]:
    temporary = destination.with_suffix(destination.suffix + ".part")
    temporary.unlink(missing_ok=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()

    request = Request(image_url(number), headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=timeout) as response, temporary.open("wb") as output:
            content_type = response.headers.get_content_type()
            if content_type != "image/jpeg":
                raise ValidationError(f"unexpected content type: {content_type}")
            while chunk := response.read(CHUNK_SIZE):
                output.write(chunk)
                digest.update(chunk)
            output.flush()
            os.fsync(output.fileno())

        width, height, size = validate_image(temporary)
        os.replace(temporary, destination)
        return width, height, size, digest.hexdigest()
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def download_with_retries(
    number: int,
    destination: Path,
    timeout: int,
    retries: int,
    logger: RunLogger,
) -> Tuple[int, int, int, str]:
    for attempt in range(1, retries + 1):
        try:
            return download_once(number, destination, timeout)
        except (HTTPError, URLError, TimeoutError, OSError, ValidationError) as error:
            if attempt == retries:
                raise
            delay = min(60.0, (2 ** (attempt - 1)) + random.random())
            logger.log(
                f"RETRY {page_id(number)} attempt={attempt}/{retries} "
                f"wait={delay:.1f}s error={error}"
            )
            time.sleep(delay)
    raise AssertionError("retry loop ended unexpectedly")


def requested_numbers(start: int, end: int) -> Iterable[int]:
    if start < FIRST_VIEW or end > LAST_VIEW or start > end:
        raise ValueError(
            f"requested range must satisfy {FIRST_VIEW} <= start <= end <= {LAST_VIEW}"
        )
    return range(start, end + 1)


def build_parser(repo_root: Path) -> argparse.ArgumentParser:
    default_base = repo_root / ".cache" / "sources" / "bnf-gallica"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=FIRST_VIEW)
    parser.add_argument("--end", type=int, default=LAST_VIEW)
    parser.add_argument("--output", type=Path, default=default_base / "master")
    parser.add_argument("--manifest", type=Path, default=default_base / "acquisition.jsonl")
    parser.add_argument("--status", type=Path, default=default_base / "status.json")
    parser.add_argument("--log", type=Path, default=default_base / "download.log")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY_SECONDS)
    parser.add_argument("--retries", type=int, default=DEFAULT_RETRIES)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--force", action="store_true", help="redownload valid existing files")
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="validate the requested local files without network access",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show the resolved range and paths without downloading",
    )
    return parser


def run(args: argparse.Namespace, logger: RunLogger) -> int:
    numbers = list(requested_numbers(args.start, args.end))
    output_dir = args.output.resolve()
    manifest_path = args.manifest.resolve()
    status_path = args.status.resolve()
    manifest_records = load_manifest(manifest_path)

    logger.log(
        f"START range=f{args.start}-f{args.end} count={len(numbers)} "
        f"output={output_dir} native_resolution=true"
    )

    if args.dry_run:
        logger.log(f"DRY-RUN first_url={image_url(numbers[0])}")
        logger.log(f"DRY-RUN last_url={image_url(numbers[-1])}")
        return 0

    completed = 0
    downloaded = 0
    skipped = 0
    recovered = 0
    failures = []
    started_at = utc_now()

    def write_status(state: str) -> None:
        atomic_write_json(
            status_path,
            {
                "state": state,
                "source": "bnf-gallica",
                "range": {"start": args.start, "end": args.end, "total": len(numbers)},
                "completed": completed,
                "downloaded": downloaded,
                "skipped": skipped,
                "recovered": recovered,
                "failures": failures,
                "started_at": started_at,
                "updated_at": utc_now(),
                "output": str(output_dir),
                "manifest": str(manifest_path),
            },
        )

    write_status("running")

    for index, number in enumerate(numbers, start=1):
        destination = output_dir / f"f{number:04d}.jpg"
        try:
            if args.verify_only:
                if not destination.exists():
                    failures.append({"id": page_id(number), "error": "missing"})
                    logger.log(f"MISSING {page_id(number)} {index}/{len(numbers)}")
                    write_status("running_with_failures")
                    continue

                width, height, size = validate_image(destination)
                digest = sha256_file(destination)
                expected = manifest_records.get(page_id(number))
                if expected and expected.get("sha256") not in (None, digest):
                    raise ValidationError(
                        f"checksum mismatch: expected {expected['sha256']}, got {digest}"
                    )
                if not expected or not expected.get("sha256"):
                    record = make_record(
                        number,
                        destination,
                        output_dir,
                        width,
                        height,
                        size,
                        digest,
                        "recovered_during_verification",
                    )
                    append_manifest(manifest_path, record)
                    manifest_records[record["id"]] = record
                    recovered += 1
                completed += 1
                skipped += 1
                logger.log(
                    f"VERIFIED {page_id(number)} {index}/{len(numbers)} "
                    f"dimensions={width}x{height} bytes={size} sha256={digest}"
                )
                write_status("running")
                continue

            if destination.exists() and not args.force:
                record, needs_append = existing_image_record(
                    number, destination, output_dir, manifest_records
                )
                if needs_append:
                    append_manifest(manifest_path, record)
                    manifest_records[record["id"]] = record
                    recovered += 1
                    disposition = "RECOVERED"
                else:
                    skipped += 1
                    disposition = "SKIP"
                completed += 1
                logger.log(
                    f"{disposition} {page_id(number)} {index}/{len(numbers)} "
                    f"dimensions={record['width']}x{record['height']} bytes={record['bytes']}"
                )
                write_status("running")
                continue

            request_started = time.monotonic()
            width, height, size, digest = download_with_retries(
                number, destination, args.timeout, args.retries, logger
            )
            elapsed = time.monotonic() - request_started
            record = make_record(
                number,
                destination,
                output_dir,
                width,
                height,
                size,
                digest,
                "downloaded",
            )
            append_manifest(manifest_path, record)
            manifest_records[record["id"]] = record
            downloaded += 1
            completed += 1
            logger.log(
                f"OK {page_id(number)} {index}/{len(numbers)} "
                f"dimensions={width}x{height} bytes={size} seconds={elapsed:.1f}"
            )
            write_status("running")
            if args.delay > 0 and index < len(numbers):
                time.sleep(args.delay)
        except (HTTPError, URLError, TimeoutError, OSError, ValidationError) as error:
            failures.append({"id": page_id(number), "error": str(error)})
            logger.log(f"FAILED {page_id(number)} {index}/{len(numbers)} error={error}")
            write_status("running_with_failures")

    state = "complete" if not failures else "complete_with_failures"
    write_status(state)
    logger.log(
        f"FINISH state={state} completed={completed}/{len(numbers)} "
        f"downloaded={downloaded} skipped={skipped} recovered={recovered} "
        f"failures={len(failures)}"
    )
    return 0 if not failures else 1


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    parser = build_parser(repo_root)
    args = parser.parse_args()
    if args.delay < 0:
        parser.error("--delay must not be negative")
    if args.retries < 1:
        parser.error("--retries must be at least 1")
    if args.timeout < 1:
        parser.error("--timeout must be at least 1")

    logger = RunLogger(args.log.resolve())

    interrupted = False

    def handle_signal(signum: int, _frame: object) -> None:
        nonlocal interrupted
        interrupted = True
        raise DownloadInterrupted(f"received signal {signum}")

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        return run(args, logger)
    except DownloadInterrupted as error:
        try:
            status_path = args.status.resolve()
            if status_path.exists():
                with status_path.open("r", encoding="utf-8") as handle:
                    status_payload = json.load(handle)
                status_payload["state"] = "interrupted"
                status_payload["updated_at"] = utc_now()
                atomic_write_json(status_path, status_payload)
        except (OSError, ValueError, json.JSONDecodeError) as status_error:
            logger.log(f"WARNING could not mark status as interrupted: {status_error}")
        logger.log(f"INTERRUPTED {error}; completed files remain resumable")
        return 130
    except (ValueError, ValidationError) as error:
        logger.log(f"ERROR {error}")
        return 2
    finally:
        if interrupted:
            logger.log("EXIT interrupted=true")
        logger.close()


if __name__ == "__main__":
    sys.exit(main())
