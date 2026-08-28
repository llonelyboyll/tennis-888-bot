@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # Lấy thông số truyền thẳng từ link trên điện thoại
        player1 = request.args.get('player1', 'Djokovic')
        player2 = request.args.get('player2', 'Alcaraz')
        score1 = request.args.get('score1', '6-4, 3-2')
        score2 = request.args.get('score2', '4-6, 2-3')
        server = request.args.get('server', player1)
    else:
        # Nhận dữ liệu dạng JSON từ hệ thống tennis bên ngoài
        data = request.json or {}
        player1 = data.get('player1', 'Djokovic')
        player2 = data.get('player2', 'Alcaraz')
        score1 = data.get('score1', '6-4, 3-2')
        score2 = data.get('score2', '4-6, 2-3')
        server = data.get('server', player1)

    # Đoạn code xử lý tính toán Markov/momentum và gửi tin nhắn về Telegram của anh ở đây
    # ...
    
    return "Đã phân tích và gửi kết quả về Telegram thành công!"
