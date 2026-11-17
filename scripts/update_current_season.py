#!/usr/bin/env python3
"""
Patch const CURRENT in index.html with live data for the in-progress season.

Pulls everything from the public Sleeper API (no key needed):
standings (including the weekly median game), week-over-week movement,
the latest week's matchups and highlights, season-to-date highlights,
manager lineup efficiency, transactions and next week's schedule.

Run from the repo root:
    python scripts/update_current_season.py

Options:
    --league-id ID   use this Sleeper league instead of looking it up
    --dry-run        print a summary but don't write index.html

No external dependencies — pure Python stdlib only.
"""
import argparse
import json
import re
import sys
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"

API = "https://api.sleeper.app/v1"
COMMISSIONER = "cjlauer16"       # Sleeper username used to find the league each year
LEAGUE_NAME = "WAFFL"
FALLBACK_LEAGUE_ID = "1334191960918859776"  # 2026 WAFFL league

# Which positions can fill each lineup slot.
SLOT_ELIGIBILITY = {
    "QB": {"QB"}, "RB": {"RB"}, "WR": {"WR"}, "TE": {"TE"}, "K": {"K"}, "DEF": {"DEF"},
    "FLEX": {"RB", "WR", "TE"},
    "WRRB_FLEX": {"RB", "WR"},
    "REC_FLEX": {"WR", "TE"},
    "SUPER_FLEX": {"QB", "RB", "WR", "TE"},
    "IDP_FLEX": {"DL", "LB", "DB"},
    "DL": {"DL"}, "LB": {"LB"}, "DB": {"DB"},
}


def get(path):
    req = urllib.request.Request(f"{API}{path}", headers={"User-Agent": "waffl-history-updater"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


# ── League lookup ─────────────────────────────────────────────────────────────

def find_league(season):
    try:
        user = get(f"/user/{COMMISSIONER}")
        leagues = get(f"/user/{user['user_id']}/leagues/nfl/{season}") or []
        for lg in leagues:
            if lg.get("name", "").strip().upper() == LEAGUE_NAME:
                return lg["league_id"]
    except Exception as e:  # network hiccup, renamed user, etc.
        print(f"  League lookup failed ({e}); using fallback ID", file=sys.stderr)
    return FALLBACK_LEAGUE_ID


# ── Lineup math ───────────────────────────────────────────────────────────────

def player_positions(pid, players):
    if pid in players:
        p = players[pid]
        return set(p.get("fantasy_positions") or [p.get("position")])
    if pid and pid.isalpha():  # team defenses are keyed by abbreviation
        return {"DEF"}
    return set()


def _greedy_fill(pool, slots):
    """pool: [(points, pid, position)] — fill the most restrictive slots first, flexes last."""
    used = set()
    total = 0.0
    for slot in sorted(slots, key=lambda s: len(SLOT_ELIGIBILITY.get(s, ()))):
        elig = SLOT_ELIGIBILITY.get(slot, set())
        for pts, pid, pos in pool:
            if pid not in used and pos in elig:
                used.add(pid)
                total += pts
                break
    return total


def optimal_points(player_ids, points, slots, players):
    """Best possible score for a week's roster.

    Greedy is exact when every player has one position; for the few
    multi-position players (e.g. a WR/DB two-way player) try each position.

    Note: this can come out higher than Sleeper's own "max points" (roster
    settings `ppts`). Sleeper fills WR slots before IDP_FLEX, so in 2026 it
    put Travis Hunter (WR/DB) at WR whenever he outscored Winnie24's WR2 and
    left their IDP_FLEX empty (weeks 2, 3, 6: 19.6 pts total). Every other
    roster matches Sleeper exactly; ours is the true best possible lineup.
    """
    single, multi = [], []
    for pid in player_ids:
        pts = points.get(pid, 0) or 0
        pos = sorted(player_positions(pid, players))
        (multi if len(pos) > 1 else single).append((pts, pid, pos))
    best = 0.0
    choices = [[]]
    for pts, pid, pos in multi[:6]:  # cap the search; real rosters have 0–2
        choices = [c + [(pts, pid, p)] for c in choices for p in pos]
    for c in choices:
        pool = sorted([(p, i, ps[0] if ps else "") for p, i, ps in single] + c, reverse=True)
        best = max(best, _greedy_fill(pool, slots))
    return round(best, 2)


def player_name(pid, players):
    p = players.get(pid)
    if not p:
        return pid
    if p.get("position") == "DEF":
        return f"{p.get('team') or pid} D/ST"
    return p.get("full_name") or f"{p.get('first_name', '')} {p.get('last_name', '')}".strip() or pid


# ── Build the CURRENT payload ─────────────────────────────────────────────────

def build(league_id):
    state = get("/state/nfl")
    league = get(f"/league/{league_id}")
    users = get(f"/league/{league_id}/users")
    rosters = get(f"/league/{league_id}/rosters")

    ls = league.get("settings", {})
    playoff_start = ls.get("playoff_week_start") or 15
    reg_season_end = playoff_start - 1
    playoff_teams = ls.get("playoff_teams") or 6
    has_median = bool(ls.get("league_average_match"))
    last_week = ls.get("last_scored_leg") or 0
    if league.get("status") == "complete":
        last_week = max(last_week, 17)
    slots = [s for s in league.get("roster_positions", []) if s not in ("BN", "IR", "TAXI")]

    user_by_id = {u["user_id"]: u for u in users}
    teams = {}
    for r in rosters:
        u = user_by_id.get(r.get("owner_id"), {})
        name = u.get("display_name") or f"Team {r['roster_id']}"
        team_name = (u.get("metadata") or {}).get("team_name") or name
        teams[r["roster_id"]] = {"user_name": name, "team_name": team_name}

    print(f"  League {league_id} ({league.get('season')}), last scored week {last_week}")
    print("  Downloading player database…")
    players = get("/players/nfl")

    # ── Weekly results ──
    weeks = {}  # week -> list of team-week dicts
    for w in range(1, last_week + 1):
        entries = get(f"/league/{league_id}/matchups/{w}") or []
        rows = []
        for m in entries:
            rid = m["roster_id"]
            pts = round(m.get("points") or 0, 2)
            pp = m.get("players_points") or {}
            opt = optimal_points(m.get("players") or [], pp, slots, players)
            starters = [p for p in (m.get("starters") or []) if p and p != "0"]
            bench = [p for p in (m.get("players") or []) if p not in starters]
            top_starter = max(starters, key=lambda p: pp.get(p, 0), default=None)
            top_bench = max(bench, key=lambda p: pp.get(p, 0), default=None)
            rows.append({
                "roster_id": rid,
                "matchup_id": m.get("matchup_id"),
                "points": pts,
                "optimal": max(opt, pts),
                "top_starter": top_starter and {"name": player_name(top_starter, players), "points": pp.get(top_starter, 0)},
                "top_bench": top_bench and {"name": player_name(top_bench, players), "points": pp.get(top_bench, 0)},
            })
        weeks[w] = rows

    # ── Standings (regular season only) ──
    def standings_through(n):
        rec = {rid: {"wins": 0, "losses": 0, "ties": 0, "pf": 0.0, "pa": 0.0, "h2h_w": 0, "h2h_l": 0,
                     "med_w": 0, "med_l": 0, "ap_w": 0, "ap_l": 0, "results": []} for rid in teams}
        for w in range(1, min(n, reg_season_end) + 1):
            rows = weeks.get(w, [])
            scores = sorted(r["points"] for r in rows)
            median = (scores[len(scores) // 2 - 1] + scores[len(scores) // 2]) / 2 if scores else 0
            by_mid = defaultdict(list)
            for r in rows:
                if r["matchup_id"] is not None:
                    by_mid[r["matchup_id"]].append(r)
            for r in rows:
                t = rec[r["roster_id"]]
                t["pf"] += r["points"]
                t["ap_w"] += sum(1 for s in scores if s < r["points"])
                t["ap_l"] += sum(1 for s in scores if s > r["points"])
                res = ""
                opp = [o for o in by_mid.get(r["matchup_id"], []) if o is not r]
                if opp:
                    o = opp[0]
                    t["pa"] += o["points"]
                    if r["points"] > o["points"]:
                        t["wins"] += 1; t["h2h_w"] += 1; res += "W"
                    elif r["points"] < o["points"]:
                        t["losses"] += 1; t["h2h_l"] += 1; res += "L"
                    else:
                        t["ties"] += 1; res += "T"
                if has_median:
                    if r["points"] > median:
                        t["wins"] += 1; t["med_w"] += 1; res += "W"
                    elif r["points"] < median:
                        t["losses"] += 1; t["med_l"] += 1; res += "L"
                    else:
                        t["ties"] += 1; res += "T"
                t["results"].append(res)
        order = sorted(rec, key=lambda rid: (rec[rid]["wins"] + rec[rid]["ties"] / 2, rec[rid]["pf"]), reverse=True)
        return rec, order

    reg_week = min(last_week, reg_season_end)
    rec, order = standings_through(reg_week)
    _, prev_order = standings_through(reg_week - 1) if reg_week > 1 else (None, order)
    prev_rank = {rid: i + 1 for i, rid in enumerate(prev_order)}

    def streak(results):
        flat = "".join(results)
        if not flat:
            return ""
        last = flat[-1]
        n = len(flat) - len(flat.rstrip(last))
        return f"{last}{n}"

    standings = []
    for i, rid in enumerate(order):
        t = rec[rid]
        latest = t["results"][-1] if t["results"] else ""
        standings.append({
            "roster_id": rid,
            **teams[rid],
            "rank": i + 1,
            "prev_rank": prev_rank.get(rid, i + 1),
            "wins": t["wins"], "losses": t["losses"], "ties": t["ties"],
            "h2h": f"{t['h2h_w']}-{t['h2h_l']}",
            "median": f"{t['med_w']}-{t['med_l']}",
            "all_play": f"{t['ap_w']}-{t['ap_l']}",
            "all_play_pct": round(t["ap_w"] / max(1, t["ap_w"] + t["ap_l"]), 3),
            "points_for": round(t["pf"], 2),
            "points_against": round(t["pa"], 2),
            "point_diff": round(t["pf"] - t["pa"], 2),
            "ppg": round(t["pf"] / max(1, reg_week), 2),
            "last_week": f"{latest.count('W')}-{latest.count('L')}" if latest else "",
            "streak": streak(t["results"]),
        })

    # ── Latest week ──
    def week_detail(w):
        rows = weeks.get(w, [])
        if not rows:
            return None
        scores = sorted(r["points"] for r in rows)
        median = round((scores[len(scores) // 2 - 1] + scores[len(scores) // 2]) / 2, 2)
        by_mid = defaultdict(list)
        for r in rows:
            if r["matchup_id"] is not None:
                by_mid[r["matchup_id"]].append(r)
        games = []
        for mid, pair in sorted(by_mid.items()):
            if len(pair) != 2:
                continue
            a, b = sorted(pair, key=lambda r: r["points"], reverse=True)
            games.append({
                "winner": teams[a["roster_id"]]["user_name"], "winner_team": teams[a["roster_id"]]["team_name"],
                "loser": teams[b["roster_id"]]["user_name"], "loser_team": teams[b["roster_id"]]["team_name"],
                "winner_score": a["points"], "loser_score": b["points"],
                "margin": round(a["points"] - b["points"], 2),
                "winner_beat_median": a["points"] > median, "loser_beat_median": b["points"] > median,
                "winner_top": a["top_starter"], "loser_top": b["top_starter"],
            })
        games.sort(key=lambda g: g["winner_score"], reverse=True)
        hi = max(rows, key=lambda r: r["points"])
        lo = min(rows, key=lambda r: r["points"])
        bench = max(rows, key=lambda r: r["optimal"] - r["points"])
        star = max((r for r in rows if r["top_starter"]), key=lambda r: r["top_starter"]["points"], default=None)
        return {
            "week": w,
            "is_playoffs": w >= playoff_start,
            "median": median,
            "games": games,
            "high": {"team": teams[hi["roster_id"]]["user_name"], "score": hi["points"]},
            "low": {"team": teams[lo["roster_id"]]["user_name"], "score": lo["points"]},
            "blowout": max(games, key=lambda g: g["margin"]) if games else None,
            "closest": min(games, key=lambda g: g["margin"]) if games else None,
            "bench_blunder": {
                "team": teams[bench["roster_id"]]["user_name"],
                "left": round(bench["optimal"] - bench["points"], 2),
                "player": bench["top_bench"],
            },
            "player_of_week": star and {"team": teams[star["roster_id"]]["user_name"], **star["top_starter"]},
        }

    latest = week_detail(last_week) if last_week else None

    # ── Season-to-date highlights (regular season) ──
    all_games, all_rows = [], []
    for w in range(1, reg_week + 1):
        d = week_detail(w)
        if not d:
            continue
        all_games += [dict(g, week=w) for g in d["games"]]
        all_rows += [dict(r, week=w) for r in weeks[w]]
    season_highlights = {}
    if all_games:
        b = max(all_games, key=lambda g: g["margin"])
        c = min(all_games, key=lambda g: g["margin"])
        hi = max(all_rows, key=lambda r: r["points"])
        lo = min(all_rows, key=lambda r: r["points"])
        season_highlights = {
            "biggest_blowout": {"week": b["week"], "winner": b["winner"], "loser": b["loser"],
                                "score": f"{b['winner_score']:.2f} - {b['loser_score']:.2f}", "margin": b["margin"]},
            "closest_game": {"week": c["week"], "team1": c["winner"], "team2": c["loser"],
                             "score1": c["winner_score"], "score2": c["loser_score"], "margin": c["margin"]},
            "highest_week": {"week": hi["week"], "team": teams[hi["roster_id"]]["user_name"], "score": hi["points"]},
            "lowest_week": {"week": lo["week"], "team": teams[lo["roster_id"]]["user_name"], "score": lo["points"]},
        }

    # ── Weekly score grid ──
    weekly_scores = {}
    for rid in teams:
        cells = []
        for w in range(1, last_week + 1):
            row = next((r for r in weeks.get(w, []) if r["roster_id"] == rid), None)
            res = rec[rid]["results"][w - 1] if w <= reg_week and w - 1 < len(rec[rid]["results"]) else ""
            cells.append({"pts": row["points"] if row else None, "res": res})
        weekly_scores[teams[rid]["user_name"]] = cells

    # ── Transactions ──
    tx_by_roster = defaultdict(lambda: {"trades": 0, "moves": 0, "faab": 0, "waivers": 0})
    totals = {"total_trades": 0, "total_moves": 0, "total_faab_spent": 0, "waiver_claims": 0}
    max_leg = max(last_week + 1, state.get("leg") or 0)
    for leg in range(1, min(max_leg, 18) + 1):
        for t in get(f"/league/{league_id}/transactions/{leg}") or []:
            if t.get("status") != "complete":
                continue
            typ = t.get("type")
            totals["total_moves"] += 1
            if typ == "trade":
                totals["total_trades"] += 1
            if typ == "waiver":
                totals["waiver_claims"] += 1
                totals["total_faab_spent"] += (t.get("settings") or {}).get("waiver_bid", 0) or 0
            for rid in t.get("roster_ids") or []:
                s = tx_by_roster[rid]
                s["moves"] += 1
                if typ == "trade":
                    s["trades"] += 1
                if typ == "waiver":
                    s["waivers"] += 1
                    s["faab"] += (t.get("settings") or {}).get("waiver_bid", 0) or 0

    # ── Manager stats (regular season) ──
    manager_stats = []
    for rid in teams:
        actual = optimal = 0.0
        mistakes = 0
        for w in range(1, reg_week + 1):
            rows = weeks.get(w, [])
            me = next((r for r in rows if r["roster_id"] == rid), None)
            if not me:
                continue
            actual += me["points"]
            optimal += me["optimal"]
            opp = next((r for r in rows if r["matchup_id"] == me["matchup_id"] and r is not me), None)
            if opp and me["points"] < opp["points"] and me["optimal"] > opp["points"]:
                mistakes += 1
        left = optimal - actual
        tx = tx_by_roster[rid]
        manager_stats.append({
            "roster_id": rid, **teams[rid],
            "trades": tx["trades"], "total_moves": tx["moves"], "faab_spent": tx["faab"],
            "avg_pts_left": round(left / max(1, reg_week), 1),
            "total_pts_left": round(left, 2),
            "efficiency_pct": round(100 * actual / optimal, 1) if optimal else 0,
            "costly_mistakes": mistakes,
        })
    manager_stats.sort(key=lambda m: m["efficiency_pct"], reverse=True)

    # ── Next week ──
    upcoming = None
    nxt = last_week + 1
    if nxt <= 17 and league.get("status") != "complete":
        entries = get(f"/league/{league_id}/matchups/{nxt}") or []
        by_mid = defaultdict(list)
        for m in entries:
            if m.get("matchup_id") is not None:
                by_mid[m["matchup_id"]].append(m["roster_id"])
        rank = {s["roster_id"]: s for s in standings}
        games = []
        for mid, pair in sorted(by_mid.items()):
            if len(pair) != 2:
                continue
            games.append([{
                "user_name": teams[r]["user_name"], "team_name": teams[r]["team_name"],
                "rank": rank[r]["rank"], "record": f"{rank[r]['wins']}-{rank[r]['losses']}",
                "ppg": rank[r]["ppg"],
            } for r in sorted(pair, key=lambda r: rank[r]["rank"])])
        games.sort(key=lambda g: g[0]["rank"] + g[1]["rank"])
        upcoming = {"week": nxt, "is_playoffs": nxt >= playoff_start, "games": games}

    return {
        "year": int(league.get("season")),
        "league_id": league_id,
        "status": league.get("status"),
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "last_week": last_week,
        "reg_season_end": reg_season_end,
        "playoff_week_start": playoff_start,
        "playoff_teams": playoff_teams,
        "has_median": has_median,
        "standings": standings,
        "latest_week": latest,
        "upcoming": upcoming,
        "highlights": season_highlights,
        "weekly_scores": weekly_scores,
        "transaction_summary": totals,
        "manager_stats": manager_stats,
    }


def patch_html(current):
    html = INDEX.read_text(encoding="utf-8")
    blob = json.dumps(current, ensure_ascii=False)
    replacement = f"/*__CURRENT_START__*/const CURRENT = {blob};/*__CURRENT_END__*/"
    patched, n = re.subn(
        r"/\*__CURRENT_START__\*/.*?/\*__CURRENT_END__\*/",
        lambda m: replacement,
        html,
        flags=re.DOTALL,
    )
    if n == 0:
        print("ERROR: CURRENT marker not found in index.html", file=sys.stderr)
        sys.exit(1)
    INDEX.write_text(patched, encoding="utf-8")
    print(f"  Patched index.html with {current['year']} data through week {current['last_week']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--league-id")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    season = get("/state/nfl").get("league_season")
    league_id = args.league_id or find_league(season)
    current = build(league_id)
    if args.dry_run:
        print(json.dumps({k: current[k] for k in ("year", "last_week", "transaction_summary")}, indent=2))
        for s in current["standings"]:
            print(f"  {s['rank']:>2}. {s['user_name']:<15} {s['wins']}-{s['losses']}  PF {s['points_for']}")
    else:
        patch_html(current)
