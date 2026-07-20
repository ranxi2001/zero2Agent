"""Deterministic labs for understanding model API and tool-call protocols.

The lab uses a fake provider so protocol behavior is reproducible and does not
need an API key. The message model is intentionally provider-neutral; vendor
SDKs map these concepts to different wire formats.
"""

from __future__ import annotations

import copy
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence


class LabError(Exception):
    """Base error for the lab."""


class ProtocolError(LabError):
    """The message history violates a tool-call protocol invariant."""


class RateLimitError(LabError):
    """A retryable provider-side rate limit used by fault-injection tests."""


class ProviderTimeoutError(LabError):
    """A retryable timeout used by fault-injection tests."""


class ServiceUnavailableError(LabError):
    """A retryable 5xx-style failure used by fault-injection tests."""


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: str


@dataclass
class Message:
    role: str
    content: Any = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_call_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"role": self.role}
        if self.content is not None:
            data["content"] = self.content
        if self.tool_calls:
            data["tool_calls"] = [asdict(call) for call in self.tool_calls]
        if self.tool_call_id is not None:
            data["tool_call_id"] = self.tool_call_id
        return data


@dataclass(frozen=True)
class Usage:
    input_units: int
    output_units: int


@dataclass
class ModelTurn:
    message: Message
    stop_reason: str
    request_id: str
    usage: Usage


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    required: tuple[str, ...]
    handler: Callable[[dict[str, Any]], Mapping[str, Any]]

    def definition(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {key: {"type": "string"} for key in self.required},
                "required": list(self.required),
            },
        }

    def execute(self, raw_arguments: str) -> dict[str, Any]:
        try:
            arguments = json.loads(raw_arguments)
        except json.JSONDecodeError as exc:
            return {"ok": False, "error": "invalid_json", "detail": str(exc)}

        if not isinstance(arguments, dict):
            return {"ok": False, "error": "arguments_must_be_object"}

        missing = [key for key in self.required if key not in arguments]
        if missing:
            return {"ok": False, "error": "missing_required", "fields": missing}

        wrong_types = {key: type(arguments[key]).__name__ for key in self.required if not isinstance(arguments[key], str)}
        if wrong_types:
            return {"ok": False, "error": "invalid_type", "fields": wrong_types}

        empty = [key for key in self.required if not arguments[key].strip()]
        if empty:
            return {"ok": False, "error": "empty_required", "fields": empty}

        try:
            return {"ok": True, "data": dict(self.handler(arguments))}
        except Exception as exc:  # The lab deliberately turns tool failures into data.
            return {"ok": False, "error": "tool_failed", "detail": str(exc)}


def default_tools() -> dict[str, ToolSpec]:
    def weather(arguments: dict[str, Any]) -> Mapping[str, Any]:
        return {"city": arguments["city"], "temperature_c": 18, "condition": "clear"}

    def current_time(arguments: dict[str, Any]) -> Mapping[str, Any]:
        return {"timezone": arguments["timezone"], "time": "09:30"}

    def unstable(_: dict[str, Any]) -> Mapping[str, Any]:
        raise RuntimeError("simulated upstream outage")

    return {
        "get_weather": ToolSpec("get_weather", "Get current weather for a city", ("city",), weather),
        "get_time": ToolSpec("get_time", "Get current time for a timezone", ("timezone",), current_time),
        "unstable_lookup": ToolSpec("unstable_lookup", "A tool that fails for fault injection", ("query",), unstable),
    }


