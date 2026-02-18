# Jarvis: AI Voice-Controlled Shopping Assistant 🤖🛍️

Jarvis is a powerful, voice-activated automation system designed to make online shopping effortless. Using the Google Gemini API for intent parsing and Playwright for browser automation, Jarvis can search for products, select items by voice, and complete the entire checkout process—including selecting Cash on Delivery (COD)—on Amazon.

---

## 🏁 Master Command Sequence (Setup to Finish)
If you have Python installed, run these in your terminal to get started immediately:

```bash
# Setup Folders
mkdir -p commerce_agents user_data Jarvis/final

# Create & Activate Virtual Environment
python3 -m venv venv
source venv/bin/activate  # macOS
# .\venv\Scripts\activate # Windows

# Install Everything
pip install -r requirements.txt
playwright install chromium

# Run Jarvis
# macOS:
python3 main.py
# Windows:
python main.py
```

---

## 🛡️ Security Note
Jarvis is designed for personal use and convenience. It automates browser interactions and handles sensitive information (like login credentials via browser profiles and potentially payment details if not using COD). Please ensure you understand the implications of using such a tool and only use it on trusted systems. The `user_data` folder stores your Amazon session; keep it secure.

---

## 🌟 Key Features
- **Full Automation**: Search, Select, Add to Cart, and Place Order (End-to-End).
- **Voice Controlled**: Natural language processing via Google Gemini.
- **Cross-Platform**: Optimized for both **macOS** and **Windows**.
- **Robust Checkout**: Handles intermediate screens like "Use this payment method" and "Pending Order" duplicates.
- **Persistent Login**: Uses browser profiles to keep you logged in to Amazon.
- **Smart Feedback**: Real-time voice updates (e.g., "Scrolling down", "Order placed").

---

## 📋 Prerequisites

### General
1. **Python 3.10 to 3.13** installed.
   - **Windows**: Use `winget install Python.Python.3.12` or visit [python.org](https://www.python.org/downloads/) to download the installer manually. *(IMPORTANT: Check "Add Python to PATH" during installation)*.
   - **macOS (Terminal)**: `brew install python@3.12`
2. **Google Gemini API Key**: Get one from [Google AI Studio](https://a studio.google.com/).
3. **Microphone Access**: Ensure your system mic is working and permissions are granted to your terminal/IDE.

### macOS Specific
- **Homebrew**: Needed for audio drivers.
- **PortAudio**: `brew install portaudio` (required for PyAudio).

### Windows Specific
- **Microsoft C++ Build Tools**: May be required if `PyAudio` doesn't install via wheels.
- **Siri/Samantha/Zira Voices**: JARVIS automatically attempts to use high-quality system voices.

---

## 🚀 Setup Instructions

### 0. Create Folder Structure (Optional)
If you are setting this up manually instead of cloning, run this to create all required folders:
```bash
mkdir -p commerce_agents user_data Jarvis/final
```

### 1. Clone & Prepare
```bash
# Clone the repository
git clone <your-repo-link>
cd Jarvis

# Create a virtual environment
python -m venv venv

# Activate Virtual Environment
# macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 2. Install Dependencies
```bash
# Install Python packages
pip install -r requirements.txt

# (Optional) Install Playwright browser drivers 
# Note: Jarvis is configured to use your installed Chrome browser.
# Only run this if you don't have Chrome or have errors.
# playwright install chromium
```

### 3. Audio Configuration (CRITICAL)
**For macOS Users:**
If you encounter `PyAudio` installation errors, run:
```bash
brew install portaudio
pip install --global-option='build_ext' --global-option='-I/usr/local/include' --global-option='-L/usr/local/lib' pyaudio
```

### 4. Environment Variables
Create a file named `.env` in the root directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here  # Optional Fallback 1
GROQ_API_KEY=your_groq_api_key_here      # Optional Fallback 2 (Recommended)
```

---

## 🔊 How to Use

1. **Start Jarvis:**
   ```bash
   python main.py
   ```
2. **First Run (Manual Login):**
   - JARVIS will open a browser window.
   - If it's your first time, manually log in to Amazon inside that window.
   - JARVIS will save your session in the `user_data` folder so you stay logged in for future runs.
3. **Voice Commands:**
   - **Navigate**: "Open Amazon" or "Go to Amazon".
   - **Search**: "Search for [product name]" or "Find [product]".
   - **Navigate Results**: "Scroll down", "Scroll up", or say "Yes" when asked to see more.
   - **Select Item**: 
     - "Select the first one" / "Option one".
     - "Select the product with name [full name]".
     - "Select the product with price [amount]".
     - "Open it".
   - **Cart & Checkout**:
     - "Add to cart".
     - "Proceed to checkout".
     - "Cash on Delivery" or "Use COD".
   - **Place Order**:
     - "Place order" -> Then say "Yes" or "Proceed" when Jarvis asks for final confirmation.
   - **Order Cancellation**:
     - "Cancel my order" -> Jarvis will ask for confirmation, then handle the site automation.
   - **System UI**: "Refresh page", "Go back", "Shut down".

---

## 🛠️ Troubleshooting

| Issue | Solution |
| :--- | :--- |
| **"Microphone not found"** | Unplug and replug your mic, or check Terminal/VSCode permissions in Privacy Settings. |
| **"429 Resource Exhausted"** | You've reached your Gemini API free tier limit. Wait 60 seconds and try again. |
| **"Could not find COD"** | JARVIS uses robust evaluate-clicks, but sometimes Amazon UI changes. Use "Refresh" to try again. |
| **"429 Gemini Limit"** | If Gemini fails, JARVIS automatically uses the **Helious Router** to failover to OpenAI. |
| **Windows TTS issues** | Ensure `pyttsx3` is installed. JARVIS will fallback to basic terminal output if TTS fails. |

---

## 🎓 Academic: Helious Router (3-Tier LLM Failover)
Jarvis implements a custom **3-Tier LLM Router** (internally referred to as the "Helious Router") to ensure 100% uptime.

### How to Demonstrate:
1. **Show the Code**: Open `brain.py` and show the `parse_intent` function. Point to the nested `try-except` blocks where:
   - **Tier 1**: Google Gemini (Primary)
   - **Tier 2**: OpenAI GPT-4o-mini (Secondary)
   - **Tier 3**: Groq Llama 3 (Tertiary - Final Safety Net)
2. **Trigger the Failover**:
   - Open your `.env` file.
   - Temporarily add a character to your `GEMINI_API_KEY` to make it invalid.
   - Run `python main.py` and issue a command (e.g., "Search for a high-end laptop").
   - **Observe the Terminal**: It will print: `DEBUG: Gemini Failure (...). Attempting OpenAI failover...`
   - Jarvis will still successfully process the logic using OpenAI, proving the failover mechanism works perfectly.

---

## 🗣️ A-Z Voice Command Script (The Shopping Journey)
Follow these commands in order for a successful automated purchase:

1. **Wake Up**: "Open Amazon"
2. **Find Product**: "Search for [Product Name]" (e.g., "Search for boat rockerz 255")
3. **Explore**: "Scroll down" or "Scroll up"
4. **Identify**: "Select the first one" OR "Select the one with price 998"
5. **Add**: "Add to cart"
6. **Checkout**: "Proceed to checkout"
7. **Payment**: "Cash on Delivery"
8. **Final Confirmation**: "Place order" -> Then say "Yes" when Jarvis asks for confirmation.
9. **Abort (Optional)**: "Cancel my order" -> Say "Yes" to confirm cancellation.

---
*Created by Jarvis Team. "Sir, I am standing by for your next command."*
