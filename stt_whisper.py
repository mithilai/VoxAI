# import sounddevice as sd
# import numpy as np
# import webrtcvad
# import wavio
# import whisper
# import os
# import collections
# import time
# from datetime import datetime

# # Load Whisper model once
# model = whisper.load_model("base")
# sample_rate = 16000
# frame_duration = 30  # ms per audio chunk
# frame_size = int(sample_rate * frame_duration / 1000)
# vad = webrtcvad.Vad(2)

# # Ensure temp folder exists
# TEMP_DIR = os.path.join(os.getcwd(), "temp")
# os.makedirs(TEMP_DIR, exist_ok=True)

# def record_with_vad(max_duration=10, silence_timeout=1.0):
#     """
#     Record audio from microphone until silence is detected or max_duration is reached.
#     Returns numpy array of audio.
#     """
#     buffer = collections.deque(maxlen=int(silence_timeout * 1000 / frame_duration))
#     audio_frames = []
#     start_time = time.time()
#     silence_start = None

#     with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16') as stream:
#         while True:
#             frame, _ = stream.read(frame_size)
#             frame_bytes = frame.tobytes()
#             is_speech = vad.is_speech(frame_bytes, sample_rate)
#             audio_frames.append(frame)
#             buffer.append(is_speech)

#             if not any(buffer):
#                 if silence_start is None:
#                     silence_start = time.time()
#                 elif time.time() - silence_start > silence_timeout:
#                     break
#             else:
#                 silence_start = None

#             if time.time() - start_time > max_duration:
#                 break

#     return np.concatenate(audio_frames, axis=0)

# def transcribe_audio(audio: np.ndarray):
#     """
#     Save numpy audio to project temp/ folder with unique filename and transcribe with Whisper.
#     Returns the transcript and path to saved WAV file.
#     """
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
#     audio_path = os.path.join(TEMP_DIR, f"recording_{timestamp}.wav")
    
#     wavio.write(audio_path, audio, sample_rate, sampwidth=2)
#     result = model.transcribe(audio_path)
#     return result["text"], audio_path

# import sounddevice as sd
# import numpy as np
# import webrtcvad
# import wavio
# import whisper
# import os
# import collections
# import time

# # Load Whisper model once
# model = whisper.load_model("base")
# sample_rate = 16000
# frame_duration = 30  # ms per audio chunk
# frame_size = int(sample_rate * frame_duration / 1000)
# vad = webrtcvad.Vad(2)

# # Ensure temp folder exists
# TEMP_DIR = os.path.join(os.getcwd(), "temp")
# os.makedirs(TEMP_DIR, exist_ok=True)

# # Fixed filename (will overwrite each time)
# AUDIO_FILENAME = os.path.join(TEMP_DIR, "recording.wav")

# def record_with_vad(max_duration=10, silence_timeout=1.0):
#     """
#     Record audio from microphone until silence is detected or max_duration is reached.
#     Returns numpy array of audio.
#     """
#     buffer = collections.deque(maxlen=int(silence_timeout * 1000 / frame_duration))
#     audio_frames = []
#     start_time = time.time()
#     silence_start = None

#     with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16') as stream:
#         while True:
#             frame, _ = stream.read(frame_size)
#             frame_bytes = frame.tobytes()
#             is_speech = vad.is_speech(frame_bytes, sample_rate)
#             audio_frames.append(frame)
#             buffer.append(is_speech)

#             if not any(buffer):
#                 if silence_start is None:
#                     silence_start = time.time()
#                 elif time.time() - silence_start > silence_timeout:
#                     break
#             else:
#                 silence_start = None

#             if time.time() - start_time > max_duration:
#                 break

#     return np.concatenate(audio_frames, axis=0)

# def transcribe_audio(audio: np.ndarray):
#     """
#     Save numpy audio to fixed filename (overwrites each time) and transcribe with Whisper.
#     Returns the transcript and path to saved WAV file.
#     """
#     # Always overwrite the same file
#     audio_path = AUDIO_FILENAME
#     wavio.write(audio_path, audio, sample_rate, sampwidth=2)
#     result = model.transcribe(audio_path)
#     return result["text"], audio_path

