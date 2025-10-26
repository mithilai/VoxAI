import streamlit as st
from ttt_groq import get_groq_response
from tts_elabs import text_to_speech_elabs
from stt_whisper import transcribe_audio
import tempfile
import threading
import shutil
import uuid
import os
import base64
import time

# ---- Streamlit config ----
st.set_page_config(page_title="🎙️ Speaking AI", layout="centered")
st.title("🧠 Speaking AI (Whisper + Groq + ElevenLabs)")

# ---- Session Setup ----
if "messages" not in st.session_state:
    st.session_state.messages = []

TEMP_DIR = os.path.join(tempfile.gettempdir(), "speaking_ai_temp")
os.makedirs(TEMP_DIR, exist_ok=True)

def add_message(role, content):
    st.session_state.messages.append({"role": role, "content": content})
    st.chat_message(role).write(content)

def play_audio_hidden(audio_path):
    """Play TTS audio in background and remove after playback."""
    import pygame
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        pygame.mixer.quit()
        os.remove(audio_path)
    except Exception as e:
        print(f"⚠️ Audio playback error: {e}")
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
        except:
            pass

def process_audio(audio_bytes):
    """Save uploaded audio, transcribe, generate Groq response, play TTS."""
    # Save unique temp file
    temp_wav = os.path.join(TEMP_DIR, f"user_{uuid.uuid4().hex}.wav")
    with open(temp_wav, "wb") as f:
        f.write(audio_bytes)

    # Stage 1: Transcribe
    transcript = transcribe_audio(audio_bytes)
    add_message("user", transcript)

    # Stage 2: Groq
    response = get_groq_response(transcript)
    add_message("assistant", response)

    # Stage 3: TTS hidden
    tts_path = text_to_speech_elabs(response)
    if tts_path and os.path.exists(tts_path):
        unique_tts_path = os.path.join(TEMP_DIR, f"tts_{uuid.uuid4().hex}.mp3")
        shutil.copy(tts_path, unique_tts_path)
        try:
            os.remove(tts_path)
        except:
            pass
        threading.Thread(target=play_audio_hidden, args=(unique_tts_path,), daemon=True).start()

# ---- JavaScript Recorder ----
st.markdown("""
<script>
let mediaRecorder;
let audioChunks = [];

async function startRecording() {
    if (!navigator.mediaDevices) {
        alert("Microphone not supported");
        return;
    }
    const stream = await navigator.mediaDevices.getUserMedia({audio:true});
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];
    mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
    
    mediaRecorder.onstop = async e => {
        let blob = new Blob(audioChunks, {type:'audio/wav'});
        let reader = new FileReader();
        reader.readAsDataURL(blob);
        reader.onloadend = function() {
            let base64String = reader.result.split(',')[1];
            window.parent.postMessage({func:'processAudio', data: base64String}, "*");
        }
    };
    
    mediaRecorder.start();

    // Silence detection: stop after ~1 sec silence
    let audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    let source = audioCtx.createMediaStreamSource(stream);
    let analyser = audioCtx.createAnalyser();
    source.connect(analyser);
    analyser.fftSize = 512;
    let dataArray = new Uint8Array(analyser.fftSize);
    let silenceStart = null;
    
    function checkSilence() {
        analyser.getByteTimeDomainData(dataArray);
        let rms = Math.sqrt(dataArray.reduce((sum,v)=>sum+(v-128)**2,0)/dataArray.length);
        if (rms < 5) {  // adjust threshold
            if (!silenceStart) silenceStart = Date.now();
            else if (Date.now() - silenceStart > 1000) {  // 1 sec silence
                mediaRecorder.stop();
                return;
            }
        } else {
            silenceStart = null;
        }
        requestAnimationFrame(checkSilence);
    }
    checkSilence();
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
    }
}
</script>
""", unsafe_allow_html=True)

st.markdown("""
<button onclick="startRecording()">🎙️ Push to Talk</button>
""", unsafe_allow_html=True)

# ---- Receive audio from JS ----
audio_data = st.experimental_get_query_params().get("audio_data")
if audio_data:
    audio_bytes = base64.b64decode(audio_data[0])
    threading.Thread(target=process_audio, args=(audio_bytes,), daemon=True).start()

# ---- Display chat ----
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])
