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

def fetch_real_match_from_rapidapi(p1_keyword, p2_keyword):
    url = "https://tennis-api-atp-wta-itf.p.rapidapi.com/tennis/v2/extend/api/matches/live"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "tennis-api-atp-wta-itf.p.rapidapi.com"
    }
    try:
        response = requests.get(url, headers=headers, timeout=6)
        if response.status_code == 200:
            data = response.json()
            matches = []
            if isinstance(data, list):
                matches = data
            elif isinstance(data, dict):
                for k in ["matches", "results", "content", "data", "events"]:
                    if k in data and isinstance(data[k], list):
                        matches = data[k]
                        break
                if not matches:
                    matches = [data]

            p1_low = p1_keyword.lower()
            p2_low = p2_keyword.lower()

            for match in matches:
                match_str = str(match).lower()
                # Kiểm tra xem tên 2 vận động viên có khớp trong gói dữ liệu live không
                if any(t in match_str for t in p1_low.split() if len(t) > 2) or \
                   any(t in match_str for t in p2_low.split() if len(t) > 2):
                    return match
    except Exception as e:
        print(f"Lỗi kết nối API: {e}")
    return None

@app.route('/', methods=['GET'])
def home():
    return "Tennis Real API Bot đang hoạt động!"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json or {}
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "").strip()
        
        if text.startswith("/start"):
            welcome_msg = (
                "🎾 *Bot Quét Dữ Liệu Live API Thật*\n\n"
                "Nhập tên cặp đấu, bot sẽ tự động truy vấn dữ liệu từ RapidAPI:\n"
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
                
                send_telegram_message(chat_id, f"🔄 Đang query trực tiếp dữ liệu từ API cho *{p1} vs {p2}*...")
                
                match_data = fetch_real_match_from_rapidapi(p1, p2)
                
                if match_data:
                    # Bóc tách thông tin từ API thật
                    score_info = match_data.get("score", {})
                    display_score = score_info.get("display", score_info.get("sets", "Đang cập nhật"))
                    status = match_data.get("status", "Đang diễn ra trực tiếp (Live)")
                    
                    prediction_msg = (
                        f"🔥 *KẾT QUẢ DỮ LIỆU TỪ RAPIDAPI*\n\n"
                        f"⚔️ *Trận đấu:* {p1} vs {p2}\n"
                        f"⚡ *Trạng thái API:* {status}\n"
                        f"📊 *Tỷ số thực tế trên sàn:* `{display_score}`\n\n"
                        f"🎯 *Dữ liệu thô từ hệ thống:* Đã lấy thành công từ server API chính thức."
                    )
                else:
                    prediction_msg = (
                        f"⚠️ *Không tìm thấy trận đấu đang đánh trực tiếp trên API*\n\n"
                        f"Trận *{p1} vs {p2}* hiện có thể chưa lên sóng live hoặc API đang trễ nhịp. Anh kiểm tra lại tên hoặc chờ trận đấu chuyển sang trạng thái live nhé!"
                    )
                
                send_telegram_message(chat_id, prediction_msg)
                return "OK", 200

        send_telegram_message(chat_id, "⚠️ Sai cú pháp! Nhập theo mẫu: `Tên 1 vs Tên 2`")
        return "OK", 200

    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
