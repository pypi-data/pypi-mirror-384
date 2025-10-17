from __future__ import annotations

from typing import Iterable, List, Tuple

import idb.analysis as ida_analysis
from idb.analysis import Function, func_t
from idb.netnode import Netnode


class FunctionReader:
    def __init__(self, database) -> None:
        self.database = database
        self.node = Netnode(database, "$ funcs")
        self._analysis = ida_analysis.Functions(database)
        self.comments = dict(getattr(self._analysis, "comments", {}))
        self.repeatable_comments = dict(getattr(self._analysis, "repeatable_comments", {}))

    def entries(self) -> Iterable[Tuple[int, int, str, Tuple[Tuple[int, int], ...]]]:
        for entry in self.node.supentries(tag="S"):
            buffer = bytes(entry.value)
            record = func_t(buffer, wordsize=self.database.wordsize)
            view = Function(self.database, record.startEA)
            label = view.get_name()
            chunks: List[Tuple[int, int]] = []
            try:
                for chunk in view.get_chunks():
                    chunks.append((chunk.effective_address, chunk.length))
            except KeyError:
                chunks.append((record.startEA, record.endEA - record.startEA))
            yield record.startEA, record.endEA, label, tuple(chunks)
