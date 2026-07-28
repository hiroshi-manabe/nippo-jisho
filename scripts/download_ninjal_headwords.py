#!/usr/bin/env python3
"""Download and verify NINJAL's Nippo Jisho headword dataset."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
from pathlib import Path
import sys
from typing import Sequence
from urllib.request import Request, urlopen
from zipfile import BadZipFile, ZipFile


VERSION = "202510"
ARCHIVE_NAME = f"ew-nippo-{VERSION}.zip"
DOWNLOAD_URL = (
    "https://www2.ninjal.ac.jp/textdb_dataset/nipp/data/"
    f"{ARCHIVE_NAME}"
)
EXPECTED_SHA256 = "6bb4f084b9e10778ecfc32e2e2f54c6c4c120f4b6cc91813cccba2b074250175"
EXPECTED_RECORDS = 32_878
DATA_DIRECTORY = f"ew-nippo-{VERSION}"
TSV_NAME = f"ew-nippo-{VERSION}.txt"
EXPECTED_MEMBERS = {
    f"{DATA_DIRECTORY}/",
    f"{DATA_DIRECTORY}/{TSV_NAME}",
    f"{DATA_DIRECTORY}/ew-nippo-{VERSION}.xlsx",
    f"{DATA_DIRECTORY}/readme_ew-nippo-{VERSION}.txt",
}
EXPECTED_COLUMNS = [
    "整理番号",
    "見出し語ID",
    "見出し語",
    "見出し語（片仮名）",
    "動詞終止形（現代）",
    "原本所在",
    "影印本所在",
    "邦訳本所在",
    "BnF画像",
    "備考",
    "日国ID",
    "日国ID（参考）",
]
USER_AGENT = "nippo-jisho-source-acquisition/0.1 (+local scholarly project)"
CHUNK_SIZE = 1024 * 1024


class ValidationError(Exception):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def validate_archive(path: Path) -> None:
    checksum = sha256_file(path)
    if checksum != EXPECTED_SHA256:
        raise ValidationError(
            f"archive SHA-256 mismatch: expected {EXPECTED_SHA256}, got {checksum}"
        )

    try:
        with ZipFile(path) as archive:
            members = set(archive.namelist())
            if members != EXPECTED_MEMBERS:
                missing = sorted(EXPECTED_MEMBERS - members)
                extra = sorted(members - EXPECTED_MEMBERS)
                raise ValidationError(
                    f"unexpected archive members; missing={missing}, extra={extra}"
                )
            corrupt_member = archive.testzip()
            if corrupt_member:
                raise ValidationError(f"corrupt ZIP member: {corrupt_member}")
    except BadZipFile as error:
        raise ValidationError(f"invalid ZIP archive: {error}") from error


def validate_tsv(path: Path, expected_records: int = EXPECTED_RECORDS) -> dict[str, int]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if reader.fieldnames != EXPECTED_COLUMNS:
            raise ValidationError(
                f"unexpected TSV columns: {reader.fieldnames!r}"
            )

        identifiers: set[str] = set()
        records = 0
        bnf_links = 0
        supplement_records = 0
        for records, row in enumerate(reader, start=1):
            if row["整理番号"] != str(records):
                raise ValidationError(
                    f"non-sequential record number at row {records}: {row['整理番号']!r}"
                )
            identifier = row["見出し語ID"]
            if not identifier or identifier in identifiers:
                raise ValidationError(
                    f"missing or duplicate headword ID at row {records}: {identifier!r}"
                )
            identifiers.add(identifier)
            if row["BnF画像"]:
                if not row["BnF画像"].startswith(
                    "https://gallica.bnf.fr/ark:/12148/bpt6k852354j/f"
                ):
                    raise ValidationError(
                        f"unexpected BnF URL at row {records}: {row['BnF画像']!r}"
                    )
                bnf_links += 1
            if int(row["原本所在"][:3]) >= 332:
                supplement_records += 1

    if records != expected_records:
        raise ValidationError(
            f"unexpected TSV record count: expected {expected_records}, got {records}"
        )

    return {
        "records": records,
        "unique_ids": len(identifiers),
        "bnf_links": bnf_links,
        "supplement_records": supplement_records,
    }


def download(archive_path: Path, timeout: int) -> None:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = archive_path.with_suffix(archive_path.suffix + ".part")
    temporary.unlink(missing_ok=True)
    request = Request(DOWNLOAD_URL, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=timeout) as response, temporary.open("wb") as output:
            while chunk := response.read(CHUNK_SIZE):
                output.write(chunk)
            output.flush()
            os.fsync(output.fileno())
        validate_archive(temporary)
        os.replace(temporary, archive_path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def extract(archive_path: Path, unpacked_dir: Path) -> None:
    unpacked_dir.mkdir(parents=True, exist_ok=True)
    with ZipFile(archive_path) as archive:
        archive.extractall(unpacked_dir)


def default_base(repo_root: Path) -> Path:
    return repo_root / ".cache" / "external" / "ninjal-headwords" / VERSION


def build_parser(repo_root: Path) -> argparse.ArgumentParser:
    base = default_base(repo_root)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=base / ARCHIVE_NAME)
    parser.add_argument("--unpacked", type=Path, default=base / "unpacked")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--reextract", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    repo_root = Path(__file__).resolve().parents[1]
    args = build_parser(repo_root).parse_args(argv)
    tsv_path = args.unpacked / DATA_DIRECTORY / TSV_NAME

    try:
        if not args.archive.exists():
            if args.verify_only:
                raise ValidationError(f"archive not found: {args.archive}")
            print(f"Downloading {DOWNLOAD_URL}")
            download(args.archive, args.timeout)

        validate_archive(args.archive)
        if args.reextract or not tsv_path.exists():
            if args.verify_only:
                raise ValidationError(f"unpacked TSV not found: {tsv_path}")
            extract(args.archive, args.unpacked)

        summary = validate_tsv(tsv_path)
    except (OSError, ValidationError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(
        f"Verified NINJAL Nippo Jisho headwords {VERSION}: "
        f"records={summary['records']} unique_ids={summary['unique_ids']} "
        f"bnf_links={summary['bnf_links']} "
        f"supplement_records={summary['supplement_records']}"
    )
    print(f"TSV: {tsv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
