import tempfile
import unittest
from pathlib import Path

from agentglass import AgentGlass, EventType, InMemoryStore, JSONLStore


class RecorderTests(unittest.TestCase):
    def test_run_tool_and_model_event_order(self):
        store = InMemoryStore()
        client = AgentGlass(store=store, service_name="unit-test")
        with client.start_run(run_id="run_test", attributes={"task": "lookup"}) as run:
            run.record(EventType.MODEL_REQUEST, name="planner", attributes={"model": "synthetic"})
            with run.tool("docs.search", input={"query": "traces"}) as tool:
                tool.set_output({"matches": 2})
        events = store.for_run("run_test")
        self.assertEqual(
            [event.event_type for event in events],
            [EventType.RUN_STARTED, EventType.CUSTOM, EventType.MODEL_REQUEST,
             EventType.TOOL_STARTED, EventType.TOOL_COMPLETED, EventType.RUN_COMPLETED],
        )
        self.assertEqual([event.sequence for event in events], list(range(len(events))))
        self.assertEqual(events[4].attributes["output"], {"matches": 2})
        self.assertEqual(events[-1].status, "completed")

    def test_sensitive_data_is_redacted_before_persisting(self):
        store = InMemoryStore()
        with AgentGlass(store=store).start_run() as run:
            run.record(EventType.CUSTOM, attributes={"api_key": "never-store-this", "note": "dev@example.com"})
        serialized = "\n".join(event.to_json() for event in store.all())
        self.assertNotIn("never-store-this", serialized)
        self.assertNotIn("dev@example.com", serialized)

    def test_tool_errors_are_recorded_and_exception_reraised(self):
        store = InMemoryStore()
        with self.assertRaisesRegex(RuntimeError, "tool exploded"):
            with AgentGlass(store=store).start_run(run_id="run_failure") as run:
                with run.tool("broken_tool"):
                    raise RuntimeError("tool exploded")
        events = store.for_run("run_failure")
        self.assertEqual(events[-2].event_type, EventType.TOOL_ERROR)
        self.assertEqual(events[-1].event_type, EventType.RUN_FAILED)
        self.assertEqual(events[-1].status, "failed")

    def test_span_links_completion_to_start(self):
        store = InMemoryStore()
        with AgentGlass(store=store).start_run() as run:
            with run.span("retrieve", kind="retrieval") as span:
                span.set_output({"documents": 1})
        events = store.all()
        started = next(event for event in events if event.event_type == EventType.SPAN_STARTED)
        finished = next(event for event in events if event.event_type == EventType.SPAN_COMPLETED)
        self.assertEqual(finished.parent_event_id, started.event_id)
        self.assertGreaterEqual(finished.duration_ms, 0)
        self.assertEqual(finished.attributes["output"], {"documents": 1})

    def test_finish_is_idempotent_and_blocks_late_events(self):
        store = InMemoryStore()
        run = AgentGlass(store=store).start_run()
        self.assertIsNotNone(run.finish())
        self.assertIsNone(run.finish())
        with self.assertRaisesRegex(RuntimeError, "after a run has finished"):
            run.record(EventType.CUSTOM, name="too_late")


class JSONLStoreTests(unittest.TestCase):
    def test_append_and_reload(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "trace.jsonl"
            store = JSONLStore(path)
            with AgentGlass(store=store).start_run(run_id="persisted") as run:
                run.record(EventType.CUSTOM, name="checkpoint")
            reloaded = JSONLStore(path).all()
            self.assertEqual(len(reloaded), 3)
            self.assertEqual(reloaded[1].name, "checkpoint")
            self.assertEqual(len(JSONLStore(path).for_run("persisted")), 3)

    def test_corrupt_line_reports_path_and_line_number(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.jsonl"
            path.write_text('{"not":"an event"}\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, r"broken\.jsonl:1"):
                JSONLStore(path).all()


if __name__ == "__main__":
    unittest.main()
