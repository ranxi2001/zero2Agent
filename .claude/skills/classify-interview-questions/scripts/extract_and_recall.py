#!/usr/bin/env python3
"""Extract interview questions from a Nowcoder page or text, then recall similar indexed questions."""

from __future__ import annotations

import argparse
import concurrent.futures
import html
import json
import math
import os
import re
import sys
import time
import tomllib
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from recall_similar_questions import decode_input, default_index_paths, parse_indexes, recall


INITIAL_STATE_MARKER = "window.__INITIAL_STATE__="
LIST_PREFIX_RE = re.compile(r"^\s*(?:[-*]|\d+[.、)])\s*(.+)$")
QUESTION_START_RE = re.compile(
    r"^(?:如何|怎么|怎样|什么|为什么|为何|是否|能否|讲解|解释|分析|设计|实现|介绍|"
    r"平时|如果|在没有|一次|大模型|Agent|Function\s*Call|Tool\s*Result|ReAct|Context\s*Engineering)",
    re.IGNORECASE,
)
NOISE_RE = re.compile(
    r"^(?:作者|链接|来源|面试时间|工作职责|下面是|问题如下|反问环节|面试感想|"
    r"发面经|标签|评论|推荐|查看更多)[:：]?$",
    re.IGNORECASE,
)
INTERVIEW_EVIDENCE_RE = re.compile(
    r"面经|(?:一|二|三|四|终)面|面试(?:问题|问到|官|时间|过程)|手撕|现场编程|笔试题",
    re.IGNORECASE,
)
NON_INTERVIEW_TITLE_RE = re.compile(
    r"offer.{0,4}(?:选择|帮选|求助)|招聘|内推|捞简历|求助|学习路线|拼课|资料|前景讨论|方向选择|"
    r"面试.{0,4}(?:汇总|整理|题库|教程|解析)|真题.{0,4}(?:汇总|整理|解析)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class CodexAPIConfig:
    base_url: str
    token: str
    model: str
    wire_api: str
    source: str

    def safe_summary(self) -> dict[str, str]:
        return {
            "source": self.source,
            "host": urlparse(self.base_url).netloc,
            "model": self.model,
            "wireApi": self.wire_api,
        }


class BlockTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "li":
            self.parts.append("\n- ")
        elif tag in {"p", "br", "h1", "h2", "h3", "blockquote"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"li", "p", "h1", "h2", "h3", "blockquote"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def text(self) -> str:
        value = html.unescape("".join(self.parts))
        value = re.sub(r"[\t\r ]+", " ", value)
        value = re.sub(r"\n{3,}", "\n\n", value)
        return value.strip()


def html_to_text(value: str) -> str:
    parser = BlockTextExtractor()
    parser.feed(value)
    parser.close()
    return parser.text()


def find_content_data(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        if "title" in value and any(key in value for key in ("richText", "newContent", "content")):
            return value
        for child in value.values():
            found = find_content_data(child)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = find_content_data(child)
            if found:
                return found
    return None


def find_config_value(value: Any, keys: set[str]) -> str:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized_key = re.sub(r"[^a-z0-9]", "", str(key).lower())
            if normalized_key in keys and isinstance(child, (str, int, float)) and str(child).strip():
                return str(child).strip()
        for child in value.values():
            found = find_config_value(child, keys)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = find_config_value(child, keys)
            if found:
                return found
    return ""


def config_from_json(path: Path) -> CodexAPIConfig | None:
    data = json.loads(path.read_text(encoding="utf-8"))
    base_url = find_config_value(data, {"baseurl", "openaibaseurl", "apibase"})
    token = find_config_value(
        data,
        {"token", "apikey", "openaiapikey", "bearertoken", "experimentalbearertoken"},
    )
    model = find_config_value(data, {"model", "modelname"})
    wire_api = find_config_value(data, {"wireapi", "apitype"}) or "responses"
    if not base_url or not token:
        return None
    return CodexAPIConfig(
        base_url=base_url.rstrip("/"),
        token=token,
        model=model,
        wire_api=wire_api.lower(),
        source=str(path),
    )


def config_from_toml(path: Path, codex_home: Path) -> CodexAPIConfig | None:
    with path.open("rb") as stream:
        data = tomllib.load(stream)
    provider_name = str(data.get("model_provider") or "openai")
    providers = data.get("model_providers") or {}
    provider = providers.get(provider_name) or {}
    base_url = str(provider.get("base_url") or data.get("openai_base_url") or "").strip()
    token = str(provider.get("experimental_bearer_token") or "").strip()
    auth_path = codex_home / "auth.json"
    if not token and auth_path.is_file():
        auth = json.loads(auth_path.read_text(encoding="utf-8"))
        token = str(auth.get("OPENAI_API_KEY") or auth.get("token") or "").strip()
    if not base_url or not token:
        return None
    return CodexAPIConfig(
        base_url=base_url.rstrip("/"),
        token=token,
        model=str(data.get("model") or "").strip(),
        wire_api=str(provider.get("wire_api") or "responses").lower(),
        source=str(path),
    )


def load_codex_api_config(explicit_path: str | None = None) -> CodexAPIConfig:
    codex_home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
    candidates: list[Path] = []
    if explicit_path:
        candidates.append(Path(explicit_path).expanduser())
    else:
        candidates.extend(
            [
                codex_home / "config.json",
                codex_home / "codex.json",
                Path.cwd() / ".codex" / "config.json",
                codex_home / "config.toml",
            ]
        )
    errors: list[str] = []
    for path in candidates:
        if not path.is_file():
            continue
        try:
            config = config_from_toml(path, codex_home) if path.suffix.lower() == ".toml" else config_from_json(path)
        except (OSError, UnicodeError, json.JSONDecodeError, tomllib.TOMLDecodeError) as error:
            errors.append(f"{path}: {error}")
            continue
        if config:
            return config
    detail = f" Invalid configs: {'; '.join(errors)}" if errors else ""
    raise ValueError(
        "No Codex API config with base URL and token was found. "
        "Use --codex-config or configure ~/.codex/config.json/config.toml and auth.json."
        + detail
    )


def parse_nowcoder_html(page_html: str) -> tuple[str, str]:
    marker_index = page_html.find(INITIAL_STATE_MARKER)
    if marker_index < 0:
        raise ValueError("Nowcoder page does not contain window.__INITIAL_STATE__")
    json_start = marker_index + len(INITIAL_STATE_MARKER)
    state, _ = json.JSONDecoder().raw_decode(page_html[json_start:])
    content_data = find_content_data(state)
    if not content_data:
        raise ValueError("Nowcoder initial state does not contain article content")
    title = str(content_data.get("title") or "Untitled Nowcoder article").strip()
    body = max(
        (str(content_data.get(key) or "") for key in ("richText", "newContent", "content")),
        key=len,
    )
    if "<" in body and ">" in body:
        body = html_to_text(body)
    return title, body


def fetch_nowcoder(url: str) -> tuple[str, str]:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; zero2Agent-question-audit/1.0)",
            "Accept-Language": "zh-CN,zh;q=0.9",
        },
    )
    with urlopen(request, timeout=30) as response:
        page_html = response.read().decode("utf-8")
    return parse_nowcoder_html(page_html)


