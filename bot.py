import os
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Lỗi: Thiếu Token hoặc Chat ID trong biến môi trường!")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": int(TELEGRAM_CHAT_ID),
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        print(f"Telegram API Status: {response.status_code}")
        print(f"Telegram API Response: {response.text}")
    except Exception as e:
        print(f"Lỗi kết nối HTTP tới Telegram: {e}")

@app.route('/', methods=['GET'])
def home():
    return "Tennis Live Bot đang hoạt động bình thường trên Server!"

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        player1 = request.args.get('player1', 'Djokovic')
        player2 = request.args.get('player2', 'Alcaraz')
        score1 = request.args.get('score1', '6-4, 3-2')
        score2 = request.args.get('score2', '4-6, 2-3')
        server = request.args.get('server', player1)
    else:
        data = request.json or {}
        player1 = data.get('player1', 'Djokovic')
        player2 = data.get('player2', 'Alcaraz')
        score1 = data.get('score1', '6-4, 3-2')
        score2 = data.get('score2', '4-6, 2-3')
        server = data.get('server', player1)

    message = f"🎾 *Phân tích trận đấu Tennis*\n\n" \
              f"👤 *{player1}* vs *{player2}*\n" \
              f"📊 Tỷ số: {score1} - {score2}\n" \
              f"🎯 Đang giao bóng: {server}\n" \
              f"⚡ Hệ thống phân tích đã sẵn sàng!"

    send_telegram_message(message)
    
    return f"Da gui tin nhan ve Telegram cho chat_id: {TELEGRAM_CHAT_ID}!"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
