---
name: markov-2-amibroker
description: >
  Markov 2.0 Hedge Fund Regime Method — AmiBroker AFL implementation.
  Builds a stride-sampled 3×3 transition matrix (BULL / SIDEWAYS / BEAR),
  computes the stationary distribution, and generates a regime-differential
  signal. Implements the three documented statistical fixes. Use when the user
  asks to add Markov regime analysis, a regime filter, or a market state signal
  to an Amibroker AFL formula. No external data or Python required — all
  computation runs inside Amibroker on the user's own database.
---

# Markov 2.0 — AmiBroker AFL Skill

## When you are invoked

Read this file first, then act. The user wants to apply the Markov 2.0 regime
method inside Amibroker using AFL (AmiBroker Formula Language). Everything runs
locally against their own data. There is no yfinance, no Python, no installs.

Begin with a 4-line brief:
1. What Markov 2.0 does (states → transition matrix → signal).
2. Which file they need (Explore for analysis, Signal for trading).
3. The one question you must answer before proceeding: FILTER or STANDALONE?
4. Ask them to type **go** when ready.

Then wait for **go** before generating or modifying any AFL code.

---

## The method

### States (default)
Label each bar as **BULL**, **SIDEWAYS**, or **BEAR** using the 20-bar
cumulative return of the symbol's Close price:

- BULL      : return ≥ +5 %
- BEAR      : return ≤ −5 %
- SIDEWAYS  : everything else

State indices in all AFL code: **0 = BEAR, 1 = SIDEWAYS, 2 = BULL**.

### Transition matrix
Count state→state transitions, row-normalise to probabilities (each row sums
to 1.0). The diagonal is **stickiness** — the probability that a regime
persists to the next period. Report the diagonal prominently; it is the
load-bearing number.

### Signal
`Signal = P(next = BULL | current) − P(next = BEAR | current)`

- Positive → bullish conviction (magnitude = strength)
- Negative → bearish conviction
- Near zero → regime is ambiguous / sideways

### Multi-step forecasts
Raise the matrix to a power n (matrix power) to forecast n periods ahead.
Note that as n → ∞ every row converges to the stationary distribution — long-
horizon forecasts carry no signal beyond the base-rate regime mix.

---

## The three fixes (non-negotiable)

### FIX 1 — Stride sampling (autocorrelation fix)
**Never** build the matrix from overlapping rolling windows. Consecutive 20-day
windows share 19 bars, which artificially inflates diagonal persistence.

**Always** count transitions between **non-overlapping** windows:
- Stride = Window (default 20 bars)
- Transition pairs: `State[0] → State[20]`, `State[20] → State[40]`, etc.
- In AFL: inside a loop, only count when `(i % Window) == 0`; from-state is
  `State[i - Window]`, to-state is `State[i]`.

**Always** show **both** matrices — overlapping (legacy) and stride-sampled
(true) — side by side with a one-line warning that only stride is valid.
Never suppress the overlapping matrix; the comparison teaches the user why FIX 1
matters (overlapping diagonal will always be higher).

### FIX 2 — Label verification
After building the matrix, **self-check the state labels**. Print the first 5
stride periods (raw return + assigned state) to Amibroker's Output window via
`_TRACE()`. This lets the user verify that their data's known bull/bear periods
map correctly before trusting any matrix values.

If a user reports that BULL and BEAR look swapped, check the threshold signs and
the `IIf` ordering in the `State` array calculation — never flip the labels by
changing display order.

### FIX 3 — Two explicit modes (always ask; never leave ambiguous)

**FILTER mode** (default):
> Markov gates an existing strategy. Longs are only allowed when
> `Signal > threshold`, shorts only when `Signal < −threshold`, flat otherwise.
> The user's entry/exit logic stays theirs; Markov decides **when** it is
> allowed to act.

**STANDALONE mode**:
> Trade the signal directly. `Signal > threshold → Buy`, `Signal < −threshold
> → Short` (if enabled), else flat. Position size scales to `|Signal|` capped
> at `MaxPosSizePct`.

If the user has not specified a mode, ask exactly once:
> "Which mode: FILTER (Markov gates your strategy) or STANDALONE (trade the
> signal directly)?" Then wait for an answer before writing any Buy/Sell logic.

---

## AFL implementation reference

Two AFL files live alongside this SKILL.md:

### `Markov_Regime_Explore.afl`
- **Purpose**: Exploration formula — analysis, not trading.
- **Output**: Per-symbol columns showing current state, signal, both 3×3
  matrices (overlapping + stride), stationary distribution.
- **Run it when**: User wants to scan a watchlist for regime conviction or
  inspect the matrix for a single symbol.
- **How to run**: Analysis → New Analysis → Explore. Sort the "Signal%" column
  descending to surface high-conviction bullish setups.

### `Markov_Regime_Signal.afl`
- **Purpose**: Generates `Buy`, `Sell`, `Short`, `Cover` arrays for backtesting
  and chart display.
- **FIX 3 embedded**: Mode = FILTER (index 0) or STANDALONE (index 1) via
  `ParamList`.
