from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT))

from lab import (  # noqa: E402
    AgentLoop,
    FakeProvider,
    Message,
    ModelTurn,
    ProtocolError,
    StreamAssembler,
    ToolCall,
    TraceRecorder,
    Usage,
    assemble_stream,
    default_tools,
    redact,
    validate_history,
)


class AgentLoopTests(unittest.TestCase):
    def test_plain_text_response_does_not_enter_tool_loop(self) -> None:
        result = AgentLoop(FakeProvider("text")).run("Say hello")
        self.assertEqual("completed", result.status)
        self.assertEqual(0, result.tool_calls)

    def test_single_tool_round_trip(self) -> None:
        result = AgentLoop(FakeProvider("single")).run("Weather in Shanghai")
        self.assertEqual("completed", result.status)
        self.assertEqual(1, result.tool_calls)
        self.assertEqual([], validate_history(result.history))

    def test_parallel_tool_calls_keep_call_ids(self) -> None:
        result = AgentLoop(FakeProvider("parallel")).run("Weather and time in Shanghai")
        self.assertEqual("completed", result.status)
        self.assertEqual(2, result.tool_calls)
        result_ids = {message.tool_call_id for message in result.history if message.role == "tool"}
        self.assertEqual({"call_weather_1", "call_time_1"}, result_ids)

    def test_parallel_failure_keeps_the_successful_result(self) -> None:
        result = AgentLoop(FakeProvider("parallel_partial_failure")).run("Weather and air quality")
        self.assertEqual("completed", result.status)
        tool_results = [json.loads(message.content) for message in result.history if message.role == "tool"]
        self.assertEqual({True, False}, {item["ok"] for item in tool_results})

    def test_invalid_arguments_become_data_and_can_be_repaired(self) -> None:
        result = AgentLoop(FakeProvider("invalid_args")).run("Weather in Shanghai")
        self.assertEqual("completed", result.status)
        self.assertEqual(2, result.tool_calls)
        first_result = next(message for message in result.history if message.role == "tool")
        self.assertEqual("missing_required", json.loads(first_result.content)["error"])

    def test_repetition_guard_stops_a_runaway_loop(self) -> None:
        result = AgentLoop(FakeProvider("repeat"), max_same_action=2).run("Keep checking")
        self.assertEqual("stuck", result.status)
        self.assertIn("repeated action blocked", result.errors[-1])

    def test_retryable_provider_fault_is_bounded(self) -> None:
        result = AgentLoop(FakeProvider("single", transient_failures=1)).run("Weather")
        self.assertEqual("completed", result.status)
        self.assertTrue(any("simulated 429" in error for error in result.errors))

        timeout = AgentLoop(FakeProvider("single", faults=["timeout", "5xx"])).run("Weather")
        self.assertEqual("completed", timeout.status)
        self.assertTrue(any("simulated timeout" in error for error in timeout.errors))
        self.assertTrue(any("simulated 503" in error for error in timeout.errors))

    def test_non_retryable_model_stops_are_not_reported_as_success(self) -> None:
        refused = AgentLoop(FakeProvider("refusal")).run("Unsafe request")
        truncated = AgentLoop(FakeProvider("truncated")).run("Very long request")
        self.assertEqual("refused", refused.status)
        self.assertEqual("truncated", truncated.status)

    def test_invalid_model_tool_batches_are_blocked_before_execution(self) -> None:
        for scenario in ("duplicate_ids", "truncated_tool_call"):
            with self.subTest(scenario=scenario):
                result = AgentLoop(FakeProvider(scenario)).run("Unsafe model output")
                self.assertEqual("protocol_error", result.status)
                self.assertEqual(0, result.tool_calls)
                self.assertFalse(any(message.role == "tool" for message in result.history))

    def test_schema_rejects_wrong_type_and_empty_value(self) -> None:
        tool = default_tools()["get_weather"]
        self.assertEqual("invalid_type", tool.execute('{"city":123}')["error"])
        self.assertEqual("empty_required", tool.execute('{"city":"  "}')["error"])

    def test_semantically_equal_json_hits_repetition_guard(self) -> None:
        class EquivalentRepeatProvider(FakeProvider):
            def __init__(self) -> None:
                super().__init__("repeat")

            def complete(self, messages, definitions):
                self.calls += 1
                arguments = '{"city":"Shanghai"}' if self.calls % 2 else '{ "city" : "Shanghai" }'
                message = Message(
                    "assistant", tool_calls=[ToolCall(f"call_{self.calls}", "get_weather", arguments)]
                )
                return ModelTurn(message, "tool_calls", f"req_{self.calls}", Usage(1, 1))

        result = AgentLoop(EquivalentRepeatProvider(), max_same_action=1).run("Repeat")
        self.assertEqual("stuck", result.status)
        self.assertEqual([], validate_history(result.history))

    def test_explicit_empty_tool_registry_stays_empty(self) -> None:
        class CapturingProvider(FakeProvider):
            def __init__(self) -> None:
                super().__init__("text")
                self.definitions = None

            def complete(self, messages, definitions):
                self.definitions = definitions
                return super().complete(messages, definitions)

        provider = CapturingProvider()
        result = AgentLoop(provider, tools={}).run("No tools")
        self.assertEqual("completed", result.status)
        self.assertEqual([], provider.definitions)

    def test_model_call_count_is_per_run(self) -> None:
        loop = AgentLoop(FakeProvider("text"))
        self.assertEqual(1, loop.run("one").model_calls)
        self.assertEqual(1, loop.run("two").model_calls)

    def test_context_ablations_fail_for_explainable_reasons(self) -> None:
        for mode in ("drop_assistant_call", "mismatch_call_id", "sliding_window"):
            with self.subTest(mode=mode):
                result = AgentLoop(FakeProvider("parallel")).run("Weather and time", ablation=mode)
                self.assertEqual("protocol_error", result.status)
                self.assertTrue(result.errors)

        flattened = AgentLoop(FakeProvider("parallel"), max_same_action=1).run(
            "Weather and time", ablation="flatten_roles"
        )
        self.assertEqual("stuck", flattened.status)


