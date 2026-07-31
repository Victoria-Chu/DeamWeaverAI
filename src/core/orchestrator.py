import asyncio
import json
import logging
from pathlib import Path
from typing import Any

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from config.settings import settings
from src.core.prompts import BedtimeStorySchema, get_bedtime_prompt
from src.inputs.camera import CameraCapture
from src.inputs.voice import VoiceInputHandler
from src.outputs.audio import TTSSynthesizer
from src.outputs.image import ImageGenerator

logger = logging.getLogger(__name__)

class BedtimeStoryOrchestrator:
    """Orchestrates the entire Bedtime Storybook creation pipeline."""

    def __init__(self, child_name: str, child_age: int, duration_minutes: int, mode: str) -> None:
        """
        Initializes the orchestrator.

        Args:
            child_name: Name of the child reader.
            child_age: Age of the child.
            duration_minutes: Duration of the bedtime reading in minutes.
            mode: Mode of operation ("Voice" or "Image").
        """
        self.child_name: str = child_name
        self.child_age: int = child_age
        self.duration_minutes: int = duration_minutes
        self.mode: str = mode  # "Voice" or "Image"
        self.camera: CameraCapture = CameraCapture()
        self.voice_handler: VoiceInputHandler = VoiceInputHandler()
        self.tts: TTSSynthesizer = TTSSynthesizer(wpm_speed=settings.default_wpm_speed)
        self.image_gen: ImageGenerator = ImageGenerator()

    async def run_pipeline(
        self, 
        user_prompt: str, 
        enable_audio: bool = True, 
        enable_images: bool = True,
        pre_captured_transcript: str | None = None, 
        pre_captured_image_bytes: bytes | None = None
    ) -> dict[str, Any]:
        """
        Coordinates the bedtime storytelling pipeline:
        1. Capture inputs based on the selected mode (OpenCV camera bytes vs voice transcription).
        2. Construct system prompt using child configurations.
        3. Call Gemini to generate structured output story JSON.
        4. Trigger async synthesizers and generators (Edge-TTS, Imagen).

        Args:
            user_prompt: Base prompt/theme string from user.
            enable_audio: Whether to synthesize TTS audio narration.
            enable_images: Whether to generate scene illustrations.
            pre_captured_transcript: Prefetched voice transcript if already recorded.
            pre_captured_image_bytes: Prefetched camera JPEG bytes if already captured.

        Returns:
            A dictionary containing the structured story, audio path list, and image path list.
        """
        logger.info(f"Initiating Bedtime Story Orchestration for {self.child_name} (Age {self.child_age}). Target: {self.duration_minutes} mins.")
        
        # 1. Inputs Acquisition
        context_spark: str = ""
        image_bytes: bytes | None = None
        if self.mode == "Image":
            if pre_captured_image_bytes:
                image_bytes = pre_captured_image_bytes
                context_spark = " [Vision Input: Stuffed animal/toy in captured image] "
            else:
                success, jpeg_bytes = self.camera.capture_jpeg_bytes()
                if success and jpeg_bytes:
                    image_bytes = jpeg_bytes
                    context_spark = " [Vision Input: Stuffed animal/toy in captured image] "
                else:
                    logger.warning("Webcam capture failed or returned no bytes. Continuing without vision.")
        else:
            if pre_captured_transcript:
                voice_transcript: str = pre_captured_transcript
            else:
                voice_transcript = self.voice_handler.record_and_transcribe()
            context_spark = f" [Voice Input Spark: {voice_transcript}] "

        combined_topic: str = f"{user_prompt} {context_spark}"

        # 2. System Prompts setup
        system_prompt: str = get_bedtime_prompt(
            self.child_name, 
            self.child_age, 
            self.duration_minutes, 
            combined_topic
        )

        # 3. Call Gemini API
        story_json: dict[str, Any] | None = None
        client: genai.Client | None = None

        if genai is not None and types is not None and settings.gemini_api_key:
            try:
                client = genai.Client(api_key=settings.gemini_api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini Client: {e}")

        if client and types is not None:
            try:
                contents: list[Any] = []
                if image_bytes:
                    contents.append(types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg'))
                contents.append(system_prompt)

                logger.info(f"Calling {settings.gemini_model_name} for structured bedtime story...")
                response = client.models.generate_content(
                    model=settings.gemini_model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=BedtimeStorySchema,
                        temperature=0.7,
                    )
                )
                
                story_json = json.loads(response.text)
                logger.info("Successfully received structured story from Gemini API.")
            except Exception as e:
                logger.error(f"Error calling Gemini API: {e}. Falling back to default story.")

        # Fallback to mock JSON if API fails or client not configured
        if not story_json:
            word_count: int = self.duration_minutes * settings.default_wpm_speed
            chapter_words: int = int(word_count / 3)
            
            story_json = {
                "title": f"{self.child_name}'s Magical Moon Dream",
                "metadata": {
                    "target_age": self.child_age,
                    "target_duration_minutes": self.duration_minutes,
                    "total_word_count": word_count
                },
                "cover_art_prompt": "A beautiful child dreaming of flying a soft paper airplane to the silver moon.",
                "episodes": [
                    {
                        "chapter": 1,
                        "title": "A Spark in the Night",
                        "narration_text": f"Chapter 1 narration content... Once upon a time, {self.child_name} sat by the window. A glowing silver paper airplane floated in Lele's cozy room. (~{chapter_words} words)",
                        "illustration_prompt": "A glowing silver paper airplane floating in Lele's cozy room."
                    },
                    {
                        "chapter": 2,
                        "title": "Rising to the Moon",
                        "narration_text": f"Chapter 2 narration content... {self.child_name} flew higher and higher into the soft night sky. Lele and a fluffy panda sat on a floating cloud looking at stars. (~{chapter_words} words)",
                        "illustration_prompt": "Lele and a fluffy panda sitting on a floating cloud looking at stars."
                    },
                    {
                        "chapter": 3,
                        "title": "Cozy Bedsides",
                        "narration_text": f"Chapter 3 narration content... The adventure ended as the soft night wind sang a lullaby. Lele slept peacefully in a warm bed with glowing lanterns surrounding. (~{chapter_words} words)",
                        "illustration_prompt": "Sleeping peacefully in a warm bed with glowing lanterns surrounding."
                    }
                ]
            }

        # 4. Asynchronous Output Synthesizers
        audio_task: asyncio.Task[Path] | None = None
        images_task: asyncio.Task[list[Path]] | None = None
        
        audio_paths: list[Path] = []
        image_paths: list[Path] = []

        if enable_audio:
            # Combine narration text to generate audio narration track
            full_narrative: str = " ".join([ep["narration_text"] for ep in story_json["episodes"]])
            audio_task = asyncio.create_task(self.tts.synthesize_speech_async(full_narrative, "narration.mp3"))

        if enable_images:
            image_prompts: list[str] = [story_json["cover_art_prompt"]] + [ep["illustration_prompt"] for ep in story_json["episodes"]]
            images_task = asyncio.create_task(self.image_gen.generate_illustrations_parallel(image_prompts))

        if audio_task and images_task:
            audio_path, image_paths = await asyncio.gather(audio_task, images_task)
            audio_paths = [audio_path]
        elif audio_task:
            audio_path = await audio_task
            audio_paths = [audio_path]
        elif images_task:
            image_paths = await images_task

        return {
            "story": story_json,
            "audio_paths": audio_paths,
            "image_paths": image_paths
        }

