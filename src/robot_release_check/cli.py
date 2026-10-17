from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .checks import run_checks
from .io import load_project
from .report import build_json_report, render_text, write_html


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="robot-release-check",
        description="Check whether supplied robot release evidence still covers the declared delivered release.",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    p.add_argument("project_dir", type=Path, help="Directory containing release.json, tests.json, changes.json, closures.json")
    p.add_argument("--html", type=Path, help="Write an HTML report to this path")
    p.add_argument("--json", dest="json_out", type=Path, help="Write machine-readable findings JSON to this path")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        release, tests, changes, closures = load_project(args.project_dir)
        findings = run_checks(release, tests, changes, closures)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(render_text(release, tests, findings))

    if args.html:
        args.html.parent.mkdir(parents=True, exist_ok=True)
        write_html(args.html, release, tests, findings)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(build_json_report(release, tests, findings), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return 1 if any(f.status != "PASS" for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
