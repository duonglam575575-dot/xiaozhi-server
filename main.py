@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("ESP32-S3 đã kết nối thành công qua WebSocket!")
    audio_buffer = bytearray()
    
    try:
        while True:
            # Nhận dữ liệu từ ESP32-S3 (có thể là text hoặc binary audio)
            message = await websocket.receive()
            
            if "bytes" in message:
                chunk = message["bytes"]
                audio_buffer.extend(chunk)
                
                # Khi thu đủ một lượng âm thanh (ví dụ: khoảng 3-5 giây hoặc khi ngắt quãng)
                if len(audio_buffer) > 16000 * 2 * 3:  # Khoảng 3 giây audio 16kHz 16-bit
                    # Bước 1: Lưu buffer thành file wav tạm thời để gửi đi STT
                    wav_io = io.BytesIO()
                    with wave.open(wav_io, 'wb') as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(16000)
                        wf.writeframes(audio_buffer)
                    wav_io.seek(0)
                    wav_io.name = "audio.wav"
                    
                    # Reset lại bộ đệm âm thanh sau khi xử lý xong
                    audio_buffer.clear()
                    
            elif "text" in message:
                text_data = message["text"]
                print(f"Nhận tin nhắn dạng text: {text_data}")
                
    except WebSocketDisconnect:
        print("ESP32-S3 đã ngắt kết nối.")
    except Exception as e:
        print(f"Lỗi kết nối Websocket: {e}")
Bạn đã gửi
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("ESP32-S3 đã kết nối thành công qua WebSocket!")
    audio_buffer = bytearray()
    
    try:
        while True:
            # Nhận dữ liệu từ ESP32-S3 (có thể là text hoặc binary audio)
            message = await websocket.receive()
            
            if "bytes" in message:
                chunk = message["bytes"]
                audio_buffer.extend(chunk)
                
                # Khi thu đủ một lượng âm thanh (ví dụ: khoảng 3-5 giây hoặc khi ngắt quãng)
                if len(audio_buffer) > 16000 * 2 * 3:  # Khoảng 3 giây audio 16kHz 16-bit
                    # Bước 1: Lưu buffer thành file wav tạm thời để gửi đi STT
                    wav_io = io.BytesIO()
                    with wave.open(wav_io, 'wb') as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(16000)
                        wf.writeframes(audio_buffer)
                    wav_io.seek(0)
                    wav_io.name = "audio.wav"
                    
                    # Reset lại bộ đệm âm thanh sau khi xử lý xong
                    audio_buffer.clear()
                    
            elif "text" in message:
                text_data = message["text"]
                print(f"Nhận tin nhắn dạng text: {text_data}")
                
    except WebSocketDisconnect:
        print("ESP32-S3 đã ngắt kết nối.")
    except Exception as e:
        print(f"Lỗi kết nối Websocket: {e}")
