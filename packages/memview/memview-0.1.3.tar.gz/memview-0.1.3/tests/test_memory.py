#########################################################################################
#                                                                                       #
# MIT License                                                                           #
#                                                                                       #
# Copyright (c) 2025 Ioannis D. (devcoons)                                              #
#                                                                                       #
#########################################################################################

from __future__ import annotations

import pytest

from memview.memory import SparseMemory
from memview.errors import OverlapError

def test_sparse_memory_add_and_read_basic():
    mem = SparseMemory(fill=0xAA)
    mem.add(0x1000, b"\xDE\xAD\xBE\xEF")
    data, mask = mem.read(0x0FFC, 16)
    assert data[:4] == b"\xAA\xAA\xAA\xAA"
    assert data[4:8] == b"\xDE\xAD\xBE\xEF"
    assert data[8:] == b"\xAA" * 8
    assert mask[4:8] == b"\x01\x01\x01\x01"
    assert mask[:4] == b"\x00\x00\x00\x00"

def test_sparse_memory_overlap_raises():
    mem = SparseMemory()
    mem.add(0x0000, b"\x00\x01\x02\x03")
    with pytest.raises(OverlapError):
        mem.add(0x0002, b"\x99\x99")
