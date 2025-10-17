from __future__ import annotations

from typing import Iterable, List, Tuple

import idb.analysis as analysis
import idb.netnode as netnode

from .records import StructMemberRecord, StructureRecord


class StructureScanner:
    def __init__(self, database) -> None:
        self.database = database
        self.struct_ids = self._load_structure_ids()

    def scan(self) -> Iterable[StructureRecord]:
        if not self.struct_ids:
            return
        for identity in self.struct_ids:
            record = self._build(identity)
            if record is None:
                continue
            yield record

    def _load_structure_ids(self) -> List[int]:
        try:
            node = netnode.Netnode(self.database, "$ structs")
        except Exception:
            return []
        result: List[int] = []
        for entry in node.altentries():
            value = netnode.as_uint(entry.value) - 1
            if value not in result:
                result.append(value)
        return result

    def _build(self, identity: int) -> StructureRecord | None:
        try:
            structure = analysis.Struct(self.database, identity)
        except Exception:
            return None
        try:
            packed = structure.netnode.supval(tag="M", index=0)
        except KeyError:
            return None
        if packed is None:
            return None
        parser = analysis.Unpacker(packed, wordsize=self.database.wordsize)
        flags = parser.dd()
        count = parser.dd()
        members: List[StructMemberRecord] = []
        for _ in range(count):
            node_offset = parser.addr()
            member_offset = parser.addr()
            member_size = parser.addr()
            member_flag = parser.dd()
            parser.dd()
            member_nodeid = structure.netnode.nodebase + node_offset
            member = analysis.StructMember(self.database, member_nodeid)
            name = member.get_name()
            member_type = member.get_type()
            try:
                comment = member.get_member_comment()
            except Exception:
                comment = None
            try:
                repeatable = member.get_repeatable_member_comment()
            except Exception:
                repeatable = None
            members.append(
                StructMemberRecord(
                    name=name,
                    type=member_type,
                    offset=member_offset,
                    size=member_size,
                    flag=member_flag,
                    comment=comment,
                    repeatable_comment=repeatable,
                )
            )
        struct_name = structure.get_name()
        if not struct_name:
            struct_name = f"struct_{identity:08X}"
        return StructureRecord(name=struct_name, flags=flags, members=tuple(members))
