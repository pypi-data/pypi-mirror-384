from __future__ import annotations

from typing import Dict, Tuple

import idb.analysis as analysis


class ReferenceResolver:
    def __init__(self, database) -> None:
        self.database = database
        self.code_out_cache: Dict[int, Tuple[Tuple[str, int, int], ...]] = {}
        self.data_out_cache: Dict[int, Tuple[Tuple[str, int, int], ...]] = {}
        self.code_in_cache: Dict[int, Tuple[Tuple[str, int, int], ...]] = {}
        self.data_in_cache: Dict[int, Tuple[Tuple[str, int, int], ...]] = {}

    def outgoing(self, address: int) -> Tuple[Tuple[str, int, int], ...]:
        code = self._code_out(address)
        data = self._data_out(address)
        if not code:
            return data
        if not data:
            return code
        return code + data

    def resolve(self, address: int) -> Tuple[Tuple[str, int, int], ...]:
        return self.outgoing(address)

    def incoming(self, address: int) -> Tuple[Tuple[str, int, int], ...]:
        code = self._code_in(address)
        data = self._data_in(address)
        if not code:
            return data
        if not data:
            return code
        return code + data

    def _code_out(self, address: int) -> Tuple[Tuple[str, int, int], ...]:
        cached = self.code_out_cache.get(address)
        if cached is not None:
            return cached
        refs = tuple(("code", xref.to, xref.type) for xref in analysis.get_crefs_from(self.database, address))
        self.code_out_cache[address] = refs
        return refs

    def _data_out(self, address: int) -> Tuple[Tuple[str, int, int], ...]:
        cached = self.data_out_cache.get(address)
        if cached is not None:
            return cached
        refs = tuple(("data", xref.to, xref.type) for xref in analysis.get_drefs_from(self.database, address))
        self.data_out_cache[address] = refs
        return refs

    def _code_in(self, address: int) -> Tuple[Tuple[str, int, int], ...]:
        cached = self.code_in_cache.get(address)
        if cached is not None:
            return cached
        refs = tuple(("code", xref.frm, xref.type) for xref in analysis.get_crefs_to(self.database, address))
        self.code_in_cache[address] = refs
        return refs

    def _data_in(self, address: int) -> Tuple[Tuple[str, int, int], ...]:
        cached = self.data_in_cache.get(address)
        if cached is not None:
            return cached
        refs = tuple(("data", xref.frm, xref.type) for xref in analysis.get_drefs_to(self.database, address))
        self.data_in_cache[address] = refs
        return refs
