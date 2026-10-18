from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable


def parse_time(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("timestamp must be a non-empty ISO-8601 string")
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"invalid ISO-8601 timestamp: {value!r}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"timestamp must include a timezone offset: {value!r}")
    return parsed


@dataclass(frozen=True)
class Release:
    release_id: str
    delivered_at: datetime

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "Release":
        return cls(
            release_id=_required_str(data, "release_id"),
            delivered_at=parse_time(_required_str(data, "delivered_at")),
        )


@dataclass(frozen=True)
class TestRecord:
    test_id: str
    release_id: str
    status: str
    completed_at: datetime
    test_type: str = "unspecified"

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "TestRecord":
        return cls(
            test_id=_required_str(data, "test_id"),
            release_id=_required_str(data, "release_id"),
            status=_required_str(data, "status").upper(),
            completed_at=parse_time(_required_str(data, "completed_at")),
            test_type=str(data.get("test_type", "unspecified")),
        )


@dataclass(frozen=True)
class ChangeRecord:
    change_id: str
    release_id: str
    changed_at: datetime
    description: str = ""

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "ChangeRecord":
        return cls(
            change_id=_required_str(data, "change_id"),
            release_id=_required_str(data, "release_id"),
            changed_at=parse_time(_required_str(data, "changed_at")),
            description=str(data.get("description", "")),
        )


@dataclass(frozen=True)
class ClosureRecord:
    item_id: str
    status: str
    closed_at: datetime
    verification_evidence: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "ClosureRecord":
        evidence = data.get("verification_evidence", [])
        if evidence is None:
            evidence = []
        if not isinstance(evidence, list) or not all(isinstance(x, str) for x in evidence):
            raise ValueError("verification_evidence must be a list of strings")
        return cls(
            item_id=_required_str(data, "item_id"),
            status=_required_str(data, "status").upper(),
            closed_at=parse_time(_required_str(data, "closed_at")),
            verification_evidence=tuple(x.strip() for x in evidence if x.strip()),
        )


@dataclass(frozen=True)
class VerificationRecord:
    verification_id: str
    release_id: str

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "VerificationRecord":
        return cls(
            verification_id=_required_str(data, "verification_id"),
            release_id=_required_str(data, "release_id"),
        )


def _required_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value.strip()


def latest_qualifying_pass(
    tests: Iterable[TestRecord],
    *,
    not_after: datetime | None = None,
    release_id: str | None = None,
) -> TestRecord | None:
    passing = [
        t for t in tests
        if t.status == "PASS"
        and (not_after is None or t.completed_at <= not_after)
        and (release_id is None or t.release_id == release_id)
    ]
    return max(passing, key=lambda t: t.completed_at, default=None)
