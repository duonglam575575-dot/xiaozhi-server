import io
import os
import wave
from fastapi import FastAPI, WebSocket
from starlette.websockets import WebSocketDisconnect
from openai import OpenAI

app = FastAPI()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.acceptf = None
    print("ESP32-S3 đã kết nối WebSocket thành công!")
    audio_buffer = bytearray()
    
    try:
        while True:
            message = await websocket.receive()
            
            # Nhận dữ liệu nhị phân (audio chunks) từ ESP32
            if "bytes" in message:
                chunk = message["bytes"]
                audio_buffer.extend(chunk)
                
                # Giảm ngưỡng buffer xuống khoảng 1.5 - 2 giây để phản hồi nhanh hơn
                if len(audio_buffer) > 16000 * 2 * 2:
                    print(f"Đã nhận đủ {len(audio_buffer)} bytes audio, đang xử lý...")
                    
                    wav_io = io.BytesIO()
                    with wave.open(wav_io, 'wb') as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(16000)
                        wf.writeframes(audio_buffer)
                    wav_io.seek(0)
                    wav_io.name = "audio.wav"
                    
                    try:
                        transcript = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=wav_io
                        )
                        user_text = transcript.text
                        print(f"Người dùng nói: {user_text}")
                        
                        if user_text.strip():
                            response = client.chat.completions.create(
                                model="gpt-3.5-turbo",
                                messages=[
                                    {"role": "system", "content": "Bạn là trợ lý giọng nói ngắn gọn, thân thiện bằng tiếng Việt."},
                                    {"role": "user", "content": user_text}
                                ]
                            )
                            reply_text = response.choices[0].message.content
                            print(f"AI trả lời: {reply_text}")
                            
                            speech_response = client.audio.speech.create(
                                model="tts-1",
                                voice="alloy",
                                input=reply_text
                            )
                            audio_data = speech_response.content
                            
                            await websocket.send_bytes(audio_data)
                            print("Đã gửi âm thanh phản hồi về ESP32.")
                            
                    except Exception as ai_err:
                        print(f"Lỗi AI processing: {ai_err}")
                        
                    audio_buffer.clear()
                    
            elif "text" in message:
                print(f"Nhận text từ client: {message['text']}")
                
    except WebSocketDisconnect:
        print("ESP32-S3 đã ngắt kết nối WebSocket.")
    except Exception as e:
        print(f"Lỗi kết nối WebSocket: {e}")
