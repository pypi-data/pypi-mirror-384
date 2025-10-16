from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Iterator, Optional, Sequence

from .html_parser import HtmlParseConfig, iter_function_docs
from .models import FunctionDoc, ParameterDoc, SeeAlsoEntry
from .serialization import dumps_sorted


@dataclass(slots=True)
class ParameterRecord:
    name: str
    description: str


@dataclass(slots=True)
class SeeAlsoRecord:
    title: str
    href: str | None


@dataclass(slots=True)
class FunctionCard:
    function_id: int
    topic_id: str
    name: str
    section_path: list[str]
    syntax: list[str]
    vb6_procedure: str | None
    parameters: list[ParameterRecord]
    remarks: list[str]
    release_notes: list[str]
    see_also: list[SeeAlsoRecord]
    vba_example: list[str]
    notes: list[str]
    src_path: str
    meta: dict[str, str]
    introduced_text: Optional[str] = None
    introduced_major: Optional[int] = None
    introduced_minor: Optional[int] = None
    introduced_patch: Optional[int] = None
    deprecated_text: Optional[str] = None
    deprecated_major: Optional[int] = None
    deprecated_minor: Optional[int] = None
    deprecated_patch: Optional[int] = None


def build_cards_from_html(html_root: Path) -> list[FunctionCard]:
    config = HtmlParseConfig(root=html_root)
    docs: list[FunctionDoc] = sorted(
        iter_function_docs(config), key=lambda doc: str(doc.src_path).lower()
    )
    cards: list[FunctionCard] = []
    for idx, doc in enumerate(docs, start=1):
        cards.append(_doc_to_card(doc, function_id=idx))
    return cards


def write_cards_jsonl(cards: Sequence[FunctionCard], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        for card in cards:
            payload = asdict(card)
            fh.write(dumps_sorted(payload) + "\n")


def _doc_to_card(doc: FunctionDoc, function_id: int) -> FunctionCard:
    return FunctionCard(
        function_id=function_id,
        topic_id=doc.topic_id,
        name=doc.title,
        section_path=list(doc.section_path),
        syntax=list(doc.syntax),
        vb6_procedure=doc.vb6_procedure,
        parameters=_transform_parameters(doc.parameters),
        remarks=list(doc.remarks),
        release_notes=list(doc.release_notes),
        see_also=_transform_see_also(doc.see_also),
        vba_example=list(doc.vba_example),
        notes=list(doc.notes),
        src_path=str(doc.src_path).replace("\\", "/"),
        meta=dict(doc.meta),
        **_extract_version_metadata(doc.release_notes),
    )


def _transform_parameters(params: Iterable[ParameterDoc]) -> list[ParameterRecord]:
    return [ParameterRecord(name=p.name, description=p.description) for p in params]


def _transform_see_also(entries: Iterable[SeeAlsoEntry]) -> list[SeeAlsoRecord]:
    return [SeeAlsoRecord(title=e.title, href=e.href) for e in entries]


INTRO_REGEX = re.compile(
    r"(?:initial release|introduced|added)\s+in\s+version\s+(?P<version>\d+(?:\.\d+){0,2})",
    re.IGNORECASE,
)
DEPR_REGEX = re.compile(
    r"(?:deprecated|removed|obsolete)\s+in\s+version\s+(?P<version>\d+(?:\.\d+){0,2})",
    re.IGNORECASE,
)


def _extract_version_metadata(release_notes: Iterable[str]) -> dict[str, Optional[int | str]]:
    introduced_text: Optional[str] = None
    introduced_parts: Optional[tuple[int, int, int]] = None
    deprecated_text: Optional[str] = None
    deprecated_parts: Optional[tuple[int, int, int]] = None

    for line in release_notes:
        line_clean = line.strip()
        if not introduced_text:
            intro_match = INTRO_REGEX.search(line_clean)
            if intro_match:
                introduced_text = line_clean
                introduced_parts = _split_version(intro_match.group("version"))
        if not deprecated_text:
            depr_match = DEPR_REGEX.search(line_clean)
            if depr_match:
                deprecated_text = line_clean
                deprecated_parts = _split_version(depr_match.group("version"))
        if introduced_text and deprecated_text:
            break

    return {
        "introduced_text": introduced_text,
        "introduced_major": introduced_parts[0] if introduced_parts else None,
        "introduced_minor": introduced_parts[1] if introduced_parts else None,
        "introduced_patch": introduced_parts[2] if introduced_parts else None,
        "deprecated_text": deprecated_text,
        "deprecated_major": deprecated_parts[0] if deprecated_parts else None,
        "deprecated_minor": deprecated_parts[1] if deprecated_parts else None,
        "deprecated_patch": deprecated_parts[2] if deprecated_parts else None,
    }


def _split_version(raw: str) -> tuple[int, int, int]:
    text = raw.strip().rstrip(".")
    parts = text.split(".")
    numbers: list[int] = []
    for part in parts:
        if part.isdigit():
            numbers.append(int(part))
        else:
            match = re.search(r"\d+", part)
            numbers.append(int(match.group(0)) if match else 0)
    while len(numbers) < 3:
        numbers.append(0)
    return numbers[0], numbers[1], numbers[2]