- **FILTER mode**: User replaces the `MyBuy / MySell / MyShort / MyCover`
  placeholder arrays (marked clearly in the file) with their own strategy
  signals. The Markov gate applies automatically.
- **STANDALONE mode**: Buys on first bar crossing into `BullGate`, exits when
  signal falls below threshold. Position size scales to `|Signal|`.
- **Chart**: Plots a signal histogram panel beneath price with threshold lines.

---

## AFL syntax rules (follow exactly)

These rules reflect Amibroker AFL behaviour. Violating them produces silent
wrong results or syntax errors.

1. **State indices**: always `0 = BEAR, 1 = SIDEWAYS, 2 = BULL`. Never remap
   or reorder them — FIX 2 verifies against this mapping.

2. **Loop structure for stride sampling**:
   ```afl
   for (i = Window; i < BarCount; i++)
   {
       if ((i % Window) == 0)
       {
           fs = State[i - Window];   // from-state
           ts = State[i];            // to-state
           // count into st## counters
       }
   }
   ```

3. **Row normalisation** — always guard against zero rows:
   ```afl
   r0s = Max(st00 + st01 + st02, 1);
   P00s = st00 / r0s;
   ```

4. **Stationary distribution** via power iteration (left eigenvector):
   ```afl
   pi0 = 1/3; pi1 = 1/3; pi2 = 1/3;
   for (k = 0; k < 50; k++)
   {
       np0 = pi0*P00s + pi1*P10s + pi2*P20s;
       np1 = pi0*P01s + pi1*P11s + pi2*P21s;
       np2 = pi0*P02s + pi1*P12s + pi2*P22s;
       pi0=np0; pi1=np1; pi2=np2;
   }
   ```
   `pi0` = long-run BEAR probability, `pi1` = SIDEWAYS, `pi2` = BULL.

5. **Signal array** (always use stride matrix `P##s`, never overlapping `P##o`):
   ```afl
   Signal = IIf(State==0, P02s - P00s,
            IIf(State==1, P12s - P10s,
                          P22s - P20s));
   ```

6. **ParamList returns an integer index** (0, 1, …), not a string:
   ```afl
   ModeParam = ParamList("Mode", "FILTER|STANDALONE", 0);
   if (ModeParam == 0) { /* FILTER */ }
   else                { /* STANDALONE */ }
   ```

7. **Daily compression** — always wrap in TimeFrameSet/Restore so the formula
   is safe on any chart interval:
   ```afl
   TimeFrameSet(inDaily);
   dClose = Close;
   TimeFrameRestore();
   C_d = TimeFrameExpand(dClose, inDaily, expandLast);
   ```

8. **SetBarsRequired** — set to at least `Window * 20` so there is enough
   history for a meaningful stride count:
   ```afl
   SetBarsRequired(Window * 20, 0);
   ```

9. **_TRACE for Output window** — use `_TRACE(string)` for diagnostic output.
   Open via View → Output Window in Amibroker. Do not use `printf` for this
   purpose; `_TRACE` is the correct function.

10. **ExRem dedup** — always apply after setting Buy/Short:
    ```afl
    Buy   = ExRem(Buy,   Sell);
    Short = ExRem(Short, Cover);
    ```

---

## Lookahead bias warning (always surface this)

The full-history matrix build has **lookahead bias**: the matrix is estimated
from all available data and then applied to every historical bar, including
early bars that would not yet have seen later data. This is fine for regime
characterisation and parameter exploration. It will flatter backtest P&L.

For a genuine walk-forward:
- Split the analysis range: first N% of bars = training, remainder = test.
- Build the matrix from training bars only, then apply the fixed matrix to
  test bars.
- Tell the user to increase their Analysis range and use the `TrainPct` param
  pattern to do the split.

Always state this caveat when discussing backtest results. Use the phrase:
> "The fixed matrix shows the honest numbers for the test period — those are
> the only ones worth comparing to live trading."

---

## Optional enhancements (offer, don't force)

- **Enhanced states**: cluster on 20-day return + ATR% + relative volume so
  "bear and violent" ≠ "bear and asleep". Implement via `IIf` chains on
  combined thresholds. Report how the matrix and signal change vs price-only.
- **Multi-day forecast**: raise P to power n via repeated matrix multiplication.
  Report that convergence to stationary means n > ~30 carries no incremental
  signal.
- **Asymmetric thresholds**: separate Bull and Bear threshold params (already
  in both AFL files as `BullThreshPct` and `BearThreshPct`).
- **Regime ribbon on price chart**: `PlotOHLC` or `bgcolor` with regime colour
  array, using `styleArea | styleOwnScale` in a lower panel.

---

## What you never do

- Do not fetch external data or suggest Python/yfinance. The user's data is in
  Amibroker.
- Do not use the overlapping matrix for any trading signal or recommendation.
- Do not leave FILTER vs STANDALONE ambiguous. Ask once if unclear.
- Do not swap BULL and BEAR state indices mid-formula. Fix 2 assumes
  `0=BEAR, 1=SIDEWAYS, 2=BULL` everywhere.
- Do not add error handling, git branches, or other features not requested.
- Do not run a demo — the user will run against their own data.
