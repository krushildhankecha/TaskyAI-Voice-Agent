import whisper
import torch

model = whisper.load_model("base", device="cuda" if torch.cuda.is_available() else "cpu")

def transcribe_audio(audio_path):
    try:
        result = model.transcribe(audio_path)
        return result["text"]
    except Exception as e:
        print("STT Error:", e)
        return None
