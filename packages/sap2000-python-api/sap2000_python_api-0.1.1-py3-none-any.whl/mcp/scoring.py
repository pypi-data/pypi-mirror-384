from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Set, Tuple

from .text_utils import normalize_for_index
from .vocabulary import expand_query, group_by_domain


@dataclass(frozen=True)
class ScoringWeights:
    base: int = 1000
    decay: int = 25
    name: int = 200
    qualified: int = 150
    parameters: int = 80
    remarks: int = 40
    domain: int = 120
    exact_name: int = 150
    expansion_penalty: int = 30


@dataclass(frozen=True)
class ScoringInput:
    function_id: int
    name: str
    qualified_c: str
    qualified_py: str
    parameters: List[str]
    remarks: List[str]
    section: str
    fts_rank: int
    matched_fields: Dict[str, Set[str]]
    domain_hits: Set[str]
    expansion_matches: int


@dataclass(frozen=True)
class ScoreBreakdown:
    total: int
    components: Dict[str, int]
    order_key: Tuple[int, int, str, int]


def tokenize_query(query: str) -> List[str]:
    normalized = normalize_for_index(query)
    if not normalized:
        return []
    return normalized.split()


def score_candidate(query: str, candidate: ScoringInput, weights: ScoringWeights | None = None) -> ScoreBreakdown:
    weights = weights or ScoringWeights()
    components: Dict[str, int] = {}
    tokens = tokenize_query(query)
    expansions = expand_query(tokens)

    base_score = max(0, weights.base - candidate.fts_rank * weights.decay)
    components["fts_rank"] = base_score

    name_matches = candidate.matched_fields.get("name", set())
    name_score = weights.name * len(name_matches)
    if _is_exact_match(candidate.name, tokens):
        name_score += weights.exact_name
    if name_score:
        components["name"] = name_score

    qualified_matches = candidate.matched_fields.get("qualified", set())
    qualified_score = weights.qualified * len(qualified_matches)
    if qualified_score:
        components["qualified"] = qualified_score

    param_matches = candidate.matched_fields.get("parameters", set())
    param_score = weights.parameters * len(param_matches)
    if param_score:
        components["parameters"] = param_score

    remark_matches = candidate.matched_fields.get("remarks", set())
    remark_score = weights.remarks * len(remark_matches)
    if remark_score:
        components["remarks"] = remark_score

    domain_intersection = candidate.domain_hits.intersection(_domains_from_expansions(expansions))
    if domain_intersection:
        components["domain"] = weights.domain * len(domain_intersection)

    if candidate.expansion_matches:
        components["expansion_penalty"] = -weights.expansion_penalty * candidate.expansion_matches

    total = sum(components.values())
    order_key = (-total, candidate.fts_rank, candidate.name.lower(), candidate.function_id)
    return ScoreBreakdown(total=total, components=components, order_key=order_key)


def _is_exact_match(name: str, tokens: Iterable[str]) -> bool:
    normalized_name = normalize_for_index(name)
    query_string = " ".join(tokens)
    return normalized_name == query_string and normalized_name != ""


def _domains_from_expansions(expansions: Dict[str, Set[str]]) -> Set[str]:
    domain_map = group_by_domain()
    detected: Set[str] = set()
    for domain_name, canonical_terms in domain_map.items():
        canonical_set = set(canonical_terms)
        for expansion_set in expansions.values():
            if expansion_set & canonical_set:
                detected.add(domain_name)
                break
    return detected
