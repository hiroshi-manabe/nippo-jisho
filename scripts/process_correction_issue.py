#!/usr/bin/env python3
"""Apply schema-2 transcription Issues and finalize settled submissions."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import difflib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import unicodedata
from urllib.request import urlopen

try:
    from .build_public_review import alternate_tilde_carrier, transcription_version
    from .compile_level1_markdown import export_markdown, parse_markdown
except ImportError:  # Direct execution places scripts/ rather than the repo on sys.path.
    from build_public_review import alternate_tilde_carrier, transcription_version
    from compile_level1_markdown import export_markdown, parse_markdown


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "build" / "correction-issues"
REPOSITORY = "hiroshi-manabe/nippo-jisho"
PAGES_URL = "https://hiroshi-manabe.github.io/nippo-jisho/corpus.json"
WORD = r"[^\W\d_]+(?:[\u0300-\u036f]*)"
TILDE_MARKER_RE = re.compile(rf"\*(?P<before>{WORD})|(?P<after>{WORD})\*", re.UNICODE)


class IssueProcessingError(Exception):
    pass


def run(
    command: list[str],
    *,
    root: Path = ROOT,
    capture: bool = False,
) -> str:
    result = subprocess.run(
        command,
        cwd=root,
        check=False,
        text=True,
        capture_output=capture,
    )
    if result.returncode:
        detail = (result.stderr or result.stdout or "").strip()
        raise IssueProcessingError(
            f"command failed ({' '.join(command)}): {detail or result.returncode}"
        )
    return result.stdout if capture else ""


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def report_path(issue_number: int, root: Path = ROOT) -> Path:
    return root / "build" / "correction-issues" / f"issue-{issue_number}.json"


def extract_payload(body: str) -> dict:
    blocks = re.findall(r"```json\s*\n(.*?)\n```", body, re.DOTALL)
    if len(blocks) != 1:
        raise IssueProcessingError(
            f"expected exactly one fenced JSON payload, found {len(blocks)}"
        )
    try:
        payload = json.loads(blocks[0])
    except json.JSONDecodeError as error:
        raise IssueProcessingError(f"invalid correction JSON: {error}") from error
    validate_payload(payload)
    return payload


def validate_payload(payload: dict) -> None:
    if payload.get("schema") != 2:
        raise IssueProcessingError(
            f"unsupported correction schema {payload.get('schema')!r}; only schema 2 is accepted"
        )
    for field in ("page", "base_commit", "base_transcription_version"):
        if not isinstance(payload.get(field), str) or not payload[field]:
            raise IssueProcessingError(f"missing or invalid {field!r}")
    if not re.fullmatch(r"f[1-9][0-9]*", payload["page"]):
        raise IssueProcessingError(f"invalid page identifier {payload['page']!r}")
    changes = payload.get("changes")
    if not isinstance(changes, list) or not changes:
        raise IssueProcessingError("changes must be a non-empty list")
    seen: set[str] = set()
    for index, change in enumerate(changes, start=1):
        if not isinstance(change, dict):
            raise IssueProcessingError(f"change {index} is not an object")
        for field in ("line", "before", "after"):
            if not isinstance(change.get(field), str):
                raise IssueProcessingError(f"change {index} has invalid {field!r}")
        if change["line"] in seen:
            raise IssueProcessingError(f"duplicate line {change['line']!r}")
        seen.add(change["line"])
        if "comment" in change and not isinstance(change["comment"], str):
            raise IssueProcessingError(f"change {index} has a non-string comment")
        if "second_opinion" in change and not isinstance(
            change["second_opinion"], bool
        ):
            raise IssueProcessingError(
                f"change {index} has a non-boolean second_opinion"
            )


def resolve_tilde_markers(value: str) -> str:
    def replace(match: re.Match[str]) -> str:
        token = match.group("before") or match.group("after")
        carriers = [
            index
            for index, character in enumerate(token)
            if "\N{COMBINING TILDE}" in unicodedata.normalize("NFD", character)
        ]
        if len(carriers) != 1:
            raise IssueProcessingError(
                f"tilde marker {match.group(0)!r} must identify one existing tilde"
            )
        alternate = alternate_tilde_carrier(token, carriers[0])
        if alternate is None:
            raise IssueProcessingError(
                f"tilde marker {match.group(0)!r} has no unique adjacent-vowel alternative"
            )
        return alternate

    resolved = TILDE_MARKER_RE.sub(replace, value)
    if "*" in resolved:
        raise IssueProcessingError(
            "unresolved '*' annotation; use it only immediately before or after an eligible word"
        )
    return resolved


def parse_correction_notation(value: str) -> tuple[str, list[tuple[int, int]]]:
    value = resolve_tilde_markers(value)
    text: list[str] = []
    ranges: list[tuple[int, int]] = []
    opened: int | None = None
    for character in value:
        if character == "[":
            if opened is not None:
                raise IssueProcessingError("roman spans cannot be nested")
            opened = len(text)
        elif character == "]":
            if opened is None:
                raise IssueProcessingError("roman span has an unmatched closing bracket")
            if opened == len(text):
                raise IssueProcessingError("roman span cannot be empty")
            ranges.append((opened, len(text)))
            opened = None
        else:
            text.append(character)
    if opened is not None:
        raise IssueProcessingError("roman span has no closing bracket")
    return unicodedata.normalize("NFC", "".join(text)), ranges


def line_text(line: dict) -> str:
    return "".join(run["text"] for run in line["runs"])


def line_map(page: dict) -> dict[str, dict]:
    return {
        line["id"]: line
        for zone in page["zones"]
        for line in zone.get("lines", [])
    }


def style_key(style: dict) -> str:
    return json.dumps(style, ensure_ascii=False, sort_keys=True)


def choose_style(source: list[dict], left: int, right: int) -> dict:
    segment = source[left:right]
    if segment:
        key = Counter(style_key(style) for style in segment).most_common(1)[0][0]
        return json.loads(key)
    before = source[left - 1] if left else None
    after = source[left] if left < len(source) else None
    if before == after and before:
        return dict(before)
    return dict(before or after or {"typeface": "roman"})


def corrected_runs(
    line: dict, target: str, roman_ranges: list[tuple[int, int]]
) -> list[dict]:
    before = line_text(line)
    source_styles = [
        {key: value for key, value in run.items() if key != "text"}
        for run in line["runs"]
        for _ in run["text"]
    ]
    target_styles: list[dict | None] = [None] * len(target)
    matcher = difflib.SequenceMatcher(a=before, b=target, autojunk=False)
    for tag, old_start, old_end, new_start, new_end in matcher.get_opcodes():
        if tag == "equal":
            target_styles[new_start:new_end] = source_styles[old_start:old_end]
        elif tag == "replace" and old_end - old_start == new_end - new_start:
            target_styles[new_start:new_end] = source_styles[old_start:old_end]
        elif tag in {"replace", "insert"}:
            style = choose_style(source_styles, old_start, old_end)
            target_styles[new_start:new_end] = [
                dict(style) for _ in range(new_end - new_start)
            ]
    for start, end in roman_ranges:
        if not (0 <= start < end <= len(target)):
            raise IssueProcessingError("roman span falls outside resolved correction text")
        for index in range(start, end):
            target_styles[index] = {**target_styles[index], "typeface": "roman"}
    if any(style is None for style in target_styles):
        raise IssueProcessingError(f"could not preserve typeface for {line['id']}")
    runs: list[dict] = []
    for character, style in zip(target, target_styles):
        assert style is not None
        if runs and {
            key: value for key, value in runs[-1].items() if key != "text"
        } == style:
            runs[-1]["text"] += character
        else:
            runs.append({**style, "text": character})
    return runs


def page_id(view: str) -> str:
    return f"bnf-f{int(view[1:]):04d}"


def source_path(root: Path, view: str) -> Path:
    return root / "pilot" / "format-v1-trial" / "level1-source" / f"{page_id(view)}.md"


def compiled_path(root: Path, view: str) -> Path:
    return root / "pilot" / "format-v1-trial" / "level1" / f"{page_id(view)}.json"


def current_transcription_version(page: dict) -> str:
    zones = []
    for zone in page["zones"]:
        lines = []
        for line in zone.get("lines", []):
            text = line_text(line)
            lines.append({**line, "text": text})
        zones.append({**zone, "lines": lines})
    return transcription_version(zones)


def ensure_clean_tracked_worktree(root: Path) -> None:
    status = run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        root=root,
        capture=True,
    ).strip()
    if status:
        raise IssueProcessingError(
            "tracked worktree changes exist; finish or set them aside before processing an Issue"
        )


def fetch_issue(issue_number: int, repository: str) -> dict:
    raw = run(
        [
            "gh",
            "issue",
            "view",
            str(issue_number),
            "--repo",
            repository,
            "--json",
            "number,title,body,state,url",
        ],
        capture=True,
    )
    issue = json.loads(raw)
    if issue["state"] != "OPEN":
        raise IssueProcessingError(f"Issue #{issue_number} is not open")
    return issue


def validate_base_commit(root: Path, commit: str) -> None:
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise IssueProcessingError(f"base commit {commit} is unavailable locally")


def apply_change(line: dict, change: dict) -> dict:
    current = line_text(line)
    if current != change["before"]:
        raise IssueProcessingError(
            f"{change['line']} before mismatch: expected {change['before']!r}, found {current!r}"
        )
    target, roman_ranges = parse_correction_notation(change["after"])
    return {
        "line": change["line"],
        "before": change["before"],
        "submitted_after": change["after"],
        "resolved_after": target,
        "roman_ranges": roman_ranges,
        **({"comment": change["comment"]} if change.get("comment") else {}),
    }


def apply_resolved(line: dict, item: dict) -> None:
    line["runs"] = corrected_runs(line, item["resolved_after"], item["roman_ranges"])


def validation_commands(root: Path) -> list[list[str]]:
    return [
        [
            "python3",
            "scripts/compile_level1_markdown.py",
            "compile",
            "pilot/format-v1-trial/level1-source",
            "pilot/format-v1-trial/level1",
        ],
        ["python3", "scripts/render_format_trial.py", "pilot/format-v1-trial"],
        ["python3", "scripts/build_public_review.py"],
        ["python3", "-m", "unittest", "discover", "-s", "tests"],
    ]


def regenerate_and_test(root: Path) -> None:
    for command in validation_commands(root):
        run(command, root=root)


def prepare(
    issue_number: int,
    *,
    root: Path = ROOT,
    repository: str = REPOSITORY,
) -> dict:
    ensure_clean_tracked_worktree(root)
    issue = fetch_issue(issue_number, repository)
    payload = extract_payload(issue["body"])
    validate_base_commit(root, payload["base_commit"])
    markdown_path = source_path(root, payload["page"])
    json_path = compiled_path(root, payload["page"])
    if not markdown_path.exists() or not json_path.exists():
        raise IssueProcessingError(f"page {payload['page']} is not transcribed")
    page = parse_markdown(markdown_path)
    current_version = current_transcription_version(page)
    lines = line_map(page)
    applied: list[dict] = []
    pending: list[dict] = []
    for change in payload["changes"]:
        line = lines.get(change["line"])
        if line is None:
            raise IssueProcessingError(f"unknown line {change['line']!r}")
        item = apply_change(line, change)
        if change.get("second_opinion", False):
            pending.append({**item, "decision": "pending"})
        else:
            apply_resolved(line, item)
            applied.append(item)
    markdown_path.write_text(export_markdown(page), encoding="utf-8")
    regenerate_and_test(root)
    report = {
        "format": "nippo-correction-issue-report",
        "format_version": 1,
        "issue": issue_number,
        "issue_url": issue["url"],
        "repository": repository,
        "page": payload["page"],
        "page_id": page_id(payload["page"]),
        "base_commit": payload["base_commit"],
        "submitted_transcription_version": payload["base_transcription_version"],
        "current_transcription_version_at_prepare": current_version,
        "page_version_changed": current_version
        != payload["base_transcription_version"],
        "applied_unflagged": applied,
        "second_opinions": pending,
        "status": "awaiting_second_opinion" if pending else "ready_to_finalize",
    }
    write_json(report_path(issue_number, root), report)
    return report


def apply_second_opinion_decisions(report: dict, root: Path) -> list[str]:
    markdown_path = source_path(root, report["page"])
    page = parse_markdown(markdown_path)
    lines = line_map(page)
    accepted: list[str] = []
    pending: list[str] = []
    for item in report["second_opinions"]:
        decision = item.get("decision", "pending")
        if decision == "pending":
            pending.append(item["line"])
            continue
        if decision == "reject":
            if line_text(lines[item["line"]]) != item["before"]:
                raise IssueProcessingError(
                    f"rejected {item['line']} no longer matches its original text"
                )
            continue
        if decision == "qualify":
            qualified = item.get("qualified_after")
            if not isinstance(qualified, str) or not qualified:
                raise IssueProcessingError(
                    f"qualified {item['line']} needs a qualified_after value"
                )
            resolved, ranges = parse_correction_notation(qualified)
            item["resolved_after"] = resolved
            item["roman_ranges"] = ranges
        elif decision != "accept":
            raise IssueProcessingError(
                f"invalid decision {decision!r} for {item['line']}"
            )
        line = lines[item["line"]]
        if line_text(line) != item["before"]:
            raise IssueProcessingError(
                f"pending {item['line']} changed before its decision was applied"
            )
        apply_resolved(line, item)
        accepted.append(item["line"])
    if pending:
        raise IssueProcessingError(
            "second-opinion decisions still pending: " + ", ".join(pending)
        )
    markdown_path.write_text(export_markdown(page), encoding="utf-8")
    return accepted


def update_history(report: dict, accepted_lines: list[str], root: Path) -> None:
    history_path = root / "pilot" / "human-review" / "correction-history.json"
    history = load_json(history_path)
    page = next(
        (item for item in history["pages"] if item["id"] == report["page_id"]), None
    )
    if page is None:
        page = {
            "id": report["page_id"],
            "issues_applied": 0,
            "distinct_lines": 0,
            "accepted_edits": 0,
            "issues": [],
        }
        history["pages"].append(page)
        history["pages"].sort(key=lambda item: item["id"])
    if any(item["number"] == report["issue"] for item in page["issues"]):
        raise IssueProcessingError(
            f"Issue #{report['issue']} is already present in correction history"
        )
    issue_record = {
        "number": report["issue"],
        "url": report["issue_url"],
        "applied_at": date.today().isoformat(),
        "lines": accepted_lines,
    }
    page["issues"].append(issue_record)
    page["issues_applied"] = len(page["issues"])
    page["accepted_edits"] = sum(len(item["lines"]) for item in page["issues"])
    page["distinct_lines"] = len(
        {line for item in page["issues"] for line in item["lines"]}
    )
    page["last_applied"] = issue_record["applied_at"]
    write_json(history_path, history)


def expected_paths(report: dict) -> set[str]:
    stem = report["page_id"]
    return {
        f"pilot/format-v1-trial/level1-source/{stem}.md",
        f"pilot/format-v1-trial/level1/{stem}.json",
        f"pilot/format-v1-trial/generated/{stem}-page.md",
        "pilot/format-v1-trial/generated/selected-reading-views.md",
        "pilot/human-review/correction-history.json",
    }


def changed_paths(root: Path) -> set[str]:
    output = run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        root=root,
        capture=True,
    )
    return {line[3:] for line in output.splitlines() if line.strip()}


def wait_for_deployment(commit: str, repository: str, root: Path) -> str:
    run_id = None
    for _ in range(60):
        raw = run(
            [
                "gh",
                "run",
                "list",
                "--repo",
                repository,
                "--workflow",
                "Deploy public review site",
                "--commit",
                commit,
                "--limit",
                "1",
                "--json",
                "databaseId,status,conclusion,url",
            ],
            root=root,
            capture=True,
        )
        runs = json.loads(raw)
        if runs:
            run_id = str(runs[0]["databaseId"])
            break
        time.sleep(2)
    if run_id is None:
        raise IssueProcessingError("Pages workflow did not appear for the pushed commit")
    run(
        ["gh", "run", "watch", run_id, "--repo", repository, "--exit-status"],
        root=root,
    )
    return run_id


def verify_deployment(report: dict, commit: str, pages_url: str) -> None:
    with urlopen(pages_url, timeout=30) as response:
        corpus = json.load(response)
    if corpus.get("commit") != commit:
        raise IssueProcessingError(
            f"deployed corpus is at {corpus.get('commit')}, expected {commit}"
        )
    page = next(
        (item for item in corpus["pages"] if item["page_id"] == report["page_id"]),
        None,
    )
    if page is None or not any(
        item["number"] == report["issue"]
        for item in page["corrections"].get("issues", [])
    ):
        raise IssueProcessingError("deployed correction history does not contain the Issue")


def finalize(
    issue_number: int,
    *,
    root: Path = ROOT,
    local_only: bool = False,
    pages_url: str = PAGES_URL,
) -> dict:
    path = report_path(issue_number, root)
    if not path.exists():
        raise IssueProcessingError(f"missing preparation report {path}")
    report = load_json(path)
    if report.get("status") not in {"ready_to_finalize", "awaiting_second_opinion"}:
        raise IssueProcessingError(f"report status is {report.get('status')!r}")
    accepted = [item["line"] for item in report["applied_unflagged"]]
    accepted.extend(apply_second_opinion_decisions(report, root))
    update_history(report, accepted, root)
    regenerate_and_test(root)
    changed = changed_paths(root)
    unexpected = changed - expected_paths(report)
    if unexpected:
        raise IssueProcessingError(
            "unexpected tracked changes prevent finalization: "
            + ", ".join(sorted(unexpected))
        )
    report["accepted_lines"] = accepted
    if local_only:
        report["status"] = "locally_finalized"
        write_json(path, report)
        return report
    branch = run(["git", "branch", "--show-current"], root=root, capture=True).strip()
    if branch != "main":
        raise IssueProcessingError(f"automatic publication requires main, found {branch!r}")
    paths = sorted(changed)
    if not paths:
        raise IssueProcessingError("no tracked changes are available to finalize")
    run(["git", "add", "--", *paths], root=root)
    run(["git", "diff", "--cached", "--check"], root=root)
    run(
        [
            "git",
            "commit",
            "-m",
            f"Apply {report['page']} corrections from issue {issue_number}",
        ],
        root=root,
    )
    commit = run(["git", "rev-parse", "HEAD"], root=root, capture=True).strip()
    run(["git", "push", "origin", branch], root=root)
    workflow_run = wait_for_deployment(commit, report["repository"], root)
    verify_deployment(report, commit, pages_url)
    note = (
        f"Applied {len(accepted)} human-confirmed correction(s) in commit "
        f"{commit[:7]}. Schema-2 notation was resolved before writing Level 1 text. "
        "Tests and the deployed corpus verification passed."
    )
    run(
        [
            "gh",
            "issue",
            "close",
            str(issue_number),
            "--repo",
            report["repository"],
            "--comment",
            note,
        ],
        root=root,
    )
    report.update(
        {
            "status": "closed",
            "commit": commit,
            "workflow_run": int(workflow_run),
        }
    )
    write_json(path, report)
    return report


def process_issue(args: argparse.Namespace) -> int:
    report = prepare(args.issue, repository=args.repository)
    path = report_path(args.issue)
    if report["second_opinions"]:
        print(
            f"Applied {len(report['applied_unflagged'])} unflagged change(s); "
            f"{len(report['second_opinions'])} second opinion(s) await review."
        )
        print(path)
        return 3
    finalized = finalize(args.issue, local_only=args.local_only, pages_url=args.pages_url)
    print(
        f"Finalized Issue #{args.issue}: {len(finalized['accepted_lines'])} correction(s); "
        f"status={finalized['status']}"
    )
    return 0


def finalize_issue(args: argparse.Namespace) -> int:
    report = finalize(args.issue, local_only=args.local_only, pages_url=args.pages_url)
    print(
        f"Finalized Issue #{args.issue}: {len(report['accepted_lines'])} correction(s); "
        f"status={report['status']}"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, handler in (("process", process_issue), ("finalize", finalize_issue)):
        command = subparsers.add_parser(name)
        command.add_argument("issue", type=int)
        command.add_argument("--repository", default=REPOSITORY)
        command.add_argument("--pages-url", default=PAGES_URL)
        command.add_argument(
            "--local-only",
            action="store_true",
            help="stop after local generation and tests without Git or GitHub writes",
        )
        command.set_defaults(handler=handler)
    args = parser.parse_args()
    try:
        return args.handler(args)
    except (IssueProcessingError, OSError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
