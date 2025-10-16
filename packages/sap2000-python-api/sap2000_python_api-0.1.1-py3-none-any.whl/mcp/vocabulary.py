from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Set, Tuple

from .text_utils import normalize_for_index


@dataclass(frozen=True)
class ExpansionGroup:
    canonical: str
    terms: Tuple[str, ...]
    domain: str | None = None


EXPANSION_GROUPS: Tuple[ExpansionGroup, ...] = (
    ExpansionGroup("point", ("point", "joint", "pointobj", "point object", "jointobj"), "geometry"),
    ExpansionGroup("frame", ("frame", "beam", "girder", "frameobj", "member"), "geometry"),
    ExpansionGroup("area", ("area", "shell", "plate", "wall", "surface"), "geometry"),
    ExpansionGroup("solid", ("solid", "brick", "tetra", "volume"), "geometry"),
    ExpansionGroup(
        "coord",
        ("coord", "coordinate", "cartesian", "cylindrical", "spherical", "x", "y", "z"),
        "geometry",
    ),
    ExpansionGroup("result", ("result", "response", "output", "reaction", "displacement"), "results"),
    ExpansionGroup("select", ("select", "pick", "highlight", "choose"), "selection"),
    ExpansionGroup("assign", ("assign", "set", "define", "apply"), "assignment"),
    ExpansionGroup("database", ("database", "table", "tables", "record"), "data"),
    ExpansionGroup("load", ("load", "pattern", "case", "combo", "combination"), "analysis"),
)


ABBREVIATIONS: Dict[str, str] = {
    "coord": "coordinate",
    "coords": "coordinate",
    "geom": "geometry",
    "disp": "displacement",
    "def": "definition",
    "info": "information",
    "msg": "message",
    "obj": "object",
}


def _build_reverse_index() -> Dict[str, Set[str]]:
    reverse: Dict[str, Set[str]] = {}
    for group in EXPANSION_GROUPS:
        normalized_terms = [normalize_for_index(term).replace(" ", "") for term in group.terms]
        for term in normalized_terms:
            reverse.setdefault(term, set()).add(group.canonical)
        reverse.setdefault(group.canonical, set()).add(group.canonical)
    return reverse


REVERSE_INDEX = _build_reverse_index()


def expand_token(token: str) -> Set[str]:
    """Return canonical expansions for a token."""
    normalized = normalize_for_index(token).replace(" ", "")
    expansions = set()
    if normalized in REVERSE_INDEX:
        expansions.update(REVERSE_INDEX[normalized])
    elif normalized in ABBREVIATIONS:
        canonical = normalize_for_index(ABBREVIATIONS[normalized]).replace(" ", "")
        expansions.update(REVERSE_INDEX.get(canonical, {canonical}))
    else:
        expansions.add(normalized)
    return expansions


def expand_query(tokens: Iterable[str]) -> Dict[str, Set[str]]:
    """Expand tokens to canonical concepts."""
    return {token: expand_token(token) for token in tokens}


def all_canonical_terms() -> Set[str]:
    """Return set of canonical terms defined in vocabulary."""
    return {group.canonical for group in EXPANSION_GROUPS}


def group_by_domain() -> Dict[str, List[str]]:
    domain_map: Dict[str, List[str]] = {}
    for group in EXPANSION_GROUPS:
        if group.domain:
            domain_map.setdefault(group.domain, []).append(group.canonical)
    return domain_map
