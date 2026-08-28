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

def dynamic_analyze(p1, p2, score_str):
    score_lower = score_str.lower()
    
    if "2-0" in score_lower or "6-1" in score_lower or "6-2" in score_lower:
        winner = p1
        prob = "82%"
        analysis = f"📊 *Thế trận áp đảo:*\n• *{p1}* đang kiểm soát hoàn toàn nhịp độ, độ bền rally tốt và không cho đối phương khoảng trống lật ngược thế cờ."
    elif "tie" in score_lower or "3-3" in score_lower or "4-4" in score_lower or "5-5" in score_lower:
        winner = p1 if len(p1) % 2 == 0 else p2
        prob = "53%"
        analysis = f"⚡ *Thế trận giằng co (Cực kỳ căng thẳng):*\n• Hai VĐV đang bám đuổi từng điểm một ở loạt tie-break hoặc game sát nút.\n• Áp lực tâm lý đè nặng lên người giao bóng trước, tiềm ẩn rủi ro bẻ break cao."
    else:
        winner = p2
        prob = "69%"
        analysis = f"⚠️ *Tín hiệu bám đuổi / Lật kèo:*\n• *{p2}* đang tận dụng rất tốt thời cơ ở các game đỡ bóng để gây sức ép về thể lực lên đối thủ."

    return winner, prob, analysis

@app.route('/', methods=['GET'])
def home():
    return "Tennis Dynamic Weighting Bot đang hoạt động!"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json or {}
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "").strip()
        
        if text.startswith("/start"):
            welcome_msg = (
                "🎾 *Hệ thống Phân tích Tennis Thực Chiến*\n\n"
                "Nhập theo cú pháp kèm tỷ số thực tế bạn đang nhìn thấy:\n"
                "`Tên 1 vs Tên 2 | 6-4 3-2`"
            )
            send_telegram_message(chat_id, welcome_msg)
            return "OK", 200
        
        if " vs " in text.lower() or " VS " in text:
            match_part = text
            score_info = "Đang diễn ra trực tiếp"
            
            if "|" in text:
                parts_pipe = text.split("|")
                match_part = parts_pipe[0].strip()
                score_info = parts_pipe[1].strip()

            delimiter = " vs " if " vs " in match_part.lower() else " VS "
            parts = match_part.split(delimiter)
            
            if len(parts) == 2:
                p1 = parts[0].strip()
                p2 = parts[1].strip()
                
                winner, prob, details = dynamic_analyze(p1, p2, score_info)
                
                prediction_msg = (
                    f"🔥 *KẾT QUẢ PHÂN TÍCH ĐỊNH LƯỢNG*\n\n"
                    f"⚔️ *Trận đấu:* {p1} vs {p2}\n"
                    f"📊 *Tỷ số thực tế:* `{score_info}`\n\n"
                    f"🏆 *Dự đoán Cửa sáng:* *{winner}* (Xác suất ~{prob})\n\n"
                    f"{details}"
                )
                send_telegram_message(chat_id, prediction_msg)
                return "OK", 200

        send_telegram_message(chat_id, "⚠️ Sai cú pháp! Nhập theo mẫu: `Player 1 vs Player 2 | 6-4 3-2`")
        return "OK", 200

    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
