# cubicle_dash/sports_db.py
import json
import sqlite3
from pathlib import Path

BASE = Path("cubicle_dash") / "sports"
SCORE_DIR = BASE / "scoreboards"
RANK_DIR  = BASE / "standings"
DB_PATH = BASE / "database" / "sports_data.db"


def safe(d, *path, default=None):
    """Safely traverse nested dict/list paths."""
    for key in path:
        if isinstance(d, dict):
            d = d.get(key)
        elif isinstance(d, list) and isinstance(key, int):
            d = d[key] if 0 <= key < len(d) else None
        else:
            return default
        if d is None:
            return default
    return d

def ensure_schema(con):
    cur = con.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS games(
      league TEXT,
      event_id TEXT PRIMARY KEY,
      start TEXT,
      status TEXT,
      away_team TEXT,
      away_score INTEGER,
      home_team TEXT,
      home_score INTEGER
    );

    CREATE TABLE IF NOT EXISTS rankings(
      sport TEXT,
      poll TEXT,
      poll_week TEXT,
      rank INTEGER,
      team_id TEXT,
      team_name TEXT,
      points INTEGER,
      first_place INTEGER,
      PRIMARY KEY (sport, poll, poll_week, rank)
    );
    """)

    def _cols(table):
        cur.execute(f"PRAGMA table_info({table})")
        return {r[1] for r in cur.fetchall()}

    def _add(table, col_def):
        name = col_def.split()[0]
        if name not in _cols(table):
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")

    _add("games", "away_abbr TEXT")
    _add("games", "home_abbr TEXT")
    _add("games", "away_logo TEXT")
    _add("games", "home_logo TEXT")
    _add("rankings", "team_logo TEXT")

    con.commit()

def load_scoreboard(cur, path: Path, league: str):
    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    for ev in data.get("events", []):
        comp = safe(ev, "competitions", 0, default={})
        comps = comp.get("competitors", [])
        if len(comps) < 2:
            continue

        home = next((c for c in comps if c.get("homeAway") == "home"), comps[0])
        away = next((c for c in comps if c.get("homeAway") == "away"), comps[1])
        ht, at = home.get("team") or {}, away.get("team") or {}
        cur.execute(
            """INSERT OR REPLACE INTO games
               (league,event_id,start,status,
                away_team,away_abbr,away_score,away_logo,
                home_team,home_abbr,home_score,home_logo)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                league,
                ev.get("id"),
                ev.get("date"),
                safe(comp, "status", "type", "name"),
                at.get("displayName"),
                at.get("abbreviation"),
                int(away.get("score") or 0),
                at.get("logo", None),
                ht.get("displayName"),
                ht.get("abbreviation"),
                int(home.get("score") or 0),
                ht.get("logo", None),
            ),
        )

def load_rankings(cur, path: Path, sport: str):
    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    for poll in data.get("rankings", []):
        poll_name = poll.get("name")
        week = safe(poll, "occurrence", "displayValue") or str(poll.get("season") or "")
        for r in poll.get("ranks", []):
            team = r.get("team") or {}
            cur.execute(
                """INSERT OR REPLACE INTO rankings
                   (sport,poll,poll_week,rank,team_id,team_name,points,first_place,team_logo)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (
                    sport,
                    poll_name,
                    week,
                    r.get("current"),
                    team.get("id"),
                    team.get("displayName") or team.get("nickname"),
                    r.get("points"),
                    r.get("firstPlaceVotes"),
                    team.get("logo", None),
                ),
            )

def update():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    ensure_schema(con)

    # TRUNCATE TABLES
    cur.execute("DELETE FROM games;")
    cur.execute("DELETE FROM rankings;")
    con.commit()
    print("Cleared existing records")

    # Scoreboards
    leagues = {
        "nfl": SCORE_DIR / "nfl_scoreboard.json",
        "ncaaf": SCORE_DIR / "ncaaf_scoreboard.json",
        "ncaam": SCORE_DIR / "ncaam_scoreboard.json",
        "nba": SCORE_DIR / "nba_scoreboard.json",
    }
    for lg, path in leagues.items():
        load_scoreboard(cur, path, lg)

    # 
    rankings = {
        "ncaaf": RANK_DIR / "ncaaf_standings.json",
        "ncaam": RANK_DIR / "ncaam_standings.json",
        "nfl": RANK_DIR / "nba_standings.json",
        "nba": RANK_DIR / "nfl_standings.json",
    }
    for sp, path in rankings.items():
        load_rankings(cur, path, sp)

    con.commit()
    con.close()
    print(f"Reloaded fresh data into {DB_PATH.resolve()}")
update()