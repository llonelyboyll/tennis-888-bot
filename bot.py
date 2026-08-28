import os
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
WEBHOOK_URL = "https://tennis-888-bot-production.up.railway.app/webhook"

def register_webhook():
    if TELEGRAM_BOT_TOKEN:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook?url={WEBHOOK_URL}"
        try:
            resp = requests.get(url)
            print("Webhook registration result:", resp.text)
        except Exception as e:
            print(f"Lỗi đăng ký webhook: {e}")

# Tự động đăng ký ngay khi Flask khởi động worker
register_webhook()

def send_telegram_message(chat_id, text):
    if not TELEGRAM_BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Lỗi gửi tin nhắn: {e}")

@app.route('/', methods=['GET'])
def home():
    return "Tennis Live Bot đang hoạt động!"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json or {}
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "").strip()
        
        if text.startswith("/start"):
            send_telegram_message(chat_id, "Chao anh! Hay nhap ten cap dau (Vi du: Djokovic vs Alcaraz) de he thong quet live.")
            return "OK", 200
        
        if text:
            result_msg = f"Dang phan tich tran: {text}\nDu doan: Nguoi choi thang 2-1 sets!"
            send_telegram_message(chat_id, result_msg)
            return "OK", 200
            
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
