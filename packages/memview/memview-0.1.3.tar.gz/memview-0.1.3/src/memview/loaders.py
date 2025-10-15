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

from enum import Enum, auto
from pathlib import Path
from typing import Optional, Tuple
import re

from memview.memory import SparseMemory
from memview.errors import ParseError

# Import ihexsrec codecs exactly as implemented
try:
    from ihexsrec import IntelHexCodec as _IntelHexCodec
    from ihexsrec import SrecCodec as _SrecCodec
except Exception:  # pragma: no cover
    _IntelHexCodec = None
    _SrecCodec = None

#########################################################################################
#########################################################################################

class FileFormat(Enum):
    BIN = auto()
    IHEX = auto()
    SREC = auto()
    HEXDUMP = auto()

#########################################################################################
#########################################################################################

_HEX_BYTES 		= r"(?:[0-9A-Fa-f]{2}(?:\s+|$))+"
_RE_XXD 		= re.compile(r"^\s*([0-9A-Fa-f]+):\s+(" + _HEX_BYTES + r")", re.M)
_RE_HDC 		= re.compile(r"^\s*([0-9A-Fa-f]+)\s{2}(" + _HEX_BYTES + r")", re.M)
_HEXDUMP_PROFILES 	= (_RE_XXD, _RE_HDC)

#########################################################################################
#########################################################################################

def _parse_hex_bytes(chunk: str) -> bytes:
    s = "".join(chunk.strip().split())
    return bytes.fromhex(s)

#########################################################################################

def detect_format(text: str) -> Optional[FileFormat]:
    s = text.lstrip()
    if not s:
        return None
    if s.startswith(":"):
        first = s.splitlines()[0].strip()
        if len(first) >= 11:
            return FileFormat.IHEX
    if s.startswith(("S0", "S1", "S2", "S3", "S7", "S8", "S9")):
        return FileFormat.SREC
    for rx in _HEXDUMP_PROFILES:
        if rx.search(text):
            return FileFormat.HEXDUMP
    return None

#########################################################################################

def load_from_path(
    path: str | Path,
    *,
    base_address: Optional[int] = None,
    fill: int = 0xFF,
) -> Tuple[SparseMemory, FileFormat]:

    p = Path(path)
    txt: Optional[str] = None
    try:
        txt = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        txt = None

    if txt:
        kind = detect_format(txt)
        if kind == FileFormat.IHEX:
            return load_ihex(txt, fill=fill), FileFormat.IHEX
        if kind == FileFormat.SREC:
            return load_srec(txt, fill=fill), FileFormat.SREC
        if kind == FileFormat.HEXDUMP:
            return load_hexdump(txt, fill=fill), FileFormat.HEXDUMP

    if base_address is None:
        raise ParseError("--base required for BIN files (or specify memory.base_address in layout)")
    return load_bin(p, base_address=base_address, fill=fill), FileFormat.BIN

#########################################################################################

def load_from_text(text: str, *, fill: int = 0xFF) -> Tuple[SparseMemory, FileFormat]:
    kind = detect_format(text)
    if kind == FileFormat.IHEX:
        return load_ihex(text, fill=fill), FileFormat.IHEX
    if kind == FileFormat.SREC:
        return load_srec(text, fill=fill), FileFormat.SREC
    if kind == FileFormat.HEXDUMP:
        return load_hexdump(text, fill=fill), FileFormat.HEXDUMP
    raise ParseError("Unrecognized text format (expected Intel-HEX, S-Record, or hex dump)")

#########################################################################################

def load_bin(path: str | Path, *, base_address: int, fill: int = 0xFF) -> SparseMemory:
    data = Path(path).read_bytes()
    mem = SparseMemory(fill=fill)
    mem.add(int(base_address), data)
    return mem

#########################################################################################

def load_ihex(text: str, *, fill: int = 0xFF) -> SparseMemory:
    if _IntelHexCodec is None:
        raise ParseError("Intel-HEX support requires the 'ihexsrec' package")
    img = _IntelHexCodec.parse_lines(text.splitlines())
    mem = SparseMemory(fill=fill)
    for start, end_excl, data in img.iter_segments():
        mem.add(int(start), bytes(data))
    return mem

#########################################################################################

def load_srec(text: str, *, fill: int = 0xFF) -> SparseMemory:
    if _SrecCodec is None:
        raise ParseError("S-Record support requires the 'ihexsrec' package")
    img = _SrecCodec.parse_lines(text.splitlines())
    mem = SparseMemory(fill=fill)
    for start, end_excl, data in img.iter_segments():
        mem.add(int(start), bytes(data))
    return mem

#########################################################################################

def load_hexdump(text: str, *, fill: int = 0xFF) -> SparseMemory:
    mem = SparseMemory(fill=fill)
    matched_any = False
    for rx in _HEXDUMP_PROFILES:
        for m in rx.finditer(text):
            matched_any = True
            addr = int(m.group(1), 16)
            data = _parse_hex_bytes(m.group(2))
            mem.add(addr, data)
    if not matched_any:
        raise ParseError("Unsupported hexdump format (no known patterns matched)")
    return mem

#########################################################################################
#########################################################################################
