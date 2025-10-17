from __future__ import annotations

from array import array
from bisect import bisect_right
from dataclasses import dataclass
from typing import Iterable, List

import idb
import idb.analysis as analysis

from .records import SegmentRecord


@dataclass(frozen=True)
class SegmentData:
    name: str
    start: int
    end: int
    permissions: int
    bitness: int
    align: int
    comb: int
    type: int
    selector: int
    orgbase: int
    class_name: str
    flags: array
    bytes_view: bytes

    def slice_bytes(self, address: int, length: int) -> bytes:
        offset = address - self.start
        return self.bytes_view[offset : offset + length]

    def flag_value(self, address: int) -> int:
        offset = address - self.start
        return self.flags[offset]


class SegmentTable:
    def __init__(self, database: idb.fileformat.IDB) -> None:
        segments = analysis.Segments(database).segments
        names = analysis.SegStrings(database).strings
        entries: List[SegmentData] = []
        for start in sorted(segments.keys()):
            descriptor = segments[start]
            bounds = database.id1.get_segment(descriptor.startEA)
            length = descriptor.endEA - descriptor.startEA
            offset = bounds.offset
            raw = memoryview(database.id1.buffer)[offset : offset + length * 4]
            values = array("I")
            values.frombytes(raw)
            bytes_view = bytes(bytearray(value & 0xFF for value in values))
            if descriptor.name_index < len(names):
                segment_name = names[descriptor.name_index]
            else:
                segment_name = f"seg_{descriptor.startEA:08X}"
            if descriptor.sclass < len(names):
                class_name = names[descriptor.sclass]
            else:
                class_name = ""
            entries.append(
                SegmentData(
                    name=segment_name,
                    start=descriptor.startEA,
                    end=descriptor.endEA,
                    permissions=descriptor.perm,
                    bitness=descriptor.bitness,
                    align=descriptor.align,
                    comb=descriptor.comb,
                    type=descriptor.type,
                    selector=descriptor.sel,
                    orgbase=descriptor.orgbase,
                    class_name=class_name,
                    flags=values,
                    bytes_view=bytes_view,
                )
            )
        self.entries = entries
        self.starts = [segment.start for segment in entries]

    def locate(self, address: int) -> SegmentData:
        index = bisect_right(self.starts, address) - 1
        if index < 0:
            raise KeyError(address)
        segment = self.entries[index]
        if address >= segment.end:
            raise KeyError(address)
        return segment

    def slice(self, address: int, length: int) -> bytes:
        segment = self.locate(address)
        if address + length > segment.end:
            raise IndexError(address)
        return segment.slice_bytes(address, length)

    def flag(self, address: int) -> int:
        segment = self.locate(address)
        return segment.flag_value(address)


class SegmentScanner:
    def __init__(self, segments: SegmentTable) -> None:
        self.segments = segments

    def scan(self) -> Iterable[SegmentRecord]:
        for segment in self.segments.entries:
            yield SegmentRecord(
                name=segment.name,
                start=segment.start,
                end=segment.end,
                size=segment.end - segment.start,
                permissions=segment.permissions,
                bitness=segment.bitness,
                alignment=segment.align,
                combination=segment.comb,
                segment_type=segment.type,
                selector=segment.selector,
                orgbase=segment.orgbase,
                class_name=segment.class_name,
                preview=tuple(segment.bytes_view[:64]),
            )
