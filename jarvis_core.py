import subprocess
import speech_recognition as sr
import sys
import pyttsx3

# Global engine variable
engine = None

def get_engine():
    global engine
    if engine is None:
        try:
            if sys.platform == "win32":
                # Ensure COM is initialized for this thread
                import pythoncom
                pythoncom.CoInitialize()
                engine = pyttsx3.init(driverName='sapi5')
            else:
                engine = pyttsx3.init()
            
            # Basic configuration
            voices = engine.getProperty('voices')
            for voice in voices:
                name = voice.name.lower()
                if "samantha" in name or "zira" in name or "siri" in name:
                    engine.setProperty('voice', voice.id)
                    break
            engine.setProperty('rate', 185)
        except Exception as e:
            print(f"Warning: TTS initialization failed: {e}")
            try:
                engine = pyttsx3.init()
            except:
                engine = None
    return engine

def speak(text):
    """
    Pronounces the text using platform-specific methods.
    macOS: 'say' command (most reliable).
    Windows/Linux: pyttsx3.
    """
    # Sanitization for cleaner speech
    original_text = text
    # 1. Handle commas in numbers (e.g., 1,000 -> 1000)
    text = text.replace(",", "")
    # 2. Handle Indian currency suffixes (e.g., 500/- -> 500)
    text = text.replace("/-", "")
    # 3. Handle currency symbols specifically for speech
    text = text.replace("₹", " Rupees ")
    text = text.replace("Rs.", " Rupees ")
    
    print(f"Jarvis: {original_text}")
    try:
        if sys.platform == "darwin":
            # macOS native
            subprocess.run(["say", text])
        else:
            # Windows/Linux
            current_engine = get_engine()
            if current_engine:
                current_engine.say(text)
                current_engine.runAndWait()
            else:
                print(f"DEBUG: TTS Engine is None. Cannot speak: {text}")
    except Exception as e:
        print(f"TTS Error: {e}")
        # Fallback attempt on mac if say failed?
        if sys.platform == "darwin" and engine:
             try:
                engine.say(text)
                engine.runAndWait()
             except: pass

def listen(timeout=5, phrase_time_limit=10):
    """
    Listens for audio input and returns the recognized text.
    """
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        # r.adjust_for_ambient_noise(source, duration=0.5) 
        try:
            audio = r.listen(source, timeout=10, phrase_time_limit=20)
            print("Recognizing...")
            command = r.recognize_google(audio)
            print(f"User: {command}")
            return command.lower()
        except sr.WaitTimeoutError:
            return "none"
        except sr.UnknownValueError:
            return "none"
        except sr.RequestError:
            print("Network error with speech recognition service")
            return "none"
        except Exception as e:
            print(f"Mic Error: {e}")
            return "none"
