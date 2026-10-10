from flask import Flask, request, jsonify

app = Flask(__name__)

# Route trang chủ kiểm tra server sống hay chết
@app.route("/")
def home():
    return "Xiaozhi Server is running!"

# Route API nhận dữ liệu từ thiết bị (Ví dụ: ESP32 gửi yêu cầu hoặc văn bản)
@app.route("/api/chat", methods=["POST"])
def chat():
    # Lấy dữ liệu JSON do thiết bị gửi lên
    data = request.get_json()
    
    if not data or "message" not in data:
        return jsonify({"error": "Thiếu dữ liệu message!"}), 400
    
    user_message = data["message"]
    print(f"Nhận được từ thiết bị: {user_message}")
    
    # Ở đây bạn có thể tích hợp logic xử lý (gọi AI, xử lý lệnh, v.v.)
    reply_text = f"Server đã nhận được câu hỏi: '{user_message}'"
    
    # Trả về kết quả dạng JSON cho thiết bị
    return jsonify({
        "status": "success",
        "reply": reply_text
    })

if _name_ == "_main_":
    app.run(host="0.0.0.0", port=10000)
