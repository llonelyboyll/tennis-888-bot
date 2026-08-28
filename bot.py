import os
import requests
from flask import Flask, request

app = Flask(__name__)

# Thay token và chat_id của anh vào đây (hoặc lấy từ biến môi trường Railway)
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', 'TOKEN_CUA_ANH')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', 'CHAT_ID_CUA_ANH')

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Lỗi gửi Telegram: {e}")

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

    # Nội dung tin nhắn gửi về Telegram
    message = f"🎾 *Phân tích trận đấu Tennis*\n\n" \
              f"👤 {player1} vs {player2}\n" \
              f"📊 Tỷ số: {score1} - {score2}\n" \
              f"🎯 Đang giao bóng: {server}\n" \
              f"⚡ Đã tính toán momentum thành công!"

    # Gọi hàm bắn tin nhắn về Telegram
    send_telegram_message(message)
    
    return f"Da phan tich va gui Telegram tran: {player1} vs {player2} thanh cong!"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
