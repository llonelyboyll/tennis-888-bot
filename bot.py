import os
from flask import Flask, request

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "Tennis Live Bot đang hoạt động bình thường trên Server!"

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

    # In ra log trên Railway để kiểm tra dữ liệu nhận được từ iPhone
    print(f"Match received: {player1} vs {player2} | Score: {score1} - {score2} | Server: {server}")
    
    # TODO: Thêm logic gọi API Telegram của anh ở đây để bắn tin nhắn
    
    return f"Da phan tich tran dau: {player1} vs {player2} thanh cong!"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
