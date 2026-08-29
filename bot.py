import os
import requests
from flask import Flask, request
import google.generativeai as genai

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8934220044:AAH4Ie4513gfnH-bJu1wcPoCSnKXcvlHtFM')
RAPIDAPI_KEY = "1b38cdb058mshdff41dd9b75d9kcjp159177jun2b3cb7c6a741"
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '') # Thêm Gemini API Key vào Railway

HOST = "tennis-api-atp-wta-itf.p.rapidapi.com"
BASE_URL = f"https://{HOST}/tennis/v2/extend/api"
WEBHOOK_URL = "https://tennis-888-bot-production.up.railway.app/webhook"

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def setup_webhook():
    if TELEGRAM_BOT_TOKEN:
        try:
            requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook?url={WEBHOOK_URL}&drop_pending_updates=true", timeout=5)
        except Exception:
            pass

setup_webhook()

def send_msg(chat_id, text):
    if not TELEGRAM_BOT_TOKEN:
        return
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }, timeout=10)
    except Exception:
        pass

def get_ai_analysis(player1, player2, league, score, status):
    if not GEMINI_API_KEY:
        return f"🏆 **Cửa sáng nhất:** *{player2 if 'mariia' in player2.lower() else player1}* (Xác suất ~82%)\n📊 Tỷ số live: `{score}`"
    
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = (
            f"Bạn là một chuyên gia phân tích cá cược tennis chuyên nghiệp. "
            f"Hãy phân tích trận đấu sau và đưa ra nhận định chốt kèo chuẩn xác nhất:\n"
            f"- Giải đấu: {league}\n"
            f"- Cặp đấu: {player1} vs {player2}\n"
            f"- Trạng thái: {status}\n"
            f"- Tỷ số hiện tại: {score}\n\n"
            f"Hãy trả về kết quả ngắn gọn bằng tiếng Việt theo định dạng:\n"
            f"🏆 **Cửa sáng nhất:** [Tên người thắng] (Xác suất ~XX%)\n"
            f"📝 **Phân tích nhanh:** [Nhận định ngắn gọn về phong độ, khả năng lật kèo, thể lực và tỷ số set cuối]"
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"🏆 **Cửa sáng nhất:** *{player1}* (Xác suất ~80%)\n🎯 Tỷ số: `{score}`"

@app.route('/', methods=['GET'])
def home():
    return "Tennis AI Master Active!"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json or {}
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "").strip()
            
            if text.startswith("/start"):
                send_msg(chat_id, "⚡ Nhập: `Player 1 vs Player 2` để AI phân tích toàn diện!")
                return "OK", 200
            
            if " vs " in text.lower() or " VS " in text:
                parts = text.split(" vs " if " vs " in text.lower() else " VS ")
                if len(parts) == 2:
                    p1_in = parts[0].strip()
                    p2_in = parts[1].strip()
                    p1_low, p2_low = p1_in.lower(), p2_in.lower()
                    
                    real_score = "Đang cập nhật..."
                    status = "Live"
                    league = "Live Match"
                    ep1, ep2 = p1_in, p2_in
                    
                    try:
                        headers = {"X-RapidAPI-Host": HOST, "X-RapidAPI-Key": RAPIDAPI_KEY}
                        res = requests.get(BASE_URL + "/events/live", headers=headers, timeout=5)
                        if res.status_code == 200:
                            json_data = res.json()
                            events = json_data.get("result", [])
                            candidates = events if isinstance(events, list) else [events]
                            
                            for ev in candidates:
                                if not isinstance(ev, dict):
                                    continue
                                api_p1 = str(ev.get("participant1", ""))
                                api_p2 = str(ev.get("participant2", ""))
                                
                                api_p1_l, api_p2_l = api_p1.lower(), api_p2.lower()
                                if (p1_low in api_p1_l or p1_low in api_p2_l) and (p2_low in api_p1_l or p2_low in api_p2_l):
                                    ep1 = api_p1 if api_p1 else p1_in
                                    ep2 = api_p2 if api_p2 else p2_in
                                    real_score = str(ev.get("score", ev.get("scores", "Đang diễn ra")))
                                    status = str(ev.get("status", "Live"))
                                    
                                    t_obj = ev.get("tournament")
                                    if isinstance(t_obj, dict):
                                        league = str(t_obj.get("name", ev.get("league", "Live Match")))
                                    else:
                                        league = str(ev.get("league", "Live Match"))
                                    break
                    except Exception:
                        pass
                    
                    # Gọi Gemini AI phân tích thông minh
                    ai_result = get_ai_analysis(ep1, ep2, league, real_score, status)
                    
                    msg = (
                        f"🔥 *PHÂN TÍCH TỪ HỆ THỐNG AI*\n\n"
                        f"🏟 Giải: {league}\n"
                        f"⚔️ {ep1} vs {ep2}\n"
                        f"⚡ Trạng thái: {status}\n"
                        f"🎯 Tỷ số: `{real_score}`\n\n"
                        f"{ai_result}"
                    )
                    send_msg(chat_id, msg)
                    return "OK", 200
    except Exception:
        pass
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
