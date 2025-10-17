from __future__ import annotations

from typing import Iterable, Tuple

import idb
import idb.analysis as analysis
import idb.idapython as idapython

from .disasm import Disassembler
from .functions import FunctionReader
from .names import NameResolver
from .data import DataScanner
from .records import (
    DataRecord,
    ExportRecord,
    FixupRecord,
    FunctionRecord,
    ImportRecord,
    NameRecord,
    SegmentRecord,
    StringRecord,
    StructureRecord,
    TypeRecord,
)
from .references import ReferenceResolver
from .segments import SegmentScanner, SegmentTable
from .strings import StringScanner
from .types import TypeScanner
from .globals import GlobalScanner
from .fixups import FixupScanner
from .structures import StructureScanner


class DatabaseParser:
    def __init__(self, path: str) -> None:
        self.path = path
        self.context = None
        self.database = None
        self.segment_table = None
        self.disassembler = None
        self.reader = None
        self.idainfo = None
        self.string_scanner = None
        self.name_resolver = None
        self.reference_resolver = None
        self.flags = None
        self.data_scanner = None
        self.api = None
        self.type_scanner = None
        self.global_scanner = None
        self.segment_scanner = None
        self.fixup_scanner = None
        self.structure_scanner = None

    def __enter__(self) -> "DatabaseParser":
        self.context = idb.from_file(self.path)
        self.database = self.context.__enter__()
        self.segment_table = SegmentTable(self.database)
        root = analysis.Root(self.database)
        self.idainfo = root.idainfo
        self.disassembler = Disassembler(self.idainfo.procname, self.database.wordsize, self.segment_table)
        self.reader = FunctionReader(self.database)
        self.string_scanner = StringScanner(self.segment_table)
        try:
            self.api = idapython.IDAPython(self.database)
        except Exception:
            self.api = None
        self.name_resolver = NameResolver(self.database, self.api)
        self.reference_resolver = ReferenceResolver(self.database)
        self.data_scanner = DataScanner(self.segment_table, self.name_resolver, self.reference_resolver)
        self.type_scanner = TypeScanner(self.database.til)
        self.global_scanner = GlobalScanner(self.database, self.api, self.name_resolver)
        self.segment_scanner = SegmentScanner(self.segment_table)
        self.fixup_scanner = FixupScanner(self.database)
        self.structure_scanner = StructureScanner(self.database)
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self.context is not None:
            self.context.__exit__(exc_type, exc_value, traceback)
        self.data_scanner = None
        self.reference_resolver = None
        self.name_resolver = None
        self.string_scanner = None
        self.reader = None
        self.disassembler = None
        self.segment_table = None
        self.database = None
        self.context = None
        self.api = None
        self.type_scanner = None
        self.global_scanner = None
        self.segment_scanner = None
        self.fixup_scanner = None
        self.structure_scanner = None

    def functions(self) -> Iterable[FunctionRecord]:
        for start, end, name, chunks in self.reader.entries():
            units = self.disassembler.decode(
                chunks,
                self.reader.comments,
                self.reader.repeatable_comments,
                self.name_resolver.resolve if self.name_resolver else None,
                self.reference_resolver.outgoing if self.reference_resolver else None,
            )
            yield FunctionRecord(
                start=start,
                end=end,
                name=name,
                chunks=chunks,
                units=units,
            )

    def strings(self) -> Iterable[StringRecord]:
        for record in self.string_scanner.scan():
            yield record

    def data(self) -> Iterable[DataRecord]:
        for record in self.data_scanner.scan():
            yield record

    def names(self) -> Iterable[NameRecord]:
        seen = set()

        def emit(kind: str, address: int, name: str):
            if not name:
                return
            key = (kind, address, name)
            if key in seen:
                return
            seen.add(key)
            yield NameRecord(address=address, name=name, kind=kind)

        for start, end, label, _ in self.reader.entries():
            label = label or f"sub_{start:016X}"
            for record in emit("function", start, label):
                yield record

        for data_record in self.data_scanner.scan():
            for record in emit("data", data_record.address, data_record.name):
                yield record

        for entry in analysis.enumerate_imports(self.database):
            label = f"{entry.library}!{entry.function_name}"
            for record in emit("import", entry.function_address, label):
                yield record

        for entry in analysis.enumerate_entrypoints(self.database):
            for record in emit("export", entry.address, entry.name):
                yield record
        if self.global_scanner is not None:
            for record in self.global_scanner.scan():
                for item in emit(record.kind, record.address, record.name):
                    yield item

    def imports(self) -> Iterable[ImportRecord]:
        if self.reference_resolver is None:
            resolver = lambda _addr: ()
        else:
            resolver = self.reference_resolver.incoming
        for entry in analysis.enumerate_imports(self.database):
            references = resolver(entry.function_address)
            yield ImportRecord(
                library=entry.library,
                name=entry.function_name,
                address=entry.function_address,
                references=references,
            )

    def exports(self) -> Iterable[ExportRecord]:
        if self.reference_resolver is None:
            resolver = lambda _addr: ()
        else:
            resolver = self.reference_resolver.incoming
        for entry in analysis.enumerate_entrypoints(self.database):
            references = resolver(entry.address)
            yield ExportRecord(
                name=entry.name,
                address=entry.address,
                ordinal=entry.ordinal,
                forwarded=entry.forwarded_symbol,
                references=references,
            )

    def globals(self) -> Iterable[NameRecord]:
        if self.global_scanner is None:
            return
        for record in self.global_scanner.scan():
            yield record

    def segments(self) -> Iterable[SegmentRecord]:
        if self.segment_scanner is None:
            return
        for record in self.segment_scanner.scan():
            yield record

    def fixups(self) -> Iterable[FixupRecord]:
        if self.fixup_scanner is None:
            return
        for record in self.fixup_scanner.scan():
            yield record

    def structures(self) -> Iterable[StructureRecord]:
        if self.structure_scanner is None:
            return
        for record in self.structure_scanner.scan():
            yield record

    def types(self) -> Iterable[TypeRecord]:
        if self.type_scanner is None:
            return
        for record in self.type_scanner.scan():
            yield record


