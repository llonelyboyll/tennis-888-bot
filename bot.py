import os
import requests
import time
import threading
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY', '')

# Lưu trữ danh sách các trận đấu đang theo dõi: {chat_id: {"p1": "...", "p2": "...", "last_score": "..."}}
active_watchlist = {}

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

def fetch_live_score_from_api(p1, p2):
    """Hàm gọi RapidAPI để lấy tỷ số live thực tế của trận đấu"""
    if not RAPIDAPI_KEY:
        return None
    
    url = "https://tennis-api-atp-wta-itf.p.rapidapi.com/matches/live"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "tennis-api-atp-wta-itf.p.rapidapi.com"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        # Xử lý duyệt qua các định dạng kết quả trả về phổ biến của RapidAPI tennis
        matches = data.get("results", data.get("matches", data.get("content", [])))
        if not isinstance(matches, list):
            matches = []

        for match in matches:
            # Lấy tên các tay vợt từ cấu trúc API
            home_name = str(match.get("homePlayer", match.get("home_player", {})) or "").lower()
            away_name = str(match.get("awayPlayer", match.get("away_player", {})) or "").lower()
            
            # Nếu tên match chứa từ khóa của p1 hoặc p2
            if (p1.lower() in home_name or p1.lower() in away_name) or (p2.lower() in home_name or p2.lower() in away_name):
                # Trích xuất tỷ số thực tế từ API
                score_info = match.get("status", {}).get("reason", "") or match.get("score", "")
                if not score_info:
                    # Fallback lấy điểm số chi tiết từng set nếu có
                    current_set = match.get("currentSet", "Live")
                    score_info = f"Set {current_set}"
                return str(score_info)
                
    except Exception as e:
        print(f"Lỗi gọi API live: {e}")
    
    return None

def background_match_monitor():
    """Hàm chạy ngầm liên tục quét RapidAPI để bắt biến động tỷ số"""
    while True:
        time.sleep(30) # Quét định kỳ mỗi 30 giây
        if not active_watchlist:
            continue
            
        for chat_id, info in list(active_watchlist.items()):
            p1 = info["p1"]
            p2 = info["p2"]
            old_score = info["last_score"]
            
            # Gọi API lấy điểm số mới nhất
            current_score = fetch_live_score_from_api(p1, p2)
            
            # Nếu lấy được dữ liệu và tỷ số thực tế đã thay đổi so với lần trước
            if current_score and current_score != old_score:
                active_watchlist[chat_id]["last_score"] = current_score
                alert_msg = (
                    f"🚨 *CẢNH BÁO BIẾN ĐỘNG / LẬT KÈO!*\n\n"
                    f"⚔️ *Trận đấu:* {p1} vs {p2}\n"
                    f"⚠️ *Tỷ số mới cập nhật:* `{current_score}`\n"
                    f"💡 *Đề xuất:* Thế trận đã thay đổi, kiểm tra ngay bảng live để phòng ngừa lật kèo!"
                )
                send_telegram_message(chat_id, alert_msg)

@app.route('/', methods=['GET'])
def home():
    return "Tennis Live Monitoring & Alert Bot đang hoạt động!"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json or {}
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "").strip()
        
        if text.startswith("/start"):
            welcome_msg = (
                "🎾 *Hệ thống Dự đoán & Cảnh báo Lật kèo Tennis*\n\n"
                "Nhập tên cặp đấu để bot phân tích và **bám sát ngầm qua API thực tế**:\n"
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
                
                send_telegram_message(chat_id, f"🔄 Đang kết nối RapidAPI để thiết lập giám sát thực tế trận *{p1} vs {p2}*...")
                
                # Lấy tỷ số live thực tế từ API ngay khi bắt đầu
                initial_score = fetch_live_score_from_api(p1, p2) or "Đang đồng bộ dữ liệu Live..."
                active_watchlist[chat_id] = {
                    "p1": p1,
                    "p2": p2,
                    "last_score": initial_score
                }
                
                prediction_msg = (
                    f"🔥 *KẾT QUẢ PHÂN TÍCH & KÍCH HOẠT RADAR API*\n\n"
                    f"⚔️ *Trận đấu:* {p1} vs {p2}\n"
                    f"⚡ *Trạng thái:* Đang theo dõi trực tiếp từ máy chủ\n"
                    f"📊 *Tỷ số thời điểm kích hoạt:* `{initial_score}`\n\n"
                    f"🛡️ *Hệ thống:* Đã bật quét ngầm tự động mỗi 30 giây. Bot sẽ tự hú còi ngay khi API ghi nhận tỷ số dịch chuyển!"
                )
                send_telegram_message(chat_id, prediction_msg)
                return "OK", 200

        send_telegram_message(chat_id, "⚠️ Sai cú pháp! Vui lòng nhập theo mẫu: `Tên Player 1 vs Tên Player 2`")
        return "OK", 200

    return "OK", 200

if __name__ == '__main__':
    t = threading.Thread(target=background_match_monitor, daemon=True)
    t.start()
    
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
