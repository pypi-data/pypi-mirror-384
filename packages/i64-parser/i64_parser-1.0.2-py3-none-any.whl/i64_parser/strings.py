from __future__ import annotations

from typing import Iterable

from .records import StringRecord
from .segments import SegmentData, SegmentTable


class StringScanner:
    def __init__(self, segments: SegmentTable, ascii_min: int = 5, utf16_min: int = 5) -> None:
        self.segments = segments
        self.ascii_min = ascii_min
        self.utf16_min = utf16_min

    def scan(self) -> Iterable[StringRecord]:
        for segment in self.segments.entries:
            for record in self._scan_segment(segment):
                yield record

    def _scan_segment(self, segment: SegmentData) -> Iterable[StringRecord]:
        ascii_records = self._scan_ascii(segment)
        utf16_records = self._scan_utf16(segment)
        yield from ascii_records
        yield from utf16_records

    def _scan_ascii(self, segment: SegmentData) -> Iterable[StringRecord]:
        data = segment.bytes_view
        limit = len(data)
        index = 0
        while index < limit:
            value = data[index]
            if self._is_ascii_byte(value):
                start = index
                end = index
                while end < limit and self._is_ascii_byte(data[end]):
                    end += 1
                if end - start >= self.ascii_min and end < limit and data[end] == 0 and self._is_string_flag(segment.flags[start]):
                    text = data[start:end].decode("ascii")
                    address = segment.start + start
                    yield StringRecord(address=address, text=text, encoding="ascii")
                    index = end + 1
                    continue
                index = start + 1
                continue
            index += 1

    def _scan_utf16(self, segment: SegmentData) -> Iterable[StringRecord]:
        data = segment.bytes_view
        limit = len(data)
        index = 0
        while index + 1 < limit:
            if self._is_ascii_byte(data[index]) and data[index + 1] == 0:
                start = index
                cursor = index
                while cursor + 1 < limit and self._is_ascii_byte(data[cursor]) and data[cursor + 1] == 0:
                    cursor += 2
                if cursor + 1 < limit and data[cursor] == 0 and data[cursor + 1] == 0:
                    length = (cursor - start) // 2
                    if length >= self.utf16_min and self._is_string_flag(segment.flags[start]):
                        text = data[start:cursor:2].decode("ascii")
                        address = segment.start + start
                        yield StringRecord(address=address, text=text, encoding="utf16")
                        index = cursor + 2
                        continue
                index = start + 2
                continue
            index += 1

    def _is_ascii_byte(self, value: int) -> bool:
        if 0x20 <= value <= 0x7E:
            return True
        if value in (0x09, 0x0A, 0x0D):
            return True
        return False

    def _is_string_flag(self, flag: int) -> bool:
        return (flag >> 28) == 5
