# ============================================================
# TENNIS LIVE AI BOT
# RapidAPI - Tennis API ATP WTA ITF
#
# LIVE DATA
#   -> live events
#   -> score / points / indicator
#   -> stats
#   -> timeline
#   -> live probability
#   -> Monte Carlo
#   -> Telegram
#
# Python 3.10+
# ============================================================

import os
import time
import random
import logging
import requests

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ============================================================
# CONFIG
# ============================================================

RAPIDAPI_KEY = os.getenv(
    "RAPIDAPI_KEY",
    "dbcb6f204emshf93e9e1bb342b5fp1c720djsn909778cd5b67"
)

RAPIDAPI_HOST = "tennis-api-atp-wta-itf.p.rapidapi.com"

TELEGRAM_BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN",
    "PASTE_TELEGRAM_BOT_TOKEN_HERE"
)

TELEGRAM_CHAT_ID = os.getenv(
    "TELEGRAM_CHAT_ID",
    "PASTE_TELEGRAM_CHAT_ID_HERE"
)

# Không nên thấp hơn 5 giây.
# API có giới hạn request nên 8-10 giây là hợp lý.
POLL_SECONDS = 8

# Số lần mô phỏng mỗi lần dữ liệu thay đổi
SIMULATIONS = 10000

# Chỉ gửi Telegram khi state trận đấu thay đổi
SEND_ONLY_ON_CHANGE = True

# Timeout API
REQUEST_TIMEOUT = 10


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

log = logging.getLogger("TENNIS-BOT")


# ============================================================
# RAPID API CLIENT
# ============================================================

class TennisAPI:

    def __init__(self):

        self.base_url = (
            "https://"
            + RAPIDAPI_HOST
            + "/tennis/v2/extend/api"
        )

        self.session = requests.Session()

        self.session.headers.update({
            "Content-Type": "application/json",
            "x-rapidapi-host": RAPIDAPI_HOST,
            "x-rapidapi-key": RAPIDAPI_KEY,
            "User-Agent": "TennisLiveAI/1.0"
        })

    # --------------------------------------------------------
    # Generic GET
    # --------------------------------------------------------

    def get(self, path: str):

        url = self.base_url + path

        try:

            response = self.session.get(
                url,
                timeout=REQUEST_TIMEOUT
            )

            if response.status_code != 200:

                log.error(
                    "API HTTP %s: %s",
                    response.status_code,
                    response.text[:300]
                )

                return None

            data = response.json()

            if data.get("success") is False:

                log.error(
                    "API error: %s",
                    data.get("message")
                )

                return None

            return data

        except requests.RequestException as e:

            log.error(
                "RapidAPI request error: %s",
                e
            )

            return None

        except ValueError:

            log.error(
                "RapidAPI returned invalid JSON"
            )

            return None

    # --------------------------------------------------------
    # LIVE EVENTS
    # --------------------------------------------------------

    def live_events(self):

        # Endpoint live của Tennis API
        data = self.get("/events/live")

        if not data:
            return []

        result = data.get("result")

        if isinstance(result, list):
            return result

        # Một số response có thể dùng data
        if isinstance(result, dict):

            if isinstance(result.get("events"), list):
                return result["events"]

            if isinstance(result.get("data"), list):
                return result["data"]

        if isinstance(data.get("data"), list):
            return data["data"]

        return []

    # --------------------------------------------------------
    # EVENT DETAIL
    # --------------------------------------------------------

    def event_detail(
        self,
        player1: str,
        player2: str,
        date: str
    ):

        # API dùng player names trong URL.
        return self.get(
            f"/event/get/{player1}/{player2}/{date}"
        )


# ============================================================
# MATCH MODEL
# ============================================================

@dataclass
class MatchState:

    event_id: str

    player_a: str
    player_b: str

    score: str = ""

    status: str = ""

    points: str = ""

    indicator: str = ""

    league: str = ""

    stats: Dict[str, Any] = field(
        default_factory=dict
    )

    timeline: List[Dict[str, Any]] = field(
        default_factory=list
    )

    raw: Dict[str, Any] = field(
        default_factory=dict
    )


# ============================================================
# SAFE HELPERS
# ============================================================

def safe_int(value, default=0):

    try:
        return int(value)

    except Exception:
        return default


def safe_float(value, default=0.0):

    try:
        return float(value)

    except Exception:
        return default


def clamp(value, low, high):

    return max(
        low,
        min(high, value)
    )


# ============================================================
# PARSE SCORE
# ============================================================

