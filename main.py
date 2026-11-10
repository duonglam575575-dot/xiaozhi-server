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
    await websocket.accept()
    print("ESP32-S3 đã kết nối WebSocket thành công!")
    audio_buffer = bytearray()
    
    try:
        while True:
            message = await websocket.receive()
            
            if "bytes" in message:
                chunk = message["bytes"]
                audio_buffer.extend(chunk)
                
                if len(audio_buffer) > 16000 * 2 * 2:
                    print(f"Đang xử lý {len(audio_buffer)} bytes audio...")
                    
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
                                    {"role": "system", "content": "Bạn là trợ lý giọng nói ngắn gọn bằng tiếng Việt."},
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
                            await websocket.send_bytes(speech_response.content)
                            print("Đã gửi phản hồi âm thanh.")
                            
                    except Exception as ai_err:
                        print(f"Lỗi AI: {ai_err}")
                        
                    audio_buffer.clear()
                    
    except WebSocketDisconnect:
        print("ESP32 đã ngắt kết nối.")
    except Exception as e:
        print(f"Lỗi WebSocket: {e}")
