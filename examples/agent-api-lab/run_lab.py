from __future__ import annotations

import argparse
import json
from pathlib import Path

from lab import AgentLoop, FakeProvider, TraceRecorder


ABLATIONS = ("complete", "drop_assistant_call", "mismatch_call_id", "flatten_roles", "sliding_window")


def run_once(
    scenario: str,
    ablation: str,
    trace_path: Path | None,
    transient_failures: int,
    faults: list[str],
) -> dict:
    provider = FakeProvider(scenario=scenario, transient_failures=transient_failures, faults=faults)
    result = AgentLoop(provider, trace=TraceRecorder(trace_path)).run(
        "Report the current Shanghai weather and local time.", ablation=ablation
    )
    return {"scenario": scenario, "ablation": ablation, **result.summary()}


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect a deterministic model/tool-call protocol")
    parser.add_argument("--scenario", choices=FakeProvider.SCENARIOS, default="parallel")
    parser.add_argument("--ablation", choices=ABLATIONS, default="complete")
    parser.add_argument("--all-ablations", action="store_true")
    parser.add_argument("--transient-failures", type=int, default=0)
    parser.add_argument("--fault", action="append", choices=("429", "timeout", "5xx"), default=[])
    parser.add_argument("--trace", type=Path, help="Optional path for a redacted JSONL trace")
    args = parser.parse_args()

    if args.all_ablations:
        if args.trace is not None:
            parser.error("--trace cannot be combined with --all-ablations; run each ablation with its own trace path")
        rows = [run_once(args.scenario, mode, None, args.transient_failures, args.fault) for mode in ABLATIONS]
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return

    result = run_once(args.scenario, args.ablation, args.trace, args.transient_failures, args.fault)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
