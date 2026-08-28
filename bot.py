import os
import requests
import time
import threading
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY', '1b38cdb05bmsh8ff4fdd9b75d91cp159177jsn2b3cb7c6d741')

live_engines = {}

def send_telegram_message(chat_id, text):
    if not TELEGRAM_BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Lỗi gửi tin nhắn: {e}")

def fetch_pure_bet365_live(p1, p2):
    """
    🌐 Lấy trực tiếp 100% dữ liệu từ Bet365 API trên RapidAPI, không dùng giả lập
    """
    url = "https://bet365.p.rapidapi.com/events/inplay"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "bet365.p.rapidapi.com"
    }
    p1_key = p1.split()[-1].lower()
    p2_key = p2.split()[-1].lower()
    
    try:
        response = requests.get(url, headers=headers, params={"sport": "13"}, timeout=6)
        if response.status_code == 200:
            data = response.json()
            matches = data.get("results", data.get("data", data.get("matches", [])))
            if isinstance(matches, list):
                for match in matches:
                    m_title = str(match.get("title", match.get("name", ""))()).lower()
                    if p1_key in m_title or p2_key in m_title:
                        score = match.get("scores", match.get("score", ""))
                        status = match.get("status", match.get("time", "Live"))
                        if score:
                            return f"{score} ({status})"
    except Exception as e:
        print(f"Lỗi gọi API Bet365: {e}")
        
    return None

def background_live_engine_worker():
    while True:
        time.sleep(5)
        if not live_engines:
            continue
            
        for chat_id, info in list(live_engines.items()):
            p1 = info["p1"]
            p2 = info["p2"]
            old_state = info["last_state"]
            
            new_state = fetch_pure_bet365_live(p1, p2)
            
            if new_state and new_state != old_state:
                live_engines[chat_id]["last_state"] = new_state
                
                alert_msg = (
                    f"🚨 *CẬP NHẬT TỶ SỐ BET365!*\n\n"
                    f"⚔️ *Trận đấu:* {p1} vs {p2}\n"
                    f"📡 *Tỷ số Live chính xác:* `{new_state}`"
                )
                send_telegram_message(chat_id, alert_msg)

@app.route('/', methods=['GET'])
def home():
    return "🔥 PURE BET365 LIVE TENNIS FEED đang hoạt động!"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json or {}
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "").strip()
        
        if text.startswith("/start"):
            welcome_msg = (
                "🔥 *PURE BET365 TENNIS FEED*\n\n"
                "Chỉ lấy và hiển thị tỷ số trực tiếp từ nguồn API Bet365.\n"
                "Nhập tên cặp đấu để bắt đầu:\n"
                "`Player 1 vs Player 2`"
            )
            send_telegram_message(chat_id, welcome_msg)
            return "OK", 200
        
        if " vs " in text.lower() or " VS " in text:
            delimiter = " vs " if " vs " in text.lower() else " VS "
            parts = text.split(delimiter)
            if len(parts) == 2:
                p1 = parts[0].strip()
                p2 = parts[1].strip()
                
                send_telegram_message(chat_id, f"⚡ Đang truy xuất luồng Bet365 cho trận *{p1} vs {p2}*...")
                
                current_state = fetch_pure_bet365_live(p1, p2)
                if not current_state:
                    current_state = "Đang chờ trận đấu cập nhật trên hệ thống Bet365..."
                
                live_engines[chat_id] = {
                    "p1": p1,
                    "p2": p2,
                    "last_state": current_state
                }
                
                response_msg = (
                    f"╔══════════════════════════╗\n"
                    f"     🔥 *BET365 LIVE FEED*     \n"
                    f"╚══════════════════════════╝\n\n"
                    f"⚔️ *Trận đấu:* {p1} vs {p2}\n"
                    f"📡 *Tỷ số Live:* `{current_state}`"
                )
                send_telegram_message(chat_id, response_msg)
                return "OK", 200

        send_telegram_message(chat_id, "⚠️ Sai cú pháp! Nhập theo mẫu: `Player 1 vs Player 2`")
        return "OK", 200

    return "OK", 200

if __name__ == '__main__':
    t = threading.Thread(target=background_live_engine_worker, daemon=True)
    t.start()
    
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
