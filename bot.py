# ============================================================
# TENNIS LIVE AI BOT v3 (Đã sửa lỗi cấu hình Telegram & Key)
# RapidAPI - Tennis API ATP WTA ITF
# ============================================================

import os
import time
import logging
import requests
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ============================================================
# CONFIG
# ============================================================

HOST = "tennis-api-atp-wta-itf.p.rapidapi.com"

BASE_URL = (
    f"https://{HOST}"
    "/tennis/v2/extend/api"
)

# Đã điền sẵn RapidAPI Key của anh vào đây
RAPIDAPI_KEY = os.getenv(
    "RAPIDAPI_KEY",
    "dbcb6f204emshf93e9e1bb342b5fp1c720djsn909778cd5b67"
)

# THAY TOKEN VÀ CHAT ID CỦA TELEGRAM VÀO 2 DƯỚI NÀY:
TELEGRAM_BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN",
    "PASTE_TELEGRAM_BOT_TOKEN_HERE"
)

TELEGRAM_CHAT_ID = os.getenv(
    "TELEGRAM_CHAT_ID",
    "PASTE_TELEGRAM_CHAT_ID_HERE"
)

# 8 giây / lần là hợp lý.
POLL_SECONDS = 8

REQUEST_TIMEOUT = 12

# Chỉ gửi Telegram khi trận có thay đổi.
SEND_ONLY_ON_CHANGE = True

# Không gửi spam nếu probability thay đổi quá ít.
MIN_PROBABILITY_CHANGE = 0.015


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

log = logging.getLogger(
    "TENNIS-LIVE-AI"
)


# ============================================================
# HTTP CLIENT
# ============================================================

class APIClient:

    def __init__(self):

        self.session = requests.Session()

        self.session.headers.update({
            "Content-Type": "application/json",
            "X-RapidAPI-Host": HOST,
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "User-Agent": "TennisLiveAI/3.0"
        })


    def get(self, path):

        url = BASE_URL + path

        try:

            response = self.session.get(
                url,
                timeout=REQUEST_TIMEOUT
            )

            if response.status_code == 429:

                log.warning(
                    "RapidAPI rate limit"
                )

                return None


            if response.status_code != 200:

                log.error(
                    "HTTP %s | %s",
                    response.status_code,
                    response.text[:500]
                )

                return None


            data = response.json()

            if isinstance(data, dict):

                if data.get("success") is False:

                    log.error(
                        "API returned error: %s",
                        data.get("message")
                    )

                    return None


            return data


        except requests.Timeout:

            log.warning(
                "API timeout: %s",
                path
            )

            return None


        except requests.RequestException as e:

            log.error(
                "Request error: %s",
                e
            )

            return None


        except ValueError:

            log.error(
                "Invalid JSON: %s",
                path
            )

            return None


# ============================================================
# API
# ============================================================

class TennisAPI:

    def __init__(self):

        self.client = APIClient()


    def live_events(self):

        data = self.client.get(
            "/events/live"
        )

        if not data:
            return []


        result = data.get(
            "result"
        )


        if isinstance(result, list):

            return result


        if isinstance(result, dict):

            for key in (
                "events",
                "data",
                "matches",
                "results",
                "items"
            ):

                value = result.get(key)

                if isinstance(value, list):

                    return value


        value = data.get("data")

        if isinstance(value, list):

            return value


        return []


    def live_score(
        self,
        event_id
    ):

        return self.client.get(
            f"/event/live-score/get/{event_id}"
        )


    def timeline(
        self,
        event_id
    ):

        return self.client.get(
            f"/event/timeline/{event_id}"
        )


# ============================================================
# MATCH STATE
# ============================================================

@dataclass
class Match:

    event_id: str

    player1: str

    player2: str

    score: str = ""

    status: str = ""

    points: str = ""

    indicator: str = ""

    league: str = ""

    tour_type: str = ""

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
# HELPERS
# ============================================================

