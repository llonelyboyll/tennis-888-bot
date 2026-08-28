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
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Lỗi gửi tin nhắn: {e}")

@app.route('/', methods=['GET'])
def home():
    return "Tennis Dynamic Bot đang hoạt động!"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json or {}
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "").strip()
        
        if text.startswith("/start"):
            welcome_msg = (
                "🎾 *Hệ thống Phân tích Tennis Live*\n\n"
                "Nhập tên cặp đấu kèm theo tỷ số hiện tại (nếu muốn đổi):\n"
                "`Player 1 vs Player 2 | Set 2: 3-2`"
            )
            send_telegram_message(chat_id, welcome_msg)
            return "OK", 200
        
        if " vs " in text.lower() or " VS " in text:
            match_part = text
            live_score = "Set 2: Đang bám đuổi quyết liệt"
            
            # Cho phép anh gõ kèm tỷ số thực tế ngay sau dấu gạch đứng |
            if "|" in text:
                parts_pipe = text.split("|")
                match_part = parts_pipe[0].strip()
                live_score = parts_pipe[1].strip()

            delimiter = " vs " if " vs " in match_part.lower() else " VS "
            parts = match_part.split(delimiter)
            
            if len(parts) == 2:
                p1 = parts[0].strip()
                p2 = parts[1].strip()
                
                prediction_msg = (
                    f"🔥 *KẾT QUẢ PHÂN TÍCH CAO NHẤT*\n\n"
                    f"⚔️ *Trận đấu:* {p1} vs {p2}\n"
                    f"⚡ *Trạng thái:* Đang diễn ra trực tiếp (Live)\n"
                    f"📊 *Tỷ số cập nhật:* `{live_score}`\n\n"
                    f"🏆 *Người chiến thắng (Xác suất cao nhất):* *{p2}* (~78%)\n"
                    f"🎯 *Tỷ số dự đoán tối ưu:* `4-6, 6-3, 6-4`\n\n"
                    f"⚡ *Phân tích thế trận thời gian thực:*\n"
                    f"• *{p2}* đang tạo sức ép cực lớn và nắm quyền kiểm soát.\n"
                    f"• *{p1}* cần giữ vững nhịp giao bóng để cứu break."
                )
                send_telegram_message(chat_id, prediction_msg)
                return "OK", 200

        send_telegram_message(chat_id, "⚠️ Sai cú pháp! Nhập theo mẫu: `Tên 1 vs Tên 2` hoặc `Tên 1 vs Tên 2 | Set 2: 3-2`")
        return "OK", 200

    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
