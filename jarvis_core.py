import os
import subprocess
import speech_recognition as sr

def speak(text):
    """Prints text and speaks it using the Mac 'say' command, waiting for it to finish."""
    print(f"Jarvis: {text}")
    try:
        # Blocks execution until the speech is complete
        subprocess.run(["say", text], check=True)
    except Exception as e:
        print(f"Speech Error: {e}")

def listen():
    """Listens for audio and converts it to text."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.pause_threshold = 1
        audio = r.listen(source)
    try:
        print("Recognizing...")
        query = r.recognize_google(audio, language="en-in")
        return query
    except Exception:
        return "none"