def first_value(
    data: Dict[str, Any],
    keys
):

    for key in keys:

        value = data.get(key)

        if value is not None:

            return value

    return None


def to_float(value):

    try:

        if value is None:
            return 0.0

        if isinstance(value, str):

            value = value.replace(
                "%",
                ""
            )

        return float(value)

    except Exception:

        return 0.0


def clamp(
    value,
    minimum=0.01,
    maximum=0.99
):

    return max(
        minimum,
        min(maximum, value)
    )


def unwrap(data):

    if not isinstance(data, dict):

        return {}


    result = data.get("result")

    if isinstance(result, dict):

        for key in (
            "event",
            "match",
            "data"
        ):

            value = result.get(key)

            if isinstance(value, dict):

                return value

        return result


    if isinstance(data.get("data"), dict):

        return data["data"]


    return data


def parse_match(
    raw
):

    if not isinstance(raw, dict):

        return None


    player1 = first_value(
        raw,
        [
            "participant1",
            "player1",
            "home",
            "homePlayer"
        ]
    )


    player2 = first_value(
        raw,
        [
            "participant2",
            "player2",
            "away",
            "awayPlayer"
        ]
    )


    if not player1 or not player2:

        name = str(
            raw.get("name", "")
        )

        if " vs " in name:

            player1, player2 = (
                name.split(
                    " vs ",
                    1
                )
            )


    if not player1 or not player2:

        return None


    event_id = first_value(
        raw,
        [
            "id",
            "eventId",
            "event_id",
            "matchId"
        ]
    )


    if not event_id:

        event_id = (
            f"{player1}_{player2}"
        )


    return Match(

        event_id=str(event_id),

        player1=str(player1),

        player2=str(player2),

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

        tour_type=str(
            raw.get("tourType") or ""
        ),

        stats=(
            raw.get("stats")
            if isinstance(
                raw.get("stats"),
                dict
            )
            else {}
        ),

        timeline=(
            raw.get("timeline")
            if isinstance(
                raw.get("timeline"),
                list
            )
            else []
        ),

        raw=raw
    )


def merge_live_data(
    match,
    data
):

    payload = unwrap(
        data
    )

    if not payload:

        return


    value = first_value(
        payload,
        [
            "score",
            "currentScore"
        ]
    )

    if value is not None:

        match.score = str(value)


    value = first_value(
        payload,
        [
            "points",
            "point",
            "currentPoint"
        ]
    )

    if value is not None:

        match.points = str(value)


    value = first_value(
        payload,
        [
            "indicator",
            "serve",
            "server"
        ]
    )

    if value is not None:

        match.indicator = str(value)


    value = payload.get(
        "status"
    )

    if value is not None:

        match.status = str(value)


    stats = payload.get(
        "stats"
    )

    if isinstance(stats, dict):

        match.stats.update(
            stats
        )


    timeline = payload.get(
        "timeline"
    )

    if isinstance(timeline, list):

        match.timeline = timeline


def parse_score(
    score
):

    result = {
        "sets1": 0,
        "sets2": 0,
        "games1": 0,
        "games2": 0
    }


    if not score:

        return result


    parts = [
        x.strip()
        for x in str(score).split(",")
        if x.strip()
    ]


    if not parts:

        return result


    for part in parts[:-1]:

        if "-" not in part:
            continue

        try:

            a, b = (
                part
                .split("-")[:2]
            )

            a = int(a)
            b = int(b)

        except Exception:

            continue


        if a > b:

            result["sets1"] += 1

        elif b > a:

            result["sets2"] += 1


    if len(parts) == 1:

        try:

            a, b = (
                parts[0]
                .split("-")[:2]
            )

            a = int(a)
            b = int(b)

            if (
                a >= 6
                and
                a - b >= 2
            ):

                if a > b:
                    result["sets1"] = 1
                else:
                    result["sets2"] = 1

            elif (
                a == 7
                and b in (5, 6)
            ):

                result["sets1"] = 1

            elif (
                b == 7
                and a in (5, 6)
            ):

                result["sets2"] = 1

            result["games1"] = a
            result["games2"] = b

            return result

        except Exception:

            return result


    last = parts[-1]

    if "-" in last:

        try:

            a, b = (
                last
                .split("-")[:2]
            )

            result["games1"] = int(a)
            result["games2"] = int(b)

        except Exception:
            pass


    return result


