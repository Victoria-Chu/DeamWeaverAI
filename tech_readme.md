# System Architecture & Technical Specifications: Multimodal Bedtime Orchestrator

This repository hosts the source code for a local, edge-integrated **Multimodal Generative AI Story Engine** running on Windows 10. The system leverages state-of-the-art vision, language, and image generation models via the Google Gemini API, coupled with asynchronous Python workers, to construct structured, safe, and time-calibrated children's media on demand.

### 🏗️ High-Level System Architecture

```
                        [ USER INTERFACE (CustomTkinter / Streamlit Local) ]
                         (Inputs: Child's Name, Age, Duration, Mode)
                                          │
                  ┌───────────────────────┴──────────────────────┐
                  ▼                                              ▼
       [ Web-Cam Input via OpenCV ]                  [ Voice Input via PyAudio ]
                  │                                              │
                  ▼                                              ▼
       [ Gemini 2.5 Flash Vision ]                  [ Gemini Audio Transcription ]
                  └───────────────────────┬──────────────────────┘
                                          ▼
                         [ Multimodal Feature Vector ]
                                          │
                                          ▼
                      [ Structured Prompt Orchestrator ] 
                       (Inputs: {Name: "Lele"}, {Age: 6}, Duration)
                                          │
                                          ▼
                           [ Gemini 2.5 Flash LLM ] 
                          (Structured Output Engine)
                                          │
                ┌─────────────────────────┴────────────────────────┐
                ▼                                                  ▼
     [ Synthesized Story JSON ]                         [ 4 Image Prompts Generated ]
     (Dynamic pacing & word counts)                     (1 Cover + 3 Chronological Scenes)
                │                                                  │
                ▼                                                  ▼
     [ Edge-TTS Audio Engine ]                         [ Imagen API / Hugging Face ]
     (Speed-Calibrated Playback)                        (Parallel Image Generation)
                │                                                  │
                ▼                                                  ▼
      [ Streamed Audio Track ]                           [ 4 High-Res Story Slides ]
                │                                                  │
                └────────────────────────┬─────────────────────────┘
                                         ▼
                        [ INTERACTIVE DIGITAL STORYBOOK ]
                        (Syncs audio playback with visual slides)
```

---

### ⚙️ Engine Design & Key Technical Capabilities

#### 1. Dynamic Personalization & Voice/Vision Ingestion
*   **Named Entity Injection:** The pipeline accepts raw string inputs for the child's name (e.g., `{child_name: "Lele"}`), forcing the LLM to designate them as the primary protagonist while maintaining age-appropriate character behaviors.
*   **Vision:** Employs `opencv-python` to interface with the local camera, capturing a frame buffer which is optimized, compressed, and piped directly into the Gemini API to detect objects, colors, and characters using zero-shot image classification.
*   **Audio:** Captures raw audio streams using `PyAudio` and processes the waveform through Gemini's native voice transcription to extract unstructured text strings.

#### 2. Structured JSON Output & Pacing Calibration
To guarantee the story meets precise product specifications (age-appropriateness and pacing), we force Gemini to output a structured JSON schema:
*   **Pacing Calibration:** The engine maps the physical reading speed of our local Text-to-Speech (TTS) synthesizer (typically ~130 to 150 words per minute for a 6-year-old). A 10-minute target story dynamically constrains the API output to precisely $1,300 - 1,500$ words.
*   **System Prompt Guardrails:** System instructions explicitly define vocabulary complexity (e.g., Lexile framework equivalent for age 6), ban any stressful or hyper-active themes, and mandate comforting endings to encourage sleep.

#### 3. Parallel Image Generation & Audio Syncing
*   **The 4-Slide Storybook:** Instead of heavy, high-latency video rendering, the orchestrator requests **one high-level cover image** and **three major scene illustrations** (beginning, middle, and climax).
*   **Parallelization:** The application triggers 4 parallel, asynchronous image generation requests (via Imagen or Hugging Face Stable Diffusion) based on visual descriptions provided by the Gemini story output. This limits total generation wait time to less than 10 seconds.
*   **Playback Coordination:** The local Python UI displays the cover image during the introduction, and automatically transitions to Scene 1, 2, and 3 based on timestamps calculated from the audio playback progress of `edge-tts`.

---

### 🛠️ Technology Stack
*   **Orchestrator & Agent Management:** Built using Google **Antigravity IDE & SDK** (`google-antigravity`).
*   **AI Engine:** Google Gemini API (utilizing `gemini-2.5-flash` for hyper-fast latency and multimodal flexibility).
*   **Frameworks:** OpenCV-Python (Vision Input), PyAudio (Speech Input), Edge-TTS (Speech Output), Tkinter/Streamlit (Local UI).
*   **CI/CD Pipeline:** GitHub Actions (configured for automated testing, flake8 linting, and mock-integration safety checks).
