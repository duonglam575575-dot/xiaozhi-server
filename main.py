import os
import io
import wave
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from openai import OpenAI

app = FastAPI()

# Khởi tạo OpenAI client (lấy API key từ biến môi trường trên Render)
# Bạn cần thêm OPENAI_API_KEY vào phần Environment Variables trên Render Dashboard
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

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
                # Ta có thể gom lại để xử lý. Ở đây demo xử lý khi bộ đệm đạt đủ kích thước mẫu.
                if len(audio_buffer) > 16000 * 2 * 3: # Khoảng 3 giây audio 16kHz 16-bit
                    
                    # Bước 1: Lưu buffer thành file wav tạm thời để gửi đi STT
                    wav_io = io.BytesIO()
                    with wave.open(wav_io, 'wb') as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(16000)
                        wf.writeframes(audio_buffer)
                    wav_io.seek(0)
                    wav_io.name = "audio.wav"
                    
                    try:
                        # Bước 2: Chuyển giọng nói thành văn bản bằng OpenAI Whisper
                        transcript = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=wav_io
                        )
                        user_text = transcript.text
                        print(f"Người dùng nói: {user_text}")
                        
                        # Kiểm tra xem có gọi tên "Lyly" hay không
                        if "lyly" in user_text.lower() or "li li" in user_text.lower():
                            # Gửi text phản hồi lên màn hình ESP32 trước
                            await websocket.send_text("Lyly nghe đây ạ!")
                            
                            # Bước 3: Gọi AI (LLM) để tạo câu trả lời thông minh
                            response = client.chat.completions.create(
                                model="gpt-4o-mini",
                                messages=[
                                    {"role": "system", "content": "Bạn là Lyly, một trợ lý ảo thông minh, thân thiện và trả lời ngắn gọn bằng tiếng Việt."},
                                    {"role": "user", "content": user_text}
                                ]
                            )
                            reply_text = response.choices.message.content
                            print(f"Lyly trả lời: {reply_text}")
                            
                            # Gửi văn bản trả lời ra màn hình ESP32
                            await websocket.send_text(reply_text)
                            
                            # Bước 4: Chuyển câu trả lời thành giọng nói (TTS)
                            speech_response = client.audio.speech.create(
                                model="tts-1",
                                voice="alloy",
                                input=reply_text
                            )
                            
                            # Bước 5: Gửi file âm thanh nhị phân về ESP32 để phát ra loa MAX98357A
                            audio_bytes = speech_response.content
                            await websocket.send_bytes(audio_bytes)
                            
                    except Exception as e:
                        print(f"Lỗi xử lý AI: {e}")
                        
                    # Reset lại bộ đệm âm thanh sau khi xử lý xong
                    audio_buffer.clear()
                    
            elif "text" in message:
                text_data = message["text"]
                print(f"Nhận tin nhắn dạng text: {text_data}")
                
    except WebSocketDisconnect:
        print("ESP32-S3 đã ngắt kết nối.")
    except Exception as e:
        print(f"Lỗi kết nối WebSocket: {e}")
