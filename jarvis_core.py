import sys
import subprocess
import pyttsx3
import speech_recognition as sr
import time
try:
    import pythoncom
except ImportError:
    pythoncom = None

def speak(text):
    """
    Pronounces the text using platform-specific methods.
    macOS: 'say' command (most reliable).
    Windows: pyttsx3 with SAPI5.
    """
    original_text = text
    # Clean text for smoother speech
    text = text.replace(",", "").replace("/-", "").replace("₹", " Rupees ").replace("Rs.", " Rupees ").strip()
    
    print(f"Jarvis: {original_text}")
    
    if not text:
        return

    try:
        if sys.platform == "darwin":
            # macOS: Use native 'say' command
            subprocess.run(["say", text])
        elif sys.platform == "win32":
            # Windows: High-reliability "Atomic" speech pattern
            # 1. Give the Microphone a moment to release the audio device
            time.sleep(0.3) 
            
            try:
                if pythoncom:
                    pythoncom.CoInitialize()
                
                win_engine = pyttsx3.init(driverName='sapi5')
                win_engine.setProperty('rate', 190)
                
                # Pick a natural sounding voice if available
                voices = win_engine.getProperty('voices')
                for v in voices:
                    if any(x in v.name.lower() for x in ["zira", "samantha", "siri", "hazel"]):
                        win_engine.setProperty('voice', v.id)
                        break
                
                win_engine.say(text)
                win_engine.runAndWait()
                
                # Explicit cleanup
                del win_engine
                if pythoncom:
                    pythoncom.CoUninitialize()
            except Exception as win_err:
                print(f"Windows TTS Error: {win_err}")
        else:
            # Linux/Others: Basic fallback
            try:
                fallback_engine = pyttsx3.init()
                fallback_engine.say(text)
                fallback_engine.runAndWait()
            except:
                print(f"DEBUG: TTS Fallback failed. Could not speak: {text}")

    except Exception as e:
        print(f"General TTS Error: {e}")

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
