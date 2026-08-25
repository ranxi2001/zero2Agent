#!/usr/bin/env python3
"""Build the deterministic machine-readable interview question index."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path


SECTION_RE = re.compile(r"^##\s+([0-9]{2}-[^（\s]+)（(\d+)题）\s*$")
QUESTION_RE = re.compile(r"^(\d+)\.\s+(.+?)(?:\s+—\s+(.*))?$")
TOTAL_RE = re.compile(r"^\|\s*\*\*总计\*\*\s*\|\s*\*\*(\d+)\*\*\s*\|$")
UPDATED_RE = re.compile(r"最后更新：(\d{4}-\d{2}-\d{2})")


def build_index(source: Path) -> dict[str, object]:
    lines = source.read_text(encoding="utf-8").splitlines()
    expected_total = 0
    updated_at = ""
    dimension = ""
    expected_dimension_counts: dict[str, int] = {}
    questions: list[dict[str, object]] = []

    for line in lines:
        if not updated_at:
            updated_match = UPDATED_RE.search(line)
            if updated_match:
                updated_at = updated_match.group(1)
        total_match = TOTAL_RE.match(line)
        if total_match:
            expected_total = int(total_match.group(1))
        section_match = SECTION_RE.match(line)
        if section_match:
            dimension = section_match.group(1)
            expected_dimension_counts[dimension] = int(section_match.group(2))
            continue
        question_match = QUESTION_RE.match(line)
        if not question_match or not dimension:
            continue
        ordinal = int(question_match.group(1))
        title = question_match.group(2).strip()
        source_text = (question_match.group(3) or "").strip()
        questions.append(
            {
                "id": f"{dimension}:{ordinal:03d}",
                "dimension": dimension,
                "ordinal": ordinal,
                "title": title,
                "source": source_text,
                "searchText": f"{title} {source_text}".strip(),
            }
        )

    actual_counts = Counter(str(question["dimension"]) for question in questions)
    if expected_total != len(questions):
        raise ValueError(f"Markdown total is {expected_total}, parsed {len(questions)} questions")
    if dict(actual_counts) != expected_dimension_counts:
        raise ValueError(
            f"Dimension counts differ: expected {expected_dimension_counts}, parsed {dict(actual_counts)}"
        )
    for name, count in actual_counts.items():
        ordinals = [
            int(question["ordinal"])
            for question in questions
            if question["dimension"] == name
        ]
        if ordinals != list(range(1, count + 1)):
            raise ValueError(f"Question ordinals are not continuous in {name}: {ordinals}")

    return {
        "schemaVersion": 1,
        "updatedAt": updated_at,
        "questionCount": len(questions),
        "dimensions": expected_dimension_counts,
        "questions": questions,
    }


def serialize(index: dict[str, object]) -> str:
    return json.dumps(index, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    skill_dir = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=str(skill_dir / "question-index.md"))
    parser.add_argument("--out", default=str(skill_dir / "question-index.json"))
    parser.add_argument("--check", action="store_true", help="Fail if output is stale")
    arguments = parser.parse_args()
    try:
        content = serialize(build_index(Path(arguments.source)))
        output_path = Path(arguments.out)
        if arguments.check:
            if not output_path.is_file() or output_path.read_text(encoding="utf-8") != content:
                raise ValueError(f"{output_path} is stale; rebuild it without --check")
        else:
            output_path.write_text(content, encoding="utf-8", newline="\n")
    except (OSError, UnicodeError, ValueError) as error:
        parser.error(str(error))
    index = json.loads(content)
    print(f"questions={index['questionCount']} dimensions={len(index['dimensions'])} output={arguments.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
