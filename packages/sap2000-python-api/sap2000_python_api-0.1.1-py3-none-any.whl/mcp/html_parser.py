from __future__ import annotations

import logging
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup, Tag
import re

TextTag = Tag  # alias for readability

from .models import FunctionDoc, ParameterDoc, SeeAlsoEntry

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class HtmlParseConfig:
    root: Path
    encoding: str = "windows-1252"


def iter_function_docs(config: HtmlParseConfig) -> Iterator[FunctionDoc]:
    """Yield function documents parsed from the HTML tree."""
    for html_path in sorted(config.root.rglob("*.htm")):
        doc = parse_function_doc(html_path, config)
        if doc is None:
            continue
        yield doc


def parse_function_doc(html_path: Path, config: HtmlParseConfig) -> Optional[FunctionDoc]:
    """Parse a single HTML document into a FunctionDoc."""
    try:
        content = html_path.read_text(encoding=config.encoding, errors="ignore")
    except FileNotFoundError:
        logger.warning("Missing HTML file: %s", html_path)
        return None

    soup = BeautifulSoup(content, "lxml")
    header = soup.find("h1")
    if header is None:
        return None

    title = header.get_text(strip=True)
    if not title:
        return None

    sections = _collect_sections(soup)
    if "syntax" not in sections:
        # Non-function topics usually lack syntax block; skip.
        return None

    meta = {
        meta_tag["name"]: meta_tag.get("content", "")
        for meta_tag in soup.find_all("meta")
        if meta_tag.has_attr("name")
    }

    topic_id = meta.get("topic-id", title)
    section_path = list(html_path.relative_to(config.root).parent.parts)

    return FunctionDoc(
        topic_id=topic_id,
        title=title,
        section_path=section_path,
        syntax=_parse_syntax(sections.get("syntax", [])),
        vb6_procedure=_parse_vb6(sections.get("vb6 procedure")),
        parameters=_parse_parameters(sections.get("parameters", [])),
        remarks=_to_text_lines(sections.get("remarks", [])),
        release_notes=_to_text_lines(sections.get("release notes", [])),
        see_also=_parse_see_also(sections.get("see also", [])),
        vba_example=_collect_code_lines(sections.get("vba example", [])),
        notes=_to_text_lines(sections.get("notes", [])),
        src_path=html_path.relative_to(config.root),
        meta=meta,
    )


def _collect_sections(soup: BeautifulSoup) -> dict[str, list[TextTag]]:
    sections: dict[str, list[TextTag]] = {}
    current_label: Optional[str] = None
    node = soup.find("h1")
    while node is not None:
        node = node.next_sibling
        if node is None:
            break
        if isinstance(node, str):
            continue
        if isinstance(node, Tag) and node.name == "h2":
            current_label = node.get_text(strip=True).lower()
            sections.setdefault(current_label, [])
            continue
        if current_label and isinstance(node, Tag):
            sections[current_label].append(node)
    return sections


def _parse_syntax(blocks: Iterable[TextTag]) -> list[str]:
    lines: list[str] = []
    for elem in blocks:
        if isinstance(elem, Tag):
            text = _clean_text(elem)
            if text:
                lines.append(text)
    return lines


def _parse_vb6(blocks: Optional[list[Tag]]) -> Optional[str]:
    if not blocks:
        return None
    sentences = []
    for elem in blocks:
        if isinstance(elem, Tag):
            text = _clean_text(elem)
            if text:
                sentences.append(text)
    return "\n".join(sentences) if sentences else None


def _parse_parameters(blocks: list[Tag]) -> list[ParameterDoc]:
    parameters: list[ParameterDoc] = []
    current_name: Optional[str] = None
    current_desc: list[str] = []
    raw_blocks: list[str] = []

    def flush() -> None:
        nonlocal current_name, current_desc, raw_blocks
        if current_name:
            description = " ".join(current_desc).strip()
            parameters.append(
                ParameterDoc(
                    name=current_name,
                    description=description,
                    raw_blocks=raw_blocks.copy(),
                )
            )
        current_name = None
        current_desc = []
        raw_blocks = []

    for elem in _iter_parameter_tags(blocks):
        if not isinstance(elem, Tag):
            continue
        text = _clean_text(elem)
        if not text:
            continue
        raw_blocks.append(elem.decode())
        classes = elem.get("class", [])
        if "ParameterName" in classes or elem.name in {"dt", "th"}:
            if current_name:
                flush()
            current_name = text
            current_desc = []
        else:
            if current_name is None:
                current_name = text
            else:
                current_desc.append(text)
    flush()
    return parameters


def _iter_parameter_tags(blocks: Iterable[TextTag]) -> Iterator[TextTag]:
    for elem in blocks:
        if not isinstance(elem, Tag):
            continue
        if elem.name in {"p", "li", "dt", "dd", "th", "td"}:
            yield elem
        else:
            for child in elem.children:
                if isinstance(child, Tag):
                    yield from _iter_parameter_tags([child])


def _to_text_lines(blocks: Optional[list[TextTag]]) -> list[str]:
    if not blocks:
        return []
    lines = []
    for elem in blocks:
        if isinstance(elem, Tag):
            text = _clean_text(elem)
            if text:
                lines.append(text)
    return lines


def _collect_code_lines(blocks: Optional[list[Tag]]) -> list[str]:
    if not blocks:
        return []
    lines = []
    for elem in blocks:
        if isinstance(elem, Tag):
            text = _clean_text(elem, collapse_newlines=False)
            if text:
                lines.extend(text.splitlines())
    return lines


def _parse_see_also(blocks: Optional[list[Tag]]) -> list[SeeAlsoEntry]:
    entries: list[SeeAlsoEntry] = []
    if not blocks:
        return entries
    for elem in blocks:
        if not isinstance(elem, Tag):
            continue
        for anchor in elem.find_all("a"):
            title = _clean_text(anchor)
            href = anchor.get("href")
            if title:
                entries.append(SeeAlsoEntry(title=title, href=href))
    return entries


def _clean_text(tag: Tag, collapse_newlines: bool = True) -> str:
    raw = "".join(tag.strings)
    if collapse_newlines:
        raw = raw.replace("\r", "")
        raw = re.sub(r"\s+", " ", raw)
    else:
        raw = raw.replace("\r", "")
        raw = re.sub(r"[ \t]+", " ", raw)
    return raw.strip()
