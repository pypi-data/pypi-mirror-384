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

from pathlib import Path
import argparse
import sys

from memview.errors import MemViewError, ParseError
from memview.loaders import load_from_path, detect_format, FileFormat
from memview.layout import load_layout, inspect as run_inspect
from memview.reporters import to_text, to_json, to_csv

#########################################################################################
#########################################################################################

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="memview",
        description="Inspect and visualize binary memory layouts."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_insp = sub.add_parser("inspect", help="Decode fields from a binary using a layout (TOML or YAML).")
    p_insp.add_argument("input", help="Path to input file (bin/hex/srec/hexdump)")
    p_insp.add_argument("--layout", required=True, help="Path to layout file (.toml/.yaml/.yml)")
    p_insp.add_argument("--format", choices=["text", "json", "csv"], default="text")
    p_insp.add_argument("--base", type=lambda x: int(x, 0), help="REQUIRED for input formats without addresses (e.g., .bin). Start address in hex or dec.")
    p_insp.add_argument("--fill", type=lambda x: int(x, 0) & 0xFF, default=0xFF, help="Fill byte used for gaps when normalizing memory.")
    p_insp.add_argument("--bit-order", choices=["lsb", "msb"], help="Override default bitfield bit order for this run.")

    args = parser.parse_args()

    try:
        if args.cmd == "inspect":
            return _cmd_inspect(args, parser)
        else:
            parser.error(f"Unknown command: {args.cmd}")
    except MemViewError as e:
        print(f"memview: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("memview: interrupted", file=sys.stderr)
        return 130

#########################################################################################

def _cmd_inspect(args, parser: argparse.ArgumentParser) -> int:
    in_path = Path(args.input)
    text = None
    try:
        text = in_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        text = None

    kind = detect_format(text) if text else None
    base = args.base if kind is None else None

    if kind is None:
        if base is None:
            raise ParseError("Binary input detected (no embedded addresses). Use --base (e.g., --base 0x08000000).")

    layout = load_layout(args.layout)
    mem, detected = load_from_path(in_path, base_address=base, fill=args.fill)

    if args.base is not None and detected in (FileFormat.IHEX, FileFormat.SREC, FileFormat.HEXDUMP):
        print(f"warning: --base ignored for {detected.name}", file=sys.stderr)

    report = run_inspect(layout, mem, default_bit_order=args.bit_order)

    if args.format == "text":
        print(to_text(report))
    elif args.format == "json":
        print(to_json(report, pretty=True))
    elif args.format == "csv":
        print(to_csv(report))
    else:
        parser.error(f"unsupported format: {args.format}")
    return 0 if not report.issues else 2

#########################################################################################

if __name__ == "__main__":
    raise SystemExit(main())

#########################################################################################
#########################################################################################