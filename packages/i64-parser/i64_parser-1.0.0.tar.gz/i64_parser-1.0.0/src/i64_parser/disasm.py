from __future__ import annotations

from typing import Callable, Iterable, List, Mapping, Tuple

import capstone

from .records import CodeUnit
from .segments import SegmentTable


class Disassembler:
    def __init__(self, processor: str, wordsize: int, segments: SegmentTable) -> None:
        self.segments = segments
        self.engine = self._build_engine(processor, wordsize)

    def _build_engine(self, processor: str, wordsize: int) -> capstone.Cs:
        if processor == "metapc":
            if wordsize == 8:
                mode = capstone.CS_MODE_64
            elif wordsize == 4:
                mode = capstone.CS_MODE_32
            else:
                mode = capstone.CS_MODE_16
            engine = capstone.Cs(capstone.CS_ARCH_X86, mode)
        else:
            raise ValueError(processor)
        engine.detail = False
        return engine

    def decode(
        self,
        chunks: Tuple[Tuple[int, int], ...],
        comments: Mapping[int, str] | None = None,
        repeatable_comments: Mapping[int, str] | None = None,
        resolver: Callable[[int], str | None] | None = None,
        xref_resolver: Callable[[int], Tuple[Tuple[str, int, int], ...]] | None = None,
    ) -> Tuple[CodeUnit, ...]:
        units: List[CodeUnit] = []
        for start, length in chunks:
            data = self.segments.slice(start, length)
            cursor = start
            for instruction in self.engine.disasm(data, start):
                if instruction.address > cursor:
                    gap = instruction.address - cursor
                    units.extend(
                        self._emit_data(
                            cursor,
                            data[cursor - start : cursor - start + gap],
                            comments,
                            repeatable_comments,
                            resolver,
                            xref_resolver,
                        )
                    )
                    cursor = instruction.address
                text = instruction.mnemonic
                if instruction.op_str:
                    text = f"{instruction.mnemonic} {instruction.op_str}"
                comment = None
                if comments is not None:
                    comment = comments.get(instruction.address)
                if comment is None and repeatable_comments is not None:
                    comment = repeatable_comments.get(instruction.address)
                label = None
                if resolver is not None:
                    label = resolver(instruction.address)
                references = ()
                if xref_resolver is not None:
                    references = xref_resolver(instruction.address)
                units.append(
                    CodeUnit(
                        address=instruction.address,
                        display=text,
                        opcodes=tuple(instruction.bytes),
                        comment=comment,
                        label=label,
                        references=references,
                    )
                )
                cursor = instruction.address + len(instruction.bytes)
            tail = length - (cursor - start)
            if tail > 0:
                units.extend(
                    self._emit_data(
                        cursor,
                        data[cursor - start : cursor - start + tail],
                        comments,
                        repeatable_comments,
                        resolver,
                        xref_resolver,
                    )
                )
                cursor += tail
        return tuple(units)

    def _emit_data(
        self,
        address: int,
        data: bytes,
        comments: Mapping[int, str] | None = None,
        repeatable_comments: Mapping[int, str] | None = None,
        resolver: Callable[[int], str | None] | None = None,
        xref_resolver: Callable[[int], Tuple[Tuple[str, int, int], ...]] | None = None,
    ) -> Iterable[CodeUnit]:
        result: List[CodeUnit] = []
        offset = 0
        while offset < len(data):
            byte = data[offset]
            display = f"db 0x{byte:02X}"
            comment = None
            absolute = address + offset
            if comments is not None:
                comment = comments.get(absolute)
            if comment is None and repeatable_comments is not None:
                comment = repeatable_comments.get(absolute)
            label = None
            if resolver is not None:
                label = resolver(absolute)
            references = ()
            if xref_resolver is not None:
                references = xref_resolver(absolute)
            result.append(
                CodeUnit(
                    address=absolute,
                    display=display,
                    opcodes=(byte,),
                    comment=comment,
                    label=label,
                    references=references,
                )
            )
            offset += 1
        return result
