from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .config import DEFAULT_ENV
from .scoring import ScoringInput, ScoringWeights, ScoreBreakdown, score_candidate
from .text_utils import normalize_for_index, generate_char_ngrams
from .vocabulary import group_by_domain
from .vocabulary import expand_query


app = FastAPI(title="SAP2000 MCP API")


# Simple connection manager
class DB:
    conn: Optional[sqlite3.Connection] = None


def connect() -> sqlite3.Connection:
    if DB.conn is None:
        path = DEFAULT_ENV.work_dir / "db" / "sap2000_mcp.db"
        DB.conn = sqlite3.connect(str(path))
        DB.conn.row_factory = sqlite3.Row
    return DB.conn


@app.on_event("shutdown")
def _close() -> None:
    if DB.conn is not None:
        DB.conn.close()
        DB.conn = None


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


class FindFunctionsRequest(BaseModel):
    q: str
    top_k: int = 10
    verb_intent: Optional[str] = None
    expand_level: Optional[str] = None
    domain_hints: Optional[List[str]] = None
    explain: bool = True


class FindFunctionResult(BaseModel):
    function_id: int
    name: str
    section: Optional[str]
    qualified_c: Optional[str]
    qualified_py: Optional[str]
    score: int
    src_path: Optional[str]
    expansion_used: List[str]
    match_fields: List[str]
    sentence_snippets: List[str]
    scoring: Dict[str, int]


class FindFunctionsResponse(BaseModel):
    results: List[FindFunctionResult]


@app.post("/find_functions", response_model=FindFunctionsResponse)
def find_functions(req: FindFunctionsRequest) -> FindFunctionsResponse:
    query = req.q.strip()
    if not query:
        return FindFunctionsResponse(results=[])

    tokens = _tokenize(query)
    if (req.expand_level or "expanded").lower() == "literal":
        expansions = {t: {t} for t in tokens}
    else:
        expansions = expand_query(tokens)
    fts_query = _build_fts_query(expansions)

    rows = _search_candidates(fts_query, limit=max(200, req.top_k * 10))
    if not rows:
        return FindFunctionsResponse(results=[])

    results: List[Tuple[int, Dict[str, int], sqlite3.Row, Dict[str, Set[str]], Set[str], int]] = []
    for rank, row in enumerate(rows):
        matched_fields, expansion_used = _calc_matches(row, tokens, expansions)
        candidate = ScoringInput(
            function_id=row["id"],
            name=row["name"],
            qualified_c=row["qualified_c"] or "",
            qualified_py=row["qualified_py"] or "",
            parameters=(row["parameters_text"] or "").split(),
            remarks=(row["remarks"] or "").split(". "),
            section=row["section"] or "",
            fts_rank=rank,
            matched_fields=matched_fields,
            domain_hits=set(req.domain_hints or []),
            expansion_matches=len(expansion_used),
        )
        breakdown = score_candidate(query, candidate, ScoringWeights())
        components = dict(breakdown.components)
        intent = (req.verb_intent or "").lower().strip()
        boost = _intent_boost(intent, row["name"], row["qualified_c"] or "", row["qualified_py"] or "")
        if boost:
            components["intent"] = boost
        # Domain hint boost: candidate 텍스트에서 감지된 도메인과 요청 힌트 교집합
        detected_domains = _detect_domains(row)
        hint_set = set(req.domain_hints or [])
        domain_boost = 120 * len(detected_domains & hint_set) if hint_set else 0
        if domain_boost:
            components["domain_hint"] = domain_boost
        total = breakdown.total + boost
        total += domain_boost
        results.append((total, components, row, matched_fields, expansion_used, rank))

    # Sort by our deterministic order key
    results.sort(key=lambda r: (-r[0], r[5], (r[2]["name"] or "").lower(), r[2]["id"]))

    top: List[FindFunctionResult] = []
    for total, components, row, matched_fields, expansion_used, _ in results[: req.top_k]:
        snippets = _extract_snippets(row["remarks"] or "", tokens)
        top.append(
            FindFunctionResult(
                function_id=row["id"],
                name=row["name"],
                section=row["section"],
                qualified_c=row["qualified_c"],
                qualified_py=row["qualified_py"],
                score=total,
                src_path=row["src_path"],
                expansion_used=sorted(list(expansion_used)),
                match_fields=sorted(list(matched_fields.keys())),
                sentence_snippets=snippets,
                scoring=components,
            )
        )

    return FindFunctionsResponse(results=top)


class ToPythonRequest(BaseModel):
    function_id: int
    policy: str = "tuple_ret"
    binding_mode: str = "direct"


class ToPythonResponse(BaseModel):
    function_id: int
    qualified_py: str
    signature: str
    call_snippet: str
    hints: str
    params: List[Dict[str, Any]]
    returns: List[Dict[str, Any]]
    src_path: Optional[str]


