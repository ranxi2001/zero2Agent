#!/usr/bin/env python3
"""Reduce per-article LLM recall results into deterministic candidate queues."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any


QUEUE_FILES = {
    "duplicate_evidence": "duplicate-evidence.jsonl",
    "enhancement": "enhancement.jsonl",
    "novel": "novel.jsonl",
    "review": "review.jsonl",
    "out_of_scope": "out-of-scope.jsonl",
}
OUT_OF_SCOPE_RE = re.compile(
    r"职业规划|工作时长|工作地点|老家|什么时候(?:可以)?入职|什么时候来公司实习|"
    r"(?:还有|哪些|有什么).{0,6}(?:offer|公司在聊)|转正|职级|级别|层级|绩效|晋升|内部转岗|"
    r"为什么.{0,8}(?:离职|换工作)|变换工作|跳槽|你现在是在.{0,12}工作吗|你的名字|"
    r"平台给.{0,8}培养|兴趣爱好|日常生活|拿过国奖|"
    r"学校.{0,8}(?:课程|哪门课)|哪门课.{0,8}(?:感兴趣|帮助)|工作之外|"
    r"最近.{0,8}工作经历|实习.{0,10}(?:做什么|做了什么)|人数多少|"
    r"平常开发语言是什么|选择你擅长的语言|你有什么想问|打算看什么样的机会",
    re.IGNORECASE,
)
INCOMPLETE_RE = re.compile(
    r"^(?:请列出多种解决方法|这些框架有什么区别|要解决的问题|用了什么模型|"
    r"二分查找的进阶题|手撕[:：].{0,30}|那么这个结尾|背后有什么机制|如果允许使用除法|"
    r"uuid\s*内部如何适配|你的skill，对所有的issues怎么处理|2n\+1 个数.*找出单)",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--same-threshold", type=float, default=0.85)
    parser.add_argument("--overlap-threshold", type=float, default=0.80)
    parser.add_argument("--different-threshold", type=float, default=0.85)
    return parser.parse_args()


def normalized_question(value: str) -> str:
    return re.sub(r"[\W_]+", "", value, flags=re.UNICODE).casefold()


def scope_decision(question: str) -> tuple[str, str] | None:
    if OUT_OF_SCOPE_RE.search(question):
        return "out_of_scope", "non-technical or personal interview question"
    if INCOMPLETE_RE.search(question):
        return "review", "incomplete question or missing referent"
    return None


def best_match(matches: list[dict[str, Any]], relation: str) -> dict[str, Any] | None:
    candidates = [match for match in matches if match.get("llmRelation") == relation]
    if not candidates:
        return None
    return max(candidates, key=lambda match: float(match.get("llmConfidence") or 0))


def confidence(match: dict[str, Any] | None) -> float:
    return float(match.get("llmConfidence") or 0) if match else 0.0


def classify_question(
    question: dict[str, Any],
    same_threshold: float,
    overlap_threshold: float,
    different_threshold: float,
) -> tuple[str, dict[str, Any] | None, str]:
    matches = [match for match in question.get("matches") or [] if isinstance(match, dict)]
    same = best_match(matches, "same")
    overlap = best_match(matches, "overlap")
    different = best_match(matches, "different")
    if confidence(same) >= same_threshold:
        return "duplicate_evidence", same, "high-confidence same question"
    if confidence(overlap) >= overlap_threshold:
        return "enhancement", overlap, "high-confidence overlapping constraint"
    if same or overlap:
        selected = max((match for match in (same, overlap) if match), key=confidence)
        return "review", selected, "same/overlap relation below automatic threshold"
    if confidence(different) >= different_threshold:
        return "novel", different, "all recalled relations are different"
    return "review", different, "missing or low-confidence LLM relation"


def atomic_write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    os.replace(temp_path, path)


def build_queues(
    summary_path: Path,
    output_dir: Path,
    same_threshold: float = 0.85,
    overlap_threshold: float = 0.80,
    different_threshold: float = 0.85,
) -> dict[str, Any]:
    for name, value in (
        ("same-threshold", same_threshold),
        ("overlap-threshold", overlap_threshold),
        ("different-threshold", different_threshold),
    ):
        if not 0 <= value <= 1:
            raise ValueError(f"{name} must be between 0 and 1, got {value}")

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    queues: dict[str, list[dict[str, Any]]] = {name: [] for name in QUEUE_FILES}
    seen: set[tuple[str, str]] = set()
    duplicate_extractions = 0
    successful_articles = 0

    article_payloads: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for article in summary.get("articles", []):
        if article.get("status") != "ok":
            continue
        result_path = Path(str(article["resultPath"]))
        if not result_path.is_file():
            raise ValueError(f"Missing result JSON for article {article.get('index')}: {result_path}")
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        successful_articles += 1
        article_payloads.append((article, payload))

    for article, payload in article_payloads:
        source_classification = payload.get("sourceClassification") or {}
        for question in payload.get("questions") or []:
            question_text = str(question.get("question") or "").strip()
            fingerprint = (str(article["url"]), normalized_question(question_text))
            if not question_text or fingerprint in seen:
                duplicate_extractions += 1
                continue
            seen.add(fingerprint)
            if scoped := scope_decision(question_text):
                decision, reason = scoped
                selected = None
            else:
                decision, selected, reason = classify_question(
                    question,
                    same_threshold,
                    overlap_threshold,
                    different_threshold,
                )
            matches = [
                {
                    key: match.get(key)
                    for key in (
                        "dimension",
                        "title",
                        "score",
                        "recallScore",
                        "llmRelation",
                        "llmConfidence",
                        "llmReason",
                    )
                }
                for match in (question.get("matches") or [])[:5]
            ]
            record = {
                "articleIndex": article["index"],
                "articleTitle": article["title"],
                "url": article["url"],
                "resultPath": str(result_path),
                "sourceClassification": source_classification,
                "questionId": question.get("id"),
                "question": question_text,
                "decision": decision,
                "decisionReason": reason,
                "selectedMatch": selected,
                "topMatches": matches,
            }
            queues[decision].append(record)

    output_dir.mkdir(parents=True, exist_ok=True)
    for queue, filename in QUEUE_FILES.items():
        atomic_write_jsonl(output_dir / filename, queues[queue])
    queue_summary = {
        "schemaVersion": 1,
        "sourceSummary": str(summary_path),
        "successfulArticles": successful_articles,
        "questionCount": sum(len(records) for records in queues.values()),
        "duplicateExtractionsRemoved": duplicate_extractions,
        "thresholds": {
            "same": same_threshold,
            "overlap": overlap_threshold,
            "different": different_threshold,
        },
        "counts": {queue: len(records) for queue, records in queues.items()},
        "files": QUEUE_FILES,
    }
    temp_path = output_dir / "queue-summary.tmp"
    temp_path.write_text(json.dumps(queue_summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temp_path, output_dir / "queue-summary.json")
    return queue_summary


def main() -> int:
    arguments = parse_args()
    summary = build_queues(
        arguments.summary.resolve(),
        arguments.out.resolve(),
        arguments.same_threshold,
        arguments.overlap_threshold,
        arguments.different_threshold,
    )
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
