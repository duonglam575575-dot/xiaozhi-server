import os
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from openai import OpenAI

app = FastAPI()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@app.get("/")
def root():
    return {"status": "Server is running"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("ESP32-S3 đã kết nối WebSocket thành công!")
    
    audio_buffer = bytearray()
    
    try:
        while True:
            message = await websocket.receive()
            
            if "bytes" in message and message["bytes"]:
                chunk = message["bytes"]
                audio_buffer.extend(chunk)
                
                if len(audio_buffer) >= 16384:
                    try:
                        audio_data = bytes(audio_buffer)
                        audio_buffer.clear()
                        
                        def process_ai_pipeline(pcm_bytes):
                            import tempfile
                            import wave
                            
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
                                temp_filename = temp_audio.name
                                with wave.open(temp_filename, 'wb') as wf:
                                    wf.setnchannels(1)
                                    wf.setsampwidth(2)
                                    wf.setframerate(16000)
                                    wf.writeframes(pcm_bytes)
                            
                            with open(temp_filename, "rb") as audio_file:
                                transcript = client.audio.transcriptions.create(
                                    model="whisper-1",
                                    file=audio_file,
                                    language="vi"
                                )
                            
                            os.unlink(temp_filename)
                            user_text = transcript.text
                            print(f"User nói: {user_text}")
                            
                            if not user_text.strip():
                                return None
                                
                            response = client.chat.completions.create(
                                model="gpt-3.5-turbo",
                                messages=[
                                    {"role": "system", "content": "Bạn là trợ lý giọng nói ngắn gọn, thân thiện, trả lời bằng tiếng Việt dưới 3 câu."},
                                    {"role": "user", "content": user_text}
                                ]
                            )
                            bot_reply = response.choices[0].message.content
                            print(f"Bot trả lời: {bot_reply}")
                            
                            tts_response = client.audio.speech.create(
                                model="tts-1",
                                voice="alloy",
                                input=bot_reply,
                                response_format="pcm"
                            )
                            return tts_response.content

                        speech_bytes = await asyncio.to_thread(process_ai_pipeline, audio_data)
                        
                        if speech_bytes:
                            await websocket.send_bytes(speech_bytes)
                            
                    except Exception as e:
                        print(f"Lỗi xử lý AI pipeline: {e}")
                        
            elif "text" in message:
                text_data = message["text"]
                print(f"Nhận text từ ESP32: {text_data}")
                
    except WebSocketDisconnect:
        print("ESP32-S3 đã ngắt kết nối WebSocket.")
    except Exception as e:
        print(f"Lỗi kết nối WebSocket: {e}")
