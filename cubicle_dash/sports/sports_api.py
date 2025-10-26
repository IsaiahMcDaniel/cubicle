import requests, datetime as dt, json

def week_range():
    """Return current Monday–Sunday range like 20251020-20251026."""
    today = dt.date.today()
    start = today - dt.timedelta(days=today.weekday())
    end = start + dt.timedelta(days=6)
    return f"{start:%Y%m%d}-{end:%Y%m%d}"

def fetch_and_save(url, filename, params=None):
    """GET a URL and write the JSON response to a file."""
    r = requests.get(url, params=params or {}, timeout=15)
    r.raise_for_status()
    data = r.json()
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {filename}")

def update():
    dates = week_range()

    # ---- SCOREBOARDS ----
    scoreboards = {
        "nfl": ("https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
                {"dates": dates}),
        "ncaaf": ("https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard",
                  {"dates": dates, "groups": "80"}),
        "ncaam": ("https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard",
                  {"dates": dates, "groups": "50", "limit": "400"}),
        "nba": ("https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
                {"dates": dates}),
    }

    for name, (url, params) in scoreboards.items():
        fetch_and_save(url, fr"cubicle_dash\sports\scoreboards\{name}_scoreboard.json", params)

    # ---- STANDINGS/RANKINGS ----
    standings = {
        "nfl": f"https://site.web.api.espn.com/apis/v2/sports/football/nfl/standings",
        "nba": f"https://site.web.api.espn.com/apis/v2/sports/basketball/nba/standings",
        "ncaaf": f"https://site.api.espn.com/apis/site/v2/sports/football/college-football/rankings",
        "ncaam": f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/rankings",
    }

    for name, url in standings.items():
        fetch_and_save(url, fr"cubicle_dash\sports\standings\{name}_standings.json", {"season": dt.date.today().year})

