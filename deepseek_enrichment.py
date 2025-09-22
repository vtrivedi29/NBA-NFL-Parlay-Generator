import os
import json
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# CONFIG
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_URL = "https://api.deepseek.com/v1/completions"  

RAW_DATA_DIR = "data/raw"
ENRICHED_DATA_DIR = "data/enriched"
os.makedirs(ENRICHED_DATA_DIR, exist_ok=True)

def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

# DEEPSEEK ENRICHMENT
def run_deepseek_enrichment(compiled_file: str) -> pd.DataFrame:
    """Send compiled player stats + props to DeepSeek for pattern recognition."""
    with open(compiled_file, "r") as f:
        data = json.load(f)

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek-reasoner",
        "messages": [
            {"role": "system", "content": "You are an expert NFL betting analyst. You specialize in identifying bets with misaligned odds."},
            {
                "role": "user", "content": "Analyze this dataset of player stats and betting odds. "
                "Return ONLY valid JSON (no explanations, no markdown) with this structure: "
                "{\"bets\": [{\"player\": \"NAME\", \"bet_type\": \"TYPE\", \"odds\": -110, \"confidence\": 0.72}]} "
                f"Dataset:\n{json.dumps(data)[:4000]}..."
            }
        ]
    }

    print("[INFO] Sending data to DeepSeek API …")
    r = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload, timeout=120)

    if r.status_code != 200:
        raise RuntimeError(f"DeepSeek API error {r.status_code}: {r.text}")

    response = r.json()
    content = response["choices"][0]["message"]["content"]
    print("[DEBUG] Raw DeepSeek content:\n", content[:1000])

    try:
        enriched = json.loads(content)  # Expect DeepSeek to return structured JSON
    except json.JSONDecodeError:
        raise RuntimeError("DeepSeek response was not valid JSON")

    # Save enriched JSON
    out_json = os.path.join(ENRICHED_DATA_DIR, f"enriched_{timestamp()}.json")
    with open(out_json, "w") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)

    print(f"[SUCCESS] Saved enriched data → {out_json}")

    if isinstance(enriched, list):
        return pd.DataFrame(enriched)
    elif isinstance(enriched, dict) and "bets" in enriched:
        return pd.DataFrame(enriched["bets"])
    else:
        raise RuntimeError("Unexpected DeepSeek response format")