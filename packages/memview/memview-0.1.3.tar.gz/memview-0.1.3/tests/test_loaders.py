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
from memview.loaders import load_from_path, detect_format, FileFormat, load_hexdump

def _hex_from_bytes_at(addr: int, payload: bytes) -> str:
    doc = IHEXSREC()
    doc.write(addr, payload)
    return "\n".join(doc.to_intel_hex())

def _srec_from_bytes_at(addr: int, payload: bytes) -> str:
    doc = IHEXSREC()
    doc.write(addr, payload)
    return "\n".join(doc.to_srec())

def test_load_bin_requires_base(tmp_path: Path):
    p = tmp_path / "raw.bin"
    p.write_bytes(b"\xDE\xAD\xBE\xEF")
    mem, fmt = load_from_path(p, base_address=0x08000000, fill=0xFF)
    data, mask = mem.read(0x08000000, 4)
    assert data == b"\xDE\xAD\xBE\xEF"
    assert fmt == FileFormat.BIN

def test_load_ihex_roundtrip(tmp_path: Path):
    text = _hex_from_bytes_at(0x08001000, b"\x01\x02\x03\x04")
    p = tmp_path / "fw.hex"
    p.write_text(text)
    mem, fmt = load_from_path(p, fill=0x00)
    assert fmt == FileFormat.IHEX
    d, m = mem.read(0x08001000, 4)
    assert d == b"\x01\x02\x03\x04"
    assert m == b"\x01\x01\x01\x01"

def test_load_srec_roundtrip(tmp_path: Path):
    text = _srec_from_bytes_at(0x00002000, b"\xAA\xBB\xCC")
    p = tmp_path / "fw.srec"
    p.write_text(text)
    mem, fmt = load_from_path(p, fill=0xFF)
    assert fmt == FileFormat.SREC
    d, m = mem.read(0x00002000, 3)
    assert d == b"\xAA\xBB\xCC"
    assert m == b"\x01\x01\x01"

def test_load_hexdump_xxd(tmp_path: Path):
    dump = "00000010: de ad be ef 00 11 22 33\n00000018: 44 55 66 77"
    mem = load_hexdump(dump, fill=0xFF)
    d, m = mem.read(0x10, 12)
    assert d == bytes.fromhex("DE AD BE EF 00 11 22 33 44 55 66 77")
    assert m == b"\x01" * 12

def test_detect_formats(tmp_path: Path):
    p_hex = tmp_path / "a.hex"
    p_hex.write_text(_hex_from_bytes_at(0x0, b"\x00"))
    assert detect_format(p_hex.read_text()) == FileFormat.IHEX
    p_srec = tmp_path / "a.srec"
    p_srec.write_text(_srec_from_bytes_at(0x0, b"\x00"))
    assert detect_format(p_srec.read_text()) == FileFormat.SREC
    p_txt = tmp_path / "d.txt"
    p_txt.write_text("00000000: 00 11 22 33")
    assert detect_format(p_txt.read_text()) == FileFormat.HEXDUMP