def point_probability(
    points
):

    if not points:
        return 0.50


    text = str(points).lower().strip()

    mapping = {
        "love": 0,
        "0": 0,
        "15": 1,
        "30": 2,
        "40": 3,
        "a": 4,
        "adv": 4,
        "advantage": 4
    }


    if "-" not in text:

        return 0.50


    a, b = (
        text.split("-")[:2]
    )


    a = mapping.get(
        a.strip(),
        None
    )

    b = mapping.get(
        b.strip(),
        None
    )


    if a is None or b is None:

        try:

            a = float(
                text.split("-")[0]
            )

            b = float(
                text.split("-")[1]
            )

        except Exception:

            return 0.50


    if a > b:
        return 0.58

    if b > a:
        return 0.42

    return 0.50


def pair(
    stats,
    names
):

    value = None

    for name in names:

        if name in stats:

            value = stats[name]
            break


    if not isinstance(
        value,
        list
    ):

        return 0.0, 0.0


    a = (
        to_float(value[0])
        if len(value) > 0
        else 0.0
    )

    b = (
        to_float(value[1])
        if len(value) > 1
        else 0.0
    )


    return a, b


def analyze_stats(
    match
):

    stats = match.stats


    aces1, aces2 = pair(
        stats,
        [
            "aces",
            "ace"
        ]
    )


    df1, df2 = pair(
        stats,
        [
            "double_faults",
            "doubleFaults",
            "double_fault"
        ]
    )


    serve1, serve2 = pair(
        stats,
        [
            "win_1st_serve",
            "first_serve_won",
            "firstServeWon"
        ]
    )


    bp1, bp2 = pair(
        stats,
        [
            "break_point_conversions",
            "breakPointsWon"
        ]
    )


    return {
        "aces1": aces1,
        "aces2": aces2,

        "df1": df1,
        "df2": df2,

        "serve1": serve1,
        "serve2": serve2,

        "bp1": bp1,
        "bp2": bp2
    }


def analyze_timeline(
    match
):

    score1 = 0.0
    score2 = 0.0

    recent = []


    for event in match.timeline:

        if not isinstance(
            event,
            dict
        ):

            continue


        text = str(
            event.get(
                "text",
                ""
            )
        )


        if not text:
            continue


        recent.append(text)


        lower = text.lower()


        p1 = (
            match.player1.lower()
            in lower
        )

        p2 = (
            match.player2.lower()
            in lower
        )


        if "break" in lower:

            if p1:

                score1 += 2.5

            elif p2:

                score2 += 2.5


        elif "hold" in lower:

            if p1:

                score1 += 0.8

            elif p2:

                score2 += 0.8


    return {
        "score1": score1,
        "score2": score2,
        "recent": recent[-10:]
    }


