"""Groundtruth Core — Trace Engine.

A Trace is an ordered log of spans produced by running a subject (an agent, a
judge, a planner) against a Case. Every Groundtruth product records to this one
format, so detectors and the future dashboard stay product-agnostic.

Spans carry no wall-clock timestamps: runs must be byte-for-byte reproducible.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Span:
    kind: str                       # user_goal | tool_call | tool_result | final
    name: str = ""                  # tool name where relevant
    content: str = ""               # text payload
    data: dict[str, Any] = field(default_factory=dict)  # structured payload


@dataclass
class Trace:
    subject: str
    case_id: str
    spans: list[Span] = field(default_factory=list)

    def add(
        self,
        kind: str,
        name: str = "",
        content: str = "",
        data: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Span:
        """Append a span. Subject-controlled payloads (tool arguments) go in
        `data`, where a key called `kind`, `name` or `content` is ordinary
        content instead of a collision with this signature; `**kwargs` stays
        for the harness's own fixed-key spans."""
        payload = dict(data or {})
        payload.update(kwargs)
        span = Span(kind=kind, name=name, content=content, data=payload)
        self.spans.append(span)
        return span

    def tool_calls(self) -> list[Span]:
        return [s for s in self.spans if s.kind == "tool_call"]

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Trace:
        """Rebuild a Trace from its serialized form — the inverse of `to_dict`.
        Committed traces are the durable record of a run, so a detector change
        can be re-scored against them without re-running the subject."""
        trace = cls(subject=d["subject"], case_id=d["case_id"])
        for s in d.get("spans", []):
            trace.add(
                s["kind"],
                name=s.get("name", ""),
                content=s.get("content", ""),
                data=s.get("data", {}),
            )
        return trace

    def to_dict(self) -> dict[str, Any]:
        from . import SCHEMA_VERSION

        return {
            "schema_version": SCHEMA_VERSION,
            "subject": self.subject,
            "case_id": self.case_id,
            "spans": [asdict(s) for s in self.spans],
        }
