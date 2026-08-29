def fetch_live_match_stats(player1, player2):
    url = BASE_URL + "/events/live"
    headers = {
        "X-RapidAPI-Host": HOST,
        "X-RapidAPI-Key": RAPIDAPI_KEY
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            events = data.get("result", [])
            if isinstance(events, list):
                for ev in events:
                    p1_name = str(ev.get("participant1", ""))
                    p2_name = str(ev.get("participant2", ""))
                    if player1.lower() in p1_name.lower() or player2.lower() in p2_name.lower():
                        # Lấy trực tiếp chuỗi điểm số từ API trả về
                        score = ev.get("scores") or ev.get("score") or "Đang cập nhật"
                        status = ev.get("status", "Đang diễn ra")
                        return {
                            "p1_name": p1_name if p1_name else player1,
                            "p2_name": p2_name if p2_name else player2,
                            "status": status,
                            "score": str(score)
                        }
    except Exception as e:
        print(f"Lỗi gọi API live: {e}")
    
    return {
        "p1_name": player1,
        "p2_name": player2,
        "status": "Đang diễn ra",
        "score": "Đang cập nhật"
    }
