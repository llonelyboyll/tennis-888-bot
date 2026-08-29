import os
import time
import logging
import requests

# ================= CONFIG =================
HOST = "tennis-api-atp-wta-itf.p.rapidapi.com"
BASE_URL = f"https://{HOST}/tennis/v2/extend/api"

# Ép cứng key chuẩn vào đây để chạy trực tiếp không qua biến môi trường
RAPIDAPI_KEY = "1b38cdb058mshdff41dd9b75d9kcjp159177jun2b3cb7c6a741"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

POLL_SECONDS = 10
REQUEST_TIMEOUT = 12

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("TENNIS-BOT")

# ================= API CLIENT =================
def fetch_live_matches():
    url = BASE_URL + "/events/live"
    headers = {
        "X-RapidAPI-Host": HOST,
        "X-RapidAPI-Key": RAPIDAPI_KEY
    }
    try:
        res = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        if res.status_code == 200:
            data = res.json()
            result = data.get("result")
            if isinstance(result, list):
                return result
            elif isinstance(result, dict):
                return result.get("events", [])
    except Exception as e:
        log.error("Lỗi gọi API live: %s", e)
    return []

def fetch_match_detail(event_id):
    url = BASE_URL + f"/event/live-score/get/{event_id}"
    headers = {
        "X-RapidAPI-Host": HOST,
        "X-RapidAPI-Key": RAPIDAPI_KEY
    }
    try:
        res = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        if res.status_code == 200:
            data = res.json()
            return data.get("result", {})
    except Exception:
        pass
    return {}

# ================= TELEGRAM =================
def send_telegram(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        log.error("Lỗi gửi Telegram: %s", e)

# ================= LOGIC DỰ ĐOÁN =================
def analyze_and_predict(match_raw, detail_raw):
    p1 = match_raw.get("participant1", "Player 1")
    p2 = match_raw.get("participant2", "Player 2")
    
    score = detail_raw.get("score") or match_raw.get("score") or "0-0"
    points = detail_raw.get("points") or match_raw.get("points") or "0-0"
    league = match_raw.get("league", {}).get("name", "Tennis Match")
    
    p1_score = 50.0
    p2_score = 50.0
    
    try:
        if "-" in str(score):
            sets = str(score).split(",")[-1].strip()
            if "-" in sets:
                g1, g2 = map(int, sets.split("-")[:2])
                if g1 > g2:
                    p1_score += (g1 - g2) * 8
                elif g2 > g1:
                    p2_score += (g2 - g1) * 8
    except Exception:
        pass

    total = p1_score + p2_score
    p1_rate = (p1_score / total) * 100
    p2_rate = (p2_score / total) * 100

    winner = p1 if p1_rate >= p2_rate else p2
    win_rate = max(p1_rate, p2_rate)

    return {
        "league": league,
        "p1": p1,
        "p2": p2,
        "score": score,
        "points": points,
        "winner": winner,
        "win_rate": win_rate,
        "p1_rate": p1_rate,
        "p2_rate": p2_rate
    }

# ================= MAIN LOOP =================
def main():
    log.info("BOT TENNIS ĐÃ KHỞI ĐỘNG...")
    sent_cache = {}

    while True:
        try:
            matches = fetch_live_matches()
            log.info("Đang quét thấy %d trận đấu trực tiếp.", len(matches))

            for raw in matches:
                event_id = str(raw.get("id"))
                status = str(raw.get("status", "")).lower()

                if "ended" in status or "finished" in status:
                    continue

                detail = fetch_match_detail(event_id)
                info = analyze_and_predict(raw, detail)

                signature = f"{info['score']}_{info['points']}"
                if sent_cache.get(event_id) == signature:
                    continue

                sent_cache[event_id] = signature

                msg = f"""
🎾 TẶNG KÈO / DỰ ĐOÁN TENNIS LIVE

🏟 Giải: {info['league']}
👤 {info['p1']} vs 👤 {info['p2']}

📊 Tỷ số: {info['score']}
⚡ Điểm hiện tại: {info['points']}

🎯 DỰ ĐOÁN NGƯỜI THẮNG:
🏆 {info['winner']} (Độ tin cậy: {info['win_rate']:.1f}%)

Tỷ lệ dòng tiền/thế trận:
- {info['p1']}: {info['p1_rate']:.1f}%
- {info['p2']}: {info['p2_rate']:.1f}%
""".strip()

                send_telegram(msg)
                log.info("Đã gửi tin nhắn trận: %s vs %s", info['p1'], info['p2'])

        except Exception as e:
            log.error("Lỗi vòng lặp chính: %s", e)

        time.sleep(POLL_SECONDS)

if __name__ == "__main__":
    main()
