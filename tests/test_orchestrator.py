import asyncio
import unittest
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

    def test_pipeline_execution_fallback(self) -> None:
        """Tests that the pipeline returns fallback story details when the Gemini API is unconfigured."""
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

    @patch('src.core.orchestrator.types')
    @patch('src.core.orchestrator.genai')
    def test_pipeline_execution_with_gemini_api(self, mock_genai: MagicMock, mock_types: MagicMock) -> None:
        """Tests pipeline orchestration logic when calling mock Gemini Client API."""
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

