import os
import time
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
from glob import glob
from datetime import datetime
from dotenv import load_dotenv
from deepseek_enrichment import run_deepseek_enrichment

#CONFIG
load_dotenv()
RAW_DATA_DIR = "data/raw"
ENRICHED_DATA_DIR = "data/enriched"

SGO_API_KEY = os.getenv("SGO_API_KEY")
SGO_EVENTS_V2 = "https://api.sportsgameodds.com/v2/events"
BASE_URL = "https://www.teamrankings.com/nfl/player-stat/"

STATS = {
    "pass_completions": "passing-plays-completed",
    "pass_attempts": "passing-plays-attempted",
    "passing_yards_gross": "passing-gross-yards",
    "passing_touchdowns": "passing-touchdowns",
    "interceptions": "passing-plays-intercepted",
    "longest_pass": "passing-longest-yards",
    "passing_rushing_yards": "passing-and-rushing-yards",
    "qb_rating": "qb-rating-nfl",
    "rush_attempts": "rushing-plays",
    "rushing_yards": "rushing-net-yards",
    "rushing_touchdowns": "rushing-touchdowns",
    "longest_rush": "rushing-longest-yards",
    "rushing_receiving_yards": "rushing-and-receiving-yards",
    "rushing_receiving_touchdowns": "rushing-and-receiving-touchdowns",
    "receptions": "receiving-receptions",
    "receiving_yards": "receiving-yards",
    "receiving_touchdowns": "receiving-touchdowns",
    "longest_receptions": "receiving-longest-yards",
    "pass_targets": "receiving-targeted",
    "points_kicking": "kicking-points",
    "solo_tackles": "defense-solo-tackles",
    "total_touchdowns": "total-touchdowns",
}

# API FUNCTIONS
def filter_player_props(data: dict) -> list[dict]:
    """Extract only player props with playerID ending in _NFL."""
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

