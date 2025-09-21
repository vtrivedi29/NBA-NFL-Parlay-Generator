import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
RAW_DATA_DIR = "data/raw"
os.makedirs(RAW_DATA_DIR, exist_ok=True)

SGO_API_KEY = os.getenv("SGO_API_KEY")
SGO_EVENTS_V2 = "https://api.sportsgameodds.com/v2/events"

def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def filter_player_props(data: dict) -> list[dict]:
    """
    Extract only player props from the API response.
    Player props always have a playerID ending with _NFL.
    """
    filtered = []
    for event in data.get("data", []):
        event_filtered = {"eventID": event.get("eventID"), "odds": {}}
        for oddID, market in event.get("odds", {}).items():
            pid = market.get("playerID")
            if pid and pid.endswith("_NFL"):
                event_filtered["odds"][oddID] = market
        if event_filtered["odds"]:
            filtered.append(event_filtered)
    return filtered

def fetch_sgo_events(
    league_id: str = "NFL",
    bookmakers: list[str] | None = None,
    limit: int = 100,
    page: int = 1,
):
    """Fetch one page of odds from SportsGameOdds."""
    if not SGO_API_KEY:
        raise RuntimeError("SGO_API_KEY is not set. Put it in your .env as SGO_API_KEY=...")

    params = {
        "apiKey": SGO_API_KEY,
        "leagueID": league_id,
        "oddsAvailable": "true",
        "limit": str(limit),
        "page": str(page),
    }
    if bookmakers:
        params["bookmakerID"] = ",".join(bookmakers)

    print(f"[INFO] Requesting SGO events (page={page}, limit={limit}) …")
    r = requests.get(SGO_EVENTS_V2, params=params, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"SGO API error {r.status_code}: {r.text}")

    return r.json()

def save_json(data, prefix="sgo_events"):
    out = os.path.join(RAW_DATA_DIR, f"{prefix}_{timestamp()}.json")
    with open(out, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[SUCCESS] Saved → {out}")
    return out

def main():
    print("=== NFL Odds Extraction: SportsGameOdds with Player Prop Filtering ===")

    try:
        # Fetch first page
        data = fetch_sgo_events(
            league_id="NFL",
            bookmakers=["fanduel", "draftkings", "prizepicks", "underdog"],
            limit=100,
            page=1,
        )

        # Save full dataset
        save_json(data, prefix="sgo_events_full")

        # Save filtered player props
        filtered = filter_player_props(data)
        save_json(filtered, prefix="sgo_events_playerprops")

        print(f"[INFO] Retrieved {len(data.get('data', []))} events total.")
        print(f"[INFO] Filtered {len(filtered)} events containing player props.")

    except Exception as e:
        print("[ERROR] Could not fetch SGO data:", e)

    print("[DONE] API extraction complete.")

if __name__ == "__main__":
    main()