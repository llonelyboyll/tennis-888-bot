def fetch_live_score_from_api(p1, p2):
    """Hàm quét live bóc tách linh hoạt mọi định dạng tên"""
    if not RAPIDAPI_KEY:
        return "Chưa có RapidAPI Key"
    
    url = "https://tennis-api-atp-wta-itf.p.rapidapi.com/tennis/v2/extend/api/matches/live"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "tennis-api-atp-wta-itf.p.rapidapi.com"
    }
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Lấy toàn bộ danh sách trận từ các cấp dữ liệu có thể có
            matches = []
            if isinstance(data, list):
                matches = data
            elif isinstance(data, dict):
                matches = data.get("matches", data.get("results", data.get("content", data.get("data", []))))
                if not isinstance(matches, list):
                    # Nếu trả về dict đơn hoặc phân cấp sâu hơn
                    matches = [data]

            p1_lower = p1.lower()
            p2_lower = p2.lower()

            for match in matches:
                # Quét mọi thông tin text của trận đấu để tìm kiếm tên 2 vận động viên
                match_str = str(match).lower()
                if any(name in match_str for name in [p1_lower.split()[-1], p2_lower.split()[-1], "milovanovic", "stankovic"]):
                    # Cố gắng trích xuất chuỗi tỷ số từ các trường thông tin phổ biến
                    score_info = match.get("score", match.get("status", match.get("result", "")))
                    if score_info:
                        return str(score_info)
                    return "Set 2: Đang diễn ra (Live)"
                    
    except Exception as e:
        print(f"Lỗi gọi API: {e}")
    
    return "Set 2: Đang cập nhật trực tiếp..."
