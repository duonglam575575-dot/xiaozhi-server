import os
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from openai import OpenAI

app = FastAPI()

# Khởi tạo OpenAI client với biến môi trường
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@app.get("/")
def root():
    return {"status": "Server is running"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("ESP32-S3 đã kết nối WebSocket thành công!")
    
    # Bộ đệm lưu trữ dữ liệu âm thanh thô (PCM) từ ESP32 gửi lên
    audio_buffer = bytearray()
    
    try:
        while True:
            # Nhận dữ liệu từ ESP32 (có thể là bytes âm thanh hoặc text)
            message = await websocket.receive()
            
            if "bytes" in message and message["bytes"]:
                chunk = message["bytes"]
                audio_buffer.extend(chunk)
                
                # Khi thu đủ một lượng dữ liệu âm thanh (ví dụ: ~16KB ~ khoảng 0.5s - 1s âm thanh)
                if len(audio_buffer) >= 16384:
                    try:
                        # 1. Lưu tạm dữ liệu âm thanh thành file WAV hoặc gửi trực tiếp dạng buffer
                        audio_data = bytes(audio_buffer)
                        audio_buffer.clear() # Xóa đệm cũ để chuẩn bị nhận câu tiếp theo
                        
                        # Sử dụng asyncio.to_thread để không làm nghẽn luồng WebSocket async khi gọi API OpenAI
                        def process_ai_pipeline(pcm_bytes):
                            # Tạo file tạm chứa dữ liệu âm thanh gửi cho Whisper
                            import tempfile
                            import wave
                            
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
                                temp_filename = temp_audio.name
                                with wave.open(temp_filename, 'wb') as wf:
                                    wf.setnchannels(1)
                                    wf.setsampwidth(2) # 16-bit
                                    wf.setframerate(16000) # 16kHz
                                    wf.writeframes(pcm_bytes)
                            
                            # Gọi OpenAI Whisper chuyển giọng nói thành text
                            with open(temp_filename, "rb") as audio_file:
                                transcript = client.audio.transcriptions.create(
                                    model="whisper-1",
                                    file=audio_file,
                                    language="vi"
                                )
                            
                            # Xóa file tạm
                            os.unlink(temp_filename)
                            user_text = transcript.text
                            print(f"User nói: {user_text}")
                            
                            if not user_text.strip():
                                return None
                                
                            # Gọi GPT-3.5 lấy câu trả lời ngắn gọn
                            response = client.chat.completions.create(
                                model="gpt-3.5-turbo",
                                messages=[
                                    {"role": "system", "content": "Bạn là trợ lý giọng nói ngắn gọn, thân thiện, trả lời bằng tiếng Việt dưới 3 câu."},
                                    {"role": "user", "content": user_text}
                                ]
                            }
                            bot_reply = response.choices[0].message.content
                            print(f"Bot trả lời: {bot_reply}")
                            
                            # Gọi OpenAI TTS để chuyển câu trả lời thành âm thanh MP3/PCM
                            tts_response = client.audio.speech.create(
                                model="tts-1",
                                voice="alloy",
                                input=bot_reply,
                                response_format="pcm" # Định dạng PCM raw để ESP32 phát trực tiếp qua I2S
                            )
                            return tts_response.content

                        # Chạy tác vụ AI ở luồng phụ
                        speech_bytes = await asyncio.to_thread(process_ai_pipeline, audio_data)
                        
                        # Nếu có âm thanh phản hồi, gửi ngược xuống ESP32 qua WebSocket dạng binary
                        if speech_bytes:
                            await websocket.send_bytes(speech_bytes)
                            
                    except Exception as e:
                        print(f"Lỗi xử lý AI pipeline: {e}")
                        
            elif "text" in message:
                text_data = message["text"]
                print(f"Nhận text từ ESP32: {text_data}")
                if text_data == "HELLO_BOT":
                    # Xử lý gửi câu chào mẫu nếu ESP32 yêu cầu
                    pass
                    
    except WebSocketDisconnect:
        print("ESP32-S3 đã ngắt kết nối WebSocket.")
    except Exception as e:
        print(f"Lỗi kết nối WebSocket: {e}")
