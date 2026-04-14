# IGRIS

![GitHub Repo stars](https://img.shields.io/github/stars/Amir-web66/IGRIS?style=social)

> If you like this project, consider giving it a star — it helps a lot!

**IGRIS** is a local personal dashboard for tracking daily habits, study sessions, and self-discipline 
updated to be with ML behavioral analysis.
No cloud. No account. No tracking.
Just you and your data.

--updated 14/4/2026


---

## What it does

- **Daily habit tracking** — define your own habits and side tasks, check them off each day
- **Live study timer** — start/pause/resume, every session is logged with timestamps
- **Skill forge** — create custom skills that unlock when you complete the right habits consistently
- **AI brain analysis** — Python ML reads your data and produces: momentum score, burnout risk, tomorrow's prediction, habit correlation, anomaly detection
- **Analytics dashboard** — 6 charts: score trend, habit radar, study hours, mood, sleep, screen vs study
- **Full history** — every day stored locally in JSON

---

## Stack

| Layer | Tech |
|---|---|
| Frontend | HTML + CSS + vanilla JS |
| Charts | Chart.js |
| Backend | Node.js (tiny local HTTP server) |
| Data | JSON files on your machine |
| ML Analysis | Python 3 (stdlib only ) |

No frameworks. No database. No internet required after first load (fonts are cached).



---

## Setup

### Requirements
- [Node.js](https://nodejs.org) (LTS) — for the local server
- [Python 3](https://python.org) — optional, for AI insights

### Install & Run

```bash
git clone https://github.com/Amir-web66/IGRIS.git
cd igris
```

Then **double-click `START.bat`** (Windows) — or run:

```bash
node server.js
```

Dashboard opens at `http://localhost:3737`

On first launch, IGRIS will walk you through a setup to define your name, habits, and skills.

---

## Project structure

```
igris/
├── START.bat          ← double-click launcher (Windows)
├── server.js          ← local Node.js server
├── analyze.py         ← Python ML analysis script
├── public/
│   └── index.html     ← the full dashboard (single file)
└── data/              ← created on first run, gitignored
    ├── brain_data.json
    └── insights.json
```

---

## Privacy

All data stays on your machine. The `data/` folder is in `.gitignore` — your entries, sessions, and insights are **never committed**.

To back up your data, copy the `data/` folder anywhere you want.

---

## Customization

- **Habits** — add/remove anytime from the dashboard
- **Skills** — define your own: pick a name, icon, color, and which habits are required
- **Avatar** — drop an `avatar.jpg` into `public/` (gitignored by default)
- **Quotes** — edit the `QUOTES` array in `index.html`

---

## AI Insights (Python)

The `analyze.py` script runs automatically when you save data. It produces:

| Insight | Description |
|---|---|
| **Momentum score** | 0–100, combines streak + score trend + sleep + mood |
| **Burnout risk** | Detects bad patterns in last 3 days |
| **Tomorrow prediction** | Estimates next day score from current trajectory |
| **Top habits** | Which habits statistically correlate with your best days |
| **Anomaly detection** | Flags unusual drops or bad day combinations |
| **Skill trajectory** | % progress toward each skill at current pace |
| **Best day pattern** | Sleep/study/screen profile of your highest-scoring days |

No external libraries needed — pure Python standard library.

---

## Auto-start with Windows

1. Press `Win + R` → type `shell:startup` → Enter
2. Create a shortcut to `START.bat` and place it in that folder

IGRIS will open silently in the background every time you log in.

## Contribution

Any feedback, ideas, or suggestions are welcome — they help improve and evolve IGRIS.

---

Born in December 2025, IGRIS evolved from a simple paper idea into a working local system, which we hope will be useful.
