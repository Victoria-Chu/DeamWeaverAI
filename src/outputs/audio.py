import logging
from pathlib import Path

from config.settings import settings

try:
    import edge_tts
except ImportError:
    edge_tts = None

logger = logging.getLogger(__name__)

class TTSSynthesizer:
    """Synthesizes text into high-quality spoken audio narration using Edge TTS."""

    def __init__(self, voice_model: str = "en-US-GuyNeural", wpm_speed: int = 140) -> None:
        """
        Initializes the TTS synthesizer.

        Args:
            voice_model: The voice profile to use for edge-tts.
            wpm_speed: The target words per minute speed.
        """
        self.voice_model: str = voice_model
        self.wpm_speed: int = wpm_speed

    async def synthesize_speech_async(self, text: str, output_filename: str = "narration.mp3") -> Path:
        """
        Asynchronously synthesizes text into speech using edge-tts.

        Args:
            text: The narrative text to synthesize.
            output_filename: The target output filename.

        Returns:
            The Path to the generated audio narration file.
        """
        output_path: Path = settings.assets_dir / output_filename
        output_str: str = str(output_path)

        if edge_tts is None:
            logger.warning("edge-tts is not installed. Defaulting to mock narration path.")
            return output_path

        try:
            logger.info(f"Synthesizing speech with voice {self.voice_model} at {self.wpm_speed} WPM using edge-tts.")
            # Map speed change to edge-tts rate format (e.g. +10%, -15%)
            # Standard WPM is approx 150 WPM. Calculate deviation percentage.
            base_wpm: int = 150
            percent_change: int = int(((self.wpm_speed - base_wpm) / base_wpm) * 100)
            rate_str: str = f"{'+' if percent_change >= 0 else ''}{percent_change}%"

            communicate = edge_tts.Communicate(text, self.voice_model, rate=rate_str)
            await communicate.save(output_str)
            logger.info(f"Audio narration saved successfully to {output_str}")
            return output_path
        except Exception as e:
            logger.error(f"Error during audio synthesis: {e}")
            return output_path

