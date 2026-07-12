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

    def add(self, kind: str, name: str = "", content: str = "", **data: Any) -> Span:
        span = Span(kind=kind, name=name, content=content, data=dict(data))
        self.spans.append(span)
        return span

    def tool_calls(self) -> list[Span]:
        return [s for s in self.spans if s.kind == "tool_call"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "case_id": self.case_id,
            "spans": [asdict(s) for s in self.spans],
        }
