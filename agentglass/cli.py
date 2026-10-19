"""Command-line entry point for creating and inspecting local traces."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import sys

from . import __version__
from .models import EventType
from .recorder import AgentGlass
from .storage import JSONLStore


def _format_event(event) -> str:
    duration = "-" if event.duration_ms is None else f"{event.duration_ms:.3f} ms"
    return (
        f"{event.sequence:>3}  {event.timestamp:<24}  "
        f"{event.event_type.value:<17}  {event.status:<9}  "
        f"{duration:>12}  {event.name}"
    )


def _run_demo(path: Path) -> int:
    store = JSONLStore(path)
    client = AgentGlass(store=store, service_name="agentglass-offline-demo")
    with client.start_run(
        attributes={"demo": True, "environment": "local", "note": "Synthetic example; no model API is called"}
    ) as run:
        run.record(
            EventType.MODEL_REQUEST,
            name="demo-planner",
            status="ok",
            attributes={"provider": "synthetic", "model": "demo-planner", "purpose": "plan a documentation search"},
        )
        with run.tool(
            "docs.search",
            input={"query": "agent observability"},
            attributes={"system": "synthetic-demo"},
        ) as tool:
            tool.set_output({"matches": 3, "source": "local fixture"})
        run.record(
            EventType.MODEL_RESPONSE,
            name="demo-planner",
            status="ok",
            attributes={"provider": "synthetic", "model": "demo-planner", "finish_reason": "stop"},
        )
        run.record(
            EventType.CUSTOM,
            name="answer.prepared",
            status="ok",
            attributes={"summary": "The trace captures a model step, a tool call, and its result."},
        )
        run_id = run.run_id
    print(f"Created synthetic demo trace: {path}")
    print(f"Run ID: {run_id}")
    print(f"Events in this run: {len(store.for_run(run_id))}")
    print("No external model, agent framework, or network API was called.")
    return 0


def _inspect(path: Path, run_id: str | None) -> int:
    events = JSONLStore(path).all()
    if run_id:
        events = [event for event in events if event.run_id == run_id]
    if not events:
        print("No trace events found." if not run_id else f"No events found for run ID {run_id}.")
        return 1
    print(f"AgentGlass trace inspection — {path}")
    print("SEQ  TIMESTAMP                 EVENT TYPE         STATUS         DURATION  NAME")
    print("-" * 112)
    for event in events:
        print(_format_event(event))
    print(f"\n{len(events)} event(s), {len({event.run_id for event in events})} run(s)")
    return 0


def _validate(path: Path) -> int:
    try:
        events = JSONLStore(path).all()
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        return 1
    if not events:
        print("Valid JSONL file, but no events were found.")
        return 0
    run_counts = Counter(event.run_id for event in events)
    print(f"Valid: {len(events)} event(s) across {len(run_counts)} run(s) in {path}")
    print("Schema version(s): " + ", ".join(sorted({event.schema_version for event in events})))
    return 0


def _summary(path: Path) -> int:
    try:
        events = JSONLStore(path).all()
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"Could not read traces: {exc}", file=sys.stderr)
        return 1
    if not events:
        print("No trace events found.")
        return 1
    by_run: dict[str, list] = {}
    for event in events:
        by_run.setdefault(event.run_id, []).append(event)
    print(f"AgentGlass summary — {path}")
    for run_id, run_events in by_run.items():
        terminal = next(
            (event.status for event in reversed(run_events) if event.event_type in {
                EventType.RUN_COMPLETED, EventType.RUN_FAILED, EventType.RUN_CANCELLED
            }),
            "in progress",
        )
        types = Counter(event.event_type.value for event in run_events)
        tools = sum(count for name, count in types.items() if name.startswith("tool."))
        print(f"\nRun {run_id}  |  status: {terminal}  |  events: {len(run_events)}  |  tool events: {tools}")
        print("  " + ", ".join(f"{name}={count}" for name, count in sorted(types.items())))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentglass",
        description="Local-first tracing primitives for AI agent runs.",
        epilog="Privacy note: use synthetic traces for demos and inspect exported events before sharing them.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    demo = commands.add_parser("demo", help="write a synthetic, offline trace")
    demo.add_argument("--output", type=Path, default=Path("traces/demo.jsonl"), help="JSONL output path")
    inspect = commands.add_parser("inspect", help="print event timeline rows")
    inspect.add_argument("path", type=Path, help="JSONL trace file")
    inspect.add_argument("--run-id", help="only show the selected run")
    validate = commands.add_parser("validate", help="validate every event in a JSONL file")
    validate.add_argument("path", type=Path, help="JSONL trace file")
    summary = commands.add_parser("summary", help="group events by run and event type")
    summary.add_argument("path", type=Path, help="JSONL trace file")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            return _run_demo(args.output)
        if args.command == "inspect":
            return _inspect(args.path, args.run_id)
        if args.command == "validate":
            return _validate(args.path)
        if args.command == "summary":
            return _summary(args.path)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"AgentGlass error: {exc}", file=sys.stderr)
        return 1
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
