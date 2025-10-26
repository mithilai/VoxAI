import streamlit as st
from stt_whisper import record_with_vad, transcribe_audio
from ttt_groq import get_groq_response
from tts_elabs import text_to_speech_elabs
import tempfile
import pygame
import os
import time
import threading
import shutil
import uuid

# ---- Streamlit Config ----
st.set_page_config(page_title="VoxAI", layout="centered")
st.title("🧠 Chat With Mithil")

# ---- Session Setup ----
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---- Helper Functions ----
def add_message(role, content):
    """Append and display a message."""
    st.session_state.messages.append({"role": role, "content": content})
    st.chat_message(role).write(content)

def clean_temp_dir(temp_dir):
    """Ensure fresh temp directory before every new session."""
    if os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass
    os.makedirs(temp_dir, exist_ok=True)

def play_audio_hidden(audio_path):
    """Play audio silently and delete file after playback."""
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

# ---- Temp Directory ----
TEMP_DIR = os.path.join(tempfile.gettempdir(), "speaking_ai_temp")
clean_temp_dir(TEMP_DIR)

# ---- Main Logic ----
if st.button("🎙️ Push to Talk"):
    # Stage 1: Record audio
    with st.spinner("🎧 Listening... start speaking!"):
        user_audio = record_with_vad()
        time.sleep(0.3)

    # Stage 2: Transcription
    with st.spinner("🧠 Transcribing your audio..."):
        transcript, audio_path = transcribe_audio(user_audio)
        add_message("user", transcript)
        # Clean up input WAV file
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
        except:
            pass

    # Stage 3: LLM (Groq)
    with st.spinner("💬 Responding..."):
        response = get_groq_response(transcript)
        add_message("assistant", response)

    # Stage 4: TTS (Hidden Playback)
    with st.spinner("🔊 Speaking ..."):
        tts_path = text_to_speech_elabs(response)
        if tts_path and os.path.exists(tts_path):
            unique_tts_path = os.path.join(TEMP_DIR, f"tts_{uuid.uuid4().hex}.mp3")
            shutil.copy(tts_path, unique_tts_path)
            try:
                os.remove(tts_path)
            except:
                pass

            threading.Thread(
                target=play_audio_hidden, args=(unique_tts_path,), daemon=True
            ).start()

# ---- Display Chat ----
# ---- Display Chat ----
# if "rendered_index" not in st.session_state:
#     st.session_state.rendered_index = 0

# # Render only new messages
# for msg in st.session_state.messages[st.session_state.rendered_index:]:
#     st.chat_message(msg["role"]).write(msg["content"])

# # Update rendered index
# st.session_state.rendered_index = len(st.session_state.messages)

