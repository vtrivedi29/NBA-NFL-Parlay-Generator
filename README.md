# NFL Player Prop Parlay Analyzer

## Overview
This project builds an **end-to-end ETL pipeline** for analyzing NFL player prop bets.  
It extracts betting odds and player stats, transforms them into a unified dataset, enriches the data with **DeepSeek AI**, and outputs actionable betting insights, including **parlay construction** and **payout calculations**.

---

## Workflow
1. **Extract**
   - Odds from [SportsGameOdds API].
   - Player stats scraped from [TeamRankings.com].

2. **Transform**
   - Normalize player names into `FIRSTNAME_LASTNAME`.
   - Merge stats with player prop odds.
   - Output compiled dataset in `data/raw/players_compiled_<timestamp>.csv/json`.

3. **Enrich (DeepSeek)**
   - Send compiled dataset to DeepSeek for pattern recognition.
   - Identify misalignments between stats and odds.
   - Recommend bets with higher-than-implied probabilities.
   - Save enriched output in `data/enriched/`.

4. **Parlay Builder**
   - User specifies number of parlay legs and stake amount.
   - Program selects top recommended bets.
   - Calculates combined parlay odds and potential payout.
   - Displays results.

---

## File Structure
```
├── data/
│   ├── raw/            # compiled datasets (stats + odds)
│   ├── enriched/       # DeepSeek-enriched betting recommendations
├── main.py             # user interaction & parlay builder
├── deepseek_enrichment.py # API integration with DeepSeek
├── requirements.txt    # dependencies
├── DEEPSEEK_USAGE.md   # documentation of DeepSeek prompts and setup
├── ETHICS.md           # ethical considerations
└── README.md           # project overview
```
---

## Installation
```
bash
git clone <repo-url>
cd nfl-parlay-analyzer
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set up your environment variables in .env:
```
SGO_API_KEY=
DEEPSEEK_API_KEY=
```
