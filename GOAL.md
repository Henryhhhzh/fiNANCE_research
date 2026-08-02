# Goal: Build One Original, Stress-Tested, Profitable Trading Strategy

**Owner:** Henry
**Written:** 2026-08-02
**Target completion:** 2027-08-01 (12 months)
**Status:** Not started

---

## 0. The one-sentence goal

By **1 August 2027**, I will have one systematic trading strategy that survives a pre-registered
out-of-sample test and 11 named stress tests, is statistically distinguishable from known public
factors, and has traded **6 consecutive months of live paper capital** with net-of-cost performance
inside its backtested confidence bands — documented in a reproducible Git repository that a stranger
could clone and re-run to my exact numbers.

Note what this goal is *not*: it is not "make $X." Money is the output of a process I don't fully
control. The thing I control is whether the process is honest. Profit is a pass/fail threshold inside
the goal, not the goal itself.

---

## 1. Definitions — what each word in the goal means, numerically

Vague words are where self-deception lives. Each of these gets a number so I can't argue with myself
later.

### 1.1 "Profitable"

A strategy is profitable **only if all of these hold simultaneously** on the untouched out-of-sample
(OOS) period, net of the full cost model in §5:

| Metric | Threshold | Why this number |
|---|---|---|
| Net annualised Sharpe (OOS) | ≥ 1.00 | Below 1.0, the edge is indistinguishable from luck at realistic sample sizes |
| Deflated Sharpe Ratio p-value | < 0.05 | Corrects Sharpe for the number of trials I ran (Bailey & López de Prado) |
| Max drawdown (OOS) | ≤ 20% | Above this, I will abandon the strategy emotionally before it recovers |
| Calmar (CAGR / MaxDD) | ≥ 0.75 | Ties return to the pain required to earn it |
| Profit factor | ≥ 1.25 net | Gross ≥ 1.25 is easy; net is the real test |
| % of months positive | ≥ 55% | Guards against one lucky quarter carrying the curve |
| Number of OOS trades | ≥ 200 | Below ~200 the Sharpe standard error is too wide to conclude anything |
| Longest flat period | ≤ 9 months | I must know in advance how long I can be wrong |
| Return concentration | Top 5% of trades contribute < 50% of total P&L | Otherwise it's a lottery-ticket strategy in disguise |

**Absolute dollar target:** none for year one. If the process passes, size comes later.

### 1.2 "Stress-tested"

Passing **all 11 stress tests in §7**, each with a pre-registered pass threshold written *before* the
test is run and committed to Git with a timestamp so I cannot move the goalposts.

### 1.3 "Original"

Original does **not** mean "nobody has ever thought of this." That's unachievable and I shouldn't
pretend otherwise. It means the strategy's returns are **not explained by publicly documented risk
premia**. Operationally:

Regress my strategy's daily returns on this factor set:

- Fama–French 5 factors (Mkt-RF, SMB, HML, RMW, CMA)
- Momentum (UMD / Carhart)
- Short-term reversal (STR)
- Betting-Against-Beta (BAB)
- Time-series momentum (12-1 month, cross-asset)
- Volatility carry (short VIX futures proxy)
- Currency/commodity carry, if the strategy touches those assets

Pass conditions:

- **R² < 0.20** — factors explain less than a fifth of my variance
- **Alpha t-statistic > 3.0** — López de Prado's threshold for multiple-testing-aware significance,
  not the naive 2.0
- **Max pairwise correlation to any single factor < 0.30**
- **Literature check:** I search SSRN, arXiv q-fin, and Google Scholar for my core signal. If I find
  a paper describing exactly it, I must either (a) find a documented modification that materially
  changes the return profile, or (b) discard and start again. I log every search I ran.

---

## 2. Constraints — the real, boring ones

These are non-negotiable facts about my situation. A plan that ignores them isn't realistic.

### 2.1 Legal / account access

- I am 14 and live in New Zealand. The IBKR account is **legally owned by a parent**; I operate it
  under their supervision with their explicit consent. Every login, tax document, and funding
  instruction belongs to the account owner. I will not use anyone's ID but the owner's own.
- **Year one is still paper only** — not for legal reasons now, but because §9's gates say no strategy
  touches real money until it has passed all 11 stress tests and 6 months of paper. Having the account
  doesn't shorten the process; it just means the venue is already solved.
- **IBKR paper account:** free, mirrors the live account's permissions, full API parity. Request it
  from Account Settings. It is the Phase 5 venue.
- Tax: NZ has no CGT, but frequent trading makes me a **trader for income tax purposes** (profits
  taxable as income), and derivatives are additionally caught by the **financial arrangements rules**
  regardless of trading intent. Futures P&L is almost certainly taxable income. Before any live money,
  my parent and I read the IRD guidance and consider whether an accountant is warranted. Budget one
  evening; this is the account owner's liability, not mine.

### 2.2 Time

- School term: **10 hours/week** — 2 weeknights × 2h, Saturday 4h, Sunday 2h.
- School holidays: **20 hours/week**.
- Total year-one budget: roughly **560 hours**. Every phase below has an hour estimate that must sum
  to under this.

### 2.3 Money

