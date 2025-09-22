# AI Usage Log
Used **ChatGPT** for this assignment.

## Prompt Used
"You are the best idea analyzer in the world and your insight is incredibly useful in everything you find. I need you to come up with a feasibility report and find resources that would assist me in a project about NBA and NFL player prop bet generation. First, read through the assignment details to better grasp what I need to do. I was thinking of finding one source that contains the odds across different sports books if not a source that is the actual book itself. I would like the second source to be previous statistics from the NBA for all players. I would then like deepseek to effectively analyze the previous data and find betting lines that can be exploited because of small details that only AI would be able to notice. Output a feasibility report and then a table of sources, how I would access the data in those sources(webscraping/API), whether robots.txt allows me to scrape, why that source is included, and any other important bits of information for me to know. thanks, you are the best and I am counting on you."

## Summary of Response
The response provided a **detailed feasibility report** for building a pipeline that ingests:
1. **Player prop odds** across multiple sportsbooks (via Odds API or similar).
2. **Historical player statistics** (NBA via Balldontlie, NFL via nflverse).

It outlined:
- An **ETL + AI enrichment plan** with DeepSeek, focusing on feature engineering, anomaly detection, cross-book arbitrage, and context-aware insights (injury, usage, travel, weather).
- A **source comparison table** detailing access method (API vs scraping), robots.txt/ToS issues, inclusion rationale, and caveats like rate limits or cost.
- **Implementation guidance** (how to fetch odds, normalize stats, align player IDs, backtest props).
- **Risk/legal considerations**, highlighting that NBA.com’s robots.txt disallows API scraping, sportsbooks discourage scraping, and aggregator APIs are safer.
- **Deliverables mapping to the assignment**: raw/enriched data folders, DeepSeek enrichment module, usage documentation, examples, and a README.

This ensures compliance with the project structure while demonstrating creative AI usage for detecting exploitable inefficiencies in betting lines.

## Prompt
"I think i only want to focus this for NFL because I am only allowed to use exactly two sources. So besides The Odds API, what is a website I can scrape for the stats that would help in finding inefficiencies in the books?"

## Summary of Response
I recommended **Pro-Football-Reference (PFR / Sports-Reference)** as the best website to scrape for NFL stats because it offers deep game logs, box scores, player usage, team splits, and historical coverage. I explained:

- **Why PFR:** breadth of stats, strong community tooling, widely used for backtesting edges.  
- **Robots.txt & policy:** PFR robots.txt allows most stat pages but disallows dynamic/search paths. Sports-Reference explicitly asks for respectful scraping (rate-limits, caching, attribution) and discourages commercial redistribution without licensing.  
- **Scraping plan:** focus on player game logs, box scores, snap counts, and team pace/opponent splits; parse tables via `pandas.read_html` or BeautifulSoup; cache results to reduce load.  
- **Alternatives:** nflfastR (preferred if programmatic data release counts as a “source”), paid APIs like Sportradar, or other sites (less reliable).  
- **Best practice checklist:** obey robots.txt, throttle requests, cache raw HTML, attribute PFR, avoid heavy concurrency.  

Final recommendation:  
- Use **Pro-Football-Reference** as the second source (scraped responsibly).  
- If allowed, prefer **nflfastR** releases for cleaner, safer data ingestion.

## Prompt
"Now, you are the greatest software engineer in the world. I need you to create a script that extracts data from TheOdds API and nflfastR and stores it into a file for raw_data. This will later be used in the context of the rest of the project which will incorporate an ETL pipeline that uses DeepSeek API to find patterns in stats and use those patterns to predict a way to beat the odds. Users will input the number of legs they would like in a parlay. But remember, only extract the data first and we will complete the other steps later. Write this in a Python script for main.py and include whatever libraries I would need to download in a requirements.txt script"

## Summary of Response
I provided a working **Python extraction script (`main.py`)** and a **requirements file**:

