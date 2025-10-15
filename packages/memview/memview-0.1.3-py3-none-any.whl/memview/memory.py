#########################################################################################
#                                                                                       #
# MIT License                                                                           #
#                                                                                       #
# Copyright (c) 2025 Ioannis D. (devcoons)                                              #
#                                                                                       #
# Permission is hereby granted, free of charge, to any person obtaining a copy          #
# of this software and associated documentation files (the "Software"), to deal         #
# in the Software without restriction, including without limitation the rights          #
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell             #
# copies of the Software, and to permit persons to whom the Software is                 #
# furnished to do so, subject to the following conditions:                              #
#                                                                                       #
# The above copyright notice and this permission notice shall be included in all        #
# copies or substantial portions of the Software.                                       #
#                                                                                       #
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR            #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,              #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE           #
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER                #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,         #
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE         #
# SOFTWARE.                                                                             #
#                                                                                       #
#########################################################################################

#########################################################################################
# IMPORTS                                                                               #
#########################################################################################

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Tuple
import bisect

from memview.errors import OverlapError

#########################################################################################
#########################################################################################

@dataclass(frozen=True)
class Chunk:
    addr: int
    data: memoryview

#########################################################################################

class SparseMemory:
    __slots__ = ("_chunks", "fill")

    def __init__(self, fill: int = 0xFF) -> None:
        self._chunks: List[Chunk] = []
        self.fill = int(fill) & 0xFF

    def add(self, addr: int, data: bytes | bytearray | memoryview) -> None:
        if not data:
            return
        addr = int(addr)
        mv = memoryview(data).toreadonly()
        addrs = [c.addr for c in self._chunks]
        i = bisect.bisect_left(addrs, addr)
        end = addr + len(mv)
        if i > 0:
            prev = self._chunks[i - 1]
            if prev.addr + len(prev.data) > addr:
                raise OverlapError(f"overlap with previous chunk @0x{prev.addr:X}")
        if i < len(self._chunks):
            nxt = self._chunks[i]
            if nxt.addr < end:
                raise OverlapError(f"overlap with next chunk @0x{nxt.addr:X}")

        self._chunks.insert(i, Chunk(addr, mv))

    def read(self, addr: int, size: int) -> tuple[bytes, bytes]:
        addr = int(addr); size = int(size)
        out = bytearray([self.fill] * size)
        mask = bytearray([0] * size)
        if size <= 0 or not self._chunks:
            return bytes(out), bytes(mask)

        addrs = [c.addr for c in self._chunks]
        i = max(0, bisect.bisect_right(addrs, addr) - 1)
        end = addr + size

        while i < len(self._chunks):
            c = self._chunks[i]
            if c.addr >= end:
                break
            c_end = c.addr + len(c.data)
            lo = max(addr, c.addr)
            hi = min(end, c_end)
            if lo < hi:
                src_off = lo - c.addr
                dst_off = lo - addr
                n = hi - lo
                out[dst_off:dst_off+n] = c.data[src_off:src_off+n]
                mask[dst_off:dst_off+n] = b"\x01" * n
            i += 1
        return bytes(out), bytes(mask)

    def iter_ranges(self) -> Iterable[Tuple[int, bytes]]:
        for c in self._chunks:
            yield c.addr, bytes(c.data)

    def size_covered(self) -> int:
        return sum(len(c.data) for c in self._chunks)

#########################################################################################
#########################################################################################