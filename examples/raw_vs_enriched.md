# Raw vs Enriched Data

## Raw (Before DeepSeek)
- Contains full player stats from TeamRankings (e.g., completions, yards, TDs).
- Includes prop odds from SportsGameOdds (by bookmaker).
- Example: `JOSH_ALLEN` has passing stats + FanDuel/DraftKings lines.

## Enriched (After DeepSeek)
- AI analyzes stats vs odds.
- Filters props into only those with **detected misalignments** (good value bets).
- Adds:
  - `confidence`: probability the bet is favorable.
  - `justification`: human-readable reasoning (optional, may be included for debugging).

## Summary
- Raw = **all available stats + odds**.
- Enriched = **actionable betting recommendations**.
- This transformation narrows down noise into insights for parlay construction.