- **`main.py`:**
  - Fetches NFL player prop odds from **The Odds API** (via HTTP requests).
  - Fetches play-by-play data for selected seasons from **nflfastR (via nfl_data_py)**.
  - Saves Odds API data as a **JSON** file and nflfastR data as a **Parquet** file.
  - All files are stored in the `/data/raw/` directory with timestamped filenames.
  - API key is read from an environment variable (`ODDS_API_KEY`).

- **`requirements.txt`:**
  - `requests` for API calls.
  - `pandas` for data handling.
  - `nfl_data_py` to pull nflfastR datasets.
  - `pyarrow` for saving Parquet files.

- **Notes:**  
  - Users must set their Odds API key as an environment variable.  
  - This is only the **extraction stage**; transformation, enrichment, and DeepSeek analysis will come later.  
  - The script is designed to slot directly into the larger ETL pipeline.

This output sets up the raw data ingestion pipeline that your project will build on.

- **Changes Veyd made:**
  - Increased the variety of markets being extracted from Odds API

## Prompt
"can i sample the last few weeks of 2024 as well as the first few weeks of 2025 so i have a stronger amount of data? and then adjust main.py so that every week it will update but still contain the same number of weeks of recent data"

## Summary of Response
I explained that combining the **last few weeks of the 2024 season** with the **first few weeks of 2025** gives a larger and more stable dataset, since three weeks of 2025 alone is too volatile.  
I outlined a rolling strategy:
- Always keep a **fixed number of weeks** (e.g., 8) of the most recent data.  
- Each week, fetch the newest week and drop the oldest, maintaining the same window length.  
- If early in the season, fill in with late-season data from the prior year.  

I then provided an updated `main.py` script that:
- Defines a function `get_latest_completed_week(season)` 
- Pulls season schedule from `nfl_data_py` and detects most recent completed week
- Defines a function `fetch_recent_weeks(current_season, rolling_weeks)`
- Uses result from `get_latest_completed_week(current_season)` 
- Pulls weekly data from `nfl_data_py` for the current season.  
- If needed, backfills with late weeks from the prior season.  
- Combines and saves the result as a timestamped Parquet file in `/data/raw/`.  

**Example behavior:**  
At 2025 week 3 with an 8-week window → pulls weeks 1–3 from 2025 and weeks 15–18 from 2024. Later in the season, it only uses 2025 weeks.  

This ensures the dataset always reflects the most recent N weeks for prediction.

- **Changes Veyd made:**
  - Increased the ROLLING_WEEKS value to 10 instead of 8

## Prompt
"I am getting this error:
RuntimeError: Odds API error: 422 {"message":"Invalid markets:  player_pass_completions,  player_pass_interceptions,  player_pass_longest_completion,  player_pass_yds,  player_reception_tds,  player_reception_yds,  player_rush_longest,  player_rush_reception_tds,  player_rush_reception_yds,  player_rush_tds,  player_rush_yds","error_code":"INVALID_MARKET","details_url":"https://the-odds-api.com/liveapi/guides/v4/api-error-codes.html#invalid-market"}
It doesn't make sense because this document shows all the markets as valid for NFL: https://the-odds-api.com/sports-odds-data/betting-markets.html#nfl-ncaaf-cfl-player-props-api"

## Summary of Response
I explained that the `422 INVALID_MARKET` error happens because **not all listed betting markets are supported for every sport**. The Odds API documentation lists *all possible markets* across sports, but the NFL only supports a subset at any given time.

Key points:
- Some of the requested markets (e.g., `player_rush_reception_tds`, `player_rush_reception_yds`) **do not exist** or are not supported for NFL, causing the error.
- The Odds API provides an endpoint to discover valid markets for a specific sport:
[https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds-markets/?apiKey=YOUR_KEY]
- Safe, commonly supported NFL markets include:
- `player_pass_tds`
- `player_pass_yds`
- `player_rush_yds`
- `player_rec_yds`
- `player_anytime_td`
- The fix is to **use only valid markets** for NFL, confirmed via the `odds-markets` endpoint.