def extract_model_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices") or []
    if choices:
        content = choices[0].get("message", {}).get("content", "")
        if isinstance(content, str):
            return content
    if isinstance(payload.get("output_text"), str):
        return str(payload["output_text"])
    parts: list[str] = []
    for item in payload.get("output") or []:
        for content in item.get("content") or []:
            text_value = content.get("text") or content.get("output_text")
            if isinstance(text_value, str):
                parts.append(text_value)
    return "\n".join(parts)


def parse_model_json(value: str) -> dict[str, Any]:
    value = value.strip()
    value = re.sub(r"^```(?:json)?\s*", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\s*```$", "", value)
    start = value.find("{")
    if start < 0:
        raise ValueError("Model response does not contain a JSON object")
    result, _ = json.JSONDecoder().raw_decode(value[start:])
    if not isinstance(result, dict):
        raise ValueError("Model response JSON must be an object")
    return result


def call_model(
    config: CodexAPIConfig,
    system_prompt: str,
    user_prompt: str,
    timeout: float,
    retries: int = 3,
) -> dict[str, Any]:
    wire_api = config.wire_api.replace("_", "-")
    if wire_api in {"chat", "chat-completions", "chatcompletions"}:
        endpoint = f"{config.base_url}/chat/completions"
        body = {
            "model": config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
    else:
        endpoint = f"{config.base_url}/responses"
        body = {
            "model": config.model,
            "instructions": system_prompt,
            "input": user_prompt,
        }
    if not config.model:
        raise ValueError("Codex API config does not define a model; pass --llm-model")
    request = Request(
        endpoint,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {config.token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            with urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            return parse_model_json(extract_model_text(payload))
        except (HTTPError, URLError, TimeoutError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            last_error = error
            if attempt + 1 < retries:
                time.sleep(2**attempt)
    raise RuntimeError(f"Model API failed after {retries} attempts: {last_error}")


def chunk_text(text: str, maximum_chars: int = 12000) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n{2,}", text) if part.strip()]
    chunks: list[str] = []
    current: list[str] = []
    current_size = 0
    for paragraph in paragraphs:
        if current and current_size + len(paragraph) + 2 > maximum_chars:
            chunks.append("\n\n".join(current))
            current = []
            current_size = 0
        if len(paragraph) > maximum_chars:
            if current:
                chunks.append("\n\n".join(current))
                current = []
                current_size = 0
            chunks.extend(paragraph[i : i + maximum_chars] for i in range(0, len(paragraph), maximum_chars))
            continue
        current.append(paragraph)
        current_size += len(paragraph) + 2
    if current:
        chunks.append("\n\n".join(current))
    return chunks or [text]


def llm_extract_questions(
    text: str,
    config: CodexAPIConfig,
    workers: int,
    timeout: float,
) -> tuple[list[str], list[str]]:
    system_prompt = (
        "你是面经问题抽取器。只提取原帖中面试官明确问到的问题；保留技术题、项目追问和手撕题。"
        "排除作者信息、评论、推荐、答案、岗位职责和面试感想。返回严格 JSON："
        '{"questions":["问题1","问题2"]}。不要补造缺失题干。'
    )

    def extract_chunk(chunk: str) -> tuple[list[str], str]:
        try:
            payload = call_model(config, system_prompt, chunk, timeout)
            values = payload.get("questions") or []
            return [clean_candidate(str(item)) for item in values if clean_candidate(str(item))], ""
        except RuntimeError as error:
            return [], str(error)

    extracted: list[str] = []
    errors: list[str] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        for values, error in executor.map(extract_chunk, chunk_text(text)):
            extracted.extend(values)
            if error:
                errors.append(error)
    return deduplicate_questions(extracted), errors


def classify_interview_experience(title: str, text: str) -> dict[str, Any]:
    evidence = list(dict.fromkeys(INTERVIEW_EVIDENCE_RE.findall(f"{title}\n{text[:12000]}")))
    question_count = len(extract_questions(text))
    negative_title = bool(NON_INTERVIEW_TITLE_RE.search(title))
    strong_title = bool(re.search(r"面经|(?:一|二|三|四|终)面|面试", title, re.IGNORECASE))
    is_interview = question_count > 0 and (strong_title or len(evidence) >= 2) and not negative_title
    confidence = min(0.98, 0.45 + 0.12 * len(evidence) + 0.02 * min(question_count, 10))
    if not is_interview:
        confidence = max(0.1, 1.0 - confidence)
    return {
        "isInterviewExperience": is_interview,
        "confidence": round(confidence, 4),
        "method": "deterministic",
        "evidence": evidence[:8],
        "deterministicQuestionCount": question_count,
    }


def llm_classify_interview_experience(
    title: str,
    text: str,
    config: CodexAPIConfig,
    timeout: float,
) -> dict[str, Any]:
    system_prompt = (
        "判断输入是否为真实面试经历原帖。只有作者描述自己实际参加的面试，并给出公司/轮次/过程或明确面试问题时才为 true。"
        "招聘、内推、Offer选择、求助、学习路线、教程、题库整理、付费推广、评论转载均为 false。"
        "返回严格 JSON："
        '{"isInterviewExperience":true,"confidence":0.0,"evidence":["短证据"]}。'
    )
    payload = call_model(
        config,
        system_prompt,
        f"标题：{title}\n\n正文：\n{text[:12000]}",
        timeout,
    )
    return {
        "isInterviewExperience": bool(payload.get("isInterviewExperience")),
        "confidence": max(0.0, min(1.0, float(payload.get("confidence", 0.0)))),
        "method": "llm",
        "evidence": [str(item) for item in (payload.get("evidence") or [])][:8],
    }


def llm_rerank(
    question: str,
    candidates: list[dict[str, object]],
    config: CodexAPIConfig,
    timeout: float,
) -> tuple[list[dict[str, object]], str]:
    candidate_lines = [
        f"{index}. [{candidate['dimension']}] {candidate['title']}"
        for index, candidate in enumerate(candidates, start=1)
    ]
    system_prompt = (
        "你是面试题语义去重评审器。判断候选题与输入题的核心考点和工程约束是否相同。"
        "same=同一道题，overlap=部分覆盖但约束不同，different=不同题。"
        "返回严格 JSON："
        '{"judgments":[{"id":1,"relation":"same|overlap|different",'
        '"confidence":0.0,"reason":"一句话"}]}。只使用给定候选 id。'
    )
    user_prompt = f"输入题：{question}\n\n候选题：\n" + "\n".join(candidate_lines)
    try:
        payload = call_model(config, system_prompt, user_prompt, timeout)
    except RuntimeError as error:
        return candidates, str(error)

    judgments: dict[int, dict[str, Any]] = {}
    for judgment in payload.get("judgments") or []:
        try:
            candidate_id = int(judgment.get("id"))
            confidence = max(0.0, min(1.0, float(judgment.get("confidence", 0.0))))
        except (TypeError, ValueError):
            continue
        relation = str(judgment.get("relation") or "different").lower()
        if relation not in {"same", "overlap", "different"}:
            continue
        judgments[candidate_id] = {
            "relation": relation,
            "confidence": confidence,
            "reason": str(judgment.get("reason") or "").strip(),
        }

    return apply_judgments(candidates, judgments), ""


def apply_judgments(
    candidates: list[dict[str, object]],
    judgments: dict[int, dict[str, Any]],
) -> list[dict[str, object]]:
    relation_weight = {"same": 1.0, "overlap": 0.65, "different": 0.05}
    reranked: list[dict[str, object]] = []
    for candidate_id, candidate in enumerate(candidates, start=1):
        result = dict(candidate)
        result["recallScore"] = result["score"]
        judgment = judgments.get(candidate_id)
        if judgment:
            semantic_score = relation_weight[judgment["relation"]] * judgment["confidence"]
            result["llmRelation"] = judgment["relation"]
            result["llmConfidence"] = round(judgment["confidence"], 6)
            result["llmReason"] = judgment["reason"]
            result["score"] = round(0.4 * float(result["recallScore"]) + 0.6 * semantic_score, 6)
        reranked.append(result)
    reranked.sort(key=lambda item: (-float(item["score"]), str(item["title"])))
    return reranked


def llm_rerank_batch(
    items: list[tuple[str, list[dict[str, object]]]],
    config: CodexAPIConfig,
    timeout: float,
) -> list[tuple[list[dict[str, object]], str]]:
    blocks: list[str] = []
    for question_id, (question, candidates) in enumerate(items, start=1):
        blocks.append(f"问题 {question_id}：{question}")
        blocks.extend(
            f"  候选 {question_id}.{candidate_id}：[{candidate['dimension']}] {candidate['title']}"
            for candidate_id, candidate in enumerate(candidates, start=1)
        )
    system_prompt = (
        "你是面试题语义去重评审器。分别判断每个问题下所有候选的核心考点和工程约束是否相同。"
        "same=同一道题，overlap=部分覆盖但约束不同，different=不同题。"
        "返回严格 JSON："
        '{"results":[{"questionId":1,"judgments":[{"candidateId":1,'
        '"relation":"same|overlap|different","confidence":0.0,"reason":"一句话"}]}]}。'
        "每个问题的每个候选都必须返回，不能跨问题比较。"
    )
    try:
        payload = call_model(config, system_prompt, "\n".join(blocks), timeout)
    except RuntimeError as error:
        return [(candidates, str(error)) for _, candidates in items]

    results_by_question: dict[int, dict[int, dict[str, Any]]] = {}
    for question_result in payload.get("results") or []:
        try:
            question_id = int(question_result.get("questionId"))
        except (TypeError, ValueError):
            continue
        judgments: dict[int, dict[str, Any]] = {}
        for judgment in question_result.get("judgments") or []:
            try:
                candidate_id = int(judgment.get("candidateId"))
                confidence = max(0.0, min(1.0, float(judgment.get("confidence", 0.0))))
            except (TypeError, ValueError):
                continue
            relation = str(judgment.get("relation") or "different").lower()
            if relation not in {"same", "overlap", "different"}:
                continue
            judgments[candidate_id] = {
                "relation": relation,
                "confidence": confidence,
                "reason": str(judgment.get("reason") or "").strip(),
            }
        results_by_question[question_id] = judgments

    output: list[tuple[list[dict[str, object]], str]] = []
    for question_id, (_, candidates) in enumerate(items, start=1):
        judgments = results_by_question.get(question_id)
        if not judgments:
            output.append((candidates, f"LLM batch omitted question {question_id}"))
            continue
        output.append((apply_judgments(candidates, judgments), ""))
    return output


def clean_candidate(value: str) -> str:
    value = re.sub(r"[`*_#>]", "", value)
    value = re.sub(r"\s+", " ", value).strip(" -\t")
    value = re.sub(r"^\d+[.、)]\s*", "", value)
    return value.strip()


def looks_like_question(value: str, from_list: bool) -> bool:
    if not value or len(value) < 4 or len(value) > 300:
        return False
    if NOISE_RE.match(value):
        return False
    if value.endswith(("?", "？")):
        return True
    if from_list and QUESTION_START_RE.match(value):
        return True
    return False


def deduplicate_questions(values: list[str]) -> list[str]:
    questions: list[str] = []
    seen: set[str] = set()
    for value in values:
        candidate = clean_candidate(value)
        normalized = re.sub(r"\W+", "", candidate).lower()
        if not candidate or not normalized or normalized in seen:
            continue
        seen.add(normalized)
        questions.append(candidate)
    return questions


def extract_questions(text: str) -> list[str]:
    questions: list[str] = []
    for raw_line in text.splitlines():
        line = clean_candidate(raw_line)
        if not line:
            continue
        list_match = LIST_PREFIX_RE.match(raw_line)
        candidate = clean_candidate(list_match.group(1) if list_match else line)
        if not looks_like_question(candidate, from_list=bool(list_match)):
            continue
        questions.append(candidate)
    return deduplicate_questions(questions)


def load_source(arguments: argparse.Namespace) -> tuple[str, str, str]:
    if arguments.url:
        title, text = fetch_nowcoder(arguments.url)
        return title, text, arguments.url.split("?")[0]
    if arguments.input == "-":
        text = decode_input(sys.stdin.buffer.read())
        return "stdin", text, "stdin"
    path = Path(arguments.input)
    return path.name, path.read_text(encoding="utf-8"), str(path.resolve())


def recall_band(score: float) -> str:
    if score >= 0.78:
        return "high"
    if score >= 0.52:
        return "review"
    return "low"


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        f"# Question Recall Audit: {result['title']}",
        "",
        f"- Source: {result['source']}",
        f"- Extracted questions: {result['stats']['questionCount']}",
        f"- Indexed questions: {result['stats']['indexedQuestionCount']}",
        "",
    ]
    for item in result["questions"]:
        lines.extend([f"## Q{item['id']}: {item['question']}", ""])
        has_llm = any("llmRelation" in match for match in item["matches"])
        if has_llm:
            lines.append(
                "| Rank | Final | Recall | Relation | Confidence | Dimension | Indexed question | Reason |"
            )
            lines.append("|---:|---:|---:|---|---:|---|---|---|")
        else:
            lines.append("| Rank | Score | Band | Dimension | Indexed question | BM25 | N-gram |")
            lines.append("|---:|---:|---|---|---|---:|---:|")
        for rank, match in enumerate(item["matches"], start=1):
            title = str(match["title"]).replace("|", "\\|")
            if has_llm:
                reason = str(match.get("llmReason") or "").replace("|", "\\|")
                lines.append(
                    f"| {rank} | {match['score']:.4f} | {float(match.get('recallScore', match['score'])):.4f} | "
                    f"{match.get('llmRelation', '')} | {float(match.get('llmConfidence', 0)):.2f} | "
                    f"{match['dimension']} | {title} | {reason} |"
                )
            else:
                lines.append(
                    f"| {rank} | {match['score']:.4f} | {item['band'] if rank == 1 else ''} | "
                    f"{match['dimension']} | {title} | {match['bm25']:.4f} | {match['ngram']:.4f} |"
                )
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--url", help="Nowcoder discuss URL")
    source.add_argument("--input", help="UTF-8 text/Markdown file; use - for stdin")
    parser.add_argument("--index", action="append", help="Question index path; repeatable")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--candidate-k", type=int, default=12, help="Local candidates sent to LLM rerank")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--out", help="Write UTF-8 output to this path")
    parser.add_argument("--llm", action="store_true", help="Enable LLM extraction and reranking")
    parser.add_argument("--llm-extract", action="store_true", help="Use LLM to extract questions")
    parser.add_argument("--llm-rerank", action="store_true", help="Use LLM to semantically rerank candidates")
    parser.add_argument("--codex-config", help="Explicit Codex JSON/TOML config path")
    parser.add_argument("--llm-model", help="Override model from Codex config")
    parser.add_argument("--workers", type=int, default=8, help="Parallel LLM calls")
    parser.add_argument("--rerank-batch-size", type=int, default=1, help="Questions per LLM rerank call")
    parser.add_argument("--llm-timeout", type=float, default=90.0, help="Seconds per API call")
    parser.add_argument(
        "--allow-non-interview",
        action="store_true",
        help="Bypass the interview-experience gate for controlled diagnostics",
    )
    arguments = parser.parse_args()
    if arguments.top_k < 1:
        parser.error("--top-k must be at least 1")
    if arguments.candidate_k < arguments.top_k:
        parser.error("--candidate-k must be greater than or equal to --top-k")
    if arguments.workers < 1:
        parser.error("--workers must be at least 1")
    if arguments.rerank_batch_size < 1:
        parser.error("--rerank-batch-size must be at least 1")

    try:
        title, text, source_value = load_source(arguments)
        index_paths = [Path(value) for value in arguments.index] if arguments.index else default_index_paths()
        documents = parse_indexes(index_paths)
        llm_enabled = arguments.llm or arguments.llm_extract or arguments.llm_rerank
        api_config = load_codex_api_config(arguments.codex_config) if llm_enabled else None
        if api_config and arguments.llm_model:
            api_config = CodexAPIConfig(
                base_url=api_config.base_url,
                token=api_config.token,
                model=arguments.llm_model,
                wire_api=api_config.wire_api,
                source=api_config.source,
            )
    except (OSError, UnicodeError, ValueError) as error:
        parser.error(str(error))
    source_classification = classify_interview_experience(title, text)
    classification_error = ""
    if api_config and llm_enabled:
        try:
            source_classification = llm_classify_interview_experience(
                title, text, api_config, arguments.llm_timeout
            )
        except (RuntimeError, TypeError, ValueError) as error:
            classification_error = str(error)
    if not source_classification["isInterviewExperience"] and not arguments.allow_non_interview:
        parser.error(
            "Source is not classified as a firsthand interview experience; "
            "question extraction was skipped"
        )
    deterministic_questions = extract_questions(text)
    questions = deterministic_questions
    llm_errors: list[str] = []
    if api_config and (arguments.llm or arguments.llm_extract):
        llm_questions, extraction_errors = llm_extract_questions(
            text, api_config, arguments.workers, arguments.llm_timeout
        )
        if llm_questions:
            questions = llm_questions
        llm_errors.extend(extraction_errors)
    if not questions:
        parser.error("No question candidates extracted from source")

    result: dict[str, Any] = {
        "title": title,
        "source": source_value,
        "sourceClassification": source_classification,
        "stats": {
            "questionCount": len(questions),
            "deterministicQuestionCount": len(deterministic_questions),
            "indexedQuestionCount": len(documents),
            "topK": arguments.top_k,
            "candidateK": arguments.candidate_k,
            "rerankBatchSize": arguments.rerank_batch_size,
            "rerankRequestCount": math.ceil(len(questions) / arguments.rerank_batch_size),
        },
        "questions": [],
    }
    if api_config:
        result["llm"] = api_config.safe_summary()
    if classification_error:
        result["classificationError"] = classification_error

    local_matches = [recall(question, documents, arguments.candidate_k) for question in questions]
    reranked_matches = local_matches
    rerank_errors = [""] * len(questions)
    if api_config and (arguments.llm or arguments.llm_rerank):
        batches = [
            list(zip(questions[start : start + arguments.rerank_batch_size], local_matches[start : start + arguments.rerank_batch_size]))
            for start in range(0, len(questions), arguments.rerank_batch_size)
        ]
        with concurrent.futures.ThreadPoolExecutor(max_workers=arguments.workers) as executor:
            futures = [
                executor.submit(
                    llm_rerank_batch,
                    batch,
                    api_config,
                    arguments.llm_timeout,
                )
                for batch in batches
            ]
            completed_batches = [future.result() for future in futures]
        completed = [item for batch in completed_batches for item in batch]
        reranked_matches = [matches for matches, _ in completed]
        rerank_errors = [error for _, error in completed]
        llm_errors.extend(error for error in rerank_errors if error)

    for number, (question, matches, rerank_error) in enumerate(
        zip(questions, reranked_matches, rerank_errors), start=1
    ):
        matches = matches[: arguments.top_k]
        result["questions"].append(
            {
                "id": number,
                "question": question,
                "band": recall_band(float(matches[0]["score"])),
                "matches": matches,
                **({"llmError": rerank_error} if rerank_error else {}),
            }
        )
    if llm_errors:
        result["llmErrors"] = llm_errors

    output = (
        json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if arguments.format == "json"
        else render_markdown(result) + "\n"
    )
    if arguments.out:
        Path(arguments.out).write_text(output, encoding="utf-8", newline="\n")
    else:
        sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
