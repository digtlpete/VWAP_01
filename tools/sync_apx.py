"""Refresh embedded FormulaContent of .apx project files from disk.

Usage:
    python tools/sync_apx.py            # sync all automation/*.apx
    python tools/sync_apx.py FILE.apx   # sync one project
"""

import html
import re
import sys
from pathlib import Path

from apx_codec import encode_formula

ROOT = Path(__file__).resolve().parents[1]
MAIN_AFL = ROOT / "VWAP_01_STRATEGY.afl"

KNOWN = {
    "VWAP_01_STRATEGY.afl": MAIN_AFL,
    "Strategy.afl": MAIN_AFL,  # legacy FormulaPath alias
}


def sync(apx_path: Path) -> bool:
    apx = apx_path.read_text(encoding="utf-8", errors="strict")
    m = re.search(r"<FormulaPath>([^<]*)</FormulaPath>", apx)
    if not m:
        print(f"skip {apx_path.name}: no FormulaPath")
        return False
    name = Path(html.unescape(m.group(1)).replace("\\\\", "\\")).name
    src = KNOWN.get(name)
    if src is None or not src.exists():
        print(f"skip {apx_path.name}: no repo source for '{name}'")
        return False

    embedded = encode_formula(src.read_text(encoding="utf-8"))
    new_apx = re.sub(
        r"<FormulaContent>.*?</FormulaContent>",
        lambda _: f"<FormulaContent>{embedded}</FormulaContent>",
        apx,
        flags=re.S,
    )
    if new_apx == apx:
        print(f"ok   {apx_path.name}: already in sync")
        return False
    apx_path.write_text(new_apx, encoding="utf-8")
    print(f"SYNC {apx_path.name}  <-  {src.relative_to(ROOT)}")
    return True


def main():
    if len(sys.argv) > 1:
        targets = [Path(sys.argv[1]).resolve()]
    else:
        targets = sorted((ROOT / "automation").glob("*.apx"))
        targets = [
            t
            for t in targets
            if t.name not in ("Backtest_Regression.apx", "Cleanup_Regression.apx")
        ]
    changed = sum(sync(t) for t in targets)
    print(f"done: {changed} project(s) updated")


if __name__ == "__main__":
    main()
