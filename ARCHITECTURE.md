# System Architecture & Technical Specifications: Multimodal Bedtime Orchestrator

This repository hosts the source code for a local, edge-integrated **Multimodal Generative AI Story Engine** running on Windows 10. The system leverages state-of-the-art vision, language, and image generation models via the Google Gemini API, coupled with asynchronous Python workers, to construct structured, safe, and time-calibrated children's media on demand.

---

## 🏗️ High-Level System Architecture

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
      [ Streamed Audio Track ]                           [ 4 High-Res Story Story Slides ]
                │                                                  │
                └────────────────────────┬─────────────────────────┘
                                         ▼
                        [ INTERACTIVE DIGITAL STORYBOOK ]
                        (Syncs audio playback with visual slides)
```

---

## ⚙️ Engine Design & Key Technical Capabilities

### 1. Dynamic Personalization & Ingestion
*   **Named Entity Ingestion:** The pipeline accepts raw string inputs for the child's name (e.g., `{child_name: "Lele"}`), forcing the LLM to designate them as the primary protagonist while maintaining age-appropriate character behaviors.
*   **Multimodal Vision Input:** Employs `opencv-python` to interface with the local camera, capturing a frame buffer which is optimized, compressed, and piped directly into the Gemini API to detect objects, colors, and characters using zero-shot image classification.
*   **Voice Input Ingestion:** Captures raw audio streams using `PyAudio` and processes the waveform through Gemini's native voice transcription to extract unstructured text strings.

### 2. Gemini API Integration & JSON Schema
To guarantee the story meets precise product specifications (age-appropriateness and pacing), the orchestrator forces Gemini to output a structured JSON schema:
*   **Model:** `gemini-2.5-flash` (for vision, audio transcription, and structured text generation).
*   **Response Format:** Structured JSON Output.
*   **Target JSON Schema:**
```json
{
  "title": "String",
  "metadata": {
    "target_age": 6,
    "target_duration_minutes": 10,
    "total_word_count": 1400
  },
  "cover_art_prompt": "Detailed prompt for generating the cover slide.",
  "episodes": [
    {
      "chapter": 1,
      "title": "String",
      "narration_text": "String (~450 words)",
      "illustration_prompt": "Detailed visual prompt for generating the Scene 1 slide."
    },
    {
      "chapter": 2,
      "title": "String",
      "narration_text": "String (~450 words)",
      "illustration_prompt": "Detailed visual prompt for generating the Scene 2 slide."
    },
    {
      "chapter": 3,
      "title": "String",
      "narration_text": "String (~500 words)",
      "illustration_prompt": "Detailed visual prompt for generating the Scene 3 slide."
    }
  ]
}
```

### 3. Pacing Engine & Algorithmic Constraints
*   **Pacing Calibration:** The engine maps the physical reading speed of our local Text-to-Speech (TTS) synthesizer (assuming a child-friendly reading speed of **140 Words Per Minute (WPM)**).
    *   If duration is 10 minutes -> Target word count is exactly 1,400 words (~460 words per chapter).
    *   If duration is 15 minutes -> Target word count is exactly 2,100 words (~700 words per chapter).
*   **Safety/Guardrails:** Prompt templates append strict system instructions limiting vocabulary to an age-appropriate level, banning all scary themes/monsters/violence/loud noises, and enforcing a peaceful, sleep-inducing resolution.

### 4. Parallel Image Generation & Audio Syncing
*   **The 4-Slide Storybook:** Instead of heavy, high-latency video rendering, the orchestrator requests **one cover illustration** and **three major scene illustrations** (beginning, middle, and climax).
*   **Asynchronous Parallelism:** The application triggers parallel, asynchronous image generation requests (via Imagen 3 or Pollinations.ai fallback) using Python's `asyncio` or `concurrent.futures`. This ensures that the cover art and 3 scenes are generated concurrently, minimizing sequential API latency to under 10 seconds.
*   **Playback Coordination:** The local Python UI displays the cover image during the introduction, and automatically transitions to Scene 1, 2, and 3 based on timestamps calculated from the audio playback progress of `edge-tts` (using Pygame mixer).

---

## 🛠️ Local Libraries & Technology Stack
To maintain a high-performance, lightweight local profile, the application restricts itself to the following:
*   **GUI:** `customtkinter` (modern desktop UI) and `streamlit` (browser prototype).
*   **Vision:** `opencv-python` (webcam frame buffer capture).
*   **Audio Input:** `pyaudio` (microphone recording).
*   **Audio Output (TTS):** `edge-tts` (asynchronous, free, high-quality Microsoft Edge TTS engine).
*   **Image Generation:** `google-genai` (Imagen 3 API) or Pollinations.ai/Pillow fallbacks.
*   **Testing & CI/CD:** `pytest` (automated testing framework) and GitHub Actions (configured for automated testing and lint safety checks).
