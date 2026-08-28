#!/usr/bin/env python3
"""Shared parsing and validation for interview-question frequency data."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


SECTION_RE = re.compile(r"^##\s+([0-9]{2}-[^（\s]+)（(\d+)题）\s*$")
QUESTION_RE = re.compile(r"^(\d+)\.\s+(.+?)(?:\s+—\s+(.*))?$")
ANNOTATION_RE = re.compile(r"【([^】]+)】")
NEW_MARK_RE = re.compile(r"（(?:新增|补录索引)）")
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(https?://[^)]+\)")
GENERIC_SOURCE_RE = re.compile(
    r"30题|后端AI八股|已有正文|高频题|"
    r"八股合集|问题汇总|面试题汇总|题库汇总|面试题单"
)


@dataclass(frozen=True)
class IndexQuestion:
    dimension: str
    ordinal: int
    title: str
    source: str


def parse_question_index(path: Path) -> list[IndexQuestion]:
    questions: list[IndexQuestion] = []
    dimension = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        section_match = SECTION_RE.match(line)
        if section_match:
            dimension = section_match.group(1)
            continue
        question_match = QUESTION_RE.match(line)
        if not dimension or not question_match:
            continue
        questions.append(
            IndexQuestion(
                dimension=dimension,
                ordinal=int(question_match.group(1)),
                title=question_match.group(2).strip(),
                source=(question_match.group(3) or "").strip(),
            )
        )
    return questions


def _clean_evidence(value: str) -> str:
    return NEW_MARK_RE.sub("", value).strip(" /、，,；; ")


def _is_attributable(value: str) -> bool:
    value = _clean_evidence(value)
    if not value or value.startswith("含追问"):
        return False
    return GENERIC_SOURCE_RE.search(re.sub(r"\s+", "", value)) is None


def _expand_evidence(value: str) -> list[str]:
    """Expand explicit multi-source labels without splitting question details."""
    value = _clean_evidence(value)
    if not value:
        return []
    links = MARKDOWN_LINK_RE.findall(value)
    if len(links) > 1:
        return links
    descriptor = re.split(r"[：:]", value, maxsplit=1)[0]
    multiplicity = 1 + descriptor.count("、")
    if "http" not in descriptor.casefold():
        multiplicity += descriptor.count("/")
    if multiplicity == 1:
        return [value]
    return [f"{value} [{position}/{multiplicity}]" for position in range(1, multiplicity + 1)]


def infer_evidence(source: str) -> list[str]:
    """Seed attributable interview occurrences from the existing source notation."""
    annotations = ANNOTATION_RE.findall(source)
    primary = ANNOTATION_RE.sub("", source).strip()
    candidates = _expand_evidence(primary)
    for annotation in annotations:
        candidates.extend(_expand_evidence(annotation))

    evidence: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        candidate = _clean_evidence(candidate)
        fingerprint = re.sub(r"\s+", "", candidate).casefold()
        if not _is_attributable(candidate) or fingerprint in seen:
            continue
        seen.add(fingerprint)
        evidence.append(candidate)
    return evidence


def question_key(dimension: str, title: str) -> tuple[str, str]:
    return dimension, title.strip()


def load_frequency(path: Path) -> dict[tuple[str, str], dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schemaVersion") != 1:
        raise ValueError(f"Unsupported frequency schema: {payload.get('schemaVersion')}")
    records: dict[tuple[str, str], dict[str, object]] = {}
    first_seen: set[tuple[str, int]] = set()
    for record in payload.get("questions", []):
        dimension = str(record.get("dimension", ""))
        title = str(record.get("title", ""))
        evidence = record.get("evidence", [])
        frequency = record.get("frequency")
        first_seen_order = record.get("firstSeenOrder")
        if (
            not dimension
            or not title
            or not isinstance(evidence, list)
            or not isinstance(first_seen_order, int)
            or first_seen_order < 1
        ):
            raise ValueError(f"Invalid frequency record: {record}")
        if frequency != len(evidence):
            raise ValueError(
                f"Frequency differs from evidence count for {dimension} / {title}: "
                f"{frequency} != {len(evidence)}"
            )
        evidence_fingerprints = [
            re.sub(r"\s+", "", str(item)).casefold() for item in evidence
        ]
        if any(not fingerprint for fingerprint in evidence_fingerprints):
            raise ValueError(f"Empty evidence for {dimension} / {title}")
        if len(evidence_fingerprints) != len(set(evidence_fingerprints)):
            raise ValueError(f"Duplicate evidence for {dimension} / {title}")
        key = question_key(dimension, title)
        if key in records:
            raise ValueError(f"Duplicate frequency record: {dimension} / {title}")
        first_seen_key = dimension, first_seen_order
        if first_seen_key in first_seen:
            raise ValueError(f"Duplicate firstSeenOrder: {dimension} / {first_seen_order}")
        first_seen.add(first_seen_key)
        records[key] = record
    return records


def validate_coverage(
    questions: list[IndexQuestion], records: dict[tuple[str, str], dict[str, object]]
) -> None:
    expected = {question_key(question.dimension, question.title) for question in questions}
    actual = set(records)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing={missing[:5]} ({len(missing)} total)")
        if extra:
            details.append(f"extra={extra[:5]} ({len(extra)} total)")
        raise ValueError("Frequency coverage mismatch: " + "; ".join(details))
    for question in questions:
        record = records[question_key(question.dimension, question.title)]
        actual_evidence = {
            re.sub(r"\s+", "", str(item)).casefold()
            for item in record["evidence"]
        }
        missing_evidence = [
            item
            for item in infer_evidence(question.source)
            if re.sub(r"\s+", "", item).casefold() not in actual_evidence
        ]
        if missing_evidence:
            raise ValueError(
                f"Frequency evidence is stale for {question.dimension} / {question.title}: "
                f"missing={missing_evidence}"
            )
