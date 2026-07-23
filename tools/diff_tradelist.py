"""Compare two AmiBroker trade-list CSV exports trade-for-trade.

Exit code 0 = identical, 1 = mismatch.

Usage:
    python tools/diff_tradelist.py <golden.csv> <candidate.csv>
"""

import sys

import pandas as pd

KEY_COLS = [
    "Symbol",
    "Trade",
    "Date",
    "Price",
    "Ex. date",
    "Ex. Price",
    "Shares",
    "Profit",
    "Exit Reason",
]


def load(path):
    df = pd.read_csv(path)
    missing = [c for c in KEY_COLS if c not in df.columns]
    if missing:
        sys.exit(f"ERROR: {path} is missing columns: {missing}")
    df = df[KEY_COLS].copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df["Ex. date"] = pd.to_datetime(df["Ex. date"])
    for c in ("Price", "Ex. Price", "Profit"):
        df[c] = df[c].astype(float).round(4)
    return df.sort_values(["Date", "Symbol", "Trade"]).reset_index(drop=True)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    golden_path, cand_path = sys.argv[1], sys.argv[2]
    g, c = load(golden_path), load(cand_path)

    print(f"golden   : {len(g)} trades  ({golden_path})")
    print(f"candidate: {len(c)} trades  ({cand_path})")

    if len(g) == len(c) and g.equals(c):
        print("RESULT: IDENTICAL")
        return 0

    gk = g.assign(_k=g.astype(str).agg("|".join, axis=1))
    ck = c.assign(_k=c.astype(str).agg("|".join, axis=1))
    only_g = gk[~gk["_k"].isin(set(ck["_k"]))].drop(columns="_k")
    only_c = ck[~ck["_k"].isin(set(gk["_k"]))].drop(columns="_k")

    print(f"RESULT: MISMATCH  ({len(only_g)} only-in-golden, {len(only_c)} only-in-candidate)")
    with pd.option_context("display.width", 200, "display.max_columns", 20):
        if len(only_g):
            print("\n--- only in golden (first 10) ---")
            print(only_g.head(10).to_string(index=False))
        if len(only_c):
            print("\n--- only in candidate (first 10) ---")
            print(only_c.head(10).to_string(index=False))
    return 1


if __name__ == "__main__":
    sys.exit(main())
