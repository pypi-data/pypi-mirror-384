# memview

![PyPI - Version](https://img.shields.io/pypi/v/memview?style=for-the-badge)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/memview?style=for-the-badge)
![PyPI - License](https://img.shields.io/pypi/l/memview?style=for-the-badge)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/memview?style=for-the-badge&color=%23F0F)
![PyPI - Downloads](https://img.shields.io/pypi/dm/memview?style=for-the-badge)

Inspect and visualize **binary memory layouts** from multiple input formats (Intel HEX, S-Record, hexdumps, and raw BIN).  
Define a layout once (TOML/YAML), then decode typed fields, verify expectations, and export reports (text/JSON/CSV).

## Highlights

- Unified **sparse memory** model over HEX/SREC/hexdumps/BIN
- Declarative **layout**: segments, typed fields, expectations
- Typed decoders: `u8/u16/u32/u64`, `bytes(size)`, `bitfield`, `addr`, `str(size, encoding)`
- Bitfields with **configurable bit order**: `lsb` (default) or `msb`
- Clean **CLI**: `inspect` → text/JSON/CSV
- Minimal dependencies; install-anywhere

---

## Installation

### Requirements
- Python **3.11+**

### Install
```bash
pip install memview
```

If you’re developing locally with a `src/` layout:
```bash
pip install -e .
```

---

## Input formats

- **Intel HEX** (`.hex`) — parsed with addresses
- **S-Record** (`.srec`, `.s19`, `.mot`) — parsed with addresses
- **Hex dump** (xxd / hexdump -C style) — parsed with addresses
- **Raw BIN** — no addresses; you **must** pass `--base`

---

## CLI

### Inspect a file (layout-aware)
```bash
memview inspect fw.hex --layout fw.toml
```

### Choose output format
```bash
memview inspect fw.hex --layout fw.toml --format text
memview inspect fw.hex --layout fw.toml --format json
memview inspect fw.hex --layout fw.toml --format csv
```

### BIN requires a base address
```bash
memview inspect fw.bin --layout fw.toml --base 0x08000000
```

### Bitfield bit order override (lsb by default)
```bash
memview inspect fw.hex --layout fw.toml --bit-order msb
```

### Exit codes
- `0` — success
- `2` — success with issues (e.g., missing bytes, expectation failures)
- `1` — error

---

## Layout files

Layouts can be **TOML** (recommended) or **YAML** (if `PyYAML` is installed).

### Minimal TOML example

```toml
[memory]
fill = 0xFF
# Optional default bit order for bitfields; defaults to "lsb" if omitted
# bit_order = "lsb"  # or "msb"

[[segments]]
name = "header"
base = 0x08000000
size = 64

[[segments]]
name = "app"
base = 0x08000040
size = 0x70000

[[layout]]
name   = "magic"
at     = "header+0x00"
type   = "u32"
endian = "be"

[[layout]]
name = "flags"
at   = "header+0x04"
type = "bitfield"
# field-level override (optional): bit_order = "msb"
bits = [
  { name = "secure", bit = 0 },
  { name = "debug",  bit = 1 },
  { name = "valid",  bit = 7 }
]

[[layout]]
name   = "length"
at     = "header+0x06"
type   = "u16"
endian = "le"

[[layout]]
name   = "entry_point"
at     = "header+0x08"
type   = "addr"
endian = "le"

[[layout]]
name   = "name"
at     = "header+0x0C"
type   = "str"
size   = 8
encoding = "ascii"

[[layout]]
name   = "payload"
at     = "app+0x00"
type   = "bytes"
size   = 256
```

### Address syntax

- Absolute: `0x08000000`
- Segment + offset: `segmentName+0x04`

### Types (current)

- Scalars: `u8`, `u16`, `u32`, `u64` (with `endian = "le" | "be"`)
- `bytes(size = N)`
- `bitfield` with `bits = [{name, bit}]`  
  - **Bit numbering is LSB-first by default.**  
  - Control via `memory.bit_order = "lsb"|"msb"` or per-field `bit_order`.
- `addr` (4 bytes, endianness controllable)
- `str(size = N, encoding = "ascii" | "utf8")` (trailing NULs trimmed)

### Expectations

For integer-like fields you can set `expect`:

```toml
[[layout]]
name   = "magic"
at     = "header+0x00"
type   = "u32"
endian = "be"
expect = 0xABCD1234
```

If an expectation fails (or bytes are missing), the CLI returns `2` and lists issues.

---

## Examples

### Intel HEX
```bash
memview inspect firmware.hex --layout fw.toml
```

### S-Record
```bash
memview inspect firmware.srec --layout fw.toml --format json
```

### Hex dump (xxd / hexdump -C)
```bash
memview inspect dump.txt --layout fw.toml --format csv
```

### BIN with explicit base
```bash
memview inspect firmware.bin --layout fw.toml --base 0x08000000
```

---

## Output samples

### Text
```
Field              Addr       Type       Value
magic              0x08000000 u32(be)    0xABCD1234
flags              0x08000004 bitfield   {debug=0, secure=1, valid=1}
length             0x08000006 u16(le)    0x0020
entry_point        0x08000008 addr(le)   0x08000040
name               0x0800000C str        TEST
payload            0x08000040 bytes      [256 bytes] sha256=2f5b7b8e2a7f2a8c…
```

### JSON (excerpt)
```json
{
  "fields": [
    {"name":"magic","address":134217728,"type":"u32","value":2882343476,"meta":{"endian":"be"}},
    {"name":"payload","address":134217792,"type":"bytes","value":{"kind":"bytes","len":256,"sha256":"..."},"meta":{"size":256}}
  ],
  "issues": []
}
```

### CSV (first rows)
```
name,address,type,value,meta
magic,0x08000000,u32,0xABCD1234,{"endian":"be"}
flags,0x08000004,bitfield,{debug=0, secure=1, valid=1},{}
...
```

---

## Programmatic API (preview)

```python
from memview.loaders import load_from_path
from memview.layout import load_layout, inspect

layout = load_layout("fw.toml")
mem, kind = load_from_path("firmware.hex", fill=0xFF)
report = inspect(layout, mem, default_bit_order="lsb")
for f in report.fields:
    print(f.name, hex(f.address), f.type, f.value)
```

---

## Behavior and guarantees

- **No base address in layout for BIN.** For raw binaries, the start address must be provided on the command line via `--base`.
- Gaps are filled with `--fill` during normalization; attempts to read missing bytes for a field are reported as issues.
- Overlapping segments on ingest are rejected.
- Bitfield **default** is `lsb`. Precedence:
  1. field-level `bit_order`
  2. CLI `--bit-order`
  3. layout `memory.bit_order`
  4. implicit default `lsb`


## License

MIT © Ioannis D. (devcoons)