from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class CodeUnit:
    address: int
    display: str
    opcodes: Tuple[int, ...]
    comment: str | None = None
    label: str | None = None
    references: Tuple[Tuple[str, int, int], ...] = ()

    def to_dict(self) -> dict:
        return {
            "address": self.address,
            "display": self.display,
            "opcodes": list(self.opcodes),
            "comment": self.comment,
            "label": self.label,
            "references": [
                {"kind": kind, "target": target, "type": ref_type}
                for kind, target, ref_type in self.references
            ],
        }


@dataclass(frozen=True)
class SegmentRecord:
    name: str
    start: int
    end: int
    size: int
    permissions: int
    bitness: int
    alignment: int
    combination: int
    segment_type: int
    selector: int
    orgbase: int
    class_name: str
    preview: Tuple[int, ...]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "start": self.start,
            "end": self.end,
            "size": self.size,
            "permissions": self.permissions,
            "bitness": self.bitness,
            "alignment": self.alignment,
            "combination": self.combination,
            "segment_type": self.segment_type,
            "selector": self.selector,
            "orgbase": self.orgbase,
            "class_name": self.class_name,
            "preview": list(self.preview),
        }


@dataclass(frozen=True)
class FunctionRecord:
    start: int
    end: int
    name: str
    chunks: Tuple[Tuple[int, int], ...]
    units: Tuple[CodeUnit, ...]

    def to_dict(self) -> dict:
        return {
            "start": self.start,
            "end": self.end,
            "name": self.name,
            "chunks": [list(chunk) for chunk in self.chunks],
            "units": [unit.to_dict() for unit in self.units],
        }


@dataclass(frozen=True)
class StringRecord:
    address: int
    text: str
    encoding: str

    def to_dict(self) -> dict:
        return {
            "address": self.address,
            "text": self.text,
            "encoding": self.encoding,
        }


@dataclass(frozen=True)
class DataRecord:
    address: int
    name: str
    size: int
    payload: bytes
    references: Tuple[Tuple[str, int, int], ...]

    def to_dict(self) -> dict:
        return {
            "address": self.address,
            "name": self.name,
            "size": self.size,
            "payload": list(self.payload),
            "references": [
                {"kind": kind, "target": target, "type": ref_type}
                for kind, target, ref_type in self.references
            ],
        }


@dataclass(frozen=True)
class FixupRecord:
    address: int
    type: int | None
    length: int | None
    offset: int | None
    metadata: Tuple[Tuple[str, int | None], ...]

    def to_dict(self) -> dict:
        return {
            "address": self.address,
            "type": self.type,
            "length": self.length,
            "offset": self.offset,
            "metadata": [{ "key": key, "value": value } for key, value in self.metadata],
        }


@dataclass(frozen=True)
class ImportRecord:
    library: str
    name: str
    address: int
    references: Tuple[Tuple[str, int, int], ...]

    def to_dict(self) -> dict:
        return {
            "library": self.library,
            "name": self.name,
            "address": self.address,
            "references": [
                {"kind": kind, "target": target, "type": ref_type}
                for kind, target, ref_type in self.references
            ],
        }


@dataclass(frozen=True)
class ExportRecord:
    name: str
    address: int
    ordinal: int | None
    forwarded: str | None
    references: Tuple[Tuple[str, int, int], ...]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "address": self.address,
            "ordinal": self.ordinal,
            "forwarded": self.forwarded,
            "references": [
                {"kind": kind, "target": target, "type": ref_type}
                for kind, target, ref_type in self.references
            ],
        }


@dataclass(frozen=True)
class NameRecord:
    address: int
    name: str
    kind: str

    def to_dict(self) -> dict:
        return {"address": self.address, "name": self.name, "kind": self.kind}


@dataclass(frozen=True)
class TypeRecord:
    name: str
    kind: str
    declaration: str

    def to_dict(self) -> dict:
        return {"name": self.name, "kind": self.kind, "declaration": self.declaration}


@dataclass(frozen=True)
class StructMemberRecord:
    name: str
    type: str | None
    offset: int
    size: int
    flag: int
    comment: str | None
    repeatable_comment: str | None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "offset": self.offset,
            "size": self.size,
            "flag": self.flag,
            "comment": self.comment,
            "repeatable_comment": self.repeatable_comment,
        }


@dataclass(frozen=True)
class StructureRecord:
    name: str
    flags: int
    members: Tuple[StructMemberRecord, ...]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "flags": self.flags,
            "members": [member.to_dict() for member in self.members],
        }
