from gtts import gTTS
import uuid
import os

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def speak(text: str) -> str:
    ensure_dir("outputs/tts_audio")
    filename = f"outputs/tts_audio/{uuid.uuid4().hex}.mp3"
    tts = gTTS(text)
    tts.save(filename)
    print(f"✅ TTS saved at {filename}")
    return filename
