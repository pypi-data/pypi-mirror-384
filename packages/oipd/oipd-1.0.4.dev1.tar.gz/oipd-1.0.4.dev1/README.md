![OIPD logo](https://github.com/tyrneh/options-implied-probability/blob/main/.meta/images/OIPD%20Logo.png)

[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/oipd?logo=python&logoColor=white)](https://pypi.org/project/oipd/)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/tyrneh/options-implied-probability/blob/main/examples/OIPD_colab_demo.ipynb)
[![Chat on Discord](https://img.shields.io/badge/chat-on%20Discord-brightgreen?logo=discord&logoColor=white)](https://discord.gg/NHxWPGhhSQ)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/oipd?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/oipd)

# Overview

OIPD computes the market's expectations about the probable future prices of an asset, based on information contained in options data. 

While markets don't predict the future with certainty, under the efficient market hypothesis, these collective expectations represent the best available estimate of what might happen.

Traditionally, extracting these “risk-neutral densities” required institutional knowledge and resources, limited to specialist quant-desks. OIPD makes this capability accessible to everyone — delivering an institutional-grade tool in a simple, production-ready Python package.

<p align="center" style="margin-top: 80px;">
  <img src="https://github.com/tyrneh/options-implied-probability/blob/main/example.png" alt="example" style="width:100%; max-width:1200px; height:auto; display:block; margin-top:50px;" />
</p>



# Quick start

#### Installation
```bash
pip install oipd
```

#### Usage

![OIPDwalkthrough](https://github.com/user-attachments/assets/2da5506d-a720-4f93-820b-23b368d074bb)

```python
from oipd import RND, MarketInputs, VolModel
from datetime import date

# 1 ─ point to a ticker and provide market info
market = MarketInputs(
    valuation_date=date.today(),      # the "as-of" date for the analysis
    expiry_date=date(2025, 12, 19),   # option expiry date you care about
    risk_free_rate=0.04,              # annualized risk-free rate
)

# 2 - run estimator, auto fetching data from Yahoo Finance
est = RND.from_ticker("AAPL", market)

# 3 ─ access results and plots
est.prob_at_or_above(120)               # P(price >= $120)
est.prob_below(100)                     # P(price < $100)
est.plot()                              # plot probability and cumulative distribution functions 
smile = est.iv_smile()                  # DataFrame with fitted, bid, and ask IVs by strike
est.plot_iv()                           # visualize fitted IV smile (default: log moneyness axis)
est.plot_iv(x_axis="strike")            # strike-based axis if preferred
curve = est.meta["vol_curve"]                # access fitted smile for diagnostics and JW params
curve.diagnostics.rmse_unweighted             # structured stats (JW params, penalties, optimiser lineage)

from oipd.logging import configure_logging

configure_logging(format_string="%(levelname)s | %(message)s")  # turn on SVI optimiser logs
```

`VolModel` is optional; it defaults to the raw SVI smile for a single expiry. Pass `VolModel(method="svi-jw")` to seed calibration from Jump-Wings parameters or `VolModel(method="bspline")` for the legacy smoother.

### Term-structure surfaces

Calibrate an entire maturity surface with the new `RNDSurface` façade. Every slice is staleness-filtered, parity-adjusted, and vega-weighted before calibration. The default configuration fits an arbitrage-free SSVI surface that enforces the Gatheral–Jacquier calendar and butterfly constraints **by construction**.

```python
from oipd import RNDSurface

surface = RNDSurface.from_ticker(
    "AAPL",
    market,
    horizon="12M",                  # auto-fetch all listed expiries inside the horizon
)

surface.iv(K=[350, 400], t=0.5)      # implied vols at the 6M slice
surface.price(K=[380], t=1.0)        # forward-measure call price via Black-76
diagnostics = surface.check_no_arbitrage()
diagnostics["calendar_margins"]      # per-step calendar spread margins (should be >= 0)
diagnostics["min_theta_phi_margin"]  # Gatheral inequality margins enforced during fit
surface.plot_iv()                               # overlay log-moneyness smiles across maturities
surface.plot_iv(layout="grid")                # per-maturity grid with observed quotes
surface.plot_iv_3d()                           # interactive 3D volatility surface (Plotly)

# Prefer a penalty-stitched raw SVI surface instead of theorem-backed SSVI
raw_surface = RNDSurface.from_dataframe(
    custom_df,
    market,
    vol=VolModel(method="raw_svi"),
)
# When strict_no_arbitrage=True (default) a Gatheral α-tilt is applied automatically
# if independent slices cross; inspect the returned alpha and repaired margins:
raw_surface.check_no_arbitrage()
```

OIPD also **supports manual CSV or DataFrame uploads**. 

#### Diagnostics & validators

- `RNDSurface.check_no_arbitrage()` now reports the optimiser objective, per-interval calendar margins, and SSVI inequality margins.
- `check_butterfly`, `check_ssvi_constraints`, and `check_ssvi_calendar` (under `oipd.core.vol_surface_fitting.shared.svi` / `oipd.core.vol_surface_fitting.shared.ssvi`) expose low-level diagnostics when you need bespoke grids or custom reporting.
- Raw SVI surfaces return an automatic Gatheral α-tilt (`alpha`) and the pre-repair calendar margins so you can see how much was nudged.

See [`TECHNICAL_README.md`](TECHNICAL_README.md) for more details, and the academic theory behind the technique. 

See [more examples](examples/example.ipynb) with provided options data. 


# Use cases

**Event-driven strategies: assess market's belief about the likelihood of mergers**

- Nippon Steel offered to acquire US Steel for $55 per share; in early 2025, US Steel was trading at $30 per share. Using OIPD, you find that the market believed US Steel had a ~20% probability of acquisition (price >= $55 by end of year)
- If you believe that political backlash was overstated and the acquisition was likely to be approved, then you can quantify a trade's expected payoff. Compare your subjective belief with the market-priced probability to determine expected value of buying stock or calls

**Risk management: compute forward-looking Value-at-Risk**

- A 99% 12-month VaR of 3% is (i) backward-looking and (ii) assumes a parametric distribution, often unrealistic assumptions especially before catalysts
- Ahead of earnings season, pull option-implied distributions for holdings. The forward-looking, non-parametric distribution point to a 6% portfolio-blended VaR

**Treasury management: decide the next commodity hedge tranche**

- As an airline, a portion of next year’s jet fuel demand is hedged; the rest floats. Use OIPD to estimate the probability of breaching your budget and the expected overspend (earnings-at-risk) on the unhedged slice
- If OIPD shows higher price risk, add a small 5–10% hedged tranche using to pull P(breach)/EaR back within board guardrails

# Community

Pull requests welcome! Reach out on GitHub issues to discuss design choices.

Join the [Discord community](https://discord.gg/NHxWPGhhSQ) to share ideas, discuss strategies, and get support. Message me with your feature requests, and let me know how you use this. 



# Current Roadmap

Convenience features:
- integrate other data vendors (Alpaca, Deribit) for automatic stock and crypto options data fetching

Algorithmic improvements:
- sequential/eSSVI calibration for even tighter control of calendar spreads
- fit IV smile using SABR model
- infer forward price using a band of near-ATM option-pairs, rather than the one nearest pair
- American-option de-Americanisation module
- Research in conversion from risk-neutral to physical probabilities 

The list describes potential features and research directions; it is neither exhaustive nor a prescribed implementation schedule.
