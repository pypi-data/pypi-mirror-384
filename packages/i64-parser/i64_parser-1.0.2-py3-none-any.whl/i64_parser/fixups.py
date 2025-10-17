from __future__ import annotations

from typing import Iterable, Tuple

import idb.analysis as analysis

from .records import FixupRecord


class FixupScanner:
    def __init__(self, database) -> None:
        self.database = database

    def scan(self) -> Iterable[FixupRecord]:
        try:
            mapping = analysis.Fixups(self.database).fixups
        except Exception:
            return
        if not mapping:
            return
        for address, entry in sorted(mapping.items()):
            yield self._build_record(address, entry)

    def _build_record(self, address, entry) -> FixupRecord:
        fixup_type = self._as_int(getattr(entry, "type", None))
        length = None
        if hasattr(entry, "get_fixup_length"):
            try:
                length = entry.get_fixup_length()
            except Exception:
                length = None
        offset = self._as_int(getattr(entry, "offset", None))
        metadata = []
        for key in dir(entry):
            if key.startswith("_"):
                continue
            if key in ("offset", "type", "get_fixup_length"):
                continue
            value = getattr(entry, key)
            if callable(value):
                continue
            metadata.append((key, self._as_int(value)))
        metadata.sort(key=lambda item: item[0])
        return FixupRecord(
            address=address,
            type=fixup_type,
            length=length,
            offset=offset,
            metadata=tuple(metadata),
        )

    def _as_int(self, value):
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, (bytes, bytearray)):
            return int.from_bytes(value, "little")
        if hasattr(value, "value"):
            inner = getattr(value, "value")
            if isinstance(inner, int):
                return inner
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
