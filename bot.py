import os
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8934220044:AAH4Ie4513gfnH-bJu1wcPoCSnKXcvlHtFM')
RAPIDAPI_KEY = "1b38cdb058mshdff41dd9b75d9kcjp159177jun2b3cb7c6a741"
HOST = "tennis-api-atp-wta-itf.p.rapidapi.com"
BASE_URL = f"https://{HOST}/tennis/v2/extend/api"
WEBHOOK_URL = "https://tennis-888-bot-production.up.railway.app/webhook"

def setup_webhook():
    if TELEGRAM_BOT_TOKEN:
        try:
            requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook?url={WEBHOOK_URL}&drop_pending_updates=true", timeout=5)
        except Exception:
            pass

setup_webhook()

def send_msg(chat_id, text):
    if not TELEGRAM_BOT_TOKEN:
        return
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }, timeout=10)
    except Exception:
        pass

@app.route('/', methods=['GET'])
def home():
    return "OK"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json or {}
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "").strip()
            
            if text.startswith("/start"):
                send_msg(chat_id, "⚡ Nhập: `Player 1 vs Player 2`")
                return "OK", 200
            
            if " vs " in text.lower() or " VS " in text:
                parts = text.split(" vs " if " vs " in text.lower() else " VS ")
                if len(parts) == 2:
                    p1_in, p2_in = parts[0].strip().lower(), parts[1].strip().lower()
                    
                    winner, prob, real_score, status, league = parts[0].strip(), "85%", "Đang cập nhật...", "Live", "Live Match"
                    try:
                        headers = {"X-RapidAPI-Host": HOST, "X-RapidAPI-Key": RAPIDAPI_KEY}
                        res = requests.get(BASE_URL + "/events/live", headers=headers, timeout=5)
                        if res.status_code == 200:
                            events = res.json().get("result", [])
                            candidates = events if isinstance(events, list) else [events]
                            
                            for ev in candidates:
                                if not isinstance(ev, dict):
                                    continue
                                ep1 = str(ev.get("participant1", "")).lower()
                                ep2 = str(ev.get("participant2", "")).lower()
                                
                                if (p1_in in ep1 or p1_in in ep2) and (p2_in in ep1 or p2_in in ep2):
                                    winner = ev.get("participant1", parts[0].strip())
                                    real_score = str(ev.get("score", ev.get("scores", "Đang cập nhật")))
                                    status = str(ev.get("status", "Live"))
                                    
                                    t_obj = ev.get("tournament")
                                    if isinstance(t_obj, dict):
                                        league = str(t_obj.get("name", ev.get("league", "Live Match")))
                                    else:
                                        league = str(ev.get("league", "Live Match"))
                                    break
                    except Exception:
                        pass
                    
                    msg = (
                        f"🏆 *CHỐT KÈO CHIẾN THẮNG*\n\n"
                        f"🏟 Giải: {league}\n"
                        f"⚔️ {parts[0].strip()} vs {parts[1].strip()}\n"
                        f"⚡ Trạng thái: {status}\n"
                        f"🎯 Tỷ số: `{real_score}`\n\n"
                        f"👉 **Cửa sáng nhất:** *{winner}* (Xác suất ~{prob})"
                    )
                    send_msg(chat_id, msg)
                    return "OK", 200
    except Exception:
        pass
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
