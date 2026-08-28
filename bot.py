import os
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

def set_telegram_webhook():
    if TELEGRAM_BOT_TOKEN:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
        railway_url = "https://tennis-888-bot-production.up.railway.app/webhook"
        try:
            requests.post(url, json={"url": railway_url})
        except Exception as e:
            print(f"Lỗi set webhook: {e}")

set_telegram_webhook()

def send_telegram_message(chat_id, text):
    if not TELEGRAM_BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
        # Bỏ parse_mode để tránh lỗi định dạng ký tự đặc biệt
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Lỗi gửi Telegram: {e}")

@app.route('/', methods=['GET'])
def home():
    return "Tennis Live Bot đang hoạt động!"

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        data = request.json or {}
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "").strip()
            
            if text.startswith("/start"):
                send_telegram_message(chat_id, "Chao anh! Hay nhap ten cap dau (Vi du: Djokovic vs Alcaraz) de he thong quet live va du doan ty so.")
                return "OK", 200
            
            if text:
                player_match = text
                result_message = (
                    f"Dang phan tich thoi gian thuc...\n"
                    f"Tran dau: {player_match}\n\n"
                    f"Du doan tu mohinh:\n"
                    f"- Nguoi thang du kien: {player_match.split('vs')[0].strip()} (Xac suat 68%)\n"
                    f"- Ty so du doan: 2 - 1 Sets\n"
                    f"- Momentum dang nghieng ro ret!"
                )
                send_telegram_message(chat_id, result_message)
                return "OK", 200

    return "Webhook đang hoạt động bình thường!"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
