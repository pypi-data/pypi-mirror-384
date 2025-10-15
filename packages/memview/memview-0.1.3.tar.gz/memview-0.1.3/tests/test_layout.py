#########################################################################################
#                                                                                       #
# MIT License                                                                           #
#                                                                                       #
# Copyright (c) 2025 Ioannis D. (devcoons)                                              #
#                                                                                       #
#########################################################################################

from __future__ import annotations

from pathlib import Path

from ihexsrec import IHEXSREC
from memview.layout import load_layout, inspect
from memview.loaders import load_from_path

TOML = """
[memory]
fill = 0xFF

[[segments]]
name = "header"
base = 0x00000000
size = 64

[[segments]]
name = "app"
base = 0x00000040
size = 256

[[layout]]
name = "magic"
at = "header+0x00"
type = "u32"
endian = "be"

[[layout]]
name = "flags"
at = "header+0x04"
type = "bitfield"
bits = [{name="a",bit=0},{name="b",bit=1},{name="valid",bit=7}]

[[layout]]
name = "len"
at = "header+0x05"
type = "u16"
endian = "le"

[[layout]]
name = "entry"
at = "header+0x08"
type = "addr"
endian = "le"

[[layout]]
name = "name"
at = "header+0x0C"
type = "str"
size = 8
encoding = "ascii"

[[layout]]
name = "payload"
at = "app+0x00"
type = "bytes"
size = 4
"""

def test_layout_inspect_with_ihex(tmp_path: Path):
    doc = IHEXSREC()
    doc.write(0x00000000, b"\x12\x34\x56\x78")
    doc.write(0x00000004, b"\x80")
    doc.write(0x00000005, b"\x10\x00")
    doc.write(0x00000008, b"\x40\x00\x00\x00")
    doc.write(0x0000000C, b"TEST\x00\x00\x00\x00")
    doc.write(0x00000040, b"\xDE\xAD\xBE\xEF")
    hextext = "\n".join(doc.to_intel_hex())

    layout_path = tmp_path / "fw.toml"
    layout_path.write_text(TOML)

    input_path = tmp_path / "fw.hex"
    input_path.write_text(hextext)

    layout = load_layout(layout_path)
    mem, _ = load_from_path(input_path, fill=0xFF)
    report = inspect(layout, mem)

    rows = {f.name: f for f in report.fields}
    assert rows["magic"].value == int.from_bytes(b"\x12\x34\x56\x78", "big")
    assert rows["flags"].value["a"] == 0 and rows["flags"].value["b"] == 0 and rows["flags"].value["valid"] == 1
    assert rows["len"].value == 16
    assert rows["entry"].value == 0x00000040
    assert rows["name"].value == "TEST"
    assert rows["payload"].value == b"\xDE\xAD\xBE\xEF"
    assert report.issues == []
