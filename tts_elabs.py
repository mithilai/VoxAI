# import os
# from elevenlabs import ElevenLabs
# from dotenv import load_dotenv

# load_dotenv()

# api_key = os.getenv("ELEVEN_LABS_API_KEY")
# if not api_key:
#     raise ValueError("ELEVEN_LABS_API_KEY not found in environment!")

# client = ElevenLabs(api_key=api_key)

# def text_to_speech_elabs(text: str, voice_name: str = "CwhRBWXzGAHq8TQ4Fs17") -> str:
#     """
#     Generate speech from text using ElevenLabs TTS and save to ./temp folder.
#     Returns the path to the saved audio file.
#     """
#     try:
#         # Collect audio chunks
#         audio_chunks = []
#         for chunk in client.text_to_speech.convert(
#             text=text,
#             voice_id=voice_name,
#             model_id="eleven_multilingual_v2"
#         ):
#             audio_chunks.append(chunk)

#         audio_bytes = b''.join(audio_chunks)

#         # Create a temp folder inside the project if it doesn't exist
#         current_directory = os.path.dirname(os.path.abspath(__file__))
#         temp_folder = os.path.join(current_directory, "temp")
#         os.makedirs(temp_folder, exist_ok=True)

#         # Save the audio file in the temp folder
#         output_path = os.path.join(temp_folder, "output.mp3")
#         with open(output_path, "wb") as f:
#             f.write(audio_bytes)

#         return output_path

#     except Exception as e:
#         print("❌ Error in ElevenLabs TTS:", e)
#         return ""



# # Example usage
# # text_to_speak = "Hello world! This is a demonstration of ElevenLabs with LangChain."
# # audio_file = text_to_speech_elabs(text_to_speak)
# # print(f"Audio saved to: {audio_file}")

import os
import time
import uuid
from elevenlabs import ElevenLabs
from dotenv import load_dotenv
import pygame  # For audio playback

load_dotenv()

api_key = os.getenv("ELEVEN_LABS_API_KEY")
if not api_key:
    raise ValueError("ELEVEN_LABS_API_KEY not found in environment!")

client = ElevenLabs(api_key=api_key)

def text_to_speech_elabs(text: str, voice_name: str = "CwhRBWXzGAHq8TQ4Fs17") -> None:
    """
    Generate speech from text using ElevenLabs TTS, play it silently (no UI), 
    then delete the file after use.
    """
    try:
        # Collect audio chunks
        audio_chunks = []
        for chunk in client.text_to_speech.convert(
            text=text,
            voice_id=voice_name,
            model_id="eleven_multilingual_v2"
        ):
            audio_chunks.append(chunk)

        audio_bytes = b"".join(audio_chunks)

        # Create temp folder if needed
        current_directory = os.path.dirname(os.path.abspath(__file__))
        temp_folder = os.path.join(current_directory, "temp")
        os.makedirs(temp_folder, exist_ok=True)

        # Unique filename for every audio
        unique_filename = f"output_{uuid.uuid4().hex}.mp3"
        output_path = os.path.join(temp_folder, unique_filename)

        # Write audio
        with open(output_path, "wb") as f:
            f.write(audio_bytes)

        # Initialize pygame mixer
        pygame.mixer.init()
        pygame.mixer.music.load(output_path)
        pygame.mixer.music.play()

        # Wait for playback to finish
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

        # Cleanup
        pygame.mixer.music.stop()
        pygame.mixer.quit()

        if os.path.exists(output_path):
            os.remove(output_path)

    except Exception as e:
        print("❌ Error in ElevenLabs TTS:", e)
