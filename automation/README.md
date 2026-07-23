# Automation projects

## Shipped seed

`Backtest_Seed.apx` — minimal portfolio backtest template pointing at
`Strategy.afl`. Edit watchlist and dates in AmiBroker or via
`tools/make_regression_apx.py` knobs before trusting results.

## Generated projects

Run from the project root:

```powershell
python tools/make_regression_apx.py Strategy.afl automation/Backtest_Regression.apx
python tools/make_cleanup_apx.py <StrategyCode>
```

This produces:

| File | Role |
|------|------|
| `Backtest_Regression.apx` | Main regression backtest (scan + backtest) |
| `Cleanup_Regression.apx` | Wipe rank static vars before a run |
| `Finalize_Ranks.apx` | Single-threaded rank finalize after scan |
| `Cleanup_Regression.afl` / `Finalize_Ranks.afl` | Helper formula sources |

## Before first run

1. Set `WATCHLIST_INDEX` in `tools/make_regression_apx.py` to your watchlist.
2. Set date range (`FROM_DATE`, `TO_DATE`) to match your test universe.
3. Ensure AmiBroker database has data for that range and periodicity (seed uses
   1-minute bars).

## After editing Strategy.afl

```powershell
python tools/sync_apx.py
```

AmiBroker embeds formula text inside `.apx` files; sync keeps them current.