def save_json(data, prefix="sgo_events_props"):
    out = os.path.join(RAW_DATA_DIR, f"{prefix}_{timestamp()}.json")
    with open(out, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[SUCCESS] Saved → {out}")
    return out

# SCRAPER FUNCTIONS
def fetch_with_backoff(url: str, retries: int = 5) -> str:
    """Fetch a webpage with exponential backoff."""
    delay = 2
    for attempt in range(retries):
        try:
            print(f"[INFO] Fetching {url} (attempt {attempt+1}) …")
            r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            return r.text
        except requests.RequestException as e:
            print(f"[WARN] Request failed: {e}")
            if attempt < retries - 1:
                print(f"[INFO] Retrying in {delay}s …")
                time.sleep(delay)
                delay *= 2  # exponential backoff
            else:
                raise RuntimeError(f"Failed after {retries} attempts: {url}")

def parse_table(html: str, stat_name: str) -> pd.DataFrame:
    """Parse the table and return only Player + Value columns."""
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        raise ValueError("No table found in HTML")

    df = pd.read_html(str(table))[0]

    # Ensure only Player + Value
    if "Player" not in df.columns or "Value" not in df.columns:
        raise ValueError("Expected Player and Value columns not found")

    df = df[["Player", "Value"]].copy()
    df["Player"] = df["Player"].apply(normalize_name)
    df = df.rename(columns = {"Value": stat_name})
    return df

def scrape_stats() -> pd.DataFrame:
    """Scrape all TeamRankings stats and merge."""
    merged_df = None
    for stat_name, path in STATS.items():
        url = BASE_URL + path
        try:
            html = fetch_with_backoff(url)
            df = parse_table(html, stat_name)

            if merged_df is None:
                merged_df = df
            else:
                merged_df = pd.merge(merged_df, df, on="Player", how="outer")

            print(f"[INFO] Added {stat_name} ({len(df)} rows)")
            time.sleep(5)
        except Exception as e:
            print(f"[ERROR] Failed to process {stat_name}: {e}")

    return merged_df

# DATA COMPILING FUNCTIONS
def load_player_props() -> pd.DataFrame:
    """Load player props JSON and flatten bookmaker odds."""
    props_files = glob(os.path.join(RAW_DATA_DIR, "sgo_events_playerprops_local*.json"))
    if not props_files:
        print("[WARN] No props file found.")
        return pd.DataFrame()

    latest_file = sorted(props_files)[-1]
    print(f"[INFO] Using latest props file: {latest_file}")

    with open(latest_file, "r") as f:
        data =json.load(f)

    rows = []
    for event in data:
        for oddID, market in event.get("odds", {}).items():
            row = {
                "playerID": market.get("playerID"),
                "statID": market.get("statID"),
                "oddID": oddID,
            }
            # flatten bookmaker odds
            for book, details in market.get("byBookmaker", {}).items():
                row[book] = details.get("odds", None)
            rows.append(row)

    df = pd.DataFrame(rows)
    if not df.empty:
        df["Player"] = df["playerID"].apply(lambda pid: "_".join(pid.split("_")[:2]) if pid else None)
    return df

def save_compiled(df: pd.DataFrame, prefix="players_compiled"):
    out_csv = os.path.join(RAW_DATA_DIR, f"{prefix}_{timestamp()}.csv")
    out_json = os.path.join(RAW_DATA_DIR, f"{prefix}_{timestamp()}.json")
    df.to_csv(out_csv, index=False)
    df.to_json(out_json, orient="records", indent=2)
    print(f"[SUCCESS] Saved compiled data → {out_csv}, {out_json}")

# MISC FUNCTIONS
def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def normalize_name(name: str) -> str:
    """Convert 'First Last' -> 'FIRST_LAST' to match 'playerID'."""
    return name.strip().upper().replace(" ", "_").replace(".", "").replace("'", "")

def calculate_parlay_odds(odds_list):
    """Convert American odds list into decimal multipliers, then back to parlay odds."""
    decimal_odds = []
    for odd in odds_list:
        if int(odd) > 0:  # positive American odds
            decimal_odds.append((odd / 100) + 1)
        else:  # negative American odds
            decimal_odds.append((100 / abs(odd)) + 1)
    parlay_decimal = 1
    for d in decimal_odds:
        parlay_decimal *= d
    # Convert back to American odds
    if parlay_decimal >= 2:
        parlay_american = int((parlay_decimal - 1) * 100)
    else:
        parlay_american = int(-100 / (parlay_decimal - 1))
    return parlay_decimal, parlay_american

def drop_players_with_no_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop players who have null values for all stat columns.
    This ensures we only keep players with at least one meaningful stat.
    """
    # Identify stat columns = everything except ID/props/metadata
    non_stat_cols = {"Player", "playerID", "statID", "oddID", "odds", "confidence", "bet_type"}
    stat_cols = [col for col in df.columns if col not in non_stat_cols]

    print(f"[INFO] Checking {len(df)} players across {len(stat_cols)} stat columns")

    # Drop rows where ALL stat columns are NaN
    cleaned = df.dropna(subset=stat_cols, how="all")
    print(f"[INFO] After cleaning: {len(cleaned)} players remain")

    return cleaned

# MAIN
def main():
    print("=== NFL Odds Extraction: SportsGameOdds with Player Prop Filtering ===")
    data = None

    try:
        # Fetch first page
        data = fetch_sgo_events(
            league_id="NFL",
            bookmakers=["fanduel", "draftkings", "prizepicks", "underdog"],
            limit=100,
            page=1,
        )

        # Save full dataset
        save_json(data, prefix="sgo_events_props")
        print(f"[INFO] Retrieved {len(data.get('data', []))} events total.")

    except Exception as e:
        print("[ERROR] Could not fetch SGO data:", e)

    if data:
        filtered = filter_player_props(data)
        save_json(filtered, prefix="sgo_events_playerprops_local")
        print(f"[SUCCESS] Filtered {len(filtered)} events → sgo_events_playerprops_local")
    else:
        print("[WARN] No data available to filter.")

    print("[DONE] API filter complete.")

    print("=== Compiling Stats + Props into One Dataset ===")
    stats_df = scrape_stats()
    print(f"[INFO] Scraped stats for {len(stats_df)} players across {len(stats_df.columns)-1} categories.")

    props_df = load_player_props()
    print(f"[INFO] Loaded {len(props_df)} props.")

    if not props_df.empty:
        compiled_df = pd.merge(stats_df, props_df, on="Player", how="outer")
    else:
        compiled_df = stats_df

    compiled_df = drop_players_with_no_stats(compiled_df)

    save_compiled(compiled_df)

    print("[DONE] Compilation and filtering complete.")

    print("=== DeepSeek Enrichment + Parlay Builder ===")

    compiled_files = sorted([f for f in os.listdir(RAW_DATA_DIR) if f.startswith("players_compiled") and f.endswith(".json")])
    if not compiled_files:
        print("[ERROR] No compiled dataset found in data/raw/")
        return
    latest_file = os.path.join(RAW_DATA_DIR, compiled_files[-1])

    enriched_df = run_deepseek_enrichment(latest_file)

    while True:
        try:
            num_legs = int(input("Enter number of legs for your parlay: "))
            break
        except ValueError:
            print("[ERROR] Please enter a valid integer.")

    if num_legs > len(enriched_df):
        print("[WARN] Not enough recommended bets, reducing to available bets.")
        num_legs = len(enriched_df)

    parlay_bets = enriched_df.sort_values(by="confidence", ascending=False).head(num_legs)

    while True:
        try:
            stake = float(input("Enter your stake ($): "))
            break
        except ValueError:
            print("[ERROR] Please enter a valid number.")

    odds_list = parlay_bets["odds"].tolist()
    parlay_decimal, parlay_american = calculate_parlay_odds(odds_list)
    payout = round(stake * parlay_decimal, 2)

    print("\n=== Recommended Parlay ===")
    print(parlay_bets[["player", "bet_type", "odds", "confidence"]])
    print(f"\nParlay odds: {parlay_american} (decimal {round(parlay_decimal, 2)})")
    print(f"Stake: ${stake:.2f}")
    print(f"Potential payout: ${payout:.2f}")

if __name__ == "__main__":
    main()