| Item | Cost | Decision |
|---|---|---|
| IBKR paper trading account | $0 | **Phase 5 venue** |
| IBKR market data — US Securities Snapshot & Futures Value Bundle | ~US$10/mo, waived if monthly commissions exceed the threshold | Needed for live/paper; verify current price and waiver rule |
| IBKR CME real-time (Level 1, non-professional) | ~US$1–5/mo | Required for MES/MNQ live data |
| Historical 1-min futures data — FirstRate Data | ~US$50–90 **one-time** per symbol, full history | **Primary backtest source** |
| Historical futures data — Databento (CME MDP3) | Pay-as-you-go, tens of dollars for a few years of one symbol | Alternative; better if I need tick/BBO depth |
| Compute | $0 | My laptop. If a backtest takes >30 min, the backtest is wrong, not the laptop |
| VPS for paper trading uptime | ~US$6/mo (Hetzner CX22 or similar) | Phase 5 only |

**Total year-one cash requirement: roughly US$70–150**, most of it a one-time historical data purchase.

**Critical correction now that I have IBKR: IBKR is an execution venue, not a research data source.**
The API's historical endpoints are hard-paced (roughly 6 requests per 2 seconds, ~60 per 10 minutes),
capped in lookback per request, and give no clean way to assemble a long continuous futures history.
Anyone who assumes "I have IBKR, so my data is free" spends three weeks fighting pacing errors and
ends up with a gappy dataset. **I buy history once, and use IBKR only for live/real-time.**

### 2.4 Asset class decision (made now, not later)

**Primary: CME micro equity index futures — MES (Micro E-mini S&P 500), with MNQ (Micro Nasdaq-100)
as the correlated sibling for cross-checks.**

Reasoning, given IBKR:

- **No survivorship bias and no universe construction.** One instrument, continuously existing. This
  removes the single most expensive data problem in the original plan.
- **Exempt from the Pattern Day Trader rule.** US equities in a margin account require US$25,000 to
  day-trade more than 3 times per 5 days. Futures have no such rule. This alone rules out intraday
  equities for a small account.
- **Cheap and deep.** MES is US$5/point, tick 0.25 points = US$1.25, tight one-tick spread during RTH,
  and among the most liquid instruments in the world.
- **Small enough to size honestly.** 1 MES contract is roughly a US$30,000 notional exposure at
  current index levels — meaningful but not absurd, and it's the smallest listed unit so paper→live
  scaling has no discontinuity.
- **Nearly 23 hours a day, 5 days a week** → more observations per calendar year than cash equities.
- IBKR's futures execution and margin treatment are genuinely good, and the API supports the order
  types a systematic strategy needs (bracket orders, adaptive algos, native stops held at the
  exchange).

Honest downsides I'm accepting: index futures are among the most heavily researched instruments on
earth, so §1.3's originality bar is *harder* here than in a backwater. Overnight margin is
meaningfully larger than day margin, and margin requirements rise with volatility — exactly when I'd
least want them to. And leverage is built in, so a sizing bug is far more dangerous than it was in the
crypto plan. §8's limits are load-bearing.

**Secondary (only if primary fails at Phase 3): US equities, *daily* bars, long/short cross-sectional
held multi-day.** Daily holding avoids PDT entirely. This path costs ~US$70/mo for survivorship-bias-
free data (Norgate or Sharadar), so it is a deliberate second choice, not a default.

**Rejected: US equity options.** Assignment risk, a second dimension of data (the full surface),
wide spreads, and pin risk. Too many ways to be wrong at once for a first strategy.

---

## 3. Base rates — what I should honestly expect

Writing this down so future-me can't claim surprise.

- The large majority of retail systematic strategies that look good in backtest fail live. The single
  biggest cause is **overfitting**, second is **understated transaction costs**.
- A genuine, durable retail edge with net Sharpe > 1.0 is uncommon. Achieving it is a real result,
  not a baseline.
- Most edges decay. A strategy that works has a half-life, often 1–3 years. Part of this project is
  building the machinery to *detect* decay, not just to find an edge once.
- **Most likely outcome of this 12 months: I do not find a strategy that passes.** That outcome is
  explicitly a *success* if the process was honest, because I will have built the research
  infrastructure that makes attempt #2 through #50 cheap. §12 defines what I keep either way.

---

## 4. Data specification

### 4.1 What I collect

| Field | Detail |
|---|---|
| Instruments | ES/MES primary, NQ/MNQ secondary. Backtest on the **full-size ES** history (longer, deeper) and trade MES — they track to within a tick |
| Bar resolution | 1-minute OHLCV; aggregate upward as needed. Never downsample-then-lose the raw |
| Range | 2010-01-01 → present. Long enough to contain multiple genuinely different volatility regimes |
| Extra series | Per-contract volume and open interest (needed for roll logic), VIX daily, session boundaries (RTH 13:30–20:00 UTC vs ETH), CME holiday calendar |
| Storage | Parquet, partitioned by contract/year-month, on local disk + one external backup |

### 4.2 Data hygiene rules (each one is a script with a test)

