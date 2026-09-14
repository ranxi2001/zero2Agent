#!/usr/bin/env python3
"""Stably sort interview questions by frequency inside existing topic groups."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

from question_frequency import (
    IndexQuestion,
    load_frequency,
    parse_question_index,
    question_key,
    validate_coverage,
)


QUESTION_HEADING_RE = re.compile(r"^(##|###)\s+Q[：:]\s*(.+?)\s*$")
SOURCE_RE = re.compile(r"^>\s*来源[：:]\s*(.+?)\s*$")
SECTION_RE = re.compile(r"^##\s+([0-9]{2}-[^（\s]+)（(\d+)题）\s*$")
INDEX_QUESTION_RE = re.compile(r"^(\d+)\.\s+(.+?)(?:\s+—\s+(.*))?$")
FOOTER_RE = re.compile(
    r"^##\s+.*(?:答题模式|答题主线|推荐阅读|参考资料|相关阅读|延伸阅读|总结|小结|附：)"
)
FENCE_RE = re.compile(r"^\s*(```+|~~~+)")


@dataclass(frozen=True)
class QuestionHeading:
    line: int
    level: int
    title: str
    source: str


def markdown_headings(
    lines: list[str],
) -> tuple[list[QuestionHeading], list[int], int | None]:
    questions: list[QuestionHeading] = []
    group_boundaries: list[int] = []
    footer: int | None = None
    fence = ""
    for index, line in enumerate(lines):
        fence_match = FENCE_RE.match(line)
        if fence_match:
            marker = fence_match.group(1)[0]
            if not fence:
                fence = marker
            elif marker == fence:
                fence = ""
            continue
        if fence:
            continue
        question_match = QUESTION_HEADING_RE.match(line)
        if question_match:
            source = ""
            cursor = index + 1
            while cursor < len(lines) and cursor <= index + 6:
                source_match = SOURCE_RE.match(lines[cursor])
                if source_match:
                    source = source_match.group(1).strip()
                    break
                if QUESTION_HEADING_RE.match(lines[cursor]):
                    break
                cursor += 1
            questions.append(
                QuestionHeading(
                    line=index,
                    level=len(question_match.group(1)),
                    title=question_match.group(2).strip(),
                    source=source,
                )
            )
            continue
        if FOOTER_RE.match(line):
            footer = index
            continue
        if not line.startswith("## ") or line.startswith("### "):
            continue
        cursor = index + 1
        while cursor < len(lines) and (not lines[cursor].strip() or lines[cursor].strip() == "---"):
            cursor += 1
        if cursor < len(lines) and lines[cursor].startswith("### Q"):
            group_boundaries.append(index)
    return questions, group_boundaries, footer


def _normalized_title(value: str) -> str:
    return re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]+", "", value).casefold()


def match_body_to_index(
    path: Path, headings: list[QuestionHeading], index: list[IndexQuestion]
) -> list[int]:
    if len(headings) != len(index):
        raise ValueError(f"{path}: body has {len(headings)} questions, index has {len(index)}")
    available = set(range(len(index)))
    matches: list[int] = []
    for body_position, heading in enumerate(headings):
        left = _normalized_title(heading.title)
        candidates: list[tuple[float, int]] = []
        for position in available:
            right = _normalized_title(index[position].title)
            title_score = SequenceMatcher(None, left, right).ratio()
            if left in right or right in left:
                title_score += 0.25
            body_source = _normalized_title(heading.source)
            index_source = _normalized_title(index[position].source)
            source_score = SequenceMatcher(None, body_source, index_source).ratio()
            if body_source and index_source and (
                body_source in index_source or index_source in body_source
            ):
                source_score += 0.25
            order_bonus = max(0.0, 0.08 - abs(body_position - position) * 0.004)
            candidates.append((title_score + 0.35 * source_score + order_bonus, position))
        candidates.sort(reverse=True)
        score, position = candidates[0]
        runner_up = candidates[1][0] if len(candidates) > 1 else 0.0
        if score < 0.55 or (score < 1.0 and score - runner_up < 0.04):
            raise ValueError(
                f"{path}:{heading.line + 1}: body/index title mismatch: "
                f"{heading.title!r}; best={index[position].title!r} "
                f"(score={score:.2f}, margin={score - runner_up:.2f})"
            )
        matches.append(position)
        available.remove(position)
    if available:
        raise ValueError(f"{path}: unmatched index questions: {sorted(available)}")
    return matches


def sort_article(
    path: Path,
    index_questions: list[IndexQuestion],
    frequency: dict[tuple[str, str], dict[str, object]],
) -> tuple[str, list[int]]:
    original = path.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)
    headings, structural_boundaries, footer = markdown_headings(
        [line.rstrip("\r\n") for line in lines]
    )
    body_to_index = match_body_to_index(path, headings, index_questions)
    if not headings:
        return original, []

    question_by_line = {
        heading.line: body_to_index[body_position]
        for body_position, heading in enumerate(headings)
    }
    bucket_starts = {headings[0].line, *structural_boundaries}
    for previous, current in zip(headings, headings[1:]):
        if previous.level != current.level:
            bucket_starts.add(current.line)
    terminal = footer if footer is not None and footer > headings[-1].line else len(lines)
    bucket_starts = sorted(start for start in bucket_starts if start < terminal)
    if bucket_starts[0] > headings[0].line:
        bucket_starts.insert(0, headings[0].line)

    output = lines[: bucket_starts[0]]
    permutation: list[int] = []
    for bucket_number, bucket_start in enumerate(bucket_starts):
        bucket_end = (
            bucket_starts[bucket_number + 1]
            if bucket_number + 1 < len(bucket_starts)
            else terminal
        )
        bucket_question_lines = [
            heading.line
            for heading in headings
            if bucket_start <= heading.line < bucket_end
        ]
        if not bucket_question_lines:
            output.extend(lines[bucket_start:bucket_end])
            continue
        first_question = bucket_question_lines[0]
        output.extend(lines[bucket_start:first_question])
        blocks: list[tuple[int, int, int, list[str]]] = []
        for position, start in enumerate(bucket_question_lines):
            end = bucket_question_lines[position + 1] if position + 1 < len(bucket_question_lines) else bucket_end
            original_position = question_by_line[start]
            question = index_questions[original_position]
            record = frequency[question_key(question.dimension, question.title)]
            score = int(record["frequency"])
            first_seen_order = int(record["firstSeenOrder"])
            blocks.append((score, first_seen_order, original_position, lines[start:end]))
        blocks.sort(key=lambda block: (-block[0], block[1], block[2]))
        for _, _, original_position, block in blocks:
            output.extend(block)
            permutation.append(original_position)
    output.extend(lines[terminal:])
    return "".join(output), permutation


def reorder_index(source: str, permutations: dict[str, list[int]]) -> str:
    lines = source.splitlines(keepends=True)
    section_positions: list[tuple[int, str]] = []
    for position, line in enumerate(lines):
        match = SECTION_RE.match(line.rstrip("\r\n"))
        if match:
            section_positions.append((position, match.group(1)))
    for section_number in range(len(section_positions) - 1, -1, -1):
        start, dimension = section_positions[section_number]
        end = (
            section_positions[section_number + 1][0]
            if section_number + 1 < len(section_positions)
            else len(lines)
        )
        question_positions = [
            position
            for position in range(start + 1, end)
            if INDEX_QUESTION_RE.match(lines[position].rstrip("\r\n"))
        ]
        permutation = permutations.get(dimension)
        if permutation is None:
            continue
        if len(question_positions) != len(permutation):
            raise ValueError(
                f"{dimension}: index has {len(question_positions)} questions, permutation has {len(permutation)}"
            )
        original_lines = [lines[position] for position in question_positions]
        reordered = []
        for ordinal, original_position in enumerate(permutation, start=1):
            match = INDEX_QUESTION_RE.match(original_lines[original_position].rstrip("\r\n"))
            assert match
            suffix = f" — {match.group(3)}" if match.group(3) else ""
            newline = "\n" if original_lines[original_position].endswith("\n") else ""
            reordered.append(f"{ordinal}. {match.group(2)}{suffix}{newline}")
        for position, replacement in zip(question_positions, reordered):
            lines[position] = replacement
    return "".join(lines)


def main() -> int:
    skill_dir = Path(__file__).resolve().parents[1]
    repo = skill_dir.parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--index", type=Path, default=skill_dir / "question-index.md")
    parser.add_argument("--frequency", type=Path, default=skill_dir / "question-frequency.json")
    arguments = parser.parse_args()

    index_questions = parse_question_index(arguments.index)
    frequency = load_frequency(arguments.frequency)
    validate_coverage(index_questions, frequency)
    by_dimension: dict[str, list[IndexQuestion]] = {}
    for question in index_questions:
        by_dimension.setdefault(question.dimension, []).append(question)

    changed: list[Path] = []
    permutations: dict[str, list[int]] = {}
    article_updates: dict[Path, str] = {}
    for dimension, questions in by_dimension.items():
        article = repo / "learn-agent-interview" / dimension / "index.md"
        sorted_content, permutation = sort_article(article, questions, frequency)
        permutations[dimension] = permutation
        if sorted_content != article.read_text(encoding="utf-8"):
            changed.append(article)
            article_updates[article] = sorted_content

    original_index = arguments.index.read_text(encoding="utf-8")
    sorted_index = reorder_index(original_index, permutations)
    if sorted_index != original_index:
        changed.append(arguments.index)

    if arguments.check:
        if changed:
            raise SystemExit("Frequency order is stale: " + ", ".join(str(path) for path in changed))
    else:
        for path, content in article_updates.items():
            path.write_text(content, encoding="utf-8", newline="\n")
        if sorted_index != original_index:
            arguments.index.write_text(sorted_index, encoding="utf-8", newline="\n")
    print(
        f"questions_sorted={sum(len(v) for v in permutations.values())} "
        f"changed={len(changed)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
