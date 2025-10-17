from __future__ import annotations

import argparse
import json
import re
from typing import List

from i64_parser import DatabaseParser


def render_text(records) -> str:
    lines: List[str] = []
    for record in records:
        header = f"{record.name} 0x{record.start:016X}-0x{record.end:016X}"
        lines.append(header)
        for unit in record.units:
            if unit.label:
                lines.append(f"{unit.label}:")
            bytes_text = " ".join(f"{byte:02X}" for byte in unit.opcodes)
            line = f"  0x{unit.address:016X}: {bytes_text:<24} {unit.display}"
            details: List[str] = []
            if unit.comment:
                details.append(unit.comment)
            if unit.references:
                refs = ", ".join(
                    f"{kind}:{target:016X}/{ref_type:X}" for kind, target, ref_type in unit.references
                )
                details.append(f"xrefs {refs}")
            if details:
                line = f"{line} ; {' | '.join(details)}"
            lines.append(line)
    return "\n".join(lines)


def render_strings(records) -> str:
    lines: List[str] = []
    for record in records:
        text = record.text.encode("unicode_escape").decode("ascii")
        lines.append(f"0x{record.address:016X}: {text} [{record.encoding}]")
    return "\n".join(lines)


def render_data(records) -> str:
    lines: List[str] = []
    for record in records:
        lines.append(f"{record.name} 0x{record.address:016X} size {record.size}")
        if record.payload:
            preview = " ".join(f"{byte:02X}" for byte in record.payload[:32])
            if record.size > 32:
                preview = f"{preview} ..."
            lines.append(f"  bytes: {preview}")
        if record.references:
            refs = ", ".join(
                f"{kind}:{target:016X}/{ref_type:X}" for kind, target, ref_type in record.references
            )
            lines.append(f"  refs: {refs}")
    return "\n".join(lines)


def render_imports(records) -> str:
    lines: List[str] = []
    for record in records:
        line = f"{record.library}!{record.name} 0x{record.address:016X}"
        if record.references:
            refs = ", ".join(
                f"{kind}:{target:016X}/{ref_type:X}" for kind, target, ref_type in record.references
            )
            line = f"{line} ; refs {refs}"
        lines.append(line)
    return "\n".join(lines)


def render_exports(records) -> str:
    lines: List[str] = []
    for record in records:
        parts = [f"0x{record.address:016X}"]
        if record.ordinal is not None:
            parts.append(f"ord {record.ordinal}")
        if record.forwarded:
            parts.append(f"fwd {record.forwarded}")
        line = f"{record.name} ({', '.join(parts)})"
        if record.references:
            refs = ", ".join(
                f"{kind}:{target:016X}/{ref_type:X}" for kind, target, ref_type in record.references
            )
            line = f"{line} ; refs {refs}"
        lines.append(line)
    return "\n".join(lines)


def describe_permissions(value: int) -> str:
    result = []
    result.append("r" if value & 1 else "-")
    result.append("w" if value & 2 else "-")
    result.append("x" if value & 4 else "-")
    return "".join(result)


def render_segments(records) -> str:
    lines: List[str] = []
    for record in records:
        perms = describe_permissions(record.permissions)
        bitness = {0: 16, 1: 32, 2: 64}.get(record.bitness, 0)
        class_name = record.class_name or "-"
        base = (
            f"{record.name} 0x{record.start:016X}-0x{record.end:016X} "
            f"size {record.size} perms {perms} bit {bitness} class {class_name} type {record.segment_type}"
        )
        if record.preview:
            sample = " ".join(f"{byte:02X}" for byte in record.preview[:16])
            lines.append(f"{base} bytes {sample}")
        else:
            lines.append(base)
    return "\n".join(lines)


