import asyncio
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from config.settings import settings
from src.core.orchestrator import BedtimeStoryOrchestrator


class TestBedtimeStoryOrchestrator(unittest.TestCase):
    """Unit tests for the BedtimeStoryOrchestrator class."""

    def setUp(self) -> None:
        """Sets up test fixtures before each test method."""
        self.orchestrator: BedtimeStoryOrchestrator = BedtimeStoryOrchestrator(
            child_name="Lele", 
            child_age=6, 
            duration_minutes=10, 
            mode="Voice"
        )

    def test_initialization(self) -> None:
        """Tests orchestrator attribute setup during initialization."""
        self.assertEqual(self.orchestrator.child_name, "Lele")
        self.assertEqual(self.orchestrator.child_age, 6)
        self.assertEqual(self.orchestrator.duration_minutes, 10)

    @patch('src.core.orchestrator.TTSSynthesizer.synthesize_speech_async')
    @patch('src.core.orchestrator.ImageGenerator.generate_illustrations_parallel')
    @patch('src.core.orchestrator.VoiceInputHandler.record_and_transcribe')
    def test_pipeline_execution_fallback(
        self, 
        mock_record: MagicMock, 
        mock_gen_images: MagicMock, 
        mock_tts: MagicMock
    ) -> None:
        """Tests that the pipeline returns fallback story details when the Gemini API is unconfigured."""
        mock_record.return_value = "A magical panda flying to outer space"
        mock_gen_images.return_value = [Path("mock_cover.png"), Path("mock_scene1.png"), Path("mock_scene2.png"), Path("mock_scene3.png")]
        mock_tts.return_value = Path("mock_audio.mp3")

        result: dict[str, Any] = asyncio.run(
            self.orchestrator.run_pipeline("A magical panda flying to outer space")
        )
        self.assertIn("story", result)
        self.assertIn("audio_paths", result)
        self.assertIn("image_paths", result)
        
        story = result["story"]
        self.assertEqual(story["metadata"]["target_age"], 6)
        self.assertEqual(story["metadata"]["target_duration_minutes"], 10)
        self.assertEqual(story["metadata"]["total_word_count"], 1400)

    @patch('src.core.orchestrator.TTSSynthesizer.synthesize_speech_async')
    @patch('src.core.orchestrator.ImageGenerator.generate_illustrations_parallel')
    @patch('src.core.orchestrator.VoiceInputHandler.record_and_transcribe')
    @patch('src.core.orchestrator.types')
    @patch('src.core.orchestrator.genai')
    def test_pipeline_execution_with_gemini_api(
        self, 
        mock_genai: MagicMock, 
        mock_types: MagicMock,
        mock_record: MagicMock,
        mock_gen_images: MagicMock,
        mock_tts: MagicMock
    ) -> None:
        """Tests pipeline orchestration logic when calling mock Gemini Client API."""
        mock_record.return_value = "A magical panda flying to outer space"
        mock_gen_images.return_value = [Path("mock_cover.png"), Path("mock_scene1.png"), Path("mock_scene2.png"), Path("mock_scene3.png")]
        mock_tts.return_value = Path("mock_audio.mp3")

        # Set up mock client response
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.text = '{"title": "Panda on the Moon", "metadata": {"target_age": 6, "target_duration_minutes": 10, "total_word_count": 1400}, "cover_art_prompt": "Cover Art", "episodes": [{"chapter": 1, "title": "Start", "narration_text": "Once upon a time...", "illustration_prompt": "Illustration"}]}'
        mock_client.models.generate_content.return_value = mock_response

        # Temporarily mock the settings API key to trigger the call
        with patch.object(settings, 'gemini_api_key', 'mock_key'):
            result: dict[str, Any] = asyncio.run(
                self.orchestrator.run_pipeline("Forest theme")
            )
            self.assertEqual(result["story"]["title"], "Panda on the Moon")