class FunctionExtractor:
    def __init__(self, path: str) -> None:
        self.path = path

    def collect(self, limit: int | None = None) -> Tuple[FunctionRecord, ...]:
        with DatabaseParser(self.path) as parser:
            result = []
            for record in parser.functions():
                result.append(record)
                if limit is not None and len(result) >= limit:
                    break
            return tuple(result)


class StringExtractor:
    def __init__(self, path: str) -> None:
        self.path = path

    def collect(self, limit: int | None = None) -> Tuple[StringRecord, ...]:
        with DatabaseParser(self.path) as parser:
            result = []
            for record in parser.strings():
                result.append(record)
                if limit is not None and len(result) >= limit:
                    break
            return tuple(result)


class DataExtractor:
    def __init__(self, path: str) -> None:
        self.path = path

    def collect(self, limit: int | None = None) -> Tuple[DataRecord, ...]:
        with DatabaseParser(self.path) as parser:
            result = []
            for record in parser.data():
                result.append(record)
                if limit is not None and len(result) >= limit:
                    break
            return tuple(result)


class ImportExtractor:
    def __init__(self, path: str) -> None:
        self.path = path

    def collect(self, limit: int | None = None) -> Tuple[ImportRecord, ...]:
        with DatabaseParser(self.path) as parser:
            result = []
            for record in parser.imports():
                result.append(record)
                if limit is not None and len(result) >= limit:
                    break
            return tuple(result)


class ExportExtractor:
    def __init__(self, path: str) -> None:
        self.path = path

    def collect(self, limit: int | None = None) -> Tuple[ExportRecord, ...]:
        with DatabaseParser(self.path) as parser:
            result = []
            for record in parser.exports():
                result.append(record)
                if limit is not None and len(result) >= limit:
                    break
            return tuple(result)


class NameExtractor:
    def __init__(self, path: str) -> None:
        self.path = path

    def collect(self, limit: int | None = None) -> Tuple[NameRecord, ...]:
        with DatabaseParser(self.path) as parser:
            result = []
            for record in parser.names():
                result.append(record)
                if limit is not None and len(result) >= limit:
                    break
            return tuple(result)


class GlobalExtractor:
    def __init__(self, path: str) -> None:
        self.path = path

    def collect(self, limit: int | None = None) -> Tuple[NameRecord, ...]:
        with DatabaseParser(self.path) as parser:
            result = []
            for record in parser.globals():
                result.append(record)
                if limit is not None and len(result) >= limit:
                    break
            return tuple(result)


class SegmentExtractor:
    def __init__(self, path: str) -> None:
        self.path = path

    def collect(self, limit: int | None = None) -> Tuple[SegmentRecord, ...]:
        with DatabaseParser(self.path) as parser:
            result = []
            for record in parser.segments():
                result.append(record)
                if limit is not None and len(result) >= limit:
                    break
            return tuple(result)


class FixupExtractor:
    def __init__(self, path: str) -> None:
        self.path = path

    def collect(self, limit: int | None = None) -> Tuple[FixupRecord, ...]:
        with DatabaseParser(self.path) as parser:
            result = []
            for record in parser.fixups():
                result.append(record)
                if limit is not None and len(result) >= limit:
                    break
            return tuple(result)


class StructureExtractor:
    def __init__(self, path: str) -> None:
        self.path = path

    def collect(self, limit: int | None = None) -> Tuple[StructureRecord, ...]:
        with DatabaseParser(self.path) as parser:
            result = []
            for record in parser.structures():
                result.append(record)
                if limit is not None and len(result) >= limit:
                    break
            return tuple(result)


class TypeExtractor:
    def __init__(self, path: str) -> None:
        self.path = path

    def collect(self, limit: int | None = None) -> Tuple[TypeRecord, ...]:
        with DatabaseParser(self.path) as parser:
            result = []
            for record in parser.types():
                result.append(record)
                if limit is not None and len(result) >= limit:
                    break
            return tuple(result)