def render_fixups(records) -> str:
    lines: List[str] = []
    for record in records:
        parts: List[str] = []
        if record.type is not None:
            parts.append(f"type 0x{record.type:X}")
        if record.offset is not None:
            parts.append(f"offset 0x{record.offset:X}")
        if record.length is not None:
            parts.append(f"len {record.length}")
        if record.metadata:
            meta = ", ".join(
                f"{key}=0x{value:X}" if value is not None else f"{key}=None"
                for key, value in record.metadata
            )
            parts.append(meta)
        lines.append(f"0x{record.address:016X}: {'; '.join(parts)}")
    return "\n".join(lines)


def render_structs(records) -> str:
    blocks: List[str] = []
    for record in records:
        lines: List[str] = []
        lines.append(f"{record.name} flags 0x{record.flags:X}")
        for member in record.members:
            line = f"  0x{member.offset:04X}: {member.name}"
            if member.type:
                line = f"{line} : {member.type}"
            line = f"{line} size {member.size}"
            if member.flag:
                line = f"{line} flag 0x{member.flag:X}"
            lines.append(line)
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def render_types(records) -> str:
    blocks: List[str] = []
    for record in records:
        if not record.declaration:
            continue
        blocks.append(record.declaration)
    return "\n\n".join(blocks)

def render_names(records) -> str:
    lines: List[str] = []
    for record in records:
        lines.append(f"0x{record.address:016X}: {record.name} [{record.kind}]")
    return "\n".join(lines)


def render_globals(records) -> str:
    lines: List[str] = []
    for record in records:
        lines.append(f"0x{record.address:016X}: {record.name}")
    return "\n".join(lines)


def parse_address(value: str | None) -> int | None:
    if value is None:
        return None
    return int(value, 0)


def build_matcher(pattern: str | None):
    if not pattern:
        return None
    return re.compile(pattern)


def function_matches(record, start, end, matcher):
    if start is not None and record.start < start:
        return False
    if end is not None and record.start > end:
        return False
    if matcher and not matcher.search(record.name):
        return False
    return True


def string_matches(record, start, end, matcher):
    if start is not None and record.address < start:
        return False
    if end is not None and record.address > end:
        return False
    if matcher and not matcher.search(record.text):
        return False
    return True


def data_matches(record, start, end, matcher):
    if start is not None and record.address < start:
        return False
    if end is not None and record.address > end:
        return False
    if matcher and not matcher.search(record.name):
        return False
    return True


def name_matches(record, start, end, matcher):
    if start is not None and record.address < start:
        return False
    if end is not None and record.address > end:
        return False
    if matcher and not matcher.search(record.name):
        return False
    return True


def import_matches(record, start, end, matcher):
    if start is not None and record.address < start:
        return False
    if end is not None and record.address > end:
        return False
    if matcher and not (matcher.search(record.library) or matcher.search(record.name)):
        return False
    return True


def export_matches(record, start, end, matcher):
    if start is not None and record.address < start:
        return False
    if end is not None and record.address > end:
        return False
    if matcher and not matcher.search(record.name):
        return False
    return True


def type_matches(record, start, end, matcher):
    if matcher and not (matcher.search(record.name) or matcher.search(record.declaration)):
        return False
    return True


def segment_matches(record, start, end, matcher):
    if start is not None and record.end <= start:
        return False
    if end is not None and record.start >= end:
        return False
    if matcher and not (matcher.search(record.name) or matcher.search(record.class_name)):
        return False
    return True


def fixup_matches(record, start, end, matcher):
    if start is not None and record.address < start:
        return False
    if end is not None and record.address > end:
        return False
    if matcher and record.type is not None and matcher.search(f"0x{record.type:X}"):
        return True
    if matcher and record.offset is not None and matcher.search(f"0x{record.offset:X}"):
        return True
    if matcher and record.metadata:
        for key, value in record.metadata:
            if matcher.search(key):
                return True
            if value is not None and matcher.search(f"0x{value:X}"):
                return True
        return False
    if matcher:
        return matcher.search(f"0x{record.address:X}") is not None
    return True


