from __future__ import annotations

import functools
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

import clr  # type: ignore
from System.Reflection import Assembly, BindingFlags, MethodInfo, ParameterInfo, PropertyInfo, FieldInfo  # type: ignore

from .config import DEFAULT_ENV, EnvironmentConfig

logger = logging.getLogger(__name__)

PUBLIC_INSTANCE = BindingFlags.Public | BindingFlags.Instance
PUBLIC_IGNORE_CASE = PUBLIC_INSTANCE | BindingFlags.IgnoreCase


@functools.lru_cache(maxsize=1)
def _load_assembly(env: EnvironmentConfig = DEFAULT_ENV) -> Assembly:
    dll_path = env.dll_path
    if not dll_path.exists():
        raise FileNotFoundError(f"SAP2000 API DLL not found at {dll_path}")
    clr.AddReference(str(dll_path))
    import SAP2000v1  # type: ignore

    return Assembly.GetAssembly(SAP2000v1.cSapModel)  # type: ignore[attr-defined]


ROOT_SEGMENT_MAP = {
    "sapobject": ("SAP2000v1.cOAPI", "sap_object"),
    "helper": ("SAP2000v1.cHelper", "helper"),
}

SEGMENT_ALIAS_MAP = {
    "sapmodel": "SapModel",
    "sapmdel": "SapModel",
    "sapmoel": "SapModel",
    "sap2000": "SapModel",
    "namedsets": "NamedSet",
}

METHOD_ALIAS_MAP = {
    "getloaddistributedwthguid": "GetLoadDistributedWithGUID",
}

METHOD_SUFFIXES = ("_1", "_2", "_3", "_4")


@dataclass(slots=True)
class SyntaxPath:
    raw: str
    segments: List[str]
    method_name: str
    chain_segments: List[str]
    root_type_name: str
    python_root: str


def parse_syntax_path(syntax: str) -> Optional[SyntaxPath]:
    raw = syntax.strip()
    if not raw:
        return None
    raw_segments = [part.strip() for part in raw.split(".") if part.strip()]
    if not raw_segments:
        return None
    segments = [_normalize_segment(part) for part in raw_segments]
    if not segments:
        return None
    method_name = segments[-1]
    chain = segments[:-1]

    root_key = segments[0].lower()
    root_type_name, python_root = ROOT_SEGMENT_MAP.get(root_key, ("SAP2000v1.cSapModel", "sap_model"))

    chain_segments = chain
    if root_key in ROOT_SEGMENT_MAP:
        chain_segments = chain[1:]

    if root_type_name == "SAP2000v1.cOAPI" and chain_segments:
        first = chain_segments[0]
        if first != "SapModel":
            chain_segments = ["SapModel"] + chain_segments

    if root_type_name == "SAP2000v1.cSapModel" and chain_segments and chain_segments[0] == "SapModel":
        chain_segments = chain_segments[1:]

    return SyntaxPath(
        raw=raw,
        segments=segments,
        method_name=method_name,
        chain_segments=chain_segments,
        root_type_name=root_type_name,
        python_root=python_root,
    )


@dataclass(slots=True)
class ParameterMetadata:
    doc_name: Optional[str]
    doc_description: Optional[str]
    clr_name: str
    direction: str
    parameter_type: str
    base_type: str
    is_array: bool
    is_enum: bool
    is_optional: bool


@dataclass(slots=True)
class MethodMetadata:
    type_full_name: str
    type_name: str
    method_name: str
    qualified_c: str
    qualified_py: str
    returns_code: bool
    parameters: List[ParameterMetadata]
    return_type: str
    doc_parameters_count: int
    reflected_parameters_count: int


class ReflectionResolutionError(RuntimeError):
    """Raised when a function cannot be resolved via reflection."""


def enrich_from_reflection(
    syntax_lines: Iterable[str],
    doc_parameters: Iterable[dict],
    env: EnvironmentConfig = DEFAULT_ENV,
) -> MethodMetadata:
    doc_params_list = list(doc_parameters)
    syntax_line = next(iter(syntax_lines), "")
    path = parse_syntax_path(syntax_line)
    if path is None:
        raise ReflectionResolutionError("Unable to parse syntax path")

    assembly = _load_assembly(env)
    target_type = assembly.GetType(path.root_type_name)
    if target_type is None:
        raise ReflectionResolutionError(f"Unable to resolve root type {path.root_type_name}")

    for segment in path.chain_segments:
        next_type = _resolve_child_type(target_type, segment)
        if next_type is None:
            raise ReflectionResolutionError(
                f"Unable to resolve child segment '{segment}' on type {target_type.FullName}"
            )
        target_type = next_type

    method = _resolve_method(target_type, path.method_name, doc_params_list)
    if method is None:
        raise ReflectionResolutionError(
            f"Unable to resolve method '{path.method_name}' on type {target_type.FullName}"
        )

    qualified_c = f"{target_type.Name}.{method.Name}"
    qualified_py = _build_python_qualified(path)
    parameters_meta = _build_parameter_metadata(method, doc_params_list)
    return MethodMetadata(
        type_full_name=target_type.FullName,
        type_name=target_type.Name,
        method_name=method.Name,
        qualified_c=qualified_c,
        qualified_py=qualified_py,
        returns_code=method.ReturnType.FullName == "System.Int32",
        parameters=parameters_meta,
        return_type=method.ReturnType.FullName,
        doc_parameters_count=len(doc_params_list),
        reflected_parameters_count=len(method.GetParameters()),
    )


