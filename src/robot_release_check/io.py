from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import ChangeRecord, ClosureRecord, Release, TestRecord, VerificationRecord


REQUIRED_FILES = (
    "release.json",
    "tests.json",
    "changes.json",
    "closures.json",
    "verifications.json",
)


def load_project(path: Path):
    missing = [name for name in REQUIRED_FILES if not (path / name).is_file()]
    if missing:
        raise ValueError("missing required file(s): " + ", ".join(missing))

    release_raw = _read_json(path / "release.json")
    tests_raw = _read_json(path / "tests.json")
    changes_raw = _read_json(path / "changes.json")
    closures_raw = _read_json(path / "closures.json")
    verifications_raw = _read_json(path / "verifications.json")

    if not isinstance(release_raw, dict):
        raise ValueError("release.json must contain a JSON object")
    for name, raw in (
        ("tests.json", tests_raw),
        ("changes.json", changes_raw),
        ("closures.json", closures_raw),
        ("verifications.json", verifications_raw),
    ):
        if not isinstance(raw, list):
            raise ValueError(f"{name} must contain a JSON array")

    verifications = [VerificationRecord.from_json(x) for x in verifications_raw]
    _ensure_unique_verification_ids(verifications)

    return (
        Release.from_json(release_raw),
        [TestRecord.from_json(x) for x in tests_raw],
        [ChangeRecord.from_json(x) for x in changes_raw],
        [ClosureRecord.from_json(x) for x in closures_raw],
        verifications,
    )


def _ensure_unique_verification_ids(verifications: list[VerificationRecord]) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for record in verifications:
        if record.verification_id in seen:
            duplicates.add(record.verification_id)
        seen.add(record.verification_id)
    if duplicates:
        raise ValueError(
            "verifications.json contains duplicate verification_id(s): "
            + ", ".join(sorted(duplicates))
        )


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path.name}: {exc}") from exc
