# PK Simulator

Single-compartment oral pharmacokinetic simulator with real-time interactive visualization.

## Features

- Up to 8 doses (first at t=0, then 7 slots with interval in hours from the previous dose)
- Half-life slider (0.5–48 h) with direct numeric input
- Absorption constant Ka (0.1–10 /h)
- Optional secondary curve with modified half-life (Δt½)
- Solid line for observed period, dashed for projection (3×t½ beyond last dose)
- Reference lines: minimum efficacy (1.0, green), steady-state threshold (2.0, red), cleanup threshold (0.1, grey)
- Day markers on the x-axis (1d, 2d, 3d…)
- **Clean** button: toggle x-axis cutoff at the point concentration drops to 0.1
- **Reset** button: restore all parameters to defaults
- Light / dark theme toggle
- Parameters persisted in browser localStorage across sessions

## Model

1-compartment model, first-order oral absorption:

```
C(t) = (Ka / (Ka - Ke)) × (e^(-Ke·t) - e^(-Ka·t))
```

- `Ke = ln(2) / t½`
- Multiple doses: linear superposition
- Y axis: relative concentration (1 = 1 dose unit)
- 2000 time points per curve

## Installation

Requires Python 3.10+.

```bash
git clone https://github.com/ghedo/pk-simulator.git
cd pk-simulator
./run.sh
```

`run.sh` automatically creates a virtual environment and installs dependencies (`dash`, `plotly`, `numpy`, `kaleido`) on first run. The app opens at [http://127.0.0.1:8050](http://127.0.0.1:8050).

Manual install:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install dash plotly numpy kaleido
python pharma_sim.py
```

## Usage

1. Set **Half-Life** with the slider or by typing directly
2. Set **Ka** (absorption rate constant)
3. Enter dose intervals in the dose slots (hours from the previous dose); use the **+**/**−** buttons for ±1 h steps or type any value including 0.5 h increments
4. Optionally set **Δt½** to overlay a second curve with a longer half-life
5. Use **Clean** to zoom the x-axis to the elimination point
6. Use **Reset** to restore all parameters to defaults
7. Use the camera icon on the chart toolbar to export a PNG

---

## License

MIT License. See [LICENSE](LICENSE).

## Author

Luca Ghedini — luca.ghedini@gmail.com

## Development Effort

Built across two sessions using **Claude Code** (claude-sonnet-4-6) with [Caveman mode](https://github.com/anthropics/claude-code) enabled throughout.

### Session 1 — 2026-05-30

Initial build: PK model, interactive UI, dark mode, Clean button, Δt½ overlay.

| Metric | Value |
|--------|-------|
| Duration (calendar) | 156 min (~2.6 h) |
| Duration (active) | 114 min |
| Messages | 164 user / 235 assistant |
| Total tokens | ~18.2 M (17.9 M cache-read) |
| Estimated cost | ~$8.75 |

### Session 2 — 2026-05-31

UI polish and persistence layer.

**Added:**
- Browser localStorage persistence for all parameters (half-life, Ka, doses) across restarts
- Reset button to restore all parameters to defaults
- Custom ±1 h dose buttons (replaced native browser spinners, which snapped unpredictably with `step="any"`)
- "Show until clean" toggle button with active/inactive visual state
- Slider thumb and track colored to match the curve (Dash 4.x uses `dash-slider-*` classes, not `rc-slider-*`)
- Responsive graph (shrinks correctly when browser window narrows)
- Half-life label and value input moved below slider
- Dose rows redesigned: label left, input aligned with Ka/Δt½, ±buttons in absolute position outside input box
- All numeric inputs converted to `type="text"` with `inputMode="decimal"` to eliminate native browser spinners
- Graph margins tuned (equal left/right, tight top/bottom, x-axis title `standoff` reduced)

| Metric | Value |
|--------|-------|
| Caveman mode | full |