def struct_matches(record, start, end, matcher):
    if matcher:
        if matcher.search(record.name):
            return True
        return any(
            matcher.search(member.name) or (member.type and matcher.search(member.type))
            for member in record.members
        )
    return True


def filter_functions(records, start, end, matcher):
    return [record for record in records if function_matches(record, start, end, matcher)]


def filter_strings(records, start, end, matcher):
    return [record for record in records if string_matches(record, start, end, matcher)]


def filter_data(records, start, end, matcher):
    return [record for record in records if data_matches(record, start, end, matcher)]


def filter_names(records, start, end, matcher):
    return [record for record in records if name_matches(record, start, end, matcher)]


def filter_imports(records, start, end, matcher):
    return [record for record in records if import_matches(record, start, end, matcher)]


def filter_exports(records, start, end, matcher):
    return [record for record in records if export_matches(record, start, end, matcher)]


def filter_types(records, start, end, matcher):
    return [record for record in records if type_matches(record, start, end, matcher)]


def filter_segments(records, start, end, matcher):
    return [record for record in records if segment_matches(record, start, end, matcher)]


def filter_fixups(records, start, end, matcher):
    return [record for record in records if fixup_matches(record, start, end, matcher)]


def filter_structs(records, start, end, matcher):
    return [record for record in records if struct_matches(record, start, end, matcher)]


def collect_filtered(iterator, predicate, limit):
    result = []
    for item in iterator:
        if predicate(item):
            result.append(item)
            if limit is not None and len(result) >= limit:
                break
    return result


