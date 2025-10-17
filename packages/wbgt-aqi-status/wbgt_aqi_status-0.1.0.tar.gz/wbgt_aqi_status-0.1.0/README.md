# wbgt-aqi-status

**What it does:** Looks up today's **Heat Index (HI)** and **PM2.5 AQI**, then reports a practice-day status: **OK / Modify / Cancel** based on configurable thresholds. Designed for coaches/ADs.

**Defaults:**
- HI: OK < 95°F, Modify 95–102°F, Cancel ≥ 103°F
- AQI (US): OK ≤ 100, Modify 101–150, Cancel ≥ 151
- Rule: the stricter of HI vs AQI sets the status.

> Decision-support only. Coaches/trainers make final decisions per district policy.

## Install
```bash
pip install wbgt-aqi-status
