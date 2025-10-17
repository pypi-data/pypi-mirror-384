from __future__ import annotations

from typing import Dict

from idb.netnode import Netnode


class NameResolver:
    def __init__(self, database, api=None) -> None:
        self.database = database
        self.api = api
        self.cache: Dict[int, str | None] = {}

    def resolve(self, address: int) -> str | None:
        if address in self.cache:
            return self.cache[address]
        value = None
        node_id = address
        if hasattr(self.database, "uint"):
            try:
                node_id = self.database.uint(address)
            except Exception:
                node_id = address
        try:
            node = Netnode(self.database, node_id)
            value = node.name()
        except Exception:
            value = None
        if (not value) and self.api is not None:
            try:
                candidate = self.api.ida_name.get_name(address)
            except Exception:
                candidate = ""
            if candidate:
                value = candidate
        self.cache[address] = value
        return value
