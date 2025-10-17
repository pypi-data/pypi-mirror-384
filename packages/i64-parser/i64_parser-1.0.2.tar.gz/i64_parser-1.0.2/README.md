# i64-parser

i64-parser is a Python toolchain that reads IDA Pro `.i64`/`.idb` databases without launching IDA.
It wraps the `python-idb` library with a clean CLI that exports the artifacts reverse engineers reach for most: functions, strings, data blobs, symbol names, segments, fixups, type library entries, and structure layouts.

## Features

- **Function decoding** – Capstone-backed disassembly with address, opcodes, comments, and xrefs.
- **String & data scans** – ASCII/UTF‑16 string harvesting plus data segment slices with reference tracking.
- **Symbol surfaces** – Import/export tables, NAM-derived globals, IDA-resolved labels, and cross references.
- **Type information** – Typedef/struct/union/enum declarations rendered from the TIL section.
- **Segments & fixups** – Segment metadata (permissions, class, preview bytes) and raw fixup records.
- **Structure introspection** – Structure flags, member offsets, types, and comments straight from `$ structs`.
- **JSON or text reports** – Filtered, address-bounded views for quick inspection or downstream scripting.

## Requirements

- Python 3.9+
- [`python-idb`](https://github.com/williballenthin/python-idb)
- [`capstone`](http://www.capstone-engine.org/)

Install prerequisites:

```bash
pip install python-idb capstone
```

## Usage

```bash
python -m src.main <path-to-database> [--report kind] [options]
```

Report kinds:

```
functions, strings, data, imports, exports,
names, globals, segments, fixups, structs, types, all
```

Common options:

- `--json` – emit JSON instead of text.
- `--limit N` – stop after `N` records.
- `--start`, `--end` – inclusive address filters (hex or decimal).
- `--match REGEX` – filter by name/text/type (varies per report).

Examples:

```bash
# Dump function disassembly
python -m src.main samples/kernel32.i64 --report functions --limit 10

# Export all metadata to JSON for automation
python -m src.main samples/kernel32.i64 --report all --json > kernel32.json

# Inspect segments with read/exec permissions
python -m src.main samples/kernel32.i64 --report segments --match "rx"

# List TIL typedefs containing "PEB"
python -m src.main samples/kernel32.i64 --report types --match PEB
```

## Repository Layout

```
src/
  main.py              CLI entry point
  i64_parser/
    api.py             Database orchestration / extraction API
    data.py            Non-code segment scanning
    disasm.py          Capstone disassembly glue
    fixups.py          `$ fixups` netnode scanner
    functions.py       Function chunk enumerator
    globals.py         NAM/global symbol collector
    names.py           Name resolution helpers
    records.py         Typed dataclasses for serialized output
    references.py        ReferenceResolver class
    segments.py        Segment table + scanner
    strings.py         ASCII/UTF-16 string extraction
    structures.py      `$ structs` reader
    types.py           TIL typedef/struct/enum harvesting
```

## Workflow Notes

- All extraction methods are read-only; no database mutation occurs.
- When `python-idb` can emulate IDAPython APIs (e.g., `get_nlist_*`), the tool prefers them; otherwise it falls back to raw netnode parsing.
- New report types or filters can be added by introducing a record dataclass, scanner module, API façade, and CLI renderer—each component is isolated for clarity.

## Roadmap

- Additional metadata surfaces: fixups by type, FlowChart/basic blocks, loader metadata.
- Optional writers (CSV/SQLite) for large-scale analytics.
- Tests driven by synthetic `.i64` fixtures.

## License

This project inherits the Apache 2.0 license through `python-idb`. See `LICENSE` once it's added to the repository.
