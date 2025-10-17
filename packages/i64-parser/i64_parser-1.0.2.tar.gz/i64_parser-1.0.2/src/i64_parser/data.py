from __future__ import annotations

from typing import Iterable, Tuple

import idb.idapython as idapython

from .names import NameResolver
from .records import DataRecord
from .references import ReferenceResolver
from .segments import SegmentTable


class DataScanner:
    def __init__(
        self,
        segments: SegmentTable,
        names: NameResolver,
        references: ReferenceResolver,
    ) -> None:
        self.segments = segments
        self.names = names
        self.references = references
        self.flags = idapython.FLAGS
        self.exec_mask = idapython.idc.SEGPERM_EXEC
        self.preview = 64

    def scan(self) -> Iterable[DataRecord]:
        for segment in self.segments.entries:
            if segment.permissions & self.exec_mask:
                continue
            address = segment.start
            while address < segment.end:
                flag = segment.flag_value(address)
                if self._is_data(flag):
                    start = address
                    cursor = address
                    while cursor < segment.end and self._is_data(segment.flag_value(cursor)):
                        cursor += 1
                    size = cursor - start
                    full_payload = segment.slice_bytes(start, size)
                    references = self.references.incoming(start)
                    name = self.names.resolve(start)
                    if not name:
                        name = f"data_{start:016X}"
                    payload = full_payload[: self.preview]
                    yield DataRecord(
                        address=start,
                        name=name,
                        size=size,
                        payload=payload,
                        references=references,
                    )
                    address = cursor
                else:
                    address += 1

    def _is_data(self, flag: int) -> bool:
        cls = flag & self.flags.MS_CLS
        if cls in (0, self.flags.FF_CODE, self.flags.FF_TAIL):
            return False
        return True
