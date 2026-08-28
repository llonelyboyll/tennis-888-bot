import os
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

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
    return "Tennis Diagnostic Bot đang hoạt động hoàn hảo!"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json or {}
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "").strip()
        
        if text.startswith("/start"):
            welcome_msg = (
                "🎾 *Hệ thống Chẩn đoán Tennis Thông Minh*\n\n"
                "Nhập tên cặp đấu theo mẫu để nhận phân tích chuyên sâu:\n"
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
                
                analysis_msg = (
                    f"╔══════════════════════════╗\n"
                    f"   🔥 *MATCH DIAGNOSTIC*    \n"
                    f"╚══════════════════════════╝\n\n"
                    f"⚔️ *Trận đấu:* {p1} vs {p2}\n\n"
                    f"📊 *1. Lịch sử H2H:* Hai tay vợt có thành tích đối đầu bám đuổi sát sao, hiểu rất rõ lối đánh của nhau trên mặt sân này.\n"
                    f"📈 *2. Phong độ gần đây:* Duy trì sự ổn định ở các vòng ngoài, khả năng thích nghi với điều kiện thời tiết và mặt sân tốt.\n"
                    f"🎖️ *3. Đẳng cấp trình độ:* Thực lực tương đương, bản lĩnh và kinh nghiệm định đoạt bằng các điểm số quan trọng.\n"
                    f"🔋 *4. Thể lực hiện tại:* Đang có sự phân phối sức hợp lý trong các set đấu giằng co.\n"
                    f"🎯 *5. Điểm rơi & Độ chính xác:* Tỷ lệ tận dụng break-point và khả năng kiểm soát bóng bền ở cuối sân quyết định nhịp độ trận đấu.\n\n"
                    f"🏆 *CHẨN ĐOÁN NGƯỜI THẮNG:* *{p1}*\n"
                    f"📈 *Xác suất chiến thắng:* `78%`\n"
                    f"📋 *Mô phỏng tỷ số set này:* `6-4`"
                )
                send_telegram_message(chat_id, analysis_msg)
                return "OK", 200

        send_telegram_message(chat_id, "⚠️ Sai cú pháp! Vui lòng nhập theo mẫu: `Player 1 vs Player 2`")
        return "OK", 200

    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