1. **Timestamp audit** — every bar is UTC, monotonic, no duplicates. Assert on load.
2. **Gap log** — every missing bar recorded in `data/gaps.csv` with cause where known. Never silently
   forward-fill; forward-filling into a backtest manufactures fake tradability during outages.
3. **Delisting/relisting log** — any symbol that leaves the universe stays in the dataset with its
   final price and a delist flag. Removing it retroactively *is* survivorship bias.
4. **Outlier flags** — bars with >20% move in 1 minute get flagged, not deleted. I then check whether
   they were real (flash crash) or bad data. Deleting real crashes is how people accidentally build
   strategies that "never lose."
5. **Point-in-time roll** — the "front month" on date D is decided using only volume/OI data available
   *before* D. Rolling on a date I picked by looking at the whole history is lookahead bias.
6. **Checksum manifest** — SHA-256 of every raw file in `data/MANIFEST.txt`. If a number changes, I
   need to know whether the data moved under me.
7. **Session tagging** — every bar labelled RTH / ETH / holiday / half-day. Overnight liquidity is a
   fraction of RTH, and a strategy that unknowingly makes its money at 03:00 UTC is not tradable at
   the size the backtest assumes.

### 4.2b The continuous-contract trap (futures-specific, and the #1 way this plan gets silently ruined)

Futures contracts expire. To backtest across years I need a continuous series, and building it wrong
invalidates everything downstream. The rules:

- **Roll rule:** roll when the next contract's volume exceeds the front contract's for **2 consecutive
  sessions**. For ES this lands roughly 6–9 days before the quarterly expiry (Mar/Jun/Sep/Dec, codes
  H/M/U/Z). The rule is mechanical and uses only past data.
- **Two series, two purposes.** I maintain both:
  - **Back-adjusted (ratio method)** — continuous, gap-free, used *only* for computing returns-based
    indicators (volatility, momentum, z-scores).
  - **Raw per-contract prices** — used for *anything involving an absolute price level*: round-number
    levels, prior-day high/low, fixed-dollar stops, margin, and all order placement.
- **Why this matters:** back-adjustment shifts historical prices by the cumulative roll gap. Ten years
  back, a back-adjusted ES series can differ from the real traded price by hundreds of points, and can
  even go negative on some contracts. A strategy that says "buy at a round 50-point level" tested on
  back-adjusted data is testing levels **that never existed**. This produces beautiful, completely fake
  backtests, and it is not obvious from looking at the equity curve.
- **Roll costs are real costs.** Every roll is a round-trip (close front, open next). At ~4 rolls/year
  that's a fixed drag that must appear in the P&L, not be quietly netted out.
- **Test:** assert that on every roll date, the position transfers with the correct contract multiplier
  and the roll spread is charged. Unit-test this against a hand-computed example.

### 4.3 The data split — decided once, on day one, and never revisited

| Split | Dates | Rule |
|---|---|---|
| **Development** | 2010-01-01 → 2021-12-31 | I may look at this as much as I like |
| **Validation** | 2022-01-01 → 2025-06-30 | Walk-forward only, ≤ 5 total looks, each logged |
| **Sealed holdout** | 2025-07-01 → 2026-07-31 | **Touched exactly once, ever, in Phase 4** |

These dates were corrected on 2026-08-02, before any test was run, because the original split (dev
starting 2019) was inherited from the earlier crypto plan and left **nine of the S1 stress regimes —
Flash Crash, taper tantrum, Aug 2015, Volmageddon, Q4 2018 — outside every split.** Buying 2010–2018
data and never training on it, while claiming to stress-test against those events, would have been
incoherent. Changing this after Phase 3 begins would be goalpost-moving; changing it now costs
nothing.

The sealed holdout is stored in a separate directory, `data/SEALED/`, with a `README` that says what
it's for. If I test on it twice, the second test is worthless and I must find new data or wait for
time to pass. I will write this rule on paper and stick it above my desk.

---

## 5. Cost model — specified before any backtest runs

Backtests are optimistic because costs are guessed. So I specify costs first, and I specify them
pessimistically.

| Cost component | Model (per MES contract) | Notes |
|---|---|---|
| IBKR commission | ~US$0.25/side | Tiered schedule, lowest volume tier — the one I actually qualify for |
| CME exchange fee | ~US$0.37/side | Non-member rate for micro equity index |
| NFA regulatory fee | ~US$0.02/side | |
| **All-in commission** | **~US$0.64/side → US$1.28 round trip** | **Verify against a real IBKR statement in Phase 5 and correct this number** |
| Spread crossing | 1 tick = US$1.25 per round trip during RTH; **2–4 ticks** outside RTH | Modelled per time-of-day from actual data, never as a constant |
| Market impact | Zero at 1–5 contracts. Above ~20 contracts, model `k × (size/ADV)^0.5` | MES depth is deep enough that a small account has no impact — but §7-S9 still forces me to find the size where it appears |
| Roll cost | One full round trip per roll, ~4× per year | Charged explicitly, never netted |
| Slippage buffer | +1 tick on every entry and exit, unconditional | Deliberate pessimism margin |
| Latency | Signal computed on bar close executes at **next bar's open**, never the close | No same-bar fills, ever |

