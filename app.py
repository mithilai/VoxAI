import streamlit as st
from stt_whisper import record_with_vad, transcribe_audio
from ttt_groq import get_groq_response
from tts_elabs import text_to_speech_elabs

st.set_page_config(page_title="🎙️ Speaking AI", layout="centered")
st.title("🧠 Speaking AI (Whisper + Groq + ElevenLabs)")

if st.button("🎙️ Push to Talk"):
    # Record audio
    st.info("🎧 Listening... start speaking!")
    audio = record_with_vad()

    # Transcribe audio using Whisper
    st.info("🧠 Transcribing your speech with Whisper...")
    transcript, audio_path = transcribe_audio(audio)
    st.audio(audio_path, format="audio/wav")
    st.markdown("### 📝 Transcript:")
    st.write(transcript)

    # Get response from Groq LLM
    st.info("💬 Generating response from Groq LLM...")
    response = get_groq_response(transcript)
    st.markdown("### 🤖 AI Response:")
    st.success(response)

    # Convert response to speech using ElevenLabs
    st.info("🔊 Converting response to speech with ElevenLabs...")
    audio_file = text_to_speech_elabs(text=response)
    if audio_file:
        st.audio(audio_file, format="audio/mp3", autoplay=True)
    else:
        st.error("❌ Failed to generate TTS.")
