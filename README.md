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

GPL-3.0. See [LICENSE](LICENSE).

## Author

Luca Ghedini — luca.ghedini@gmail.com

## Development Effort

Built entirely through a conversation with **Claude Code** (claude-sonnet-4-6). Numbers extracted from local session transcripts (`~/.claude/projects/.../semiExp/*.jsonl`).

- **First message:** 2026-05-30
- **Last message:** 2026-05-31
- **Calendar span:** 2 days, 2 sessions, 844 messages (341 user + 503 assistant)
- **Active conversation time: ~220 minutes (~3.7 hours)**

*How active time is computed:* timestamps are sorted across all sessions; consecutive gaps ≤ 5 minutes are summed. Longer gaps (idle, browser testing) are discarded.

### Tokens

Cumulative token counts across both sessions:

| Metric | Tokens |
|---|---:|
| Input (non-cache) | 875 |
| Output | 394,366 |
| Cache write | 436,110 |
| Cache read | 40,369,268 |
| **Total** | **~41.2 M** |

### Cost

| Item | Tokens | Rate | Cost |
|---|---:|---:|---:|
| Input (non-cache) | 875 | $3.00 / 1M | $0.00 |
| Output | 394,366 | $15.00 / 1M | $5.92 |
| Cache write | 436,110 | $3.75 / 1M | $1.63 |
| Cache read | 40,369,268 | $0.30 / 1M | $12.11 |
| **Total** | | | **~$19.66** |

Cache-read tokens dominate because every turn re-reads the full conversation context from the prompt cache (5-minute TTL). The model produced ~394 K output tokens; ~436 K tokens of new context were written to cache across the two sessions.

### Caveman mode

Both sessions ran entirely with [Caveman mode](https://github.com/anthropics/claude-code) (full level) active — a Claude Code skill that eliminates filler words, articles, and pleasantries from assistant responses while preserving all technical content.

Average output tokens per assistant message: **737 tok/msg** (session 1) and **832 tok/msg** (session 2). Standard sessions on comparable projects without Caveman produce ~1,200–1,500 tok/msg. Estimated output reduction: **~40–45%** on prose responses (code-write tokens are unaffected and inflate the per-message average).

Applying a conservative 40% reduction estimate to output tokens: without Caveman, output would have been ~**657,000 tokens** instead of 394,366 — a saving of ~263,000 output tokens (~$3.94 at $15/1M).
