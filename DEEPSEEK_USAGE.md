# DeepSeek Usage Documentation

## Purpose
DeepSeek is used in this project as the **enrichment step** of the ETL pipeline. After compiling NFL player statistics (from TeamRankings) and betting odds (from SportsGameOdds), we pass this dataset to DeepSeek for **pattern recognition**. The model’s role is to:

1. Identify misalignments between player stats and betting odds.  
2. Recommend bets that have a higher probability of hitting than the implied odds suggest.  
3. Output a structured JSON of recommended bets, including:
   - `player`
   - `bet_type`
   - `odds`
   - `confidence`

These recommendations are then used to build parlays and calculate potential payouts based on user input.

---

## Model
We configured DeepSeek with a chat-completion style API call:

- **Model**: `deepseek-bet-analyst` (placeholder, replace with actual deployed model name).
- **Endpoint**: `https://api.deepseek.com/v1/chat/completions`

---

## Prompting Strategy
We use a two-message approach:

- **System Message**
```
You are an expert NFL betting analyst. You specialize in identifying bets with misaligned odds.
```

- **User Message**
```
Analyze this dataset of player stats and betting odds.
Return a JSON with recommended bets including: player, bet_type, odds, confidence.
Dataset:
{<compiled player stats + odds>}
```

### Important Prompt Notes
- We instruct the model to return **only JSON** to simplify parsing.  
- The dataset is truncated if too large, to avoid token limit errors.  
- Confidence is expected as a numeric probability (e.g., `0.72` meaning 72%).  

---
## Example Expected Output
```
json
{
"bets": [
  {
    "player": "JOSH_ALLEN",
    "bet_type": "passing_yards",
    "odds": -110,
    "confidence": 0.72
  },
  {
    "player": "TYREEK_HILL",
    "bet_type": "receiving_yards",
    "odds": -105,
    "confidence": 0.68
  }
]
}
```
