#!/usr/bin/env python3
"""Create, merge, or validate the interview-question frequency ledger."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from question_frequency import (
    infer_evidence,
    load_frequency,
    parse_question_index,
    question_key,
    validate_coverage,
)


def main() -> int:
    skill_dir = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=skill_dir / "question-index.md")
    parser.add_argument("--out", type=Path, default=skill_dir / "question-frequency.json")
    parser.add_argument(
        "--first-seen-index",
        type=Path,
        help="Optional historical question-index.md used to seed firstSeenOrder",
    )
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--rebuild-from-index",
        action="store_true",
        help="Discard maintained evidence and reseed it from question-index.md",
    )
    arguments = parser.parse_args()

    questions = parse_question_index(arguments.index)
    if arguments.check:
        records = load_frequency(arguments.out)
        validate_coverage(questions, records)
        print(f"questions={len(questions)} frequency_records={len(records)} status=ok")
        return 0

    existing = (
        load_frequency(arguments.out)
        if arguments.out.is_file() and not arguments.rebuild_from_index
        else {}
    )
    existing_dimensions = {str(record["dimension"]) for record in existing.values()}
    historical_questions = (
        parse_question_index(arguments.first_seen_index)
        if arguments.first_seen_index
        else questions
    )
    historical_order: dict[tuple[str, str], int] = {}
    next_order: dict[str, int] = {}
    for historical in historical_questions:
        key = question_key(historical.dimension, historical.title)
        historical_order.setdefault(key, historical.ordinal)
        next_order[historical.dimension] = max(
            next_order.get(historical.dimension, 0), historical.ordinal
        )
    for record in existing.values():
        dimension = str(record["dimension"])
        next_order[dimension] = max(
            next_order.get(dimension, 0), int(record["firstSeenOrder"])
        )
    payload_questions = []
    for question in questions:
        key = question_key(question.dimension, question.title)
        if key in existing:
            evidence = existing[key]["evidence"]
            first_seen_order = existing[key]["firstSeenOrder"]
        else:
            evidence = infer_evidence(question.source)
            first_seen_order = (
                None
                if question.dimension in existing_dimensions
                else historical_order.get(key)
            )
            if first_seen_order is None:
                next_order[question.dimension] = next_order.get(question.dimension, 0) + 1
                first_seen_order = next_order[question.dimension]
        payload_questions.append(
            {
                "dimension": question.dimension,
                "title": question.title,
                "frequency": len(evidence),
                "firstSeenOrder": first_seen_order,
                "evidence": evidence,
            }
        )

    payload = {
        "schemaVersion": 1,
        "updatedAt": date.today().isoformat(),
        "countingRule": (
            "frequency equals the number of attributable interview occurrences in evidence; "
            "generic compilations and untraceable high-frequency labels do not count; "
            "firstSeenOrder is the stable tie-breaker inside a topic group"
        ),
        "questions": payload_questions,
    }
    arguments.out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"questions={len(questions)} frequency_records={len(payload_questions)} "
        f"output={arguments.out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
