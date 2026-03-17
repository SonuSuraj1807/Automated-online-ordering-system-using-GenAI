# Windows Audio & TTS Troubleshooting Script

import sys
import os

def test_tts():
    print("--- Testing pyttsx3 (Speaking) ---")
    try:
        import pyttsx3
        print("pyttsx3 is installed.")
        
        # Try initializing with sapi5
        try:
            print("Attempting to initialize with 'sapi5' (Windows native)...")
            import pythoncom
            pythoncom.CoInitialize()
            engine = pyttsx3.init(driverName='sapi5')
            print("sapi5 initialized successfully.")
        except Exception as e:
            print(f"sapi5 initialization failed: {e}")
            print("Attempting default initialization...")
            engine = pyttsx3.init()
            print("Default initialization successful.")

        voices = engine.getProperty('voices')
        print(f"Available voices: {len(voices)}")
        for i, voice in enumerate(voices):
            print(f"  {i}: {voice.name}")

        text = "Hello! This is a test of the Jarvis Windows Text to Speech system."
        print(f"Attempting to speak: '{text}'")
        engine.say(text)
        engine.runAndWait()
        print("Speak command completed (did you hear anything?)")
        
    except ImportError:
        print("ERROR: pyttsx3 is NOT installed. Run 'pip install pyttsx3'")
    except Exception as e:
        print(f"TTS ERROR: {e}")

def test_mic():
    print("\n--- Testing SpeechRecognition (Listening) ---")
    try:
        import speech_recognition as sr
        print(f"SpeechRecognition version: {sr.__version__}")
        
        print("Available Microphones:")
        for i, mic in enumerate(sr.Microphone.list_microphone_names()):
            print(f"  {i}: {mic}")
            
    except ImportError:
        print("ERROR: SpeechRecognition is NOT installed. Run 'pip install SpeechRecognition'")
    except Exception as e:
        print(f"Mic Test Error: {e}")
        if "PyAudio" in str(e):
            print("PyAudio missing! On Windows, install using 'pip install pyaudio'")

if __name__ == "__main__":
    print(f"Platform: {sys.platform}")
    test_tts()
    test_mic()
    print("\nIf you are on Windows and speaking is silent, make sure 'pypiwin32' is installed: pip install pypiwin32")
