import pyttsx3

engine = pyttsx3.init()
engine.setProperty('rate', 150)  # Speed

def speak(text):
    print("🔊 Speaking:", text)
    engine.say(text)
    engine.runAndWait()
