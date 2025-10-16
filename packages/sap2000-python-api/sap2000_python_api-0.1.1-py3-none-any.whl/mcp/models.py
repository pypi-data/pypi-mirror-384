from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass(slots=True)
class ParameterDoc:
    """Represents a parameter entry extracted from the HTML documentation."""

    name: str
    description: str
    raw_blocks: List[str] = field(default_factory=list)


@dataclass(slots=True)
class SeeAlsoEntry:
    """Represents a see-also mapping."""

    title: str
    href: Optional[str]


@dataclass(slots=True)
class FunctionDoc:
    """Intermediate representation of a function topic extracted from HTML."""

    topic_id: str
    title: str
    section_path: List[str]
    syntax: List[str]
    vb6_procedure: Optional[str]
    parameters: List[ParameterDoc]
    remarks: List[str]
    release_notes: List[str]
    see_also: List[SeeAlsoEntry]
    vba_example: List[str]
    notes: List[str]
    src_path: Path
    meta: dict[str, str] = field(default_factory=dict)
