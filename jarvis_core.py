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
    text = text.replace(",", "").replace("/-", "").replace("₹", " Rupees ").replace("Rs.", " Rupees ")
    
    print(f"Jarvis: {original_text}")
    try:
        if sys.platform == "darwin":
            # macOS native
            subprocess.run(["say", text])
        elif sys.platform == "win32":
            # Windows high-reliability "atomic" speech
            try:
                import pythoncom
                import pyttsx3
                pythoncom.CoInitialize()
                # Fresh engine per call prevents conflicts with the mic thread
                win_engine = pyttsx3.init(driverName='sapi5')
                win_engine.setProperty('rate', 185)
                
                # Selection of voice (prefer female/natural if found)
                voices = win_engine.getProperty('voices')
                for v in voices:
                    if any(x in v.name.lower() for x in ["zira", "samantha", "siri"]):
                        win_engine.setProperty('voice', v.id)
                        break
                
                win_engine.say(text)
                win_engine.runAndWait()
                # Properly destroy engine to release device
                del win_engine
            except Exception as win_err:
                print(f"Windows TTS Atomic Error: {win_err}")
        else:
            # Linux or others
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