def calculate_probability(
    match
):

    score = parse_score(
        match.score
    )

    p = 0.50

    set_difference = (
        score["sets1"]
        -
        score["sets2"]
    )

    p += (
        set_difference
        * 0.19
    )

    game_difference = (
        score["games1"]
        -
        score["games2"]
    )

    p += (
        game_difference
        * 0.025
    )

    current_point = (
        point_probability(
            match.points
        )
    )

    p += (
        current_point
        -
        0.50
    ) * 0.08

    timeline = analyze_timeline(
        match
    )

    timeline_total = (
        timeline["score1"]
        +
        timeline["score2"]
    )

    if timeline_total > 0:

        tp = (
            timeline["score1"]
            /
            timeline_total
        )

        p += (
            tp
            -
            0.50
        ) * 0.16

    stats = analyze_stats(
        match
    )

    serve_total = (
        stats["serve1"]
        +
        stats["serve2"]
    )

    if serve_total > 0:

        sp = (
            stats["serve1"]
            /
            serve_total
        )

        p += (
            sp
            -
            0.50
        ) * 0.08

    ace_total = (
        stats["aces1"]
        +
        stats["aces2"]
    )

    if ace_total > 0:

        ap = (
            stats["aces1"]
            /
            ace_total
        )

        p += (
            ap
            -
            0.50
        ) * 0.04

    df_total = (
        stats["df1"]
        +
        stats["df2"]
    )

    if df_total > 0:

        dp = (
            stats["df2"]
            /
            df_total
        )

        p += (
            dp
            -
            0.50
        ) * 0.04

    bp_total = (
        stats["bp1"]
        +
        stats["bp2"]
    )

    if bp_total > 0:

        bp = (
            stats["bp1"]
            /
            bp_total
        )

        p += (
            bp
            -
            0.50
        ) * 0.06

    return clamp(
        p
    )


def confidence(
    p
):

    edge = abs(
        p - 0.50
    )

    if edge >= 0.30:
        return "VERY HIGH"

    if edge >= 0.20:
        return "HIGH"

    if edge >= 0.10:
        return "MEDIUM"

    return "LOW"


def diagnose(
    match
):

    p1 = calculate_probability(
        match
    )

    p2 = (
        1.0 - p1
    )

    if p1 >= p2:

        winner = match.player1
        winner_p = p1

    else:

        winner = match.player2
        winner_p = p2

    return {
        "winner": winner,
        "p1": p1,
        "p2": p2,
        "confidence": confidence(
            winner_p
        ),
        "winner_probability": winner_p
    }


def fingerprint(
    match
):

    last_timeline = ""

    if match.timeline:

        last = match.timeline[-1]

        if isinstance(
            last,
            dict
        ):

            last_timeline = str(
                last.get(
                    "text",
                    ""
                )
            )

    return (
        match.score,
        match.points,
        match.indicator,
        match.status,
        last_timeline,
        len(match.timeline)
    )


def send_telegram(
    message
):

    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN.startswith("PASTE_"):

        log.warning(
            "Telegram token chưa được cấu hình"
        )

        return False


    if not TELEGRAM_CHAT_ID or TELEGRAM_CHAT_ID.startswith("PASTE_"):

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

                "text":
                    message,

                "disable_web_page_preview":
                    True
            },

            timeout=10
        )


        if response.status_code != 200:

            log.error(
                "Telegram HTTP %s: %s",
                response.status_code,
                response.text[:300]
            )

            return False


        return True


    except Exception as e:

        log.error(
            "Telegram error: %s",
            e
        )

        return False


def format_message(
    match,
    result
):

    p1 = (
        result["p1"] * 100
    )

    p2 = (
        result["p2"] * 100
    )

    timeline = analyze_timeline(
        match
    )

    stats = analyze_stats(
        match
    )

    last_event = (
        timeline["recent"][-1]
        if timeline["recent"]
        else "N/A"
    )


    return f"""
🎾 TENNIS LIVE AI

🏟 {match.league}
🏆 {match.tour_type}

👤 {match.player1}
vs
👤 {match.player2}

━━━━━━━━━━━━━━

📊 SCORE
{match.score}

🎯 POINT
{match.points or "N/A"}

📡 STATUS
{match.status}

━━━━━━━━━━━━━━

🏆 LIVE WIN PROBABILITY

{match.player1}: {p1:.1f}%
{match.player2}: {p2:.1f}%

🥇 CURRENT DIAGNOSIS
{result["winner"]}

🔥 CONFIDENCE
{result["confidence"]}

━━━━━━━━━━━━━━

📈 LIVE DATA

ACES
{match.player1}: {stats["aces1"]:.0f}
{match.player2}: {stats["aces2"]:.0f}

DOUBLE FAULTS
{match.player1}: {stats["df1"]:.0f}
{match.player2}: {stats["df2"]:.0f}

1ST SERVE WON
{match.player1}: {stats["serve1"]:.0f}%
{match.player2}: {stats["serve2"]:.0f}%

━━━━━━━━━━━━━━

📡 LAST EVENT
{last_event}

🔄 AUTO UPDATE
Every {POLL_SECONDS}s
""".strip()


