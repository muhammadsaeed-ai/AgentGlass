import json
import unittest

from agentglass import EventType, TraceEvent


def event_payload():
    return {
        "schema_version": "1.0", "event_id": "evt_01", "run_id": "run_01",
        "sequence": 0, "timestamp": "2026-01-02T03:04:05.000Z",
        "event_type": "run.started", "name": "run", "status": "started",
        "duration_ms": None, "parent_event_id": None, "attributes": {"environment": "test"},
    }


class TraceEventTests(unittest.TestCase):
    def test_json_round_trip(self):
        original = TraceEvent.from_dict(event_payload())
        restored = TraceEvent.from_dict(json.loads(original.to_json()))
        self.assertEqual(original, restored)
        self.assertEqual(restored.event_type, EventType.RUN_STARTED)

    def test_rejects_unknown_event_type(self):
        payload = event_payload()
        payload["event_type"] = "model.mind_reading"
        with self.assertRaisesRegex(ValueError, "unknown event_type"):
            TraceEvent.from_dict(payload)

    def test_rejects_naive_timestamp(self):
        payload = event_payload()
        payload["timestamp"] = "2026-01-02T03:04:05"
        with self.assertRaisesRegex(ValueError, "timezone"):
            TraceEvent.from_dict(payload)

    def test_rejects_negative_duration(self):
        payload = event_payload()
        payload["duration_ms"] = -0.1
        with self.assertRaisesRegex(ValueError, "duration_ms"):
            TraceEvent.from_dict(payload)

    def test_rejects_future_schema(self):
        payload = event_payload()
        payload["schema_version"] = "9.0"
        with self.assertRaisesRegex(ValueError, "Unsupported schema_version"):
            TraceEvent.from_dict(payload)


if __name__ == "__main__":
    unittest.main()
