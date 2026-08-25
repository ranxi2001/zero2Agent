#!/usr/bin/env python3
"""Recall similar interview questions with BM25 and character n-grams."""

from __future__ import annotations

import argparse
import codecs
import json
import locale
import math
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


SECTION_RE = re.compile(r"^##\s+([0-9]{2}-[^（\s]+)")
QUESTION_RE = re.compile(r"^\d+\.\s+(.+?)(?:\s+—\s+.*)?$")
HEADING_QUESTION_RE = re.compile(r"^###\s+\d+\.\s+(.+?)\s*$")
MARKDOWN_SECTION_RE = re.compile(r"^##\s+(.+?)\s*$")
TABLE_ROW_RE = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|$")
ASCII_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_+./-]*")
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]+")
SEMANTIC_RULES = (
    (
        re.compile(
            r"(?:判断|决定).{0,12}(?:(?:是否|需要|要不要).{0,8})?(?:调用|使用).{0,4}工具"
            r"|(?:调用|使用).{0,4}工具.{0,12}(?:回复|回答)"
        ),
        "semantic:tool-decision",
    ),
    (
        re.compile(r"(?:agent\s*)?(?:loop|循环).{0,12}(?:继续|结束|退出|终止)|足够的信息.{0,12}(?:输出|结论)|(?:退出|终止)条件"),
        "semantic:loop-exit",
    ),
    (
        re.compile(r"auto\s*research|deep\s*research|自动研究|研究型\s*agent"),
        "semantic:auto-research",
    ),
    (
        re.compile(r"(?:skill|agents\.md).{0,24}(?:评测|评价|验证|效果|提升|对比)|(?:评测|评价|验证|对比).{0,24}skill"),
        "semantic:skill-eval",
    ),
    (
        re.compile(r"coding\s*agent.{0,20}(?:项目|开发|工作流|重构)|(?:项目开发|工作流|重构).{0,20}coding\s*agent|ai\s*coding.{0,20}工作流"),
        "semantic:coding-workflow",
    ),
    (
        re.compile(r"(?:完整.{0,4}链路|全流程数据流)|(?:用户输入|输入).{0,20}(?:最终回答|页面展示|代码产出)"),
        "semantic:agent-full-chain",
    ),
    (
        re.compile(r"function\s*call.{0,20}tool\s*result|tool\s*result.{0,20}(?:回写|上下文|模型)"),
        "semantic:tool-result-loop",
    ),
    (
        re.compile(r"context\s*engineering.{0,24}skills?|skills?.{0,24}context\s*engineering"),
        "semantic:context-skills",
    ),
    (
        re.compile(r"\breact\b|reasoning.{0,12}action|推理.{0,8}行动.{0,8}循环"),
        "semantic:react-loop",
    ),
    (
        re.compile(r"jwt.{0,24}(?:验证|验签|真实性|完整性|签名|结构)|(?:验证|验签|真实性|完整性|签名).{0,24}jwt"),
        "semantic:jwt-verification",
    ),
)
SOURCE_SEMANTIC_TAGS = frozenset({"semantic:coding-workflow", "semantic:context-skills"})


@dataclass(frozen=True)
class IndexedQuestion:
    dimension: str
    title: str
    tokens: tuple[str, ...]
    grams: frozenset[str]


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower()
    return re.sub(r"\s+", " ", text).strip()


def character_grams(text: str) -> frozenset[str]:
    compact = re.sub(r"[^a-z0-9\u3400-\u4dbf\u4e00-\u9fff]+", "", normalize(text))
    grams: set[str] = set()
    for size in (2, 3):
        grams.update(compact[i : i + size] for i in range(max(0, len(compact) - size + 1)))
    return frozenset(grams)


def semantic_tags(text: str) -> tuple[str, ...]:
    normalized = normalize(text)
    return tuple(tag for pattern, tag in SEMANTIC_RULES if pattern.search(normalized))


