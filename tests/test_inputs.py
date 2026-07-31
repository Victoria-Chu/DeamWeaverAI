import unittest
from unittest.mock import MagicMock, patch

from src.inputs.camera import CameraCapture
from src.inputs.voice import VoiceInputHandler


class TestInputs(unittest.TestCase):
    """Unit tests for CameraCapture and VoiceInputHandler inputs."""

    @patch('src.inputs.camera.cv2')
    def test_camera_capture_failure(self, mock_cv2: MagicMock) -> None:
        """Tests that camera capture returns failure gracefully when cv2 cannot open device."""
        # Set up mock camera failure
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_cv2.VideoCapture.return_value = mock_cap

        camera = CameraCapture(device_id=0)
        success, frame = camera.capture_frame()
        self.assertFalse(success)
        self.assertIsNone(frame)

    def test_voice_transcription(self) -> None:
        """Tests that voice transcription recording and API transcription triggers correctly."""
        voice_handler = VoiceInputHandler()
        transcript: str = voice_handler.record_and_transcribe(duration_seconds=1)
        self.assertIsInstance(transcript, str)
        self.assertGreater(len(transcript), 0)

