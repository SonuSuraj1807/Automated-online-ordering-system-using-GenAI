<div align="center">

# 🏛️ Jarvis: Automated Shopping Assistant

**The Next-Gen Voice-Controlled E-Commerce Automation System**

[Faculty + HOD Approved]

---

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google%20Gemini-8E75B2?style=for-the-badge&logo=google-gemini&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)

---

</div>

## 🌟 Overview

**Jarvis** is a state-of-the-art voice-activated automation system designed to digitize and streamline the online shopping process. No more manual searching or clicking—everything is voice-driven, instant, and transparent.

> "Efficiency meets Intelligence."

---

## 📁 Project Structure

```text
Jarvis/
├── commerce_agents/      # Specialized shopping logic
├── docs/reports/         # Generated project reports & documentation
├── notes/                # Training datasets & voice command lists
├── jarvis_core.py        # Speech (STT/TTS) & System controls
├── brain.py              # 3-Tier LLM Failover Logic (Helious Router)
├── main.py               # Main State Machine & User Loop
├── browser_manager.py    # Playwright session handler
├── requirements.txt      # Project dependencies
├── venv/                 # Virtual Environment
└── .env                  # Secure API Credentials
```

---

## 🚀 Setup Instructions

### 1. Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Configure API Keys
Create a `.env` file and add your keys:
```env
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
```

---

## 🔊 How to Use

1. **Wake Up**: `python3 main.py`
2. **Find Product**: "Search for high-end headphones"
3. **Explore**: "Scroll down" or "Select the first one"
4. **Action**: "Add to cart" -> "Proceed to checkout"
5. **Finalize**: "Use Cash on Delivery" -> "Place Order"

---

<div align="center">

### Made with ❤️ for the Future of Automation

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>
