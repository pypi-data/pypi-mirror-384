#########################################################################################
#                                                                                       #
# MIT License                                                                           #
#                                                                                       #
# Copyright (c) 2025 Ioannis D. (devcoons)                                              #
#                                                                                       #
#########################################################################################

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List

from memview.reporters import to_text, to_json, to_csv

@dataclass
class FieldResult:
    name: str
    address: int
    type: str
    value: Any
    meta: dict

@dataclass
class Report:
    fields: List[FieldResult]
    issues: List[str]

def test_reporters_formats():
    rep = Report(
        fields=[
            FieldResult("magic", 0x1000, "u32", 0xDEADBEEF, {"endian": "be"}),
            FieldResult("flags", 0x1004, "bitfield", {"a":1,"b":0}, {}),
            FieldResult("payload", 0x2000, "bytes", b"\x00\x01\x02\x03", {}),
        ],
        issues=["payload length mismatch"]
    )
    txt = to_text(rep)
    assert "magic" in txt and "0x00001000" in txt and "u32(be)" in txt
    j = to_json(rep)
    assert '"name": "magic"' in j and '"issues":' in j
    c = to_csv(rep)
    assert "magic" in c and "payload" in c and "# ISSUE:" in c