def estimate_units(messages: Sequence[Message]) -> int:
    serialized = json.dumps([message.to_dict() for message in messages], ensure_ascii=False)
    return max(1, len(serialized) // 4)


class FakeProvider:
    """A scripted provider that still obeys a realistic request/response cycle."""

    SCENARIOS = (
        "text",
        "single",
        "parallel",
        "parallel_partial_failure",
        "invalid_args",
        "tool_failure",
        "repeat",
        "refusal",
        "truncated",
        "duplicate_ids",
        "truncated_tool_call",
    )

    def __init__(
        self,
        scenario: str = "parallel",
        transient_failures: int = 0,
        faults: Sequence[str] | None = None,
    ):
        if scenario not in self.SCENARIOS:
            raise ValueError(f"unknown scenario: {scenario}")
        self.scenario = scenario
        self.faults = ["429"] * transient_failures + list(faults or ())
        self.calls = 0

    def complete(self, messages: Sequence[Message], _: Sequence[dict[str, Any]]) -> ModelTurn:
        self.calls += 1
        request_id = f"fake_req_{self.calls:03d}"
        if self.calls <= len(self.faults):
            fault = self.faults[self.calls - 1]
            if fault == "429":
                raise RateLimitError(f"{request_id}: simulated 429")
            if fault == "timeout":
                raise ProviderTimeoutError(f"{request_id}: simulated timeout")
            if fault == "5xx":
                raise ServiceUnavailableError(f"{request_id}: simulated 503")
            raise ValueError(f"unknown fault: {fault}")

        tool_results = [message for message in messages if message.role == "tool"]
        successful_results = [message for message in tool_results if _tool_result_ok(message)]

        forced_stop_reason: str | None = None
        if self.scenario == "text":
            message = Message("assistant", "A plain text response with no tool call.")
        elif self.scenario == "single":
            message = (
                Message(
                    "assistant",
                    tool_calls=[ToolCall(f"call_weather_{self.calls}", "get_weather", '{"city":"Shanghai"}')],
                )
                if not tool_results
                else Message("assistant", "Shanghai is 18 C and clear in this deterministic lab.")
            )
        elif self.scenario == "parallel":
            message = (
                Message(
                    "assistant",
                    tool_calls=[
                        ToolCall(f"call_weather_{self.calls}", "get_weather", '{"city":"Shanghai"}'),
                        ToolCall(f"call_time_{self.calls}", "get_time", '{"timezone":"Asia/Shanghai"}'),
                    ],
                )
                if not tool_results
                else Message("assistant", "Shanghai is clear at 09:30.")
            )
        elif self.scenario == "parallel_partial_failure":
            message = (
                Message(
                    "assistant",
                    tool_calls=[
                        ToolCall(f"call_weather_ok_{self.calls}", "get_weather", '{"city":"Shanghai"}'),
                        ToolCall(f"call_lookup_failed_{self.calls}", "unstable_lookup", '{"query":"air quality"}'),
                    ],
                )
                if not tool_results
                else Message("assistant", "Weather succeeded; air quality was unavailable.")
            )
        elif self.scenario == "invalid_args":
            if not tool_results:
                message = Message("assistant", tool_calls=[ToolCall("call_weather_bad", "get_weather", "{}")])
            elif not successful_results:
                message = Message(
                    "assistant", tool_calls=[ToolCall("call_weather_fixed", "get_weather", '{"city":"Shanghai"}')]
                )
            else:
                message = Message("assistant", "The corrected tool call succeeded.")
        elif self.scenario == "tool_failure":
            message = (
                Message(
                    "assistant",
                    tool_calls=[ToolCall("call_unstable_1", "unstable_lookup", '{"query":"status"}')],
                )
                if not tool_results
                else Message("assistant", "The upstream tool failed; no result was fabricated.")
            )
        elif self.scenario == "repeat":
            message = Message(
                "assistant", tool_calls=[ToolCall(f"call_repeat_{self.calls}", "get_weather", '{"city":"Shanghai"}')]
            )
        elif self.scenario == "refusal":
            message = Message("assistant", "The request was refused by the deterministic provider.")
            forced_stop_reason = "refusal"
        elif self.scenario == "truncated":
            message = Message("assistant", "Partial output")
            forced_stop_reason = "max_output"
        elif self.scenario == "duplicate_ids":
            message = Message(
                "assistant",
                tool_calls=[
                    ToolCall("call_duplicate", "get_weather", '{"city":"Shanghai"}'),
                    ToolCall("call_duplicate", "get_time", '{"timezone":"Asia/Shanghai"}'),
                ],
            )
        else:  # truncated_tool_call
            message = Message(
                "assistant", tool_calls=[ToolCall("call_partial", "get_weather", '{"city":"Shang')]
            )
            forced_stop_reason = "max_output"

        stop_reason = forced_stop_reason or ("tool_calls" if message.tool_calls else "completed")
        output_units = max(1, len(json.dumps(message.to_dict(), ensure_ascii=False)) // 4)
        return ModelTurn(message, stop_reason, request_id, Usage(estimate_units(messages), output_units))


def _tool_result_ok(message: Message) -> bool:
    try:
        value = json.loads(message.content)
    except (TypeError, json.JSONDecodeError):
        return False
    return bool(value.get("ok")) if isinstance(value, dict) else False


def validate_history(messages: Sequence[Message]) -> list[str]:
    """Validate invariants shared by common tool-calling APIs.

    Exact role names differ by provider, but a tool result still needs to map to
    a prior model-issued call. This validator intentionally focuses on that
    causal relationship instead of one vendor's complete schema.
    """

    errors: list[str] = []
    issued: set[str] = set()
    resolved: set[str] = set()
    saw_user_goal = False

    for index, message in enumerate(messages):
        if message.role == "user":
            saw_user_goal = True
        if message.role == "assistant":
            for call in message.tool_calls:
                if call.id in issued:
                    errors.append(f"message {index}: duplicate tool call id {call.id}")
                issued.add(call.id)
        if message.role == "tool":
            if not saw_user_goal:
                errors.append(f"message {index}: tool result has no visible user goal")
            if not message.tool_call_id:
                errors.append(f"message {index}: tool result is missing tool_call_id")
            elif message.tool_call_id not in issued:
                errors.append(f"message {index}: unknown tool_call_id {message.tool_call_id}")
            elif message.tool_call_id in resolved:
                errors.append(f"message {index}: duplicate result for {message.tool_call_id}")
            else:
                resolved.add(message.tool_call_id)

    unresolved = issued - resolved
    if unresolved:
        errors.append(f"unresolved tool calls: {', '.join(sorted(unresolved))}")
    return errors


def validate_model_turn(turn: ModelTurn, history: Sequence[Message]) -> list[str]:
    """Reject malformed model output before any tool can produce a side effect."""

    errors: list[str] = []
    calls = turn.message.tool_calls
    if turn.message.role != "assistant":
        errors.append(f"model response role must be assistant, got {turn.message.role}")
    if calls and turn.stop_reason != "tool_calls":
        errors.append(f"tool calls arrived with incompatible stop_reason {turn.stop_reason}")
    if not calls and turn.stop_reason == "tool_calls":
        errors.append("stop_reason says tool_calls but the response contains none")

    previous_ids = {
        call.id
        for message in history
        if message.role == "assistant"
        for call in message.tool_calls
    }
    response_ids: set[str] = set()
    for index, call in enumerate(calls):
        if not call.id.strip():
            errors.append(f"tool call {index} has an empty id")
        elif call.id in response_ids:
            errors.append(f"duplicate tool call id in model response: {call.id}")
        elif call.id in previous_ids:
            errors.append(f"tool call id was already used in history: {call.id}")
        response_ids.add(call.id)
        if not call.name.strip():
            errors.append(f"tool call {index} has an empty name")
        if not isinstance(call.arguments, str):
            errors.append(f"tool call {index} arguments must be a JSON string")
    return errors


def transform_history(messages: Sequence[Message], mode: str) -> list[Message]:
    """Apply one controlled context ablation before a provider request."""

    result = copy.deepcopy(list(messages))
    if mode == "complete" or not any(message.role == "tool" for message in result):
        return result
    if mode == "drop_assistant_call":
        return [message for message in result if not (message.role == "assistant" and message.tool_calls)]
    if mode == "mismatch_call_id":
        for message in result:
            if message.role == "tool":
                message.tool_call_id = "call_does_not_exist"
                break
        return result
    if mode == "flatten_roles":
        transcript = "\n".join(json.dumps(message.to_dict(), ensure_ascii=False) for message in result)
        return [Message("user", f"Flattened transcript:\n{transcript}")]
    if mode == "sliding_window":
        prefix = result[:1] if result and result[0].role in {"system", "developer"} else []
        return prefix + result[-1:]
    raise ValueError(f"unknown ablation: {mode}")


_SENSITIVE_KEYS = {
    "apikey",
    "authorization",
    "password",
    "passwd",
    "secret",
    "clientsecret",
    "cookie",
    "setcookie",
    "accesstoken",
    "refreshtoken",
    "idtoken",
    "authtoken",
}
_BEARER = re.compile(r"Bearer\s+[^\s,;\"']+", re.IGNORECASE)
_SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b(api[-_ ]?key|client[-_ ]?secret|access[-_ ]?token|refresh[-_ ]?token|password)"
    r"\s*[:=]\s*([^\s,;]+)"
)
_OPENAI_STYLE_KEY = re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b")


def _is_sensitive_key(key: Any) -> bool:
    normalized = re.sub(r"[^a-z0-9]", "", str(key).lower())
    return normalized in _SENSITIVE_KEYS or normalized.endswith(
        ("apikey", "clientsecret", "accesstoken", "refreshtoken", "idtoken", "authtoken")
    )


def redact(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            key: "[REDACTED]" if _is_sensitive_key(key) else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith(("{", "[")):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                pass
            else:
                return json.dumps(redact(parsed), ensure_ascii=False, separators=(",", ":"))
        result = _BEARER.sub("Bearer [REDACTED]", value)
        result = _SECRET_ASSIGNMENT.sub(lambda match: f"{match.group(1)}=[REDACTED]", result)
        return _OPENAI_STYLE_KEY.sub("sk-[REDACTED]", result)
    return value


class TraceRecorder:
    def __init__(self, path: Path | None = None):
        self.path = path
        self.events: list[dict[str, Any]] = []
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf-8")

    def record(self, event: str, **payload: Any) -> None:
        item = redact({"event": event, **payload})
        self.events.append(item)
        if self.path is not None:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(item, ensure_ascii=False) + "\n")


@dataclass
class LoopResult:
    status: str
    output: str | None
    iterations: int
    model_calls: int
    tool_calls: int
    input_units: int
    errors: list[str]
    history: list[Message]

    def summary(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "output": self.output,
            "iterations": self.iterations,
            "model_calls": self.model_calls,
            "tool_calls": self.tool_calls,
            "input_units": self.input_units,
            "errors": self.errors,
        }


class AgentLoop:
    def __init__(
        self,
        provider: FakeProvider,
        tools: Mapping[str, ToolSpec] | None = None,
        *,
        max_iterations: int = 6,
        max_same_action: int = 2,
        max_provider_retries: int = 2,
        trace: TraceRecorder | None = None,
    ):
        self.provider = provider
        self.tools = dict(default_tools() if tools is None else tools)
        self.max_iterations = max_iterations
        self.max_same_action = max_same_action
        self.max_provider_retries = max_provider_retries
        self.trace = trace or TraceRecorder()

    def run(self, goal: str, *, ablation: str = "complete") -> LoopResult:
        provider_calls_start = self.provider.calls
        history = [
            Message("system", "Use tools when current information is required."),
            Message("user", goal),
        ]
        action_counts: Counter[str] = Counter()
        input_units = 0
        tool_call_count = 0
        errors: list[str] = []

        for iteration in range(1, self.max_iterations + 1):
            request_messages = transform_history(history, ablation)
            protocol_errors = validate_history(request_messages)
            if protocol_errors:
                errors.extend(protocol_errors)
                self.trace.record("protocol_error", errors=protocol_errors)
                return self._result(
                    "protocol_error", None, iteration, tool_call_count, input_units, errors, history, provider_calls_start
                )

            definitions = [tool.definition() for tool in self.tools.values()]
            self.trace.record(
                "model_request",
                iteration=iteration,
                messages=[message.to_dict() for message in request_messages],
                tools=definitions,
            )

            turn = self._complete_with_retry(request_messages, definitions, errors)
            if turn is None:
                return self._result(
                    "provider_error", None, iteration, tool_call_count, input_units, errors, history, provider_calls_start
                )

            input_units += turn.usage.input_units
            self.trace.record(
                "model_response",
                request_id=turn.request_id,
                stop_reason=turn.stop_reason,
                usage=asdict(turn.usage),
                message=turn.message.to_dict(),
            )

            response_errors = validate_model_turn(turn, history)
            if response_errors:
                errors.extend(response_errors)
                self.trace.record("protocol_error", errors=response_errors)
                return self._result(
                    "protocol_error", None, iteration, tool_call_count, input_units, errors, history, provider_calls_start
                )

            # Preserve the complete model decision before executing any tool.
            history.append(turn.message)
            if not turn.message.tool_calls:
                status = {
                    "completed": "completed",
                    "refusal": "refused",
                    "max_output": "truncated",
                }.get(turn.stop_reason, "model_stopped")
                return self._result(
                    status,
                    str(turn.message.content),
                    iteration,
                    tool_call_count,
                    input_units,
                    errors,
                    history,
                    provider_calls_start,
                )

            fingerprints = [_action_fingerprint(call) for call in turn.message.tool_calls]
            projected_counts = action_counts.copy()
            for fingerprint in fingerprints:
                projected_counts[fingerprint] += 1
            repeated = [fingerprint for fingerprint in fingerprints if projected_counts[fingerprint] > self.max_same_action]
            if repeated:
                errors.append(f"repeated action blocked: {repeated[0]}")
                self.trace.record("loop_guard", reason="repeated_action", fingerprints=repeated)
                for call in turn.message.tool_calls:
                    blocked = {"ok": False, "error": "blocked_by_loop_guard"}
                    history.append(Message("tool", json.dumps(blocked), tool_call_id=call.id))
                return self._result(
                    "stuck", None, iteration, tool_call_count, input_units, errors, history, provider_calls_start
                )

            for call in turn.message.tool_calls:
                fingerprint = _action_fingerprint(call)
                action_counts[fingerprint] += 1
                tool_call_count += 1
                spec = self.tools.get(call.name)
                result = (
                    {"ok": False, "error": "unknown_tool", "name": call.name}
                    if spec is None
                    else spec.execute(call.arguments)
                )
                tool_message = Message("tool", json.dumps(result, ensure_ascii=False), tool_call_id=call.id)
                history.append(tool_message)
                self.trace.record("tool_result", call_id=call.id, tool=call.name, result=result)

        errors.append("maximum iterations reached")
        return self._result(
            "max_iterations",
            None,
            self.max_iterations,
            tool_call_count,
            input_units,
            errors,
            history,
            provider_calls_start,
        )

    def _complete_with_retry(
        self, messages: Sequence[Message], definitions: Sequence[dict[str, Any]], errors: list[str]
    ) -> ModelTurn | None:
        for attempt in range(self.max_provider_retries + 1):
            try:
                return self.provider.complete(messages, definitions)
            except (RateLimitError, ProviderTimeoutError, ServiceUnavailableError) as exc:
                errors.append(str(exc))
                self.trace.record("provider_retry", attempt=attempt + 1, error=str(exc))
        return None

    def _result(
        self,
        status: str,
        output: str | None,
        iterations: int,
        tool_calls: int,
        input_units: int,
        errors: list[str],
        history: list[Message],
        provider_calls_start: int,
    ) -> LoopResult:
        return LoopResult(
            status,
            output,
            iterations,
            self.provider.calls - provider_calls_start,
            tool_calls,
            input_units,
            list(errors),
            list(history),
        )


class StreamAssembler:
    """Reassemble provider-neutral text and JSON-argument delta events."""

    def __init__(self):
        self.text: list[str] = []
        self.arguments: dict[str, list[str]] = {}
        self.state = "open"

    def feed(self, event: Mapping[str, Any]) -> None:
        if self.state != "open":
            raise ProtocolError(f"event received after terminal state {self.state}")
        if not isinstance(event, Mapping):
            raise ProtocolError("stream event must be an object")
        event_type = event.get("type")
        if event_type == "text.delta":
            delta = event.get("delta")
            if not isinstance(delta, str):
                raise ProtocolError("text.delta requires a string delta")
            self.text.append(delta)
        elif event_type == "tool.arguments.delta":
            call_id = event.get("call_id")
            delta = event.get("delta")
            if not isinstance(call_id, str) or not call_id:
                raise ProtocolError("tool.arguments.delta requires a non-empty call_id")
            if not isinstance(delta, str):
                raise ProtocolError("tool.arguments.delta requires a string delta")
            self.arguments.setdefault(call_id, []).append(delta)
        elif event_type == "response.completed":
            self.state = "completed"
        elif event_type == "response.error":
            self.state = "error"
            raise ProtocolError(str(event.get("error", "stream failed")))
        else:
            raise ProtocolError(f"unknown stream event type: {event_type}")

    def finalize(self) -> dict[str, Any]:
        if self.state != "completed":
            raise ProtocolError("stream ended before response.completed")
        parsed_arguments: dict[str, Any] = {}
        for call_id, chunks in self.arguments.items():
            raw = "".join(chunks)
            try:
                parsed_arguments[call_id] = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ProtocolError(f"incomplete arguments for {call_id}: {exc}") from exc
        return {"text": "".join(self.text), "tool_arguments": parsed_arguments}


def assemble_stream(events: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    assembler = StreamAssembler()
    for event in events:
        assembler.feed(event)
    return assembler.finalize()


def _action_fingerprint(call: ToolCall) -> str:
    try:
        parsed = json.loads(call.arguments)
    except json.JSONDecodeError:
        normalized_arguments = call.arguments.strip()
    else:
        normalized_arguments = json.dumps(parsed, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return f"{call.name}:{normalized_arguments}"
