import os
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY', '1b38cdb05bmsh8ff4fdd9b75d91cp159177jsn2b3cb7c6d741')

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

@app.route('/', methods=['GET'])
def home():
    return "Tennis Debug Bot đang chạy!"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json or {}
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "").strip()
        
        # Gõ /live để bot kéo toàn bộ danh sách trận đang đánh trên API của anh về xem thử
        if text.startswith("/live") or text.startswith("/start"):
            url = "https://tennis-api-atp-wta-itf.p.rapidapi.com/tennis/v2/extend/api/matches/live"
            headers = {
                "X-RapidAPI-Key": RAPIDAPI_KEY,
                "X-RapidAPI-Host": "tennis-api-atp-wta-itf.p.rapidapi.com"
            }
            try:
                res = requests.get(url, headers=headers, timeout=6)
                if res.status_code == 200:
                    raw_data = res.text[:3500] # Lấy một phần chuỗi JSON trả về
                    send_telegram_message(chat_id, f"📋 *Danh sách thô từ API Key:* \n`{raw_data}`")
                else:
                    send_telegram_message(chat_id, f"⚠️ Lỗi API Status: {res.status_code}")
            except Exception as e:
                send_telegram_message(chat_id, f"⚠️ Lỗi kết nối: {e}")
            return "OK", 200

        send_telegram_message(chat_id, "⚠️ Hãy gõ lệnh `/live` để kiểm tra các trận đang có trên API key của anh.")
        return "OK", 200

    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