class StreamAndTraceTests(unittest.TestCase):
    def test_stream_reassembly_waits_for_complete_json(self) -> None:
        result = assemble_stream(
            [
                {"type": "text.delta", "delta": "Checking "},
                {"type": "tool.arguments.delta", "call_id": "call_1", "delta": '{"city":'},
                {"type": "tool.arguments.delta", "call_id": "call_1", "delta": '"Shanghai"}'},
                {"type": "response.completed"},
            ]
        )
        self.assertEqual("Checking ", result["text"])
        self.assertEqual({"city": "Shanghai"}, result["tool_arguments"]["call_1"])

    def test_half_stream_is_not_treated_as_success(self) -> None:
        with self.assertRaises(ProtocolError):
            assemble_stream([{"type": "tool.arguments.delta", "call_id": "call_1", "delta": "{"}])

    def test_stream_rejects_events_after_terminal_and_unknown_events(self) -> None:
        assembler = StreamAssembler()
        assembler.feed({"type": "response.completed"})
        with self.assertRaises(ProtocolError):
            assembler.feed({"type": "text.delta", "delta": "late"})
        with self.assertRaises(ProtocolError):
            assemble_stream([{"type": "unknown"}, {"type": "response.completed"}])
        with self.assertRaises(ProtocolError):
            assemble_stream(
                [
                    {"type": "tool.arguments.delta", "delta": "{}"},
                    {"type": "response.completed"},
                ]
            )

    def test_trace_redacts_credentials(self) -> None:
        value = redact(
            {
                "authorization": "Bearer top-secret==",
                "x-api-key": "key-value",
                "client_secret": "client-value",
                "cookie": "session=value",
                "nested": ["Bearer abc.def==", '{"api_key":"sk-live-secret123"}'],
            }
        )
        self.assertEqual("[REDACTED]", value["authorization"])
        self.assertEqual("[REDACTED]", value["x-api-key"])
        self.assertEqual("[REDACTED]", value["client_secret"])
        self.assertEqual("[REDACTED]", value["cookie"])
        self.assertEqual("Bearer [REDACTED]", value["nested"][0])
        self.assertNotIn("secret123", value["nested"][1])

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.jsonl"
            recorder = TraceRecorder(path)
            recorder.record("request", api_key="top-secret", header="Bearer token")
            content = path.read_text(encoding="utf-8")
            self.assertNotIn("top-secret", content)
            self.assertNotIn("Bearer token", content)


if __name__ == "__main__":
    unittest.main()