# Example usage
# if __name__ == "__main__":
#     print("Recording... Speak now!")
#     audio_data = record_with_vad(max_duration=10, silence_timeout=1.0)
#     transcript, path = transcribe_audio(audio_data)
#     print(f"Saved audio to: {path}")
#     print("Transcript:", transcript)


import sounddevice as sd
import numpy as np
import webrtcvad
import wavio
import whisper
import os
import collections
import time
import traceback
import uuid

# ----------------- Config -----------------
model = whisper.load_model("base")  # Load once globally
sample_rate = 16000
frame_duration = 30  # ms
frame_size = int(sample_rate * frame_duration / 1000)
vad = webrtcvad.Vad(2)

# Temp directory
TEMP_DIR = os.path.join(os.getcwd(), "temp")
os.makedirs(TEMP_DIR, exist_ok=True)
AUDIO_FILENAME = os.path.join(TEMP_DIR, "recording.wav")

# ----------------- Recording -----------------
def record_with_vad(max_duration=10, silence_timeout=1.0):
    """
    Record audio from microphone until silence is detected or max_duration reached.
    Returns numpy array of audio samples.
    """
    buffer = collections.deque(maxlen=int(silence_timeout * 1000 / frame_duration))
    audio_frames = []
    start_time = time.time()
    silence_start = None

    with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16') as stream:
        while True:
            frame, _ = stream.read(frame_size)
            frame_bytes = frame.tobytes()
            is_speech = vad.is_speech(frame_bytes, sample_rate)
            audio_frames.append(frame)
            buffer.append(is_speech)

            # Stop after silence
            if not any(buffer):
                if silence_start is None:
                    silence_start = time.time()
                elif time.time() - silence_start > silence_timeout:
                    break
            else:
                silence_start = None

            # Stop after max duration
            if time.time() - start_time > max_duration:
                break

    return np.concatenate(audio_frames, axis=0)

# ----------------- Transcription -----------------
# def transcribe_audio(audio: np.ndarray):
#     """
#     Save numpy audio to temp WAV, transcribe with Whisper, return (transcript, path).
#     Automatically deletes file after use.
#     """
#     audio_path = AUDIO_FILENAME
#     transcript = ""

#     try:
#         # Ensure correct dtype for WAV
#         if not np.issubdtype(audio.dtype, np.integer):
#             audio = np.int16(audio / np.max(np.abs(audio)) * 32767)

#         # Save audio temporarily
#         wavio.write(audio_path, audio, sample_rate, sampwidth=2)

#         # Transcribe using Whisper
#         result = model.transcribe(audio_path)
#         transcript = result.get("text", "").strip()

#     except Exception as e:
#         print(f"❌ Error in Whisper transcription: {e}")
#         traceback.print_exc()

#     finally:
#         # Cleanup after use
#         if os.path.exists(audio_path):
#             try:
#                 os.remove(audio_path)
#             except Exception as cleanup_error:
#                 print(f"⚠️ Failed to delete temp file: {cleanup_error}")

#     return transcript, audio_path

# inside stt_whisper.py

def transcribe_audio(audio=None, file_path=None):
    """
    Transcribe audio.
    Provide either:
    - audio: NumPy array
    - file_path: path to wav file
    Returns: (transcript, path)
    """
    import wavio
    transcript = ""
    
    if file_path is not None:
        path_to_use = file_path
    elif audio is not None:
        TEMP_DIR = os.path.join(os.getcwd(), "temp")
        os.makedirs(TEMP_DIR, exist_ok=True)
        path_to_use = os.path.join(TEMP_DIR, f"{uuid.uuid4().hex}.wav")
        if not np.issubdtype(audio.dtype, np.integer):
            audio = np.int16(audio / np.max(np.abs(audio)) * 32767)
        wavio.write(path_to_use, audio, 16000, sampwidth=2)
    else:
        raise ValueError("Provide either audio array or file_path")

    try:
        from whisper import load_model
        model = load_model("base")
        result = model.transcribe(path_to_use)
        transcript = result.get("text", "").strip()
    except Exception as e:
        print(f"❌ Whisper transcription error: {e}")
    return transcript, path_to_use
