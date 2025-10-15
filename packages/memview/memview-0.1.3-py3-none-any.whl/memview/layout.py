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
from typing import Any, Literal, Optional, List, Dict
from pathlib import Path

from memview.memory import SparseMemory
from memview.errors import LayoutError, MissingDataError

#########################################################################################
#########################################################################################

__all__ = [
    "Segment",
    "Field",
    "Layout",
    "FieldResult",
    "Report",
    "load_layout",
    "inspect",
    "resolve_address",
    "decode_field",
]

#########################################################################################
#########################################################################################

@dataclass(frozen=True)
class Segment:
    name: str
    base: int
    size: int

TypeName = Literal["u8", "u16", "u32", "u64", "bytes", "bitfield", "addr", "str"]
BitOrder = Literal["lsb", "msb"]

#########################################################################################
#########################################################################################

@dataclass(frozen=True)
class Field:
    name: str
    at: str
    type: TypeName
    endian: Optional[Literal["le", "be"]] = None
    size: Optional[int] = None
    bits: Optional[List[Dict[str, Any]]] = None
    encoding: Optional[str] = None
    expect: Optional[int | str] = None
    bit_order: Optional[BitOrder] = None

#########################################################################################
#########################################################################################

@dataclass(frozen=True)
class Layout:
    fill: int
    base_address: Optional[int]
    segments: List[Segment]
    fields: List[Field]
    bit_order: BitOrder

#########################################################################################
#########################################################################################

@dataclass
class FieldResult:
    name: str
    address: int
    type: str
    value: Any
    meta: Dict[str, Any]

#########################################################################################
#########################################################################################

@dataclass
class Report:
    fields: List[FieldResult]
    issues: List[str]

    def to_dict(self) -> dict:
        return {
            "fields": [vars(f) for f in self.fields],
            "issues": list(self.issues),
        }

#########################################################################################
#########################################################################################

def load_layout(path: str | Path) -> Layout:
    path = Path(path)
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore
        except Exception as e:
            raise LayoutError("PyYAML is required to load YAML layouts") from e
        data = yaml.safe_load(text) or {}
    else:
        try:
            import tomllib
        except Exception as e:
            raise LayoutError("Python 3.11+ required for TOML (tomllib)") from e
        data = tomllib.loads(text)
    return _parse_layout_dict(data)

#########################################################################################

def _parse_layout_dict(data: Dict[str, Any]) -> Layout:
    mem = data.get("memory", {})
    fill = int(mem.get("fill", 0xFF)) & 0xFF
    base = mem.get("base_address")
    if base is not None:
        base = _int_auto(base)
    bit_order = str(mem.get("bit_order", "lsb")).lower()
    if bit_order not in ("lsb", "msb"):
        raise LayoutError("memory.bit_order must be 'lsb' or 'msb'")

    segments: List[Segment] = []
    for s in data.get("segments", []):
        try:
            name = s["name"]
            base_addr = _int_auto(s["base"])
            size = _parse_size(s["size"])
        except Exception as e:
            raise LayoutError(f"invalid segment entry: {s!r}") from e
        segments.append(Segment(name=name, base=base_addr, size=size))

    fields: List[Field] = []
    for f in data.get("layout", []):
        try:
            name = f["name"]
            at = f["at"]
            t: TypeName = f["type"]
            endian = f.get("endian")
            size = f.get("size")
            bits = f.get("bits")
            encoding = f.get("encoding")
            expect = f.get("expect")
            f_bit_order = f.get("bit_order")
            if f_bit_order is not None:
                f_bit_order = str(f_bit_order).lower()
                if f_bit_order not in ("lsb", "msb"):
                    raise LayoutError(f"field '{name}' bit_order must be 'lsb' or 'msb'")
        except Exception as e:
            raise LayoutError(f"invalid field entry: {f!r}") from e

        if t not in ("u8", "u16", "u32", "u64", "bytes", "bitfield", "addr", "str"):
            raise LayoutError(f"unsupported type '{t}' in field '{name}'")
        if t == "bytes" and size is None:
            raise LayoutError(f"field '{name}' of type 'bytes' requires 'size'")
        if t == "str" and size is None:
            raise LayoutError(f"field '{name}' of type 'str' requires 'size'")

        fields.append(Field(
            name=name,
            at=at,
            type=t,
            endian=endian,
            size=(None if size is None else _parse_size(size)),
            bits=bits,
            encoding=encoding,
            expect=expect,
            bit_order=f_bit_order,  # type: ignore[arg-type]
        ))

    return Layout(fill=fill, base_address=base, segments=segments, fields=fields, bit_order=bit_order)  # type: ignore[arg-type]

#########################################################################################