def run() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--report",
        choices=[
            "functions",
            "strings",
            "data",
            "imports",
            "exports",
            "names",
            "globals",
            "segments",
            "fixups",
            "structs",
            "types",
            "all",
        ],
        default="functions",
    )
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--match")
    options = parser.parse_args()

    start = parse_address(options.start)
    end = parse_address(options.end)
    matcher = build_matcher(options.match)

    with DatabaseParser(options.path) as database:
        if options.report == "functions":
            records = collect_filtered(
                database.functions(),
                lambda record: function_matches(record, start, end, matcher),
                options.limit,
            )
            if options.json:
                print(json.dumps([record.to_dict() for record in records], indent=2))
            else:
                print(render_text(records))
        elif options.report == "strings":
            records = collect_filtered(
                database.strings(),
                lambda record: string_matches(record, start, end, matcher),
                options.limit,
            )
            if options.json:
                print(json.dumps([record.to_dict() for record in records], indent=2))
            else:
                print(render_strings(records))
        elif options.report == "data":
            records = collect_filtered(
                database.data(),
                lambda record: data_matches(record, start, end, matcher),
                options.limit,
            )
            if options.json:
                print(json.dumps([record.to_dict() for record in records], indent=2))
            else:
                print(render_data(records))
        elif options.report == "imports":
            records = collect_filtered(
                database.imports(),
                lambda record: import_matches(record, start, end, matcher),
                options.limit,
            )
            if options.json:
                print(json.dumps([record.to_dict() for record in records], indent=2))
            else:
                print(render_imports(records))
        elif options.report == "exports":
            records = collect_filtered(
                database.exports(),
                lambda record: export_matches(record, start, end, matcher),
                options.limit,
            )
            if options.json:
                print(json.dumps([record.to_dict() for record in records], indent=2))
            else:
                print(render_exports(records))
        elif options.report == "names":
            records = collect_filtered(
                database.names(),
                lambda record: name_matches(record, start, end, matcher),
                options.limit,
            )
            if options.json:
                print(json.dumps([record.to_dict() for record in records], indent=2))
            else:
                print(render_names(records))
        elif options.report == "globals":
            records = collect_filtered(
                database.globals(),
                lambda record: name_matches(record, start, end, matcher),
                options.limit,
            )
            if options.json:
                print(json.dumps([record.to_dict() for record in records], indent=2))
            else:
                print(render_globals(records))
        elif options.report == "segments":
            records = collect_filtered(
                database.segments(),
                lambda record: segment_matches(record, start, end, matcher),
                options.limit,
            )
            if options.json:
                print(json.dumps([record.to_dict() for record in records], indent=2))
            else:
                print(render_segments(records))
        elif options.report == "fixups":
            records = collect_filtered(
                database.fixups(),
                lambda record: fixup_matches(record, start, end, matcher),
                options.limit,
            )
            if options.json:
                print(json.dumps([record.to_dict() for record in records], indent=2))
            else:
                print(render_fixups(records))
        elif options.report == "structs":
            records = collect_filtered(
                database.structures(),
                lambda record: struct_matches(record, start, end, matcher),
                options.limit,
            )
            if options.json:
                print(json.dumps([record.to_dict() for record in records], indent=2))
            else:
                print(render_structs(records))
        elif options.report == "types":
            records = collect_filtered(
                database.types(),
                lambda record: type_matches(record, start, end, matcher),
                options.limit,
            )
            if options.json:
                print(json.dumps([record.to_dict() for record in records], indent=2))
            else:
                print(render_types(records))
        else:
            functions = collect_filtered(
                database.functions(),
                lambda record: function_matches(record, start, end, matcher),
                options.limit,
            )
            strings = collect_filtered(
                database.strings(),
                lambda record: string_matches(record, start, end, matcher),
                options.limit,
            )
            name_records = collect_filtered(
                database.names(),
                lambda record: name_matches(record, start, end, matcher),
                options.limit,
            )
            global_records = collect_filtered(
                database.globals(),
                lambda record: name_matches(record, start, end, matcher),
                options.limit,
            )
            segment_records = collect_filtered(
                database.segments(),
                lambda record: segment_matches(record, start, end, matcher),
                options.limit,
            )
            data_records = collect_filtered(
                database.data(),
                lambda record: data_matches(record, start, end, matcher),
                options.limit,
            )
            import_records = collect_filtered(
                database.imports(),
                lambda record: import_matches(record, start, end, matcher),
                options.limit,
            )
            export_records = collect_filtered(
                database.exports(),
                lambda record: export_matches(record, start, end, matcher),
                options.limit,
            )
            fixup_records = collect_filtered(
                database.fixups(),
                lambda record: fixup_matches(record, start, end, matcher),
                options.limit,
            )
            structure_records = collect_filtered(
                database.structures(),
                lambda record: struct_matches(record, start, end, matcher),
                options.limit,
            )
            type_records = collect_filtered(
                database.types(),
                lambda record: type_matches(record, start, end, matcher),
                options.limit,
            )
            if options.json:
                payload = {
                    "functions": [record.to_dict() for record in functions],
                    "strings": [record.to_dict() for record in strings],
                    "names": [record.to_dict() for record in name_records],
                    "globals": [record.to_dict() for record in global_records],
                    "segments": [record.to_dict() for record in segment_records],
                    "data": [record.to_dict() for record in data_records],
                    "imports": [record.to_dict() for record in import_records],
                    "exports": [record.to_dict() for record in export_records],
                    "fixups": [record.to_dict() for record in fixup_records],
                    "structs": [record.to_dict() for record in structure_records],
                    "types": [record.to_dict() for record in type_records],
                }
                print(json.dumps(payload, indent=2))
            else:
                sections = [
                    render_text(functions),
                    render_strings(strings),
                    render_names(name_records),
                    render_globals(global_records),
                    render_segments(segment_records),
                    render_data(data_records),
                    render_imports(import_records),
                    render_exports(export_records),
                    render_fixups(fixup_records),
                    render_structs(structure_records),
                    render_types(type_records),
                ]
                print("\n\n".join(section for section in sections if section))


if __name__ == "__main__":
    run()
