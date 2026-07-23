"""Run strategy regression backtest via AmiBroker OLE and export the trade list.

Deterministic protocol:
  0. Cleanup Exploration — wipe Universe-Rank static vars
  1. Scan — populate per-symbol daily score snapshots
  2. Finalize Ranks — single-symbol GenerateRanks pass
  3. Portfolio Backtest
  4. Export trade list to CSV

Usage:
    python tools/run_regression.py [output.csv] [apx_path]

Default output: results/Regression_latest.csv
Default project: automation/Backtest_Regression.apx
"""

import sys
import time
from pathlib import Path

import win32com.client

ROOT = Path(__file__).resolve().parents[1]
APX = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else ROOT / "automation" / "Backtest_Regression.apx"
CLEANUP_APX = ROOT / "automation" / "Cleanup_Regression.apx"
FINALIZE_APX = ROOT / "automation" / "Finalize_Ranks.apx"

RUN_SCAN = 0
RUN_EXPLORE = 1
RUN_BACKTEST = 2

STEP_TIMEOUT_S = 3 * 3600
POLL_S = 15


def wait_not_busy(doc, label):
    start = time.time()
    saw_busy = False
    while not doc.IsBusy:
        if time.time() - start > 60:
            break
        time.sleep(1)
    while doc.IsBusy:
        saw_busy = True
        if time.time() - start > STEP_TIMEOUT_S:
            sys.exit(f"TIMEOUT: {label} still busy after {STEP_TIMEOUT_S}s")
        time.sleep(POLL_S)
    print(
        f"{label}: done in {time.time() - start:.0f}s (busy observed: {saw_busy})",
        flush=True,
    )


def main():
    out = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "results" / "Regression_latest.csv"
    out.parent.mkdir(exist_ok=True)
    if out.exists():
        out.unlink()

    ab = win32com.client.Dispatch("Broker.Application")
    print(f"AmiBroker {ab.Version}, database: {ab.DatabasePath}", flush=True)

    def run_helper(apx_path, label):
        hdoc = ab.AnalysisDocs.Open(str(apx_path))
        if hdoc is None:
            sys.exit(f"ERROR: could not open {apx_path}")
        try:
            if not hdoc.Run(RUN_EXPLORE):
                sys.exit(f"ERROR: {label} failed to start")
            wait_not_busy(hdoc, label)
        finally:
            hdoc.Close()

    if not (CLEANUP_APX.exists() and FINALIZE_APX.exists()):
        sys.exit("ERROR: helper APX missing; run tools/make_cleanup_apx.py")

    print("step 0/4: cleanup universe-rank static vars...", flush=True)
    run_helper(CLEANUP_APX, "cleanup")

    doc = ab.AnalysisDocs.Open(str(APX))
    if doc is None:
        sys.exit(f"ERROR: could not open {APX}")

    try:
        print("step 1/4: Scan (populate universe snapshots)...", flush=True)
        if not doc.Run(RUN_SCAN):
            sys.exit("ERROR: Scan failed to start")
        wait_not_busy(doc, "scan")

        print("step 2/4: Finalize ranks (single-threaded)...", flush=True)
        run_helper(FINALIZE_APX, "finalize ranks")

        print("step 3/4: Portfolio Backtest...", flush=True)
        if not doc.Run(RUN_BACKTEST):
            sys.exit("ERROR: Backtest failed to start")
        wait_not_busy(doc, "backtest")

        print("step 4/4: Export trade list...", flush=True)
        doc.Export(str(out))
    finally:
        doc.Close()

    if not out.exists():
        sys.exit(f"ERROR: export did not produce {out}")
    n_rows = sum(1 for _ in open(out, encoding="utf-8", errors="ignore")) - 1
    print(f"exported: {out} ({out.stat().st_size} bytes, {n_rows} trades)")
    if n_rows <= 0:
        sys.exit("ERROR: export contains zero trades")


if __name__ == "__main__":
    main()