def parse_score(score: str):

    """
    Ví dụ:

    6-4
    7-6,3-6,4-2
    7-6,6-1
    """

    sets_a = 0
    sets_b = 0

    games_a = 0
    games_b = 0

    if not score:
        return (
            sets_a,
            sets_b,
            games_a,
            games_b
        )

    score = score.strip()

    parts = score.split(",")

    for part in parts:

        part = part.strip()

        if "-" not in part:
            continue

        try:

            a, b = part.split("-")[:2]

            a = int(a)
            b = int(b)

        except Exception:
            continue

        # Tie break / unfinished set
        if a > b:
            sets_a += 1

        elif b > a:
            sets_b += 1

        # Games hiện tại lấy từ set cuối
        games_a = a
        games_b = b

    # Score dạng đã hoàn thành nhiều set:
    # tính lại set từ tất cả các set ngoại trừ set cuối
    if len(parts) > 1:

        completed_a = 0
        completed_b = 0

        for part in parts[:-1]:

            if "-" not in part:
                continue

            try:

                a, b = map(
                    int,
                    part.split("-")[:2]
                )

            except Exception:
                continue

            if a > b:
                completed_a += 1

            elif b > a:
                completed_b += 1

        sets_a = completed_a
        sets_b = completed_b

    return (
        sets_a,
        sets_b,
        games_a,
        games_b
    )


# ============================================================
# PARSE MATCH
# ============================================================

def parse_match(raw: Dict[str, Any]):

    if not isinstance(raw, dict):
        return None

    player_a = (
        raw.get("participant1")
        or raw.get("player1")
        or ""
    )

    player_b = (
        raw.get("participant2")
        or raw.get("player2")
        or ""
    )

    if not player_a or not player_b:
        return None

    event_id = str(
        raw.get("id")
        or raw.get("eventId")
        or raw.get("matchId")
        or f"{player_a}_{player_b}"
    )

    return MatchState(

        event_id=event_id,

        player_a=str(player_a),

        player_b=str(player_b),

        score=str(
            raw.get("score") or ""
        ),

        status=str(
            raw.get("status") or ""
        ),

        points=str(
            raw.get("points") or ""
        ),

        indicator=str(
            raw.get("indicator") or ""
        ),

        league=str(
            raw.get("league") or ""
        ),

        stats=raw.get("stats") or {},

        timeline=raw.get("timeline") or [],

        raw=raw
    )


# ============================================================
# LIVE EVENT STATUS
# ============================================================

def is_live(match: MatchState):

    status = match.status.lower().strip()

    ended = {
        "ended",
        "finished",
        "completed",
        "cancelled",
        "postponed"
    }

    if status in ended:
        return False

    # Nếu score/points có dữ liệu thì ưu tiên xem như live
    if match.points:
        return True

    if status in {
        "inplay",
        "in-play",
        "live",
        "playing",
        "started"
    }:
        return True

    return False


# ============================================================
# TIMELINE ANALYSIS
# ============================================================

def analyze_timeline(match: MatchState):

    a_hold = 0
    b_hold = 0

    a_break = 0
    b_break = 0

    recent = []

    for event in match.timeline:

        text = str(
            event.get("text", "")
        )

        lower = text.lower()

        recent.append(text)

        if "break" in lower:

            if match.player_a.lower() in lower:

                a_break += 1

            elif match.player_b.lower() in lower:

                b_break += 1

        elif "holds" in lower:

            if match.player_a.lower() in lower:

                a_hold += 1

            elif match.player_b.lower() in lower:

                b_hold += 1

    # Chỉ lấy các event gần nhất
    recent = recent[-10:]

    return {
        "a_hold": a_hold,
        "b_hold": b_hold,
        "a_break": a_break,
        "b_break": b_break,
        "recent": recent
    }


# ============================================================
# STATS ANALYSIS
# ============================================================

def analyze_stats(match: MatchState):

    stats = match.stats

    result = {
        "a_aces": 0,
        "b_aces": 0,

        "a_df": 0,
        "b_df": 0,

        "a_first_serve": 0,
        "b_first_serve": 0,

        "a_break": 0,
        "b_break": 0
    }

    def pair(name):

        value = stats.get(name)

        if not isinstance(value, list):
            return 0, 0

        a = (
            safe_float(value[0])
            if len(value) > 0
            else 0
        )

        b = (
            safe_float(value[1])
            if len(value) > 1
            else 0
        )

        return a, b

    (
        result["a_aces"],
        result["b_aces"]
    ) = pair("aces")

    (
        result["a_df"],
        result["b_df"]
    ) = pair("double_faults")

    (
        result["a_first_serve"],
        result["b_first_serve"]
    ) = pair("win_1st_serve")

    (
        result["a_break"],
        result["b_break"]
    ) = pair(
        "break_point_conversions"
    )

    return result


# ============================================================
# SCORE PROBABILITY
# ============================================================

