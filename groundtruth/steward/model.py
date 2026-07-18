"""Steward model — findings and declarations.

Deliberately duplicates the *shape* of meta/'s finding model instead of
sharing code: a findings library shared by the scientific audit layer and
housekeeping would couple the two (ADR-0008 D5). Reopen at a third realized
findings consumer.
"""
from __future__ import annotations

from dataclasses import dataclass


class DeclarationError(Exception):
    """Constitution or debt register missing/malformed. CLI maps this to exit 2."""


@dataclass(frozen=True)
class Finding:
    check_id: str  # RC1..RC8
    path: str  # repo-relative path the finding cites
    summary: str
    line: int = 0  # 1-based; 0 means the finding is about the whole file

    def sort_key(self) -> tuple[str, str, int]:
        return (self.check_id, self.path, self.line)


@dataclass(frozen=True)
class RepoDeclarations:
    """Parsed Constitution declarations block (schema v1) — tuples of plain
    mappings, exactly as declared; validation lives in the loader."""

    schema: int
    roles: tuple
    version_anchors: tuple
    derived_artifacts: tuple
    frozen: tuple
    layer_rules: tuple
    exemptions: tuple
