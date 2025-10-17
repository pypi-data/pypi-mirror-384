from __future__ import annotations

from typing import Iterable, Tuple

from .records import TypeRecord


class TypeScanner:
    def __init__(self, til) -> None:
        self.til = til

    def scan(self) -> Iterable[TypeRecord]:
        if self.til is None:
            return
        definitions = getattr(self.til, "types", None)
        if definitions is None:
            return
        entries = getattr(definitions, "defs", None)
        if not entries:
            return
        seen: set[Tuple[str, str, str]] = set()
        for definition in entries:
            tinfo = getattr(definition, "type", None)
            if tinfo is None or not hasattr(tinfo, "get_typestr"):
                continue
            kind = self._kind(tinfo)
            if kind is None:
                continue
            name = self._name(definition, tinfo, kind)
            if not name:
                continue
            declaration = tinfo.get_typestr().strip()
            if not declaration:
                continue
            key = (kind, name, declaration)
            if key in seen:
                continue
            seen.add(key)
            yield TypeRecord(name=name, kind=kind, declaration=declaration)

    def _kind(self, tinfo) -> str | None:
        if not hasattr(tinfo, "is_decl_typedef"):
            return None
        if tinfo.is_decl_typedef():
            return "typedef"
        if tinfo.is_decl_enum():
            return "enum"
        if tinfo.is_decl_union():
            return "union"
        if tinfo.is_decl_struct() or tinfo.is_decl_udt():
            return "struct"
        return None

    def _name(self, definition, tinfo, kind: str) -> str:
        name = getattr(definition, "name", "")
        if name:
            return name
        if kind == "typedef":
            try:
                ref = tinfo.get_refname()
            except Exception:
                ref = ""
            if ref and not ref.startswith("#"):
                return ref
        candidate = tinfo.get_name() if hasattr(tinfo, "get_name") else ""
        if candidate:
            return candidate
        ordinal = getattr(definition, "ordinal", None)
        if ordinal is not None:
            return f"#{ordinal}"
        return ""