@app.post("/to_python", response_model=ToPythonResponse)
def to_python(req: ToPythonRequest) -> ToPythonResponse:
    row = _get_function(req.function_id)
    if row is None:
        raise HTTPException(status_code=404, detail="function not found")
    params = _get_parameters(req.function_id)

    out_params = [p for p in params if p["direction"] in ("out", "inout")]
    ret_names = ["ret"] + [p["name"] or p["clr_name"] for p in out_params]
    args = ", ".join([p["name"] or p["clr_name"] for p in params if p["direction"] != "out"]) or ""
    qualified_py = row["qualified_py"] or _fallback_py(row)
    method_name = qualified_py.split(".")[-1]
    section = _infer_section(row, qualified_py)
    if (req.binding_mode or "direct").lower() == "typed_wrapper" and section:
        wrapper = f"SAP2000v1.{section}(sap_model.{section[1:]})"
        qualified_py = f"{wrapper}.{method_name}"
    signature = f"{', '.join(ret_names)} = {qualified_py}({args})"

    hint_lines = [
        "# Requires: from System import Array, String, Boolean, Double",
        "class Sap2000CallError(Exception): pass",
        "if ret != 0: raise Sap2000CallError('call failed')",
    ]
    array_outs = [p for p in out_params if p["is_array"]]
    if array_outs:
        names = ", ".join([p["name"] or p["clr_name"] for p in array_outs])
        hint_lines.append(f"# Convert .NET arrays to Python lists: {names} = list({names})")
    enum_params = [p for p in params if p["is_enum"]]
    enum_types = sorted({(p["base_type"] or "") for p in enum_params if isinstance(p["base_type"], str) and "SAP2000v1." in p["base_type"]})
    if enum_types:
        hint_lines.append("# Enum parameters: use SAP2000v1.<EnumType>.<Member>, e.g., " + ", ".join(enum_types[:3]))
    returns = [{"name": "ret", "kind": "code"}] + [
        {"name": p["name"] or p["clr_name"], "kind": p["direction"], "base_type": p["base_type"]}
        for p in out_params
    ]

    # Build call_snippet with error check and conversions
    convert_lines: List[str] = []
    if array_outs:
        for p in array_outs:
            nm = p["name"] or p["clr_name"]
            convert_lines.append(f"{nm} = list({nm})")

    call_block = "\n".join([signature, "if ret != 0: raise Sap2000CallError('call failed')", *convert_lines])

    return ToPythonResponse(
        function_id=req.function_id,
        qualified_py=qualified_py,
        signature=signature,
        call_snippet=call_block,
        hints="\n".join(hint_lines),
        params=[dict(p) for p in params],
        returns=returns,
        src_path=row["src_path"],
    )


class RenderHintRequest(BaseModel):
    function_id: int


class RenderHintResponse(BaseModel):
    header: str
    body: str


@app.post("/render_hint", response_model=RenderHintResponse)
def render_hint(req: RenderHintRequest) -> RenderHintResponse:
    row = _get_function(req.function_id)
    if row is None:
        raise HTTPException(status_code=404, detail="function not found")
    header = (
        "# import: from System import Array, String, Boolean, Double\n"
        "# sap_model: cSapModel instance required\n"
        "# errors: raise Sap2000CallError on non-zero ret"
    )
    body = f"# call: {row['qualified_py'] or _fallback_py(row)}"
    return RenderHintResponse(header=header, body=body)


# Helpers
def _tokenize(text: str) -> List[str]:
    n = normalize_for_index(text)
    return [t for t in n.split() if t]


def _build_fts_query(expansions: Dict[str, Set[str]]) -> str:
    terms: List[str] = []
    for token, exps in expansions.items():
        group = " OR ".join(_quote_fts(t) for t in sorted(exps | {token}))
        terms.append(f"({group})")
    return " AND ".join(terms) if terms else ""


def _quote_fts(term: str) -> str:
    # Use raw token for FTS5 term search
    return term


def _search_candidates(fts_query: str, limit: int) -> List[sqlite3.Row]:
    conn = connect()
    # Two-step to avoid MATCH context issues and preserve rank
    ids: List[int] = []
    if fts_query:
        cur = conn.execute("SELECT rowid FROM fts WHERE fts MATCH ? LIMIT ?", (fts_query, limit))
        ids = [r[0] for r in cur.fetchall()]
    else:
        cur = conn.execute("SELECT rowid FROM fts LIMIT ?", (limit,))
        ids = [r[0] for r in cur.fetchall()]

    # Fallback via 3-gram grams if too few ids
    if len(ids) == 0 and fts_query:
        # derive grams from query
        raw = fts_query.replace('(', ' ').replace(')', ' ').replace('AND', ' ').replace('OR', ' ')
        grams = generate_char_ngrams(normalize_for_index(raw), 3)[:5]
        if grams:
            where = " OR ".join(["grams LIKE ?" for _ in grams])
            params = tuple([f"%{g}%" for g in grams])
            cur = conn.execute(f"SELECT rowid, grams FROM fts_gram WHERE {where} LIMIT ?", params + (limit,))
            scored: List[Tuple[int, int]] = []
            for rid, gtxt in cur.fetchall():
                score = sum(1 for g in grams if g in (gtxt or ""))
                if score > 0:
                    scored.append((rid, score))
            scored.sort(key=lambda x: (-x[1], x[0]))
            ids = [rid for rid, _ in scored[:limit]]

    rows: List[sqlite3.Row] = []
    for rid in ids:
        cur = conn.execute(
            (
                "SELECT f.id, f.name, f.section, f.qualified_c, f.qualified_py, f.src_path, f.reflection_status, "
                "fts.signatures, fts.parameters_text, fts.remarks, fts.release_notes "
                "FROM fts JOIN functions f ON f.id = fts.rowid "
                "WHERE f.id = ? AND (f.reflection_status IS NULL OR f.reflection_status != 'missing')"
            ),
            (rid,),
        )
        r = cur.fetchone()
        if r:
            rows.append(r)
            if len(rows) >= limit:
                break
    return rows


