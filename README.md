# Jarvis: AI-Powered Amazon Automation 🤖🛒

Jarvis is a voice-controlled AI assistant that automates the entire shopping experience on Amazon India. By combining the **Gemini 2.5 Flash** model with **Playwright**, Jarvis can search for products, navigate results, and handle the checkout process through simple voice commands.

## ✨ Features
* **Voice Control**: Fully hands-free interaction using speech-to-text.
* **Persistent Sessions**: Stays logged into your Amazon account using a local `user_data` vault.
* **Intelligent Search**: Uses LLM-based intent classification to distinguish between conversational chat and shopping tasks.
* **Smart Navigation**: Automated scrolling, product selection, and multi-tab tracking.
* **Checkout Automation**: Direct navigation to the checkout terminal for final verification.

## 🛠️ Tech Stack
* **Language**: Python 3.10+
* **Automation**: Playwright (Chromium/Chrome)
* **Brain**: Google Gemini 2.5 Flash API
* **Voice Engine**: `jarvis_core` (Custom STT/TTS module)

## 🚀 Getting Started

### Prerequisites
* Google Chrome installed.
* A Gemini API Key from Google AI Studio.

### Installation
1. **Clone the repository**
   git clone (https://github.com/SonuSuraj1807/Automated-online-ordering-system-using-GenAI.git)
   cd Automated-online-ordering-system-using-GenAI

# 2. Set up Virtual Environment
# Windows
python -m venv venv
venv\Scripts\activate
Install Dependencies

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
Install Dependencies

# 3. Install Dependencies
pip install google-genai playwright jarvis_core

playwright install chromium

# 4.Set Environment Variable
# Windows
set GEMINI_API_KEY="your_actual_key_here"

# Mac/Linux
export GEMINI_API_KEY="your_actual_key_here"

# 🎙️ Usage
Run the main script:
python main.py

Voice Commands
"Jarvis, search for a MacBook Pro."

"Scroll down."

"Select the first one."

"Add this to my cart."

"Proceed to checkout."

"Shutdown system."

📁 Project Structure
├── main.py              # Main automation engine
├── jarvis_core.py       # Speech-to-Text & Text-to-Speech logic
├── user_data/           # Saved browser session (Login data)
└── requirements.txt     # Project dependencies

📦 requirements.txt
google-genai==1.56.0
playwright==1.57.0
SpeechRecognition==3.14.5
pyttsx3==2.99
PyAudio==0.2.14
pydantic==2.12.5
httpx==0.28.1

📝 License
This project is for educational purposes only.

mermaid Diagrams
graph TD;
    User((User Voice)) -->|STT| Jarvis[Jarvis Core];
    Jarvis -->|Intent| Gemini{Gemini 2.5};
    Gemini -->|Search/Cmd| Browser[Playwright/Chrome];
    Browser -->|Result| Jarvis;
    Jarvis -->|TTS| User;

    
