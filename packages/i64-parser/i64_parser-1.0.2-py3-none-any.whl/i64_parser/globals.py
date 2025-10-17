from __future__ import annotations

from typing import Iterable, Set

from .records import NameRecord


class GlobalScanner:
    def __init__(self, database, api, resolver) -> None:
        self.database = database
        self.api = api
        self.resolver = resolver

    def scan(self) -> Iterable[NameRecord]:
        if self.api is not None:
            size = self.api.ida_name.get_nlist_size()
            for index in range(size):
                address = self.api.ida_name.get_nlist_ea(index)
                name = self.api.ida_name.get_nlist_name(index)
                if not name:
                    continue
                yield NameRecord(address=address, name=name, kind="global")
            return
        section = getattr(self.database, "nam", None)
        if section is None:
            return
        addresses = section.names()
        if not addresses:
            return
        seen: Set[int] = set()
        for address in addresses:
            if address in seen:
                continue
            seen.add(address)
            name = self.resolver.resolve(address) if self.resolver else None
            if not name:
                continue
            yield NameRecord(address=address, name=name, kind="global")