def _calc_matches(
    row: sqlite3.Row, tokens: List[str], expansions: Dict[str, Set[str]]
) -> Tuple[Dict[str, Set[str]], Set[str]]:
    matched: Dict[str, Set[str]] = {"name": set(), "qualified": set(), "parameters": set(), "remarks": set()}
    expansion_used: Set[str] = set()
    fields = {
        "name": row["name"] or "",
        "qualified": " ".join([row["qualified_c"] or "", row["qualified_py"] or ""]),
        "parameters": row["parameters_text"] or "",
        "remarks": " ".join([(row["remarks"] or ""), (row["release_notes"] or "")]),
    }
    for token in tokens:
        target = token
        exps = expansions.get(token, set())
        for field_name, text in fields.items():
            norm = normalize_for_index(text)
            if target in norm:
                matched[field_name].add(token)
            else:
                for e in exps:
                    if e and e in norm:
                        matched[field_name].add(token)
                        expansion_used.add(token)
                        break
    # remove empty
    matched = {k: v for k, v in matched.items() if v}
    return matched, expansion_used


def _extract_snippets(remarks: str, tokens: List[str]) -> List[str]:
    sentences = [s.strip() for s in remarks.split(".") if s.strip()]
    out: List[str] = []
    for s in sentences:
        n = normalize_for_index(s)
        if any(t in n for t in tokens):
            out.append(_highlight_tokens(s, tokens))
        if len(out) >= 2:
            break
    return out


def _highlight_tokens(text: str, tokens: List[str]) -> str:
    # 간단한 토큰 하이라이트(대소문자 무시), 원문 보존
    import re

    highlighted = text
    # 긴 토큰 우선 하이라이트
    for token in sorted({t for t in tokens if t}, key=len, reverse=True):
        try:
            pattern = re.compile(re.escape(token), re.IGNORECASE)
            highlighted = pattern.sub(lambda m: f"<em>{m.group(0)}</em>", highlighted)
        except re.error:
            continue
    return highlighted


def _intent_boost(intent: str, name: str, qualified_c: str, qualified_py: str) -> int:
    if not intent:
        return 0
    text = " ".join([name or "", qualified_c or "", qualified_py or ""]).lower()
    reads = ("get", "is", "has")
    writes = ("set", "add", "create", "delete", "remove", "update", "assign", "define", "move")
    if intent == "read":
        return 120 if any(w in text for w in reads) else 0
    if intent == "write":
        return 120 if any(w in text for w in writes) else 0
    return 0


def _infer_section(row: sqlite3.Row, qualified_py: str) -> Optional[str]:
    # Prefer reflected section name like 'cPointObj'
    sec = row["section"]
    if sec and isinstance(sec, str) and sec.startswith("c"):
        return sec
    # Fallback: derive from qualified_c
    qc = row["qualified_c"] or ""
    if qc:
        parts = qc.split(".")
        if len(parts) == 2:
            # parts[0] should be like 'cPointObj'
            return parts[0] if parts[0].startswith("c") else None
    return None


def _get_function(fid: int) -> Optional[sqlite3.Row]:
    conn = connect()
    cur = conn.execute(
        "SELECT * FROM functions WHERE id = ?",
        (fid,),
    )
    return cur.fetchone()


def _get_parameters(fid: int) -> List[sqlite3.Row]:
    conn = connect()
    cur = conn.execute(
        "SELECT name, description, direction, clr_name, base_type, is_array, is_enum, is_optional, position "
        "FROM parameters WHERE function_id = ? ORDER BY position ASC",
        (fid,),
    )
    return list(cur.fetchall())


def _fallback_py(row: sqlite3.Row) -> str:
    if row["qualified_c"]:
        parts = row["qualified_c"].split(".")
        if len(parts) == 2:
            return f"sap_model.{parts[0]}.{parts[1]}"
    return "sap_model.?.?"


def _detect_domains(row: sqlite3.Row) -> Set[str]:
    # 후보 텍스트에서 도메인 추정(시소러스 canonical 토큰 기반)
    domain_map = group_by_domain()
    text = " ".join([
        row["name"] or "",
        row["qualified_c"] or "",
        row["qualified_py"] or "",
        row["section"] or "",
        row["parameters_text"] or "",
        row["remarks"] or "",
        row["release_notes"] or "",
    ])
    norm = normalize_for_index(text)
    hits: Set[str] = set()
    for domain, canonicals in domain_map.items():
        for c in canonicals:
            if c in norm:
                hits.add(domain)
                break
    return hits
