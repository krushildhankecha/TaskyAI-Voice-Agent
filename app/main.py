from core.stt import transcribe_audio
from core.tts import speak
from core.llm import get_ai_response
from core.action_handler import perform_action

def main():
    print("🎤 Listening for command...")
    text = transcribe_audio("/Users/krushildhankecha/Desktop/Projects/TaskyAI-Voice-Agent/app/data/tell_me_some.mp3")  # Replace with microphone or audio input
    print(f"📝 You said: {text}")
    
    if not text:
        speak("Sorry, I didn't catch that.")
        return

    action = get_ai_response(text)
    print(f"🤖 Interpreted as: {action}")
    
    result = perform_action(action)
    speak(result)

if __name__ == "__main__":
    main()