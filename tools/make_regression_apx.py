"""Build automation/Backtest_Regression.apx from Backtest_Seed.apx.

Copies automation/Backtest_Seed.apx, refreshes embedded FormulaContent from
the repo VWAP_01_STRATEGY.afl, and applies date/watchlist/equity knobs.

Usage:
    python tools/make_regression_apx.py [afl_path] [output_apx]

Defaults: VWAP_01_STRATEGY.afl -> automation/Backtest_Regression.apx
"""

import html
import re
import sys
from pathlib import Path

from apx_codec import encode_formula

ROOT = Path(__file__).resolve().parents[1]
SRC_APX = ROOT / "automation" / "Backtest_Seed.apx"
DST_APX = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else ROOT / "automation" / "Backtest_Regression.apx"
AFL = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "VWAP_01_STRATEGY.afl"

FROM_DATE = "2016-01-01 00:00:00"
TO_DATE = "2026-07-13"

# 0-based AmiBroker watchlist index. Edit to match your universe (QQQ/TQQQ).
WATCHLIST_INDEX = 0

# Paper starting NAV ($25,000). Prefer AFL Fixed Position Value for size;
# keep equity large enough that constant-dollar trades are never skipped.
INITIAL_EQUITY = 100_000


def main():
    if not SRC_APX.exists():
        raise SystemExit(f"missing seed project: {SRC_APX}")
    if not AFL.exists():
        raise SystemExit(f"missing strategy AFL: {AFL}")

    apx = SRC_APX.read_text(encoding="utf-8", errors="strict")

    embedded = encode_formula(AFL.read_text(encoding="utf-8"))
    apx = re.sub(
        r"<FormulaContent>.*?</FormulaContent>",
        lambda _: f"<FormulaContent>{embedded}</FormulaContent>",
        apx,
        flags=re.S,
    )

    formula_path = f"<FormulaPath>{html.escape(str(AFL), quote=False)}</FormulaPath>"
    apx = re.sub(r"<FormulaPath>[^<]*</FormulaPath>", lambda _: formula_path, apx)

    apx = re.sub(r"<FromDate>[^<]*</FromDate>", f"<FromDate>{FROM_DATE}</FromDate>", apx)
    apx = re.sub(r"<ToDate>[^<]*</ToDate>", f"<ToDate>{TO_DATE}</ToDate>", apx)
    apx = re.sub(
        r"<(Backtest)?RangeFromDate>[^<]*</(Backtest)?RangeFromDate>",
        lambda m: f"<{m.group(1) or ''}RangeFromDate>{FROM_DATE}</{m.group(2) or ''}RangeFromDate>",
        apx,
    )
    apx = re.sub(
        r"<(Backtest)?RangeToDate>[^<]*</(Backtest)?RangeToDate>",
        lambda m: f"<{m.group(1) or ''}RangeToDate>{TO_DATE}</{m.group(2) or ''}RangeToDate>",
        apx,
    )

    apx = apx.replace(
        "<Category4>0</Category4>", f"<Category4>{WATCHLIST_INDEX}</Category4>"
    )

    apx = re.sub(
        r"<InitialEquity>[^<]*</InitialEquity>",
        f"<InitialEquity>{INITIAL_EQUITY}</InitialEquity>",
        apx,
    )

    DST_APX.write_text(apx, encoding="utf-8")
    print(f"wrote {DST_APX} ({len(apx)} chars)")


if __name__ == "__main__":
    main()