def enrich_match(
    api,
    match
):

    live = api.live_score(
        match.event_id
    )

    if live:

        merge_live_data(
            match,
            live
        )

    timeline = api.timeline(
        match.event_id
    )

    if timeline:

        payload = unwrap(
            timeline
        )

        if isinstance(
            payload,
            dict
        ):

            events = first_value(
                payload,
                [
                    "timeline",
                    "events",
                    "data"
                ]
            )

            if isinstance(
                events,
                list
            ):

                match.timeline = events

        elif isinstance(
            payload,
            list
        ):

            match.timeline = payload


def main():

    log.info(
        "=========================================="
    )

    log.info(
        "TENNIS LIVE AI v3 STARTED"
    )

    log.info(
        "HOST: %s",
        HOST
    )

    log.info(
        "POLL: %ss",
        POLL_SECONDS
    )

    log.info(
        "=========================================="
    )


    if not RAPIDAPI_KEY:

        log.error(
            "RAPIDAPI_KEY is missing"
        )

        return


    api = TennisAPI()

    previous = {}


    while True:

        try:

            events = (
                api.live_events()
            )

            log.info(
                "LIVE EVENTS: %d",
                len(events)
            )

            active_ids = set()

            for raw in events:

                match = parse_match(
                    raw
                )

                if not match:

                    continue

                active_ids.add(
                    match.event_id
                )

                status = (
                    match.status
                    .lower()
                    .strip()
                )

                if status in {
                    "ended",
                    "finished",
                    "completed",
                    "cancelled",
                    "postponed"
                }:

                    continue

                enrich_match(
                    api,
                    match
                )

                state = fingerprint(
                    match
                )

                result = diagnose(
                    match
                )

                old = previous.get(
                    match.event_id
                )

                probability_changed = True

                if old:

                    old_p1 = old.get(
                        "p1",
                        0.50
                    )

                    probability_changed = (
                        abs(
                            result["p1"]
                            -
                            old_p1
                        )
                        >=
                        MIN_PROBABILITY_CHANGE
                    )

                state_changed = (
                    old is None
                    or
                    old.get("state")
                    !=
                    state
                )

                log.info(
                    "%s vs %s | %s | "
                    "%.1f%% / %.1f%% | %s",
                    match.player1,
                    match.player2,
                    result["winner"],
                    result["p1"] * 100,
                    result["p2"] * 100,
                    match.score
                )

                # Ép gửi tin nhắn ở lần quét đầu tiên của trận đấu để kiểm tra Telegram
                should_send = (

                    old is None

                    or

                    (
                        SEND_ONLY_ON_CHANGE
                        and
                        state_changed
                        and
                        probability_changed
                    )

                )


                if should_send:

                    send_telegram(
                        format_message(
                            match,
                            result
                        )
                    )


                previous[
                    match.event_id
                ] = {

                    "state":
                        state,

                    "p1":
                        result["p1"],

                    "winner":
                        result["winner"]
                }


            previous = {

                k: v

                for k, v
                in previous.items()

                if k in active_ids

            }


        except KeyboardInterrupt:

            log.info(
                "BOT STOPPED"
            )

            break


        except Exception as e:

            log.exception(
                "MAIN ERROR: %s",
                e
            )


        time.sleep(
            POLL_SECONDS
        )


if __name__ == "__main__":

    main()
