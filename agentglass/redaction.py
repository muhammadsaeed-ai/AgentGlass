"""Defensive, dependency-free redaction before trace persistence."""

from __future__ import annotations

import re
from typing import Any

_REDACTED = "[REDACTED]"
_SENSITIVE_KEY = re.compile(
    r"(?:password|passwd|secret|api[_-]?key|access[_-]?token|refresh[_-]?token|"
    r"authorization|cookie|credential|private[_-]?key|client[_-]?secret|"
    r"session[_-]?token|ssn|email|phone[_-]?(?:number)?)",
    re.IGNORECASE,
)
_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_SECRET_PATTERNS = (
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{8,}", re.IGNORECASE),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{12,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{25,}\b"),
)


class Redactor:
    """Mask common secrets/PII recursively and bound payload size/depth.

    Pattern-based redaction is a safety net, not a guarantee that every secret format
    is detectable. Applications should still avoid collecting sensitive values.
    """

    def __init__(
        self,
        *,
        redact_pii: bool = True,
        max_string_length: int = 4_000,
        max_depth: int = 12,
        max_items: int = 1_000,
    ) -> None:
        if max_string_length < 32:
            raise ValueError("max_string_length must be at least 32")
        if max_depth < 1:
            raise ValueError("max_depth must be at least 1")
        if max_items < 1:
            raise ValueError("max_items must be at least 1")
        self.redact_pii = redact_pii
        self.max_string_length = max_string_length
        self.max_depth = max_depth
        self.max_items = max_items

    def sanitize(self, value: Any) -> Any:
        """Return a JSON-compatible redacted copy without mutating the input."""
        return self._walk(value, depth=0, key=None)

    def _walk(self, value: Any, *, depth: int, key: str | None) -> Any:
        if key is not None and _SENSITIVE_KEY.search(key.replace(".", "_")):
            return _REDACTED
        if depth > self.max_depth:
            return "[MAX_DEPTH]"
        if value is None or isinstance(value, (bool, int)):
            return value
        if isinstance(value, float):
            return value if value == value and abs(value) != float("inf") else "[NON_FINITE_NUMBER]"
        if isinstance(value, str):
            text = value
            for pattern in _SECRET_PATTERNS:
                text = pattern.sub(_REDACTED, text)
            if self.redact_pii:
                text = _EMAIL.sub(_REDACTED, text)
            if len(text) > self.max_string_length:
                suffix = "…[TRUNCATED]"
                text = text[: self.max_string_length - len(suffix)] + suffix
            return text
        if isinstance(value, dict):
            output: dict[str, Any] = {}
            for index, (child_key, child_value) in enumerate(value.items()):
                if index >= self.max_items:
                    output["_truncated_items"] = len(value) - self.max_items
                    break
                safe_key = str(child_key)[:256]
                output[safe_key] = self._walk(child_value, depth=depth + 1, key=safe_key)
            return output
        if isinstance(value, (list, tuple, set)):
            items = list(value)
            result = [
                self._walk(item, depth=depth + 1, key=None)
                for item in items[: self.max_items]
            ]
            if len(items) > self.max_items:
                result.append(f"[TRUNCATED {len(items) - self.max_items} ITEMS]")
            return result
        return f"[UNSUPPORTED_TYPE:{type(value).__name__}]"
