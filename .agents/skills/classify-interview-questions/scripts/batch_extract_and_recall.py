#!/usr/bin/env python3
"""Run LLM question extraction and recall for every article in a scrape manifest."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from build_recall_queues import build_queues
from source_gate import preflight_sources


DEFAULT_MODEL = "gpt-5.6-luna"
SUCCESS_STATUSES = {"ok", "pre_gate_rejected", "gate_rejected", "no_questions"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--outer-workers", type=int, default=3)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--rerank-batch-size", type=int, default=1)
    parser.add_argument("--candidate-k", type=int, default=12)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--llm-timeout", type=int, default=180)
    parser.add_argument("--same-threshold", type=float, default=0.85)
    parser.add_argument("--overlap-threshold", type=float, default=0.80)
    parser.add_argument("--different-threshold", type=float, default=0.85)
    parser.add_argument("--source-duplicate-threshold", type=float, default=0.90)
    parser.add_argument("--minimum-duplicate-chars", type=int, default=200)
    parser.add_argument("--account-minimum-articles", type=int, default=3)
    parser.add_argument("--account-rejected-ratio", type=float, default=0.50)
    parser.add_argument("--index", type=Path, action="append", default=[])
    parser.add_argument(
        "--retry-gate-rejected",
        action="store_true",
        help="Re-run articles previously rejected by the firsthand-interview gate",
    )
    return parser.parse_args()


def validate_positive(name: str, value: int) -> None:
    if value < 1:
        raise ValueError(f"{name} must be positive, got {value}")


def load_manifest(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    articles = payload.get("articles")
    if not isinstance(articles, list):
        raise ValueError(f"Manifest has no articles array: {path}")
    required = {"title", "url", "localSourcePath"}
    for index, article in enumerate(articles, 1):
        if not isinstance(article, dict) or not required.issubset(article):
            raise ValueError(f"Invalid manifest article {index}: {article}")
        source_path = Path(str(article["localSourcePath"]))
        if not source_path.is_file():
            raise ValueError(f"Missing localSourcePath for article {index}: {source_path}")
    return articles


def llm_error_count(payload: Any) -> int:
    count = 0

    def walk(value: Any) -> None:
        nonlocal count
        if isinstance(value, dict):
            for key, child in value.items():
                if key.casefold() == "llmerrors" and child:
                    count += len(child) if isinstance(child, list) else 1
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(payload)
    return count


def inspect_result(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    classification = payload.get("sourceClassification") or {}
    stats = payload.get("stats") or {}
    return {
        "questionCount": len(payload.get("questions") or []),
        "classification": classification.get("isInterviewExperience"),
        "classificationConfidence": classification.get("confidence"),
        "classificationMethod": classification.get("method"),
        "llmErrorCount": llm_error_count(payload),
        "llm": payload.get("llm") or {},
        "rerankRequestCount": stats.get("rerankRequestCount"),
    }


def load_prior_summary(path: Path, retry_gate_rejected: bool) -> dict[int, dict[str, Any]]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    reusable = set(SUCCESS_STATUSES)
    if retry_gate_rejected:
        reusable.discard("gate_rejected")
    return {
        int(item["index"]): item
        for item in payload.get("articles", [])
        if item.get("status") in reusable
    }


def write_summary(
    path: Path,
    manifest_path: Path,
    model: str,
    article_count: int,
    results: dict[int, dict[str, Any]],
) -> None:
    ordered = [results[index] for index in sorted(results)]
    counts: dict[str, int] = {}
    for item in ordered:
        status = str(item["status"])
        counts[status] = counts.get(status, 0) + 1
    payload = {
        "schemaVersion": 1,
        "model": model,
        "manifest": str(manifest_path),
        "articleCount": article_count,
        "completedCount": len(ordered),
        "counts": counts,
        "articles": ordered,
    }
    temp_path = path.with_suffix(".tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temp_path, path)


def scan_article(
    repo_root: Path,
    extract_script: Path,
    result_dir: Path,
    arguments: argparse.Namespace,
    index: int,
    article: dict[str, Any],
) -> dict[str, Any]:
    started = time.monotonic()
    result_path = result_dir / f"{index:03d}.json"
    if result_path.is_file():
        try:
            return {
                "index": index,
                "title": article["title"],
                "url": article["url"],
                "sourcePath": article["localSourcePath"],
                "resultPath": str(result_path),
                "status": "ok",
                "elapsedSeconds": 0,
                "resumed": True,
                **inspect_result(result_path),
            }
        except (OSError, ValueError, json.JSONDecodeError):
            result_path.unlink(missing_ok=True)

    command = [
        sys.executable,
        str(extract_script),
        "--input",
        str(article["localSourcePath"]),
        "--llm",
        "--llm-model",
        arguments.model,
        "--workers",
        str(arguments.workers),
        "--rerank-batch-size",
        str(arguments.rerank_batch_size),
        "--candidate-k",
        str(arguments.candidate_k),
        "--top-k",
        str(arguments.top_k),
        "--llm-timeout",
        str(arguments.llm_timeout),
        "--format",
        "json",
        "--out",
        str(result_path),
    ]
    for index_path in arguments.index:
        command.extend(["--index", str(index_path)])

    completed = subprocess.run(command, cwd=repo_root, text=True, capture_output=True, check=False)
    elapsed = round(time.monotonic() - started, 2)
    item = {
        "index": index,
        "title": article["title"],
        "url": article["url"],
        "sourcePath": article["localSourcePath"],
        "resultPath": str(result_path),
        "elapsedSeconds": elapsed,
        "resumed": False,
    }
    if completed.returncode == 0 and result_path.is_file():
        try:
            return {**item, "status": "ok", **inspect_result(result_path)}
        except (OSError, ValueError, json.JSONDecodeError) as error:
            result_path.unlink(missing_ok=True)
            return {**item, "status": "failed", "error": f"Invalid result JSON: {error}"}

    result_path.unlink(missing_ok=True)
    error_text = (completed.stderr or completed.stdout or "").strip()
    if "Source is not classified as a firsthand interview experience" in error_text:
        return {
            **item,
            "status": "gate_rejected",
            "returnCode": completed.returncode,
            "error": error_text.splitlines()[-1] if error_text else "Gate rejected",
        }
    if "No question candidates extracted from source" in error_text:
        return {
            **item,
            "status": "no_questions",
            "returnCode": completed.returncode,
            "error": error_text.splitlines()[-1] if error_text else "No question candidates",
        }
    return {
        **item,
        "status": "failed",
        "returnCode": completed.returncode,
        "error": error_text[-1200:],
    }


def main() -> int:
    arguments = parse_args()
    for name in ("outer-workers", "workers", "rerank-batch-size", "candidate-k", "top-k", "llm-timeout"):
        validate_positive(name, int(getattr(arguments, name.replace("-", "_"))))

    repo_root = Path(__file__).resolve().parents[4]
    manifest_path = arguments.manifest.resolve()
    output_dir = arguments.out.resolve()
    result_dir = output_dir / "results"
    result_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "batch-summary.json"
    articles = load_manifest(manifest_path)
    extract_script = Path(__file__).with_name("extract_and_recall.py")
    results = load_prior_summary(summary_path, arguments.retry_gate_rejected)
    preflight_rejected = preflight_sources(
        articles,
        arguments.source_duplicate_threshold,
        arguments.minimum_duplicate_chars,
        arguments.account_minimum_articles,
        arguments.account_rejected_ratio,
    )
    for index, reason in preflight_rejected.items():
        article = articles[index - 1]
        results[index] = {
            "index": index,
            "title": article["title"],
            "url": article["url"],
            "sourcePath": article["localSourcePath"],
            "resultPath": "",
            "status": "pre_gate_rejected",
            "elapsedSeconds": 0,
            "resumed": False,
            "error": reason,
        }
    pending = [(index, article) for index, article in enumerate(articles, 1) if index not in results]

    write_summary(summary_path, manifest_path, arguments.model, len(articles), results)
    build_queues(
        summary_path,
        output_dir / "queues",
        arguments.same_threshold,
        arguments.overlap_threshold,
        arguments.different_threshold,
    )

    print(
        f"[batch] model={arguments.model} articles={len(articles)} resume={len(results)} "
        f"pending={len(pending)} outer_workers={arguments.outer_workers} inner_workers={arguments.workers}",
        flush=True,
    )
    with ThreadPoolExecutor(max_workers=arguments.outer_workers) as executor:
        futures = {
            executor.submit(
                scan_article,
                repo_root,
                extract_script,
                result_dir,
                arguments,
                index,
                article,
            ): index
            for index, article in pending
        }
        for future in as_completed(futures):
            item = future.result()
            results[int(item["index"])] = item
            write_summary(summary_path, manifest_path, arguments.model, len(articles), results)
            build_queues(
                summary_path,
                output_dir / "queues",
                arguments.same_threshold,
                arguments.overlap_threshold,
                arguments.different_threshold,
            )
            print(
                f"[batch] {item['index']:03d}/{len(articles):03d} {item['status']} "
                f"q={item.get('questionCount', 0)} llmErrors={item.get('llmErrorCount', 0)} "
                f"sec={item['elapsedSeconds']} completed={len(results)}/{len(articles)}",
                flush=True,
            )

    write_summary(summary_path, manifest_path, arguments.model, len(articles), results)
    queue_summary = build_queues(
        summary_path,
        output_dir / "queues",
        arguments.same_threshold,
        arguments.overlap_threshold,
        arguments.different_threshold,
    )
    failed = [item for item in results.values() if item.get("status") == "failed"]
    llm_errors = sum(int(item.get("llmErrorCount", 0)) for item in results.values())
    print(
        f"[batch] complete summary={summary_path} queues={json.dumps(queue_summary['counts'])} "
        f"failed={len(failed)} llmErrors={llm_errors}",
        flush=True,
    )
    return 1 if failed or llm_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