def _parse_size(v: Any) -> int:
    if isinstance(v, int):
        return v
    s = str(v).lower().replace("_", "")
    mult = 1
    for suffix, m in (("kb", 1024), ("k", 1024), ("mb", 1024**2), ("m", 1024**2)):
        if s.endswith(suffix):
            s = s[: -len(suffix)]
            mult = m
            break
    return int(s, 0) * mult

#########################################################################################

def _int_auto(v: Any) -> int:
    if isinstance(v, int):
        return v
    return int(str(v), 0)

#########################################################################################

def resolve_address(layout: Layout, at: str) -> int:
    s = at.strip()
    s_low = s.lower()
    if "+" in s and not s_low.startswith("0x"):
        seg_name, off = s.split("+", 1)
        seg_name = seg_name.strip().lower()
        seg = next((x for x in layout.segments if x.name.lower() == seg_name), None)
        if seg is None:
            raise LayoutError(f"unknown segment '{seg_name}' in address '{at}'")
        return int(seg.base) + int(off, 0)
    return int(s, 0)

#########################################################################################

def _read_bytes(mem: SparseMemory, addr: int, size: int) -> bytes:
    data, mask = mem.read(addr, size)
    if 0 in mask:
        missing = sum(1 for b in mask if b == 0)
        raise MissingDataError(f"missing {missing} bytes @0x{addr:X}+{size}")
    return data

#########################################################################################

def _read_int(mem: SparseMemory, addr: int, size: int, endian: str) -> int:
    b = _read_bytes(mem, addr, size)
    return int.from_bytes(b, byteorder=("little" if endian == "le" else "big"), signed=False)

#########################################################################################

def decode_field(layout: Layout, mem: SparseMemory, f: Field, *, default_bit_order: Optional[BitOrder] = None) -> Dict[str, Any]:
    addr = resolve_address(layout, f.at)
    t = f.type
    d: Dict[str, Any] = {"name": f.name, "address": addr, "type": t}

    if t in {"u8", "u16", "u32", "u64"}:
        size = {"u8": 1, "u16": 2, "u32": 4, "u64": 8}[t]
        endian = f.endian or "le"
        val = _read_int(mem, addr, size, endian)
        d["value"] = val
        d["endian"] = endian

    elif t == "bytes":
        if f.size is None:
            raise LayoutError(f"field '{f.name}' of type 'bytes' requires 'size'")
        d["value"] = _read_bytes(mem, addr, int(f.size))
        d["size"] = int(f.size)

    elif t == "bitfield":
        base = _read_int(mem, addr, 1, "le")
        order = (f.bit_order or default_bit_order or layout.bit_order or "lsb")  # type: ignore[operator]
        bits: Dict[str, int] = {}
        for spec in f.bits or []:
            name = str(spec["name"])
            pos = int(spec["bit"])
            if order == "msb":
                pos = 7 - pos
            bits[name] = 1 if ((base >> pos) & 1) else 0
        d["value"] = bits
        d["raw"] = base
        d["bit_order"] = order

    elif t == "addr":
        endian = f.endian or "le"
        val = _read_int(mem, addr, 4, endian)
        d["value"] = val
        d["endian"] = endian

    elif t == "str":
        if f.size is None:
            raise LayoutError(f"field '{f.name}' of type 'str' requires 'size'")
        enc = (f.encoding or "ascii").lower()
        raw = _read_bytes(mem, addr, int(f.size))
        try:
            s = raw.rstrip(b"\x00").decode(enc, errors="replace")
        except LookupError as e:
            raise LayoutError(f"unknown string encoding '{f.encoding}'") from e
        d["value"] = s
        d["encoding"] = enc
        d["size"] = int(f.size)

    else:
        raise LayoutError(f"unsupported type '{t}' in field '{f.name}'")

    if f.expect is not None and isinstance(d.get("value"), int):
        exp = _int_auto(f.expect)
        d["expect_ok"] = (exp == int(d["value"]))
        d["expect"] = exp

    return d

#########################################################################################

def inspect(layout: Layout, mem: SparseMemory, *, default_bit_order: Optional[BitOrder] = None) -> Report:
    results: List[FieldResult] = []
    issues: List[str] = []
    for f in layout.fields:
        try:
            d = decode_field(layout, mem, f, default_bit_order=default_bit_order)
            meta = {k: v for k, v in d.items() if k not in ("name", "address", "type", "value")}
            results.append(FieldResult(
                name=d["name"],
                address=int(d["address"]),
                type=str(d["type"]),
                value=d.get("value"),
                meta=meta,
            ))
        except Exception as e:
            issues.append(f"{f.name}: {e}")
    return Report(fields=results, issues=issues)

#########################################################################################
#########################################################################################