def score_probability(match: MatchState):

    (
        sets_a,
        sets_b,
        games_a,
        games_b
    ) = parse_score(match.score)

    score = 0.50

    # SET ADVANTAGE
    score += (
        sets_a - sets_b
    ) * 0.17

    # GAME ADVANTAGE
    score += (
        games_a - games_b
    ) * 0.025

    # POINT ADVANTAGE
    if match.points:

        try:

            p1, p2 = match.points.split("-")

            p1 = int(p1)
            p2 = int(p2)

            if p1 > p2:
                score += 0.025

            elif p2 > p1:
                score -= 0.025

        except Exception:
            pass

    return clamp(
        score,
        0.05,
        0.95
    )


# ============================================================
# TIMELINE PROBABILITY
# ============================================================

def timeline_probability(match: MatchState):

    data = analyze_timeline(match)

    a = (
        data["a_hold"]
        + data["a_break"] * 1.5
    )

    b = (
        data["b_hold"]
        + data["b_break"] * 1.5
    )

    if a + b == 0:
        return 0.50

    return clamp(
        a / (a + b),
        0.10,
        0.90
    )


# ============================================================
# STATS PROBABILITY
# ============================================================

def stats_probability(match: MatchState):

    stats = analyze_stats(match)

    score_a = 0
    score_b = 0

    # ACES
    score_a += stats["a_aces"] * 0.5
    score_b += stats["b_aces"] * 0.5

    # DOUBLE FAULTS
    score_a -= stats["a_df"] * 0.4
    score_b -= stats["b_df"] * 0.4

    # FIRST SERVE %
    score_a += stats["a_first_serve"] * 0.04
    score_b += stats["b_first_serve"] * 0.04

    # BREAK CONVERSION
    score_a += stats["a_break"] * 0.03
    score_b += stats["b_break"] * 0.03

    if score_a == 0 and score_b == 0:
        return 0.50

    # Logistic conversion
    difference = score_a - score_b

    probability = (
        1 /
        (
            1 +
            pow(
                2.718281828,
                -difference / 10
            )
        )
    )

    return clamp(
        probability,
        0.10,
        0.90
    )


# ============================================================
# SERVER ADVANTAGE
# ============================================================

def server_probability(
    match: MatchState,
    base_probability
):

    indicator = (
        match.indicator
        or ""
    )

    if not indicator:
        return base_probability

    return base_probability


# ============================================================
# LIVE MODEL
# ============================================================

def calculate_live_probability(match):

    score_p = score_probability(match)

    timeline_p = timeline_probability(match)

    stats_p = stats_probability(match)

    # SCORE là tín hiệu chính.
    # Timeline và stats là correction.
    probability = (
        score_p * 0.60
        +
        timeline_p * 0.20
        +
        stats_p * 0.20
    )

    probability = server_probability(
        match,
        probability
    )

    return clamp(
        probability,
        0.01,
        0.99
    )


# ============================================================
# MONTE CARLO
# ============================================================

def monte_carlo(
    base_probability,
    simulations=SIMULATIONS
):

    wins_a = 0

    for _ in range(simulations):

        noise = random.gauss(
            0,
            0.018
        )

        p = clamp(
            base_probability + noise,
            0.01,
            0.99
        )

        if random.random() < p:
            wins_a += 1

    return wins_a / simulations


# ============================================================
# CONFIDENCE
# ============================================================

def confidence_label(probability):

    edge = abs(
        probability - 0.50
    )

    if edge >= 0.30:
        return "VERY HIGH"

    if edge >= 0.20:
        return "HIGH"

    if edge >= 0.10:
        return "MEDIUM"

    return "LOW"


# ============================================================
# DIAGNOSIS
# ============================================================

def diagnose(match):

    base = calculate_live_probability(
        match
    )

    sim_a = monte_carlo(
        base
    )

    sim_b = 1 - sim_a

    if sim_a >= sim_b:

        winner = match.player_a

        winner_probability = sim_a

    else:

        winner = match.player_b

        winner_probability = sim_b

    confidence = confidence_label(
        winner_probability
    )

    timeline = analyze_timeline(
        match
    )

    stats = analyze_stats(
        match
    )

    return {

        "winner": winner,

        "a_probability": sim_a,

        "b_probability": sim_b,

        "winner_probability":
            winner_probability,

        "confidence": confidence,

        "timeline": timeline,

        "stats": stats
    }


# ============================================================
# STATE FINGERPRINT
# ============================================================

def match_fingerprint(match):

    timeline_last = ""

    if match.timeline:

        last = match.timeline[-1]

        timeline_last = str(
            last.get("text", "")
        )

    return (
        match.score,
        match.points,
        match.indicator,
        match.status,
        timeline_last,
        len(match.timeline)
    )


# ============================================================
# TELEGRAM
# ============================================================

def send_telegram(text):

    if (
        not TELEGRAM_BOT_TOKEN
        or
        TELEGRAM_BOT_TOKEN.startswith("PASTE_")
    ):

        log.warning(
            "Telegram bot token chưa được cấu hình"
        )

        return False

    if (
        not TELEGRAM_CHAT_ID
        or
        TELEGRAM_CHAT_ID.startswith("PASTE_")
    ):

        log.warning(
            "Telegram chat ID chưa được cấu hình"
        )

        return False

    url = (
        "https://api.telegram.org/bot"
        +
        TELEGRAM_BOT_TOKEN
        +
        "/sendMessage"
    )

    try:

        response = requests.post(

            url,

            json={
                "chat_id":
                    TELEGRAM_CHAT_ID,

                "text": text
            },

            timeout=10
        )

        if response.status_code != 200:

            log.error(
                "Telegram error: %s",
                response.text[:300]
            )

            return False

        return True

    except Exception as e:

        log.error(
            "Telegram exception: %s",
            e
        )

        return False


# ============================================================
# FORMAT TELEGRAM
# ============================================================

def format_prediction(
    match,
    result
):

    a = (
        result["a_probability"]
        * 100
    )

    b = (
        result["b_probability"]
        * 100
    )

    stats = result["stats"]

    timeline = result["timeline"]

    return f"""
🎾 LIVE TENNIS AI

🏟 {match.league}

👤 {match.player_a}
vs
👤 {match.player_b}

📊 SCORE
{match.score}

🎯 POINT
{match.points}

📡 STATUS
{match.status}

━━━━━━━━━━━━━━

🏆 WIN PROBABILITY

{match.player_a}: {a:.1f}%
{match.player_b}: {b:.1f}%

🥇 CURRENT DIAGNOSIS
{result["winner"]}

🔥 CONFIDENCE
{result["confidence"]}

━━━━━━━━━━━━━━

📈 LIVE STATS

ACES
{match.player_a}: {stats["a_aces"]:.0f}
{match.player_b}: {stats["b_aces"]:.0f}

DOUBLE FAULTS
{match.player_a}: {stats["a_df"]:.0f}
{match.player_b}: {stats["b_df"]:.0f}

1ST SERVE WON
{match.player_a}: {stats["a_first_serve"]:.0f}%
{match.player_b}: {stats["b_first_serve"]:.0f}%

━━━━━━━━━━━━━━

🔄 LIVE MODEL
Monte Carlo: {SIMULATIONS:,}

Timeline events:
{len(match.timeline)}

Last event:
{timeline["recent"][-1] if timeline["recent"] else "N/A"}
""".strip()


# ============================================================
# MAIN ENGINE
# ============================================================

def main():

    log.info(
        "===================================="
    )

    log.info(
        "TENNIS LIVE AI STARTED"
    )

    log.info(
        "RapidAPI host: %s",
        RAPIDAPI_HOST
    )

    log.info(
        "Polling: %s seconds",
        POLL_SECONDS
    )

    log.info(
        "Monte Carlo: %s",
        SIMULATIONS
    )

    log.info(
        "===================================="
    )

    api = TennisAPI()

    previous_states = {}

    while True:

        try:

            raw_events = api.live_events()

            if not raw_events:

                log.info(
                    "Không tìm thấy live events."
                )

            else:

                log.info(
                    "Live events: %s",
                    len(raw_events)
                )

            current_ids = set()

            for raw in raw_events:

                match = parse_match(
                    raw
                )

                if not match:
                    continue

                current_ids.add(
                    match.event_id
                )

                if not is_live(match):

                    continue

                fingerprint = (
                    match_fingerprint(
                        match
                    )
                )

                old_fingerprint = (
                    previous_states.get(
                        match.event_id
                    )
                )

                changed = (
                    fingerprint
                    != old_fingerprint
                )

                previous_states[
                    match.event_id
                ] = fingerprint

                if (
                    SEND_ONLY_ON_CHANGE
                    and
                    not changed
                ):

                    continue

                result = diagnose(
                    match
                )

                log.info(
                    "%s vs %s | %s | A %.1f%% | B %.1f%%",
                    match.player_a,
                    match.player_b,
                    result["winner"],
                    result["a_probability"] * 100,
                    result["b_probability"] * 100
                )

                message = format_prediction(
                    match,
                    result
                )

                send_telegram(
                    message
                )

            previous_states = {

                k: v

                for k, v
                in previous_states.items()

                if k in current_ids
            }

        except KeyboardInterrupt:

            log.info(
                "Bot stopped."
            )

            break

        except Exception as e:

            log.exception(
                "MAIN LOOP ERROR: %s",
                e
            )

        time.sleep(
            POLL_SECONDS
        )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()