**Do the arithmetic before designing anything.** All-in round trip ≈ US$1.28 commission + US$1.25
spread + US$2.50 pessimism buffer ≈ **US$5.00 per contract round trip**, which at US$5/point is
**1.0 index points.**

That single number kills whole categories of strategy:

| Strategy targets | Cost as % of target | Verdict |
|---|---|---|
| 2-point move | 50% | Dead on arrival |
| 5-point move | 20% | Needs a very high win rate to survive |
| 15-point move | 6.7% | Workable |
| 40-point move (swing) | 2.5% | Comfortable |

**Conclusion, decided now:** I am not building a scalper. Target holding periods produce moves of
**≥ 15 index points**, which in practice means holds of hours to days, not seconds to minutes. This
constraint goes into every hypothesis doc in §6.1.

**Limit-order rule:** if the strategy assumes limit orders, I may not assume they fill. CME uses
strict FIFO queue priority, and at the back of a 2,000-lot queue at the touch, my order fills mainly
when the market is about to move against me — that's adverse selection, and it's the exact opposite of
the free spread the backtest imagines. Default assumption until proven with live queue data:
**100% marketable/taker.**

---

## 6. Research methodology — the anti-overfitting protocol

### 6.1 Hypothesis-first, always

Every strategy idea starts as a written hypothesis in `research/hypotheses/NNN-name.md` **before** any
code runs. Template:

```
ID:          007
Date:        2026-09-14
Hypothesis:  Perp funding rate spikes above the 95th percentile of the trailing 30d
             distribution are followed by mean reversion in the underlying over 4-12h.
Economic
rationale:   Extreme funding means crowded leveraged longs. Liquidation cascades
             mechanically force selling, overshooting fair value.
Who pays me: Over-leveraged retail longs paying to hold their position, plus forced
             liquidation flow.
Why hasn't
it been
arbed away:  [honest answer — if I can't write one, I stop here]
Falsifiable
prediction:  Sharpe > 0.8 net on dev set, effect concentrated in the 4-12h window and
             absent at 48h+.
Kill signal: Effect vanishes when I exclude the March 2020 and May 2021 liquidation
             cascades.
Trials used
before this: 6
```

**"Who pays me and why haven't they stopped?"** is the most important line. A strategy with no answer
is a curve fit that hasn't been caught yet.

### 6.2 Trial counting — the discipline that makes the statistics valid

I maintain `research/TRIALS.csv`: one row per distinct configuration ever backtested — every parameter
tweak, every filter added, every universe change. This number feeds directly into the Deflated Sharpe
Ratio. **If I don't count trials, my p-values are fiction.**

Hard cap: **50 trials per hypothesis family.** At 50, the family is closed. Move on.

### 6.3 Cross-validation

- **Purged K-fold with embargo** (López de Prado). Standard K-fold leaks: if a label depends on the
  next 12 hours of returns, training data adjacent to the test fold contains the answer. I purge
  overlapping samples and add a 24h embargo after each test fold.
- **Combinatorially Purged CV** to compute **PBO (Probability of Backtest Overfitting)**.
  Pass threshold: **PBO < 0.30.**
- **Walk-forward analysis**: 12-month train / 3-month test, rolling 3 months at a time, on validation
  data. All parameters re-fit each window. I report the *concatenated OOS curve*, never the in-sample
  one.

### 6.4 Parameter discipline

- **Maximum 4 free parameters** in the final strategy. Every parameter beyond that must earn its place
  by improving OOS (not IS) Sharpe by ≥ 0.15.
- Parameters must sit on a **plateau, not a spike** — see stress test S3.
- Any parameter with a suspiciously precise value (lookback = 37) gets rounded to something a human
  would pick (35 or 40) and re-tested. If rounding breaks it, it was noise.

---

## 7. The 11 stress tests

Each has a pass threshold written and committed **before** the test runs.

**S1 — Historical regime replay.** Run the strategy through each named window and record P&L, max DD,
and whether risk limits held.

| Regime | Window | What it tests |
|---|---|---|
| Flash Crash | 2010-05-06 | Intraday liquidity vacuum, stop-run, 20-minute round trip |
| US downgrade | 2011-08-01 → 2011-10-04 | Sustained high-vol whipsaw |
| Taper tantrum | 2013-05-22 → 2013-06-24 | Rate-shock regime change |
| Aug 2015 ETF break | 2015-08-24 | Overnight limit-down, opening auction dysfunction |
| Volmageddon | 2018-02-05 → 2018-02-09 | Vol-complex unwind, gap risk |
| Q4 2018 selloff | 2018-10-01 → 2018-12-26 | Grinding drawdown into an illiquid December |
| COVID crash | 2020-02-19 → 2020-03-23 | Correlation-to-1, repeated limit-down halts, margin hikes |
| 2021 melt-up | 2021-01-01 → 2021-12-31 | Low-vol persistent uptrend (kills mean reversion) |
| 2022 grind-down bear | 2022-01-01 → 2022-12-31 | Slow bleed, not a crash |
| SVB / banking stress | 2023-03-08 → 2023-03-20 | Sector contagion, rate-vol spike |
| Yen carry unwind | 2024-08-02 → 2024-08-07 | Overnight global deleveraging, gap through stops |
| 2025 tariff volatility | 2025-04-02 → 2025-04-30 | Macro-policy shock, headline-driven gaps |