**Recommendation:** Update `MARKETS` in `main.py` to only include supported markets (e.g., `"player_pass_tds,player_pass_yds,player_rush_yds,player_rec_yds,player_anytime_td"`). Add a helper function to print available NFL markets dynamically if desired.

## Prompt
"Two things:
1. the only market i can use in OddsAPI is h2h which is not applicable to my project. find another API that I can use for player prop odds and if non exists, we're going to scrape something.
2. I am getting an error related to the read_parquet function of pandas. how would I address this?"

## Summary of Response
**1. Alternate Playe [oai_citation:8‡Sports Game Odds - API Data](https://sportsgameodds.com/player-prop-odds-api-providers-2025/?utm_source=chatgpt.com):**
- I listed several APIs that *do* or *might* offer player prop odds:
  - **SportRadar**
  - **OddsJam**
  - **Sports Game Odds (SGO)**
  - **OpticOdds**
- Advantages/disadvantages: cost, coverage, request limits.
- Scraping n [oai_citation:9‡Sports Game Odds - API Data](https://sportsgameodds.com/player-prop-odds-api-providers-2025/?utm_source=chatgpt.com)possible targets are sportsbooks or odds-comparison sites, but check `robots.txt` and ToS.

**2. Fixes for read_parquet Errors:**
- Common causes:
  - Miss [oai_citation:10‡Sports Game Odds - API Data](https://sportsgameodds.com/alternatives-to-the-odds-api/?utm_source=chatgpt.com)ibraries.  
  - Parquet file is empty or corrupted.  
  - Version mismatches (Pandas vs. Parquet engine).
- Proposed fixes:
  - Install required parquet engine libs (`pyarrow`, maybe `fastparquet`).  
  - Upgrade ver [oai_citation:11‡OpticOdds](https://opticodds.com/?utm_source=chatgpt.com)cks: file exists, size > 0.  
  - Wrap `pd.read_parquet` in try/except to catch ImportErrors or invalid file errors.

**3. Actionable tweaks:**
- Update `requirements.txt` to include `pyarrow` (and optionally `fastparquet`).  
- Add helper code to read parquet safely (verifying file size, existence).  
- Investigate one of the alternate odds APIs; sample a player-prop market to see if it works for your needs.

## Prompt
"interpret this robots.txt for teamrankings.com:
User-agent: GPTBot
Disallow: /

User-agent: Amazonbot
Disallow: /

User-Agent: *
Disallow: /ajax/
Disallow: /libraries/
Disallow: /common/
Disallow: /config/
Disallow: /admin/
Disallow: /xml/
Allow: /
Disallow: /scripts/
Crawl-delay: 10

does this mean i can scrape this page? https://www.teamrankings.com/nfl/player-stats/"

## Summary of Response
I explained the rules in TeamRankings’ `robots.txt`:

- **GPTBot** and **Amazonbot** are fully disallowed from crawling any pages.  
- **All other bots** are disallowed from crawling specific directories (`/ajax/`, `/libraries/`, `/common/`, `/config/`, `/admin/`, `/xml/`, `/scripts/`) but are explicitly allowed to crawl all other paths.  
- A **crawl delay of 10 seconds** is requested, meaning scrapers should wait 10 seconds between requests.

Applied to the URL `https://www.teamrankings.com/nfl/player-stats/`:
- The path `/nfl/player-stats/` is not disallowed.  
- Therefore, crawlers (other than GPTBot and Amazonbot) **may access this page** under robots.txt.  
- The crawl-delay rule means scraping should be **rate-limited** to at most one request every 10 seconds.

⚠️ I also noted that **robots.txt is not the same as legal permission**. You should check TeamRankings’ Terms of Service to ensure compliance, and always scrape responsibly (rate-limiting, caching, attribution).

**Answer:** Yes, robots.txt allows scraping this page if you respect the crawl-delay and ToS.

**What Veyd did:**
- I checked the ToS and there was no mention of scraping/automated data collection

## Prompt
"So now, with this information, rewrite main.py so that we scrape TeamRankings and use the SportsGameOdds API and keep the same functionality as intended"

## Summary of Response
I replaced The Odds API and nflfastR data sources with:
1. **SportsGameOdds API** (SGO) → fetches NFL player prop odds.  
2. **TeamRankings.com** → scraped player stats from the page `https://www.teamrankings.com/nfl/player-stats/`.  

### New `main.py`
- **SportsGameOdds integration**
  - Uses `requests` with Bearer token authentication (`SGO_API_KEY` in `.env`).
  - Saves API responses as JSON in `/data/raw/` with timestamped filenames.
- **TeamRankings scraper**
  - Uses `requests` + `BeautifulSoup` + `pandas.read_html`.
  - Extracts the stats table and saves it as CSV in `/data/raw/`.
  - Implements a polite crawl with custom User-Agent and a 10-second delay (per robots.txt).
- **Main workflow**
  - Attempts to fetch odds and scrape stats.
  - Catches and logs errors without breaking the pipeline.
  - Prints success messages and stores all outputs in `/data/raw/`.

### Updated `requirements.txt`
```
requests
pandas
beautifulsoup4
lxml
python-dotenv
```
### Key Notes
- `.env` must include `SGO_API_KEY`.
- Both odds and stats are timestamped and stored under `data/raw/`.
- Script maintains original ETL-friendly structure for later DeepSeek enrichment.

**Answer:** The new script extracts NFL player prop odds via the SportsGameOdds API and scrapes NFL player stats from TeamRankings, storing both in raw data files for downstream use.

## Prompt
I realized that all player prop `playerID`s in the SportsGameOdds API end with `_NFL`. Since only player props include a `playerID`, could we just filter the odds data locally (without making new API calls) by checking for `"_NFL"`? I already have a full JSON dump saved from earlier because I hit the rate limit.

## Response Summary
I confirmed your discovery that **player props always have `playerID` fields ending with `_NFL`**, while game/team markets don’t. This makes filtering straightforward and avoids guessing depth charts or mapping names.  

I suggested creating a `filter_player_props` function that:  
- Iterates through each event’s odds.  
- Keeps only entries where `playerID.endswith("_NFL")`.  
- Saves the filtered data into a new JSON file (e.g., `sgo_events_playerprops_local.json`).  

This lets you:  
- Work **entirely offline** using previously saved raw API dumps.  
- Reduce API calls and stay within rate limits.  
- Guarantee that only true player props are retained.  

I also noted that the script could be extended to batch-process every saved JSON in your `data/raw/` directory, further streamlining your workflow.

## Prompt
I want to scrape TeamRankings NFL player stats pages one at a time to respect the servers. The pages include passing, rushing, receiving, kicking, and defensive categories. I need exponential backoff, a retry limit, and ideally, I’d like all of these stats merged into a single dataset per player.

## Response Summary
I provided a Python scraper that:
- Iterates over the specified TeamRankings stat pages (22 categories).
- Uses **exponential backoff** with retries to handle request failures safely.
- Waits **5 seconds between successful requests** to avoid hammering the server.
- Extracts each page’s HTML table using **BeautifulSoup** and **pandas**.
- Merges the results into a **single DataFrame** keyed on the `"Player"` column, so each player has one row with multiple stat columns.
- Saves the merged dataset as both **CSV and JSON** with timestamped filenames (e.g., `nfl_player_stats_merged_20250920_211255.csv`).

This ensures you end up with a complete dataset combining all categories while keeping the scraping respectful and resilient.

## Prompt
When scraping TeamRankings NFL player stats, I noticed each table already has a header: Rank, Player, Team, Pos, and Value. I’m only interested in Player and Value. I no longer want to merge across stats, but I do want to drop the unnecessary columns and save the files with universal names so they can be recalled later in the code.

## Response Summary
I revised the scraper design to:
- Fetch one stat page at a time (with exponential backoff and polite delays).
- Parse the HTML table and reduce it to only **Player** and **Value** columns.
- Drop the extra columns (`Rank`, `Team`, `Pos`) from the DataFrame.
- Save each stat dataset separately as **CSV and JSON**, using consistent filenames like:
  - `pass_completions.csv` / `pass_completions.json`
  - `receiving_yards.csv` / `receiving_yards.json`
  - etc.
- Keep timestamping optional for raw backups, but ensure universal names exist for easy recall in downstream code.

This way, each stat is stored independently, lightweight, and immediately reusable in the ETL pipeline without additional cleaning or merging.

## Prompt
Can we streamline the ETL process so that instead of saving every individual stat file in `data/raw`, we end up with just the compiled dataset? This dataset should merge all TeamRankings stats and SportsGameOdds props into a single CSV/JSON file, ready for enrichment with the DeepSeek API.

## Response Summary
I refactored the workflow so that:
- **Scraping**: Each TeamRankings stat page is fetched and reduced to only `Player` and `Value` columns. These are held in memory instead of being saved individually.
- **Transforming**: All stat DataFrames are merged on the `Player` column (normalized to `FIRSTNAME_LASTNAME`).  
- **Props Integration**: SportsGameOdds player props JSON is parsed, extracting `oddID`, `statID`, `playerID`, and bookmaker odds. These are merged with the stats DataFrame by player.  
- **Final Output**: Only the **compiled dataset** is written to `data/raw/` as:
  - `players_compiled_<timestamp>.csv`
  - `players_compiled_<timestamp>.json`

This eliminates clutter from multiple stat files, keeps the pipeline clean, and ensures there’s a single dataset ready for DeepSeek enrichment.

## Prompt
Now that we have the compiled dataset of player stats and odds, I want to integrate DeepSeek’s API. The goal is for DeepSeek to run pattern recognition on the compiled data, identify misalignments between stats and betting odds, and recommend bets that are more likely to hit than their implied odds. Based on user input of how many legs they want in a parlay, DeepSeek should select that number of bets, calculate the combined parlay odds, and then, given a stake amount, calculate the potential payout. The AI logic should live in a `deepseek_enrichment.py` file (saving enriched results in `data/enriched/`), and all input/output logic should be handled in `main.py`.

## Response Summary
I structured the solution into two files:

1. **`deepseek_enrichment.py`**  
   - Contains a function `run_deepseek_enrichment()` that loads the compiled dataset and sends it to the DeepSeek API.  
   - DeepSeek analyzes the data, detects misalignments, and returns recommended bets with confidence scores.  
   - Saves the enriched results into `data/enriched/enriched_<timestamp>.json`.  
   - Returns the results as a DataFrame for downstream use.  

2. **`main.py`**  
   - Handles user interaction:
     - Ask how many legs the parlay should have.  
     - Ask for the stake amount.  
   - Selects the top recommended bets by confidence.  
   - Calculates combined parlay odds using American → decimal conversions.  
   - Computes potential payout given the user’s stake.  
   - Displays the selected bets, parlay odds, stake, and payout summary.  

This completes the enrichment and analysis portion of the ETL pipeline: from raw odds/stats → compiled dataset → AI-driven insights → user-facing parlay builder with payout calculations.

# AI_USAGE.md Entry

## Prompt
I got a runtime error when calling `run_deepseek_enrichment`:  
```
TypeError: list indices must be integers or slices, not str
```
I also want to drop players who don’t have any actual stats linked to them (all stat columns are null).

## Response Summary
The error happened because DeepSeek returned a **list of bets directly**, not a dictionary with `"bets"`.  
I fixed this by adding a check in `run_deepseek_enrichment`:
- If the response is a list → load it directly into a DataFrame.  
- If it’s a dict with `"bets"` → use that key.  
- Otherwise → raise an error.

For filtering players, I added a helper `drop_players_with_no_stats()` that removes rows where **all stat columns are null** (keeping only players with at least one valid stat). This is applied after merging stats and odds to keep the dataset clean.