def _build_python_qualified(path: SyntaxPath) -> str:
    segments = [path.python_root]
    segments.extend(path.chain_segments)
    segments.append(path.method_name)
    return ".".join(segments)


def _resolve_child_type(current_type, segment: str):
    normalized = _normalize_segment(segment)
    if normalized.lower() in {"sap2000", "sapmoel"}:
        return current_type
    if normalized.lower() == "sapmodel" and current_type.FullName != "SAP2000v1.cOAPI":
        return current_type

    for candidate in _segment_variants(normalized):
        prop = current_type.GetProperty(candidate, PUBLIC_IGNORE_CASE)
        if isinstance(prop, PropertyInfo):
            return prop.PropertyType
        field = current_type.GetField(candidate, PUBLIC_IGNORE_CASE)
        if isinstance(field, FieldInfo):
            return field.FieldType
        method = current_type.GetMethod(candidate, PUBLIC_IGNORE_CASE)
        if isinstance(method, MethodInfo) and len(method.GetParameters()) == 0:
            return method.ReturnType
    return None


def _segment_variants(segment: str) -> List[str]:
    variants = [segment]
    if segment.startswith("c") and len(segment) > 1 and segment[1].isupper():
        variants.append(segment[1:])
    if "_" in segment:
        variants.append(segment.replace("_", ""))
    if " " in segment:
        variants.append(segment.replace(" ", ""))
    return list(dict.fromkeys(variants))


def _find_method_candidates(target_type, method_name: str) -> List[MethodInfo]:
    lowered = method_name.lower()
    return [
        m
        for m in target_type.GetMethods(PUBLIC_IGNORE_CASE)
        if m.Name.lower() == lowered
    ]


def _resolve_method(target_type, method_name: str, doc_parameters: Iterable[dict]) -> Optional[MethodInfo]:
    doc_params = list(doc_parameters)
    expected = len(doc_params)
    candidates = _find_method_candidates(target_type, method_name)
    if not candidates and method_name.endswith(METHOD_SUFFIXES):
        base_name = method_name.rsplit("_", 1)[0]
        candidates = _find_method_candidates(target_type, base_name)
    if not candidates:
        alias = METHOD_ALIAS_MAP.get(method_name.lower())
        if alias:
            candidates = _find_method_candidates(target_type, alias)
    if not candidates:
        return None

    def method_score(mi: MethodInfo) -> tuple:
        params = mi.GetParameters()
        total = len(params)
        required = sum(0 if p.IsOptional else 1 for p in params)
        return (abs(total - expected), abs(required - expected), total)

    candidates.sort(key=method_score)
    return candidates[0]


def _build_parameter_metadata(method: MethodInfo, doc_parameters: List[dict]) -> List[ParameterMetadata]:
    metadata: List[ParameterMetadata] = []
    parameters = method.GetParameters()
    count = max(len(doc_parameters), len(parameters))
    for idx in range(count):
        doc_entry = doc_parameters[idx] if idx < len(doc_parameters) else None
        param = parameters[idx] if idx < len(parameters) else None
        if param is None:
            continue
        direction = _infer_direction(param, doc_entry)
        param_type = param.ParameterType
        base_type = param_type
        if param_type.IsByRef:
            base_type = param_type.GetElementType()
        if base_type is None:
            base_type = param_type
        array_element = base_type
        is_array = False
        if base_type.IsArray:
            is_array = True
            array_element = base_type.GetElementType()
        metadata.append(
            ParameterMetadata(
                doc_name=doc_entry.get("name") if doc_entry else None,
                doc_description=doc_entry.get("description") if doc_entry else None,
                clr_name=param.Name,
                direction=direction,
                parameter_type=str(param.ParameterType.FullName),
                base_type=str(array_element.FullName if array_element is not None else base_type.FullName),
                is_array=is_array,
                is_enum=bool(array_element.IsEnum if array_element is not None else base_type.IsEnum),
                is_optional=param.IsOptional,
            )
        )
    return metadata


def _infer_direction(param: ParameterInfo, doc_entry: Optional[dict]) -> str:
    if param.IsOut:
        return "out"
    if param.ParameterType.IsByRef:
        if doc_entry:
            desc = (doc_entry.get("description") or "").lower()
            if "returned item" in desc or desc.startswith("returns") or "output" in desc:
                return "out"
        return "inout"
    return "in"


def _normalize_segment(segment: str) -> str:
    cleaned = segment.strip()
    if not cleaned:
        return cleaned
    key = cleaned.lower().replace("_", "").replace(" ", "")
    if key in SEGMENT_ALIAS_MAP:
        return SEGMENT_ALIAS_MAP[key]
    if " " in cleaned:
        cleaned = cleaned.replace(" ", "")
    return cleaned