def tokenize(text: str, semantic_text: str | None = None) -> tuple[str, ...]:
    normalized = normalize(text)
    tokens = list(ASCII_TOKEN_RE.findall(normalized))
    for chunk in CJK_RE.findall(normalized):
        tokens.extend(chunk[i : i + 2] for i in range(max(0, len(chunk) - 1)))
        if len(chunk) == 1:
            tokens.append(chunk)
    tokens.extend(semantic_tags(semantic_text if semantic_text is not None else normalized))
    return tuple(tokens)


def parse_index(path: Path) -> list[IndexedQuestion]:
    if path.suffix.lower() == ".json":
        return parse_json_index(path)
    questions: list[IndexedQuestion] = []
    dimension = "unknown"
    in_algorithm_table = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        section_match = SECTION_RE.match(raw_line)
        if section_match:
            dimension = section_match.group(1)
            in_algorithm_table = False
            continue
        markdown_section = MARKDOWN_SECTION_RE.match(raw_line)
        if markdown_section and not section_match:
            section_title = markdown_section.group(1).strip()
            dimension = f"backend:{section_title}"
            in_algorithm_table = section_title == "算法与手撕题单"
            continue
        heading_question = HEADING_QUESTION_RE.match(raw_line)
        if heading_question:
            title = heading_question.group(1).strip()
            questions.append(make_indexed_question(dimension, title, raw_line))
            continue
        question_match = QUESTION_RE.match(raw_line)
        if not question_match or dimension == "unknown":
            if in_algorithm_table:
                row_match = TABLE_ROW_RE.match(raw_line)
                if row_match:
                    title = row_match.group(1).strip()
                    if title not in {"题目", "------"} and not set(title) <= {"-", ":"}:
                        questions.append(make_indexed_question(dimension, title, raw_line))
            continue
        title = question_match.group(1).strip()
        questions.append(make_indexed_question(dimension, title, raw_line))
    if not questions:
        raise ValueError(f"No indexed questions found in {path}")
    return questions


def parse_json_index(path: Path) -> list[IndexedQuestion]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    questions: list[IndexedQuestion] = []
    for item in payload.get("questions") or []:
        dimension = str(item.get("dimension") or "unknown")
        title = str(item.get("title") or "").strip()
        if not title:
            continue
        search_text = str(item.get("searchText") or title)
        questions.append(make_indexed_question(dimension, title, search_text))
    declared_count = int(payload.get("questionCount") or 0)
    if declared_count != len(questions):
        raise ValueError(f"JSON index declares {declared_count}, parsed {len(questions)} questions")
    return questions


def make_indexed_question(dimension: str, title: str, search_text: str) -> IndexedQuestion:
    tokens = list(tokenize(search_text, semantic_text=title))
    tokens.extend(tag for tag in semantic_tags(search_text) if tag in SOURCE_SEMANTIC_TAGS)
    return IndexedQuestion(
        dimension=dimension,
        title=title,
        tokens=tuple(tokens),
        grams=character_grams(title),
    )


def default_index_paths() -> list[Path]:
    skill_dir = Path(__file__).resolve().parents[1]
    skill_json_index = skill_dir / "question-index.json"
    skill_markdown_index = skill_dir / "question-index.md"
    skill_index = skill_json_index if skill_json_index.is_file() else skill_markdown_index
    repo_root = Path(__file__).resolve().parents[4]
    backend_index = repo_root.parent / "zero2Leetcode" / "_includes" / "interview-seasons" / "2026" / "summer.md"
    return [path for path in (skill_index, backend_index) if path.is_file()]


def parse_indexes(paths: list[Path]) -> list[IndexedQuestion]:
    documents: list[IndexedQuestion] = []
    seen: set[tuple[str, str]] = set()
    for path in paths:
        for document in parse_index(path):
            key = (document.dimension, normalize(document.title))
            if key in seen:
                continue
            seen.add(key)
            documents.append(document)
    if not documents:
        raise ValueError("No indexed questions found")
    return documents


