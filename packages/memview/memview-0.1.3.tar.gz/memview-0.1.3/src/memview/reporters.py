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

from __future__ import annotations

#########################################################################################
# IMPORTS                                                                               #
#########################################################################################

import io
import json
import hashlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from memview.layout import Report, FieldResult

#########################################################################################
#########################################################################################

def to_text(report: "Report") -> str:
    lines = []
    lines.append(f"{'Field':18} {'Addr':10} {'Type':10} Value")
    for f in report.fields:
        addr = f"0x{int(f.address):08X}"
        typ = _fmt_type(f)
        val = _fmt_value(f)
        lines.append(f"{f.name:18} {addr:10} {typ:10} {val}")
    if report.issues:
        lines.append("")
        lines.append("Issues:")
        for msg in report.issues:
            lines.append(f"- {msg}")
    return "\n".join(lines)

#########################################################################################

def to_json(report: "Report", *, pretty: bool = True) -> str:
    payload = {
        "fields": [_field_to_json(f) for f in report.fields],
        "issues": list(report.issues or []),
    }
    if pretty:
        return json.dumps(payload, ensure_ascii=False, indent=2)
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

#########################################################################################

def to_csv(report: "Report", *, header: bool = True) -> str:
    import csv
    buf = io.StringIO()
    w = csv.writer(buf)
    cols = ["name", "address", "type", "value", "meta"]
    if header:
        w.writerow(cols)
    for f in report.fields:
        w.writerow([
            f.name,
            f"0x{int(f.address):08X}",
            f.type,
            _fmt_value(f),
            json.dumps(_field_meta(f), ensure_ascii=False, separators=(",", ":")),
        ])
    if report.issues:
        w.writerow([])
        for msg in report.issues:
            w.writerow([f"# ISSUE: {msg}"])
    return buf.getvalue()

#########################################################################################
#########################################################################################

def _fmt_type(f: "FieldResult") -> str:
    t = getattr(f, "type", "")
    meta = getattr(f, "meta", {}) or {}
    if t in {"u16", "u32", "u64"} and "endian" in meta:
        return f"{t}({meta.get('endian')})"
    if t == "addr" and "endian" in meta:
        return f"{t}({meta.get('endian')})"
    return str(t)

#########################################################################################

def _fmt_value(f: "FieldResult") -> str:
    v = getattr(f, "value", None)
    t = getattr(f, "type", "")
    if isinstance(v, int):
        width = {"u8": 2, "u16": 4, "u32": 8, "u64": 16}.get(t, 8)
        return f"0x{v:0{width}X}"
    if isinstance(v, (bytes, bytearray)):
        n = len(v)
        if n <= 16:
            return " ".join(f"{b:02X}" for b in v)
        h = hashlib.sha256(v).hexdigest()[:16]
        return f"[{n} bytes] sha256={h}…"
    if isinstance(v, dict):
        items = ", ".join(f"{k}={_fmt_kv(v[k])}" for k in sorted(v))
        return f"{{{items}}}"
    return str(v)

#########################################################################################

def _fmt_kv(x):
    if isinstance(x, bool):
        return "1" if x else "0"
    if isinstance(x, int):
        return str(x)
    return str(x)

#########################################################################################

def _field_meta(f: "FieldResult") -> dict:
    return dict(getattr(f, "meta", {}) or {})

#########################################################################################

def _field_to_json(f: "FieldResult") -> dict:
    v = getattr(f, "value", None)
    if isinstance(v, (bytes, bytearray)):
        jv = {"kind": "bytes", "len": len(v), "sha256": hashlib.sha256(v).hexdigest()}
    else:
        jv = v
    return {"name": f.name, "address": int(f.address), "type": f.type, "value": jv, "meta": _field_meta(f)}

#########################################################################################
#########################################################################################
