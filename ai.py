from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
import shutil, uuid, os, tempfile, asyncio

from stt_whisper import transcribe_audio
from ttt_groq import get_groq_response
from tts_elabs import text_to_speech_elabs

app = FastAPI()

# Serve static TTS files
TTS_DIR = "./tts"
os.makedirs(TTS_DIR, exist_ok=True)
app.mount("/tts", StaticFiles(directory=TTS_DIR), name="tts")


@app.websocket("/ws/ai")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    conversation_history = []  # optional, for context-aware LLM

    try:
        while True:  # keep connection alive
            # Receive audio bytes from client
            audio_bytes = await websocket.receive_bytes()
            temp_file = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}.wav")
            with open(temp_file, "wb") as f:
                f.write(audio_bytes)

            # Stage 1: Transcription
            await websocket.send_text("status::🎧 Transcribing your audio...")
            await asyncio.sleep(0.1)
            transcript, _ = transcribe_audio(file_path=temp_file)
            conversation_history.append({"role": "user", "content": transcript})
            await websocket.send_text(f"user::{transcript}")

            # Stage 2: Groq LLM
            await websocket.send_text("status::💬 Generating response...")
            await asyncio.sleep(0.1)
            # pass conversation history as context if needed
            full_context = "\n".join([f"{m['role']}: {m['content']}" for m in conversation_history])
            response = get_groq_response(full_context)
            conversation_history.append({"role": "assistant", "content": response})
            await websocket.send_text(f"ai::{response}")

            # Stage 3: TTS
            await websocket.send_text("status::🔊 Generating speech...")
            await asyncio.sleep(0.1)
            tts_path = text_to_speech_elabs(response)
            tts_url = None
            if tts_path and os.path.exists(tts_path):
                tts_filename = f"{uuid.uuid4().hex}.mp3"
                tts_full_path = os.path.join(TTS_DIR, tts_filename)
                shutil.copy(tts_path, tts_full_path)
                tts_url = f"/tts/{tts_filename}"
            else:
                await websocket.send_text("status::⚠️ TTS failed. Using browser TTS fallback.")

            await websocket.send_text(f"done::{tts_url}")

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        await websocket.send_text(f"status::❌ Error: {str(e)}")