**Futures-specific addition to S1:** for each window, also record whether **overnight margin
requirements rose** during the episode (CME raises them in volatility) and whether my position size
would still have been fundable. A strategy that is margin-called out of its position at the bottom
does not get to claim the recovery.

*Pass:* no single regime loses more than **1.5×** the full-period max drawdown, and no regime triggers
a risk-limit breach the system didn't handle programmatically.

**S2 — Cost sensitivity ladder.** Re-run at 1×, 1.5×, 2×, 3×, 5× the modelled cost.
*Pass:* strategy remains net-profitable at **2×** and Sharpe at 2× is ≥ 0.6.
If it dies between 1× and 1.5×, it was never real — it was a cost-model artifact.

**S3 — Parameter surface.** Sweep each parameter ±50% around its chosen value; plot the Sharpe surface.
*Pass:* Sharpe stays within **30%** of peak across the ±25% neighbourhood of every parameter, and the
surface is visually a plateau, not a needle. A needle means I found a hole in the data, not an edge.

**S4 — Execution degradation.** Three variants: (a) delay every signal by one full bar, (b) fill every
order at the *worst* price within the execution bar, (c) randomly drop 10% of signals (simulating
outages/missed fills).
*Pass:* each variant retains ≥ **60%** of baseline Sharpe.

**S5 — Monte Carlo trade resampling.** Stationary block bootstrap (block length ≈ average holding
period) over the trade sequence, 10,000 paths.
*Pass:* **5th percentile** of terminal equity is positive; **95th percentile** of max drawdown ≤ 30%.

**S6 — Monte Carlo permutation test.** Shuffle the price series (preserving return distribution,
destroying temporal structure), re-run the strategy, 1,000 times.
*Pass:* real Sharpe exceeds the **99th percentile** of the permuted distribution. This directly tests
"is there actually signal in the time ordering, or am I trading noise?"

**S7 — Synthetic path testing.** Generate 1,000 synthetic price paths from a fitted GARCH(1,1)-t model
plus a jump component calibrated to observed jump frequency.
*Pass:* median Sharpe on synthetic data is **near zero** if the edge is real. A strategy that also
"works" on synthetic random data is exploiting a statistical artifact, not a market behaviour.
(This test passes by *failing*. It is the least intuitive and most valuable test here.)

**S8 — Regime holdout.** The sealed 2025-07 → 2026-07 data. One shot.
*Pass:* OOS Sharpe ≥ 0.7 and within the **95% confidence interval** implied by the development-period
Sharpe standard error.

**S9 — Capacity analysis.** Compute the AUM at which the strategy's own market impact eats 50% of the
gross edge.
*Pass:* capacity ≥ **US$50,000**. Not because I have that, but because a capacity below it means the
edge is a rounding error that any real cost surprise erases.

**S10 — Data-error injection.** Corrupt 0.5% of bars (bad prints, zero volume, stale quotes, one-tick
spikes) and re-run.
*Pass:* Sharpe degrades by < **15%**, and no corrupted bar causes a position-sizing error, a
divide-by-zero, or an unbounded order. This tests the *code*, not the strategy.

**S11 — Adversarial review.** I write the strongest possible case that my strategy is fake, listing
every remaining way lookahead or survivorship could have entered. Then a second reviewer — a person or
a fresh AI session given only the code and no context — attempts to find the bug.
*Pass:* no unresolved critical finding. Every finding is logged in `research/ADVERSARIAL.md` with its
resolution.

---

## 8. Risk management specification

Written before deployment, enforced in code, not in willpower.

| Control | Rule |
|---|---|
| Position sizing | Volatility targeting: size so each position contributes equal risk at a 15% annualised portfolio vol target |
| Max single position | 25% of equity notional |
| Max gross exposure | 200% (i.e. 2× leverage absolute ceiling) |
| Max net exposure | 100% |
| Per-trade stop | Hard stop at 2× ATR(14), or a time stop at 3× median holding period — whichever hits first |
| Daily loss limit | −3% equity → flatten all, no new positions until next UTC day |
| Weekly loss limit | −7% equity → flatten, mandatory 48h review before re-enabling |
| Drawdown throttle | At −10% from peak, halve position size. At −15%, quarter it. At −20%, full stop and formal review |
| Correlation cap | If pairwise correlation of open positions > 0.7, treat as one position for sizing |
| Kill switch | A single command/file flag that flattens everything and disables new entries. Tested monthly |
| Fat-finger guard | Reject any order > 3× the largest order in the backtest |
| Heartbeat | If no data tick for 60s, flatten and alert. Trading on stale data is how accounts die |
| **Margin headroom** | Never use more than **25%** of account equity as initial margin. Overnight margin at 4× headroom, because CME raises requirements in volatility and IBKR force-liquidates at ~15:50 ET if overnight margin isn't met |
| **Contract count cap** | Hard-coded maximum contracts, computed from account equity, checked on every order. Leverage is built into futures — a sizing bug here is account-ending, not merely expensive |
| **Gap risk acknowledgement** | Stops do **not** cap loss through a gap. Sunday-open and post-headline gaps of 2%+ happen. Size assuming a stop can slip 3× its distance |
| **Event flat rule** | Flat into FOMC/CPI/NFP unless the strategy's edge is explicitly *about* the event and that was pre-registered in its hypothesis doc |