def bm25_scores(query_tokens: tuple[str, ...], documents: list[IndexedQuestion]) -> list[float]:
    document_frequency: Counter[str] = Counter()
    term_frequencies: list[Counter[str]] = []
    lengths: list[int] = []
    for document in documents:
        counts = Counter(document.tokens)
        term_frequencies.append(counts)
        lengths.append(sum(counts.values()))
        document_frequency.update(counts.keys())

    document_count = len(documents)
    average_length = sum(lengths) / document_count if document_count else 1.0
    query_counts = Counter(query_tokens)
    k1 = 1.5
    b = 0.75
    scores: list[float] = []
    for counts, length in zip(term_frequencies, lengths):
        score = 0.0
        for token, query_frequency in query_counts.items():
            frequency = counts.get(token, 0)
            if not frequency:
                continue
            frequency_in_docs = document_frequency[token]
            inverse_document_frequency = math.log(
                1.0 + (document_count - frequency_in_docs + 0.5) / (frequency_in_docs + 0.5)
            )
            denominator = frequency + k1 * (1.0 - b + b * length / max(average_length, 1.0))
            semantic_weight = 8.0 if token.startswith("semantic:") else 1.0
            score += (
                semantic_weight
                * query_frequency
                * inverse_document_frequency
                * frequency
                * (k1 + 1.0)
                / denominator
            )
        scores.append(score)
    return scores


def dice_similarity(left: frozenset[str], right: frozenset[str]) -> float:
    if not left or not right:
        return 0.0
    return 2.0 * len(left & right) / (len(left) + len(right))


def recall(query: str, documents: list[IndexedQuestion], top_k: int) -> list[dict[str, object]]:
    query_tokens = tokenize(query)
    query_grams = character_grams(query)
    raw_bm25 = bm25_scores(query_tokens, documents)
    maximum_bm25 = max(raw_bm25, default=0.0)
    matches: list[dict[str, object]] = []
    for document, bm25 in zip(documents, raw_bm25):
        normalized_bm25 = bm25 / maximum_bm25 if maximum_bm25 > 0 else 0.0
        ngram = dice_similarity(query_grams, document.grams)
        combined = 0.65 * normalized_bm25 + 0.35 * ngram
        matches.append(
            {
                "score": round(combined, 6),
                "bm25": round(normalized_bm25, 6),
                "ngram": round(ngram, 6),
                "dimension": document.dimension,
                "title": document.title,
            }
        )
    return sorted(matches, key=lambda item: (-float(item["score"]), str(item["title"])))[:top_k]


def load_queries(arguments: argparse.Namespace) -> list[str]:
    queries = [query.strip() for query in arguments.question if query.strip()]
    if arguments.input:
        if arguments.input == "-":
            lines = decode_input(sys.stdin.buffer.read()).splitlines()
        else:
            lines = Path(arguments.input).read_text(encoding="utf-8").splitlines()
        queries.extend(line.strip() for line in lines if line.strip())
    if not queries:
        raise ValueError("Provide --question or --input")
    return queries


def decode_input(data: bytes) -> str:
    if data.startswith(codecs.BOM_UTF8):
        return data.decode("utf-8-sig")
    if data.startswith(codecs.BOM_UTF16_LE) or data.startswith(codecs.BOM_UTF16_BE):
        return data.decode("utf-16")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        encoding = locale.getpreferredencoding(False) or "gb18030"
        return data.decode(encoding)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", action="append", help="Question index path; repeatable")
    parser.add_argument("--question", action="append", default=[], help="Question text; repeatable")
    parser.add_argument("--input", help="UTF-8 file with one question per line; use - for stdin")
    parser.add_argument("--top-k", type=int, default=5, help="Matches per question")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    arguments = parser.parse_args()
    if arguments.top_k < 1:
        parser.error("--top-k must be at least 1")

    try:
        index_paths = [Path(value) for value in arguments.index] if arguments.index else default_index_paths()
        documents = parse_indexes(index_paths)
        queries = load_queries(arguments)
    except (OSError, UnicodeError, ValueError) as error:
        parser.error(str(error))

    results = [
        {"question": query, "matches": recall(query, documents, arguments.top_k)}
        for query in queries
    ]
    if arguments.json:
        json.dump(results, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0

    for result in results:
        print(f"\nQUERY\t{result['question']}")
        for rank, match in enumerate(result["matches"], start=1):
            print(
                f"{rank}\t{match['score']:.4f}\t{match['dimension']}\t{match['title']}"
                f"\t(bm25={match['bm25']:.4f}, ngram={match['ngram']:.4f})"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
