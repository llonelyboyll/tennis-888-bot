import os
import random
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Lỗi gửi Telegram: {e}")

def advanced_live_simulation(p1, p2, score_string):
    sets = score_string.split(",")
    p1_momentum = 50.0
    p2_momentum = 50.0
    
    if len(sets) >= 2:
        current_set = sets[-1].strip()
        if "-" in current_set:
            try:
                g1, g2 = map(int, current_set.split("-"))
                if g1 > g2:
                    p1_momentum += (g1 - g2) * 4.5
                elif g2 > g1:
                    p2_momentum += (g2 - g1) * 4.5
            except ValueError:
                pass

    total = p1_momentum + p2_momentum
    p1_prob = round((p1_momentum / total) * 100, 1)
    p2_prob = round(100.0 - p1_prob, 1)
    
    p1_prob = max(15.0, min(85.0, p1_prob))
    p2_prob = round(100.0 - p1_prob, 1)

    leader = p1 if p1_prob > p2_prob else p2
    
    report = f"""⚡ *[REAL-TIME LIVE DYNAMIC ANALYZER]*
    
⚔️ *Cặp đấu:* {p1} (Trái) vs {p2} (Phải)
📊 *Tỷ số cập nhật:* `{score_string}`
----------------------------------------
🏆 *Dự báo biến động:* *{leader}* chiếm ưu thế
• *{p1} (Trái):* {p1_prob}%
• *{p2} (Phải):* {p2_prob}%

🎯 *Phân tích nhịp độ:* Hệ số momentum phản ánh sự lấn lướt trong các game đấu gần nhất. Tay vợt bên {'Trái' if p1_prob > p2_prob else 'Phải'} đang kiểm soát tốt điểm rơi và ép đối thủ vào vòng xoáy phòng ngự.
"""
    return report

@app.route("/", methods=["GET"])
def home():
    return "Tennis Live Bot đang hoạt động bình thường trên Server!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if not data:
        return {"status": "error"}, 400
        
    p1 = data.get("p1", "Player 1")
    p2 = data.get("p2", "Player 2")
    score = data.get("score", "0-0")
    
    result_text = advanced_live_simulation(p1, p2, score)
    send_telegram_message(result_text)
    
    return {"status": "success", "analysis": result_text}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
