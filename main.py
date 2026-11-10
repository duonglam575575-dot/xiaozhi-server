from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

app = FastAPI()

@app.get("/")
def home():
    return {"status": "Xiaozhi Server is running!"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("ESP32 đã kết nối thành công!")
    await websocket.send_text("Da ket noi AI Server!")

    try:
        while True:
            data = await websocket.receive()
            if "bytes" in data:
                audio_chunk = data["bytes"]
                print(f"Nhận được chunk audio từ ESP32: {len(audio_chunk)} bytes")
    except WebSocketDisconnect:
        print("ESP32 đã ngắt kết nối.")
    except Exception as e:
        print(f"Lỗi: {e}")
