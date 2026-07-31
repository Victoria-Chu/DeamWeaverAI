# System Context: Project DreamWeaver AI

## Project Objective
Build a local Windows 10 desktop application that captures multimodal inputs (webcam image + microphone speech), processes them using the Google Gemini API, and outputs a personalized, time-calibrated audio storybook (1 cover image, 3 scene illustrations, and TTS audio) for children.

## Key Technical Specifications

### 1. Gemini API Integration
*   **Model:** `gemini-2.5-flash` (for vision, audio transcription, and structured text generation).
*   **Mode:** Structured JSON Output.
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

### 2. Local Libraries & Packages
To maintain a high-performance, lightweight local profile, the Antigravity IDE must restrict itself to the following libraries:
*   **GUI:** `customtkinter` (modern desktop UI) or `streamlit` (run locally).
*   **Vision:** `opencv-python` (webcam frame buffer capture).
*   **Audio Input:** `pyaudio` or `speech_recognition`.
*   **Audio Output (TTS):** `edge-tts` (asynchronous, free, high-quality Microsoft Edge TTS engine).
*   **Image Generation:** `google-genai` (Imagen 3 API) or Hugging Face serverless inference.

### 3. Key Algorithmic Constraints (To Code)
*   **Pacing Engine:** Assume a target child-friendly reading speed of **140 Words Per Minute (WPM)**. 
    *   If duration is 10 minutes -> Target word count is exactly 1,400 words.
    *   If duration is 15 minutes -> Target word count is exactly 2,100 words.
*   **Asynchronous Parallelism:** Image generation for the cover art and 3 scenes must run in parallel using Python's `asyncio` or `concurrent.futures` to ensure the user does not wait for sequential API calls.
*   **Safety/Guardrails:** Prompt templates must append strict system instructions limiting vocabulary, banning violence/monsters/loud noises, and enforcing a peaceful, sleep-inducing resolution.
