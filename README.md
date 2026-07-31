# DreamWeaver AI 🪄

> **Turning children’s toys, names, and imagination into personalized, interactive bedtime adventures.**

DreamWeaver AI is a local Windows application that captures multimodal inputs (webcam image + microphone speech), processes them using the Google Gemini API, and outputs a personalized, time-calibrated audio storybook (1 cover image, 3 scene illustrations, and TTS audio narration) for children.

For details on the product design, see [nontech_readme.md](file:///d:/gitfolder/DreamWeaverAI/nontech_readme.md). For details on the architecture, see [tech_readme.md](file:///d:/gitfolder/DreamWeaverAI/tech_readme.md).

---

## 🚀 Step-by-Step Environment Setup & Replication

Follow these instructions to recreate the environment and run the code on a clean, secondary machine.

### 📋 Prerequisites
- **Python 3.12** (Make sure Python is added to your system PATH)
- **Windows 10/11** (Optimized for Windows desktop environments)
- **Git** (For cloning the repository)

### 1. Clone the Repository
```powershell
git clone <repository_url> DreamWeaverAI
cd DreamWeaverAI
```

### 2. Set Up Python Virtual Environment
Initialize a fresh isolated virtual environment named `.venv`:
```powershell
python -m venv .venv
```

Activate the virtual environment:
- **PowerShell / Command Prompt (Windows):**
  ```powershell
  .venv\Scripts\activate
  ```
- **Bash / Linux / macOS (Fallback):**
  ```bash
  source .venv/bin/activate
  ```

### 3. Install Dependencies
Ensure pip is updated and install the required libraries:
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

*Note: PyAudio may require building tools on some platforms if a wheel is not available. Ensure you have the Microsoft C++ Build Tools installed if you encounter errors compiling PyAudio.*

### 4. Configure Environment Variables
Copy the template `.env.example` to `.env`:
```powershell
copy .env.example .env
```
Open `.env` and fill in your Google Gemini API key:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### 5. Running the Application

You can launch either the CustomTkinter Desktop Application or the Streamlit web browser prototype:

- **Desktop Application (CustomTkinter):**
  ```powershell
  python src/app_gui.py
  ```
- **Streamlit Prototype (Web Browser UI):**
  ```powershell
  streamlit run src/app.py
  ```

### 6. Running Tests
You can run automated tests to verify the core orchestrator and inputs logic:
```powershell
python -m pytest
```
