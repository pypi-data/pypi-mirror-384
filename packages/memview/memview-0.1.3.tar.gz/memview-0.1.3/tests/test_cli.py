#########################################################################################
#                                                                                       #
# MIT License                                                                           #
#                                                                                       #
# Copyright (c) 2025 Ioannis D. (devcoons)                                              #
#                                                                                       #
#########################################################################################

from __future__ import annotations

from pathlib import Path
import sys

import pytest
from ihexsrec import IHEXSREC

import memview.cli as cli

TOML = """
[memory]
fill = 0xFF

[[segments]]
name = "header"
base = 0x08000000
size = 64

[[layout]]
name = "magic"
at = "header+0x00"
type = "u32"
endian = "be"
"""

def test_cli_inspect_ihex_text_output(capsys, tmp_path: Path, monkeypatch):
    doc = IHEXSREC()
    doc.write(0x08000000, b"\x12\x34\x56\x78")
    hextext = "\n".join(doc.to_intel_hex())

    fw = tmp_path / "fw.hex"
    fw.write_text(hextext)

    layout = tmp_path / "fw.toml"
    layout.write_text(TOML)

    argv = ["memview", "inspect", str(fw), "--layout", str(layout), "--format", "text"]
    monkeypatch.setattr(sys, "argv", argv)
    rc = cli.main()
    out = capsys.readouterr().out
    assert rc == 0
    assert "magic" in out and "0x08000000" in out

def test_cli_inspect_bin_requires_base(tmp_path: Path, monkeypatch, capsys):
    fw = tmp_path / "fw.bin"
    fw.write_bytes(b"\x00\x00\x00\x00")

    layout = tmp_path / "fw.toml"
    layout.write_text(TOML)

    argv = ["memview", "inspect", str(fw), "--layout", str(layout)]
    monkeypatch.setattr(sys, "argv", argv)
    rc = cli.main()
    err = capsys.readouterr().err
    assert rc == 1
    assert "Binary input detected" in err

def test_cli_inspect_bin_with_base_ok(capsys, tmp_path: Path, monkeypatch):
    fw = tmp_path / "fw.bin"
    fw.write_bytes(b"\x12\x34\x56\x78")

    layout = tmp_path / "fw.toml"
    layout.write_text(TOML)

    argv = ["memview", "inspect", str(fw), "--layout", str(layout), "--base", "0x08000000", "--format", "json"]
    monkeypatch.setattr(sys, "argv", argv)
    rc = cli.main()
    out = capsys.readouterr().out
    assert rc in (0, 2)
    assert '"name": "magic"' in out