---

## 9. Phase plan with dates and hour budgets

### Phase 0 — Infrastructure (2026-08-02 → 2026-09-13, 6 weeks, ~65h)

Build the machinery before the strategy. Almost everyone does this backwards.

- [ ] Git repo, Python 3.12, `uv` for dependency locking, pre-commit hooks (ruff, mypy)
- [ ] Data downloader with resumability, checksum manifest, gap log
- [ ] Bar/tick loader with the six hygiene assertions from §4.2 as **unit tests**
- [ ] Event-driven backtest engine — no vectorised shortcuts that make lookahead easy to write by
      accident. Engine processes bars strictly in order and cannot see index `i+1`.
- [ ] **Lookahead detector**: a test that runs the strategy on data where all future bars are set to
      NaN. If it still produces signals, it's peeking. This test runs in CI on every commit.
- [ ] Cost model from §5, as a swappable module
- [ ] Metrics module: Sharpe, Sortino, Calmar, max DD, profit factor, DSR, PBO, exposure, turnover
- [ ] Reproducibility: fixed seeds, locked deps, every result file stamped with the Git commit hash
- [ ] Sealed-holdout directory with a load-guard that raises unless an explicit
      `I_AM_RUNNING_THE_FINAL_TEST=1` env var is set
- [ ] **Continuous-contract builder** implementing §4.2b: volume-crossover roll, both back-adjusted and
      raw series, roll costs charged, unit-tested against a hand-computed roll
- [ ] **IBKR connectivity spike** — connect to the paper account with `ib_async` (the maintained
      community successor to `ib_insync`, which is no longer developed), pull live MES quotes, place
      and cancel one paper order. Do this in Phase 0, not Phase 5: discovering an API blocker in month
      10 would be far more expensive than discovering it in month 1.

