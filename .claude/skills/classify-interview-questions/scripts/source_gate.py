#!/usr/bin/env python3
"""Preflight scraped sources before any LLM question extraction calls."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any


EMPTY_BODY_RE = re.compile(r"^\s*(?:\(内容为空\)|内容为空|内容不存在[!！]?)\s*$", re.IGNORECASE)
TEMPLATE_RE = re.compile(
    r"以下根据.{0,20}(?:项目情况|实际情况).{0,20}补充|参考常见追问|标准答案|"
    r"剩余\s*\d+%|购买.{0,8}专栏|付费专栏|解锁剩余|我的回答[:：]",
    re.IGNORECASE,
)
TRUNCATE_MARKERS = (
    "畅所欲言吧",
    "相关推荐",
    "全站热榜",
    "创作者周榜",
    "正在热议",
)


def article_body(text: str) -> str:
    parts = re.split(r"^---\s*$", text, maxsplit=1, flags=re.MULTILINE)
    body = parts[-1]
    lines: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if stripped in {"评论", "全部评论", "推荐", "最新", "楼层"}:
            break
        if any(stripped.startswith(marker) for marker in TRUNCATE_MARKERS):
            break
        lines.append(line)
    return "\n".join(lines).strip()


def normalized_body(text: str) -> str:
    value = unicodedata.normalize("NFKC", article_body(text)).casefold()
    value = re.sub(r"https?://\S+", "", value)
    value = re.sub(r"^#.*$|^\*\*[^*]+\*\*.*$|^>.*$", "", value, flags=re.MULTILINE)
    return re.sub(r"[^a-z0-9\u3400-\u4dbf\u4e00-\u9fff]+", "", value)


def shingles(value: str, size: int = 8) -> set[str]:
    if len(value) < size:
        return {value} if value else set()
    return {value[index : index + size] for index in range(len(value) - size + 1)}


def preflight_sources(
    articles: list[dict[str, Any]],
    duplicate_threshold: float = 0.90,
    minimum_duplicate_chars: int = 200,
    account_minimum_articles: int = 3,
    account_rejected_ratio: float = 0.50,
) -> dict[int, str]:
    if not 0 <= duplicate_threshold <= 1:
        raise ValueError(f"duplicate-threshold must be between 0 and 1, got {duplicate_threshold}")
    rejected: dict[int, str] = {}
    normalized: dict[int, str] = {}
    shingle_sets: dict[int, set[str]] = {}

    for index, article in enumerate(articles, 1):
        path = Path(str(article["localSourcePath"]))
        text = path.read_text(encoding="utf-8", errors="ignore")
        body = article_body(text)
        compact = normalized_body(text)
        if EMPTY_BODY_RE.match(body) or body.startswith("内容不存在!") or body.startswith("内容不存在！"):
            rejected[index] = "empty or deleted source body"
            continue
        template_match = TEMPLATE_RE.search(body)
        if template_match:
            rejected[index] = f"template or paid-content marker: {template_match.group(0)}"
            continue
        normalized[index] = compact
        if len(compact) >= minimum_duplicate_chars:
            shingle_sets[index] = shingles(compact)

    indexes = sorted(shingle_sets)
    for position, left_index in enumerate(indexes):
        left = shingle_sets[left_index]
        for right_index in indexes[position + 1 :]:
            right = shingle_sets[right_index]
            similarity = len(left & right) / min(len(left), len(right))
            if similarity < duplicate_threshold:
                continue
            rejected[left_index] = f"near-duplicate source body with article {right_index}: {similarity:.2f}"
            rejected[right_index] = f"near-duplicate source body with article {left_index}: {similarity:.2f}"

    authors: dict[str, list[int]] = {}
    for index, article in enumerate(articles, 1):
        author = str(article.get("author") or "").strip()
        if author:
            authors.setdefault(author, []).append(index)
    for author, article_indexes in authors.items():
        rejected_count = sum(index in rejected for index in article_indexes)
        if len(article_indexes) < account_minimum_articles or rejected_count < 2:
            continue
        ratio = rejected_count / len(article_indexes)
        if ratio < account_rejected_ratio:
            continue
        for index in article_indexes:
            rejected.setdefault(
                index,
                f"source account {author} has {rejected_count}/{len(article_indexes)} preflight-rejected posts",
            )
    return rejected


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--duplicate-threshold", type=float, default=0.90)
    parser.add_argument("--minimum-duplicate-chars", type=int, default=200)
    parser.add_argument("--account-minimum-articles", type=int, default=3)
    parser.add_argument("--account-rejected-ratio", type=float, default=0.50)
    return parser.parse_args()


def main() -> int:
    arguments = parse_args()
    payload = json.loads(arguments.manifest.read_text(encoding="utf-8"))
    articles = payload.get("articles") or []
    rejected = preflight_sources(
        articles,
        arguments.duplicate_threshold,
        arguments.minimum_duplicate_chars,
        arguments.account_minimum_articles,
        arguments.account_rejected_ratio,
    )
    print(
        json.dumps(
            {
                "articleCount": len(articles),
                "acceptedCount": len(articles) - len(rejected),
                "rejectedCount": len(rejected),
                "rejected": [{"index": index, "reason": rejected[index]} for index in sorted(rejected)],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
