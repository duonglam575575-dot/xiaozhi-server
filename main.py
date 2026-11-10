import io
import os
import wave
from fastapi import FastAPI, WebSocket
from starlette.websockets import WebSocketDisconnect
from openai import OpenAI

app = FastAPI()

# Khởi tạo OpenAI client với API key từ biến môi trường trên Render
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("ESP32-S3 đã kết nối thành công qua WebSocket!")
    audio_buffer = bytearray()
    
    try:
        while True:
            message = await websocket.receive()
            
            if "bytes" in message:
                chunk = message["bytes"]
                audio_buffer.extend(chunk)
                
                # Khi thu đủ lượng âm thanh cho một câu hỏi (khoảng 3 giây)
                if len(audio_buffer) > 16000 * 2 * 3:
                    print("Đang xử lý âm thanh từ ESP32-S3...")
                    
                    # 1. Lưu buffer thành file wav tạm thời
                    wav_io = io.BytesIO()
                    with wave.open(wav_io, 'wb') as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(16000)
                        wf.writeframes(audio_buffer)
                    wav_io.seek(0)
                    wav_io.name = "audio.wav"
                    
                    try:
                        # 2. Chuyển giọng nói thành văn bản (Speech-to-Text bằng Whisper)
                        transcript = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=wav_io
                        )
                        user_text = transcript.text
                        print(f"Người dùng nói: {user_text}")
                        
                        # 3. Gửi văn bản cho AI xử lý câu trả lời (LLM)
                        response = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "Bạn là một trợ lý ảo giọng nói tiếng Việt ngắn gọn, thân thiện."},
                                {"role": "user", "content": user_text}
                            ]
                        )
                        reply_text = response.choices[0].message.content
                        print(f"AI trả lời: {reply_text}")
                        
                        # 4. Chuyển câu trả lời thành âm thanh (Text-to-Speech bằng TTS)
                        speech_response = client.audio.speech.create(
                            model="tts-1",
                            voice="alloy",
                            input=reply_text
                        )
                        audio_data = speech_response.content
                        
                        # 5. Gửi ngược dữ liệu âm thanh phản hồi về cho ESP32-S3 phát loa
                        await websocket.send_bytes(audio_data)
                        print("Đã gửi phản hồi âm thanh về cho thiết bị.")
                        
                    except Exception as ai_err:
                        print(f"Lỗi khi xử lý AI: {ai_err}")
                        
                    # Reset lại bộ đệm âm thanh sau khi hoàn thành
                    audio_buffer.clear()
                    
            elif "text" in message:
                text_data = message["text"]
                print(f"Nhận tin nhắn text: {text_data}")
                
    except WebSocketDisconnect:
        print("ESP32-S3 đã ngắt kết nối.")
    except Exception as e:
        print(f"Lỗi kết nối Websocket: {e}")
