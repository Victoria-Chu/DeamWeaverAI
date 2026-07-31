import logging
import tempfile
import wave
from pathlib import Path

try:
    import pyaudio
except ImportError:
    pyaudio = None

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from config.settings import settings

logger = logging.getLogger(__name__)

class VoiceInputHandler:
    """Handles audio recording from microphone and transcription using the Gemini API."""

    def __init__(self) -> None:
        """Initializes the voice input handler."""

    def record_to_wav(self, duration_seconds: int = 5) -> Path | None:
        """
        Records audio from the microphone and saves it to a temporary WAV file.

        Args:
            duration_seconds: Duration of the recording in seconds.

        Returns:
            The Path to the temporary WAV file, or None if the recording failed.
        """
        if pyaudio is None:
            logger.warning("PyAudio is not installed. Cannot record audio.")
            return None

        try:
            chunk: int = 1024
            sample_format: int = pyaudio.paInt16
            channels: int = 1
            fs: int = 44100

            p = pyaudio.PyAudio()
            logger.info(f"Opening microphone stream (Rate: {fs}, Channels: {channels})...")
            stream = p.open(format=sample_format,
                            channels=channels,
                            rate=fs,
                            frames_per_buffer=chunk,
                            input=True)

            logger.info(f"Recording audio for {duration_seconds} seconds...")
            frames: list[bytes] = []

            # Stream read loop
            for _ in range(int(fs / chunk * duration_seconds)):
                data: bytes = stream.read(chunk, exception_on_overflow=False)
                frames.append(data)

            # Close stream and terminate PyAudio
            stream.stop_stream()
            stream.close()
            p.terminate()
            logger.info("Microphone stream closed.")

            # Save to temporary wav file using pathlib.Path
            temp_dir: Path = Path(tempfile.gettempdir())
            wav_path: Path = temp_dir / "dreamweaver_voice.wav"
            
            # wave.open expects a string path or a file-like object on some Python versions,
            # so we use str(wav_path) for maximum safety with wave.open
            with wave.open(str(wav_path), 'wb') as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(p.get_sample_size(sample_format))
                wf.setframerate(fs)
                wf.writeframes(b''.join(frames))

            logger.info(f"Audio recorded successfully and saved to {wav_path}")
            return wav_path

        except Exception as e:
            logger.error(f"Error recording audio: {e}")
            return None

    def transcribe_audio_bytes(self, audio_bytes: bytes, mime_type: str = 'audio/wav') -> str:
        """
        Transcribes raw audio bytes using the Gemini API.

        Args:
            audio_bytes: The raw audio bytes to transcribe.
            mime_type: The MIME type of the audio data (e.g. 'audio/wav', 'audio/mp3').

        Returns:
            The transcribed text string, or a mock fallback string if transcription fails.
        """
        if genai is not None and types is not None and settings.gemini_api_key:
            try:
                logger.info(f"Transcribing audio bytes ({len(audio_bytes)} bytes, {mime_type}) using Gemini API...")
                client = genai.Client(api_key=settings.gemini_api_key)
                response = client.models.generate_content(
                    model=settings.gemini_model_name,
                    contents=[
                        types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                        "Transcribe the spoken audio. Provide only the transcription, without any extra text."
                    ]
                )
                transcription: str = response.text.strip()
                if transcription:
                    logger.info(f"Successfully transcribed audio: '{transcription}'")
                    return transcription
            except Exception as e:
                logger.error(f"Error during audio transcription: {e}")

        logger.info("Defaulting to mock voice transcription.")
        return "Write a story about a little bunny who wants to visit the moon."

    def record_and_transcribe(self, duration_seconds: int = 5) -> str:
        """
        Records audio from microphone stream and transcribes it using the Gemini API.

        Args:
            duration_seconds: Duration of the recording in seconds.

        Returns:
            The transcribed text string, or a mock fallback string if transcription fails.
        """
        wav_path: Path | None = self.record_to_wav(duration_seconds)
        if wav_path is None:
            logger.warning("No audio recorded. Defaulting to mock voice transcription.")
            return "Write a story about a little bunny who wants to visit the moon."

        # Reading bytes directly from the Path object
        audio_bytes: bytes = wav_path.read_bytes()
        return self.transcribe_audio_bytes(audio_bytes, mime_type='audio/wav')
