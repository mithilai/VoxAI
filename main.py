from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import whisper
import tempfile
from io import BytesIO
import base64
import requests
import os

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Whisper model
model = whisper.load_model("base")

# API keys
CHATGROQ_API_KEY = os.getenv("GROQ_API_KEY")
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")

# --- LLM function ---
def generate_response(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {CHATGROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": "You are a friendly AI voice assistant."},
            {"role": "user", "content": prompt},
        ],
    }
    r = requests.post(url, headers=headers, json=payload)
    return r.json()["choices"][0]["message"]["content"]

# --- ElevenLabs TTS ---
def text_to_speech_elevenlabs(text):
    url = "https://api.elevenlabs.io/v1/text-to-speech/pMsXgVXv3BLzUgSXRplE"  # example voice
    headers = {"xi-api-key": ELEVEN_API_KEY, "Content-Type": "application/json"}
    data = {"text": text, "voice_settings": {"stability":0.5, "similarity_boost":0.8}}
    r = requests.post(url, headers=headers, json=data)
    return BytesIO(r.content)

# --- WebSocket endpoint ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    audio_buffer = BytesIO()
    
    while True:
        data = await websocket.receive_text()
        if data == "END":
            # Save audio to temp file
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            tmp.write(audio_buffer.getbuffer())
            tmp.close()

            # Transcribe using Whisper
            text = model.transcribe(tmp.name)["text"]
            print("User said:", text)

            # Generate LLM response
            reply_text = generate_response(text)
            print("AI replied:", reply_text)

            # TTS using ElevenLabs
            tts_audio = text_to_speech_elevenlabs(reply_text)
            # Send back as Base64
            await websocket.send_text(base64.b64encode(tts_audio.getbuffer()).decode("utf-8"))

            audio_buffer = BytesIO()  # reset buffer
        else:
            # Append received audio chunk
            audio_buffer.write(base64.b64decode(data))