**Exit gate:** a deliberately-broken "cheating" strategy (one that reads tomorrow's close) must be
*caught* by the lookahead detector. If my harness can't catch a bug I planted on purpose, it can't
catch one I write by accident.

### Phase 1 — Market microstructure literacy (2026-09-14 → 2026-10-11, 4 weeks, ~40h)

I cannot invent something original in a domain I don't understand. Reading list:

- Ernie Chan, *Algorithmic Trading* (strategy archetypes, backtest pitfalls)
- López de Prado, *Advances in Financial Machine Learning* — ch. 3 (labelling), 4 (sample weights),
  7 (purged CV), 11 (backtest overfitting). These four chapters are the core of §6.
- Bailey & López de Prado, *The Deflated Sharpe Ratio* (paper)
- Bailey et al., *The Probability of Backtest Overfitting* (paper)
- Harvey, Liu & Zhu, *…and the Cross-Section of Expected Returns* — why t > 3.0
- CME documentation: ES/MES contract specs, settlement procedure, price limits and halt levels, the
  daily settlement vs last-trade distinction, holiday and half-day calendar
- IBKR documentation: margin methodology (day vs overnight, and the "liquidate at 15:50 ET if
  overnight margin isn't met" behaviour), order types, and the TWS API guide

**Deliverable:** a 3-page written summary of *how an ES futures contract actually works mechanically* —
tick value, roll and expiry, initial vs maintenance vs day margin, how CME price limits and halts
work, what happens on settlement day. If I can't explain it without notes, I'm not ready to trade it.

**Concrete exercise:** hand-compute the P&L, commission, and margin usage of a 3-contract MES trade
held overnight through a roll. Then check my answer against a paper-account statement. Getting this
wrong on paper is free; getting it wrong in code is not.

### Phase 2 — Replication (2026-10-12 → 2026-11-22, 6 weeks, ~60h)

Reproduce three known strategies before inventing one. This validates my harness against known
answers.

1. **Buy-and-hold long ES** — the most important replication. My equity curve must match the S&P 500
   total return to within the cost of carry. If it doesn't, my roll logic or multiplier is wrong, and
   *nothing else I build will be valid.* Do this one first, before anything else.
2. **Opening Range Breakout** on ES 30-minute opening range — a heavily documented intraday strategy.
   Expect it worked well pre-2015 and has substantially decayed. If my backtest says it still prints
   money, I have a cost or lookahead bug.
3. **Time-series momentum (12-1 month)** on the continuous ES series — expect a modest positive Sharpe
   with long flat periods, consistent with the published cross-asset literature.

**Exit gate:** my numbers land in the ballpark of published results. If replication of a known-good
strategy produces Sharpe 4.0, my harness is broken and everything downstream would be fiction. **This
gate catches more bugs than any other step in the plan.**

### Phase 3 — Original research (2026-11-23 → 2027-03-28, 18 weeks, ~180h)

The main event. Cycle: hypothesis → dev-set test → kill or refine. Log every trial.

Candidate directions (each gets a hypothesis doc before any code):

- **Overnight-vs-RTH decomposition.** The well-documented fact is that most of the S&P's return
  historically accrues overnight. The *original* question isn't "is that true" — it's whether the
  overnight premium is **conditional** on something observable at 16:00 ET (prior-day range position,
  VIX term structure slope, RTH volume profile). Conditioning is where the unexploited part might be.
- **Volatility term-structure conditioning.** VIX/VIX3M ratio as a regime switch that selects between
  a trend rule and a reversion rule, rather than as a directional signal in its own right.
- **Post-halt / post-limit behaviour.** Rare, so sample size is the enemy — but genuinely under-studied
  because most researchers exclude these bars as outliers.
- **Scheduled-event conditioning.** Behaviour around FOMC, CPI, and NFP releases — specifically the
  *drift into* the event rather than the reaction to it, which is where the crowded research is.
- **Cross-index dispersion.** MES vs MNQ relative behaviour when their correlation breaks down; a
  relative-value idea rather than a directional one.
- **Roll-period effects.** Does the quarterly roll window itself create exploitable flow? Under-
  researched precisely because most backtests paper over the roll rather than examining it.

Note how each of these is a *conditioning* idea, not a raw signal. Raw signals on ES have been mined
by professionals for forty years. The remaining space is mostly in "when does the known effect apply,
and when does it invert" — and that framing also keeps parameter counts low, which §6.4 requires.

**Rules for this phase:**
- Max 6 hypothesis families. Each capped at 50 trials.
- A hypothesis that fails is **written up and closed**, not quietly resurrected with new parameters.
- No hypothesis proceeds without an answer to "who pays me?"
- Weekly: update `TRIALS.csv`, recompute DSR with the current trial count.

**Exit gate (2027-03-28):** at least one candidate with dev-set Sharpe ≥ 1.3 gross, ≥ 1.0 net, PBO <
0.30, and passing S3, S5, S6, S7. **If nothing qualifies, I do not proceed to Phase 4.** I go back to
Phase 3 with the remaining time, or I declare the year a research success with no deployable
strategy. Forcing a weak candidate forward is the failure mode this gate exists to stop.

### Phase 4 — Full stress battery + sealed holdout (2027-03-29 → 2027-05-02, 5 weeks, ~50h)

- [ ] Run S1–S7 and S9–S10 on the validation set
- [ ] Write the adversarial case (S11), get external review
- [ ] Fix everything found
- [ ] **Then, once:** unseal the holdout, run S8, record the result before analysing it

Write down the expected result *before* unsealing. The gap between expectation and outcome is the most
honest measurement I will get all year.

**Exit gate:** all 11 stress tests pass.

### Phase 5 — Live paper trading (2027-05-03 → 2027-11-01, 6 months, ~4h/week ongoing)

- [ ] Deploy to VPS running **IB Gateway** (not TWS — Gateway is headless and far lighter), driven by
      `ib_async`
- [ ] **Automate the daily restart.** IBKR forces a session restart roughly every 24 hours. Use `IBC`
      (IB Controller) to handle login and auto-restart, and make the strategy flatten before the
      restart window rather than being disconnected while holding a position.
- [ ] Reconnection logic: on disconnect, do **not** blindly resume. Query actual positions from IBKR
      and reconcile against internal state before placing any order. Assuming your state is correct
      after a reconnect is how a strategy ends up double-sized.
- [ ] Native stops resting **at the exchange**, not simulated locally. A local stop is worthless when
      the VPS or the connection dies — which is exactly when you need it.
- [ ] Full logging: every signal, order, fill, rejection, and reconnection
- [ ] **Daily automated report**: P&L, positions, and — critically — **backtest-vs-live divergence**.
      Run the backtest engine on the same live data and diff the two signal streams. Any mismatch is a
      bug in one of them, and I need to know which.
- [ ] Weekly review, 30 min, written
- [ ] Monthly: recompute rolling Sharpe, compare against the backtest's 95% band

**Known bias to correct for: IBKR's paper account fills are optimistic.** It fills limit orders the
moment price touches them, with no queue position and effectively unlimited size at the touch, and it
applies no market impact. For a strategy holding hours-to-days at 1–5 contracts on MES this is a small
distortion; for anything limit-order-dependent it is a large one. **Correction:** the pass threshold
below is measured against the *pessimistic* cost model from §5, not against IBKR's reported paper P&L.
If the two differ by more than 10%, I trust mine.

**Pass:** 6 months with live Sharpe inside the backtest's 95% confidence band, max DD ≤ backtest max
DD × 1.5, and signal-divergence rate < 1%.

### Phase 6 — Live capital decision (2027-11+, out of scope for this goal)

Only with a parent-owned account, their informed consent, and starting capital sized so that a total
loss is genuinely irrelevant to the household. Scale-up gate: +25% account size only after 3 months
inside expected bands.

---

## 10. Kill criteria — when I stop, decided while I'm calm

Written now so that a future me who is emotionally invested cannot negotiate.

**Kill the strategy if:**
- Live/paper drawdown exceeds **1.5×** backtest max DD
- Rolling 90-day live Sharpe < 0 for two consecutive months
- Live-vs-backtest signal divergence > 5% and I can't explain the cause within one week
- The economic rationale is publicly invalidated (e.g., the exchange changes the funding mechanism the
  strategy depends on)
- Realised cost per trade exceeds the modelled cost by > 50%

**Kill the whole project if:**
- I have burned 400+ hours and Phase 2 replication still doesn't reproduce known results — my harness
  is fundamentally wrong and I should switch to a maintained framework instead
- I catch myself testing on the sealed holdout more than once, or editing a pass threshold after
  seeing a result. This is a **hard stop**. Once the discipline breaks, every downstream number is
  meaningless and continuing wastes more time than restarting.

**Explicitly NOT a kill criterion:** a stretch of losing weeks that stays within the modelled
drawdown distribution. That's the strategy working as designed. I decided the tolerance in §8; a
drawdown inside it is information I already paid for.

---

## 11. Anti-self-deception checklist

Run before declaring any result. Every "no" needs a written explanation.

- [ ] Does the backtest use only information available at decision time? (lookahead detector green)
- [ ] Is the universe point-in-time, including delisted instruments?
- [ ] Are costs modelled per-symbol and per-time-of-day, not as a global constant?
- [ ] Do signals execute at next-bar open, never same-bar close?
- [ ] Is the trial count in `TRIALS.csv` accurate and used in the DSR calculation?
- [ ] Did I test the sealed holdout exactly once?
- [ ] Were pass thresholds committed to Git before the test ran? (`git log` proves it)
- [ ] Can I state who is on the other side of my trades and why they keep taking them?
- [ ] **Is every absolute-price-level rule computed on raw contract prices, never back-adjusted ones?**
- [ ] Are roll dates decided from past-only volume data, and are roll costs charged?
- [ ] Does buy-and-hold ES in my engine still match the S&P 500 total return?
- [ ] Would my margin have held through every regime in S1, including the volatility-driven increases?
- [ ] Does the strategy have ≤ 4 free parameters?
- [ ] Would it still work if any single best trade were removed?
- [ ] Did I run it on synthetic random data and confirm it makes *nothing*?
- [ ] Can someone else clone the repo and reproduce my headline number to 3 decimal places?

---

## 12. Deliverables — what exists on 2027-08-01 regardless of outcome

Success and failure produce most of the same artifacts. That's the point.

1. **`trading-research/` Git repo**, public or private, with a README that lets a stranger reproduce
   every number
2. **Backtest engine** with lookahead detection and a passing test suite
3. **Data pipeline** with hygiene tests and gap/delist logs
4. **`research/hypotheses/`** — every hypothesis, including the ~90% that died, each with a written
   post-mortem
5. **`research/TRIALS.csv`** — the complete honest trial count
6. **Stress test report** — all 11 tests, thresholds, results, pass/fail
7. **`research/ADVERSARIAL.md`** — every way I tried to break my own result
8. **Final write-up** (~10 pages): hypothesis, method, results, limitations, what I'd do differently
9. **Learning log** — one paragraph per week, 52 entries

Items 1–5 and 9 exist even if no strategy passes. They are the compounding asset. The strategy is
the depreciating one.

---

## 13. Weekly operating rhythm

| When | Duration | Activity |
|---|---|---|
| Tue evening | 2h | Deep work — current phase task |
| Thu evening | 2h | Deep work — current phase task |
| Saturday | 4h | Main research block (longest uninterrupted stretch) |
| Sunday | 1.5h | Reading (Phase 1 list, then papers) |
| Sunday | 30 min | **Week review**: log entry, update TRIALS.csv, commit everything, set next week's one concrete objective |

Monthly (first Sunday, +1h): re-read this document. Check I haven't drifted, haven't quietly relaxed a
threshold, haven't skipped the trial log. Note any threshold I *want* to change and why — wanting to
change it is itself data.

---

## 14. Success criteria for the goal itself

**Full success:** a strategy passing §1.1, §1.2, §1.3, and Phase 5's 6-month paper test.

**Partial success (and genuinely worth having):** infrastructure built, replication gate passed, ≥ 4
hypothesis families rigorously tested and honestly killed, all deliverables in §12 exist. This is the
**expected** outcome and I should not treat it as failure.

**Failure:** thresholds moved after seeing results; sealed holdout contaminated; trial log incomplete;
or a strategy deployed to real money without passing the gates.

Note the asymmetry: every failure condition is about **honesty**, not about performance. Not finding
an edge is a normal outcome of doing science on efficient markets. Fooling myself into thinking I
found one is the only thing here that can actually cost me money.

---

## 15. First three actions

1. **Today:** `git init trading-research`, commit this file as `GOAL.md`. It is now version-controlled
   and every future edit is visible in `git log`.
2. **This week:** request the IBKR **paper** account, install `ib_async`, connect to it, pull a live
   MES quote, place and cancel one paper order. Small, but it de-risks the whole back half of the plan
   and tells me immediately whether market data permissions are a problem.
3. **Next week:** buy the ES 1-minute history, build the continuous-contract builder from §4.2b, and
   verify it by replicating buy-and-hold ES against the S&P 500 index. If those two curves don't
   match, stop and fix it before writing a single strategy.
