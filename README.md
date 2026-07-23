# Strategy scaffold

Copy this entire folder into `AFL_DEV`, rename it to your strategy name, and
`git init`. Do **not** copy SharedAFL — strategies `#include` it via absolute
paths.

## Quick start

1. Copy `_StrategyScaffold` → `AFL_DEV\MyIdea` (rename folder).
2. `cd MyIdea` and `git init`.
3. Open `Strategy.afl`; set a unique `StrategyCode` (e.g. `"MIDE"`).
4. Replace the SIGNAL section; keep SharedAFL `#include`s unchanged.
5. Edit knobs at the top of `tools/make_regression_apx.py` if needed:
   - `WATCHLIST_INDEX` — 0-based AmiBroker watchlist index
   - `FROM_DATE` / `TO_DATE`
   - `INITIAL_EQUITY`
6. Generate analysis projects:

   ```powershell
   python tools/make_regression_apx.py Strategy.afl automation/Backtest_Regression.apx
   python tools/make_cleanup_apx.py MIDE
   ```

7. Run backtest + export:

   ```powershell
   python tools/run_regression.py results/Latest.csv automation/Backtest_Regression.apx
   ```

8. After edits to `Strategy.afl`, refresh embedded formula text:

   ```powershell
   python tools/sync_apx.py
   ```

## Layout

| Path | Purpose |
|------|---------|
| `Strategy.afl` | Thin signal file over SharedAFL plumbing |
| `automation/` | AmiBroker `.apx` projects (generated + helpers) |
| `tools/` | Regression harness (OLE backtest runner, APX sync) |
| `results/` | CSV exports (gitignored except `.gitkeep`) |

## SharedAFL

Plumbing lives at `g:\OneDrive\01_TRADING\AFL_DEV\SharedAFL\lib\`. Each lib
documents its `REQUIRES` / signal contract in the file header. See
`SharedAFL\docs\contracts.md`.

## Optional renames

You may rename `Strategy.afl` → `MyIdea_Strategy.afl`. Update
`tools/sync_apx.py` (`MAIN_AFL` and `KNOWN`) and pass the new path to
`make_regression_apx.py`.

## Not included

ORB live auto-trade batch, chart `.ALY` templates, pre-market scan, and IB
fan-out stay in the ORB repo until a strategy graduates to production.

## Regression determinism

If your strategy uses the universe rank gate, always run via
`tools/run_regression.py` (cleanup → scan → finalize ranks → backtest). See
`ORB\lessons\regression-gate-determinism.md` for why.
