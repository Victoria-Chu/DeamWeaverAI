import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load env variables from a local .env file if it exists
load_dotenv()

class AppSettings(BaseModel):
    gemini_api_key: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", "").strip().strip('"').strip("'"))
    imagen_api_key: str = Field(default_factory=lambda: os.getenv("IMAGEN_API_KEY", "").strip().strip('"').strip("'"))
    gemini_model_name: str = Field(default="gemini-3.1-flash-lite")
    imagen_model_name: str = Field(default="gemini-2.5-flash-image")

    # Default Bedtime Session Persona
    default_child_name: str = Field(default="Lele")
    default_child_age: int = Field(default=6)

    # Bedtime Session Inputs/Outputs Defaults
    default_duration_minutes: int = Field(default=10)  # Range: 3 to 20 minutes
    default_wpm_speed: int = Field(default=140)  # calibrated child story reading WPM
    default_input_mode: str = Field(default="Voice")  # 'Voice' or 'Image'
    default_voice_model: str = Field(default="en-US-GuyNeural")

    # Output controls
    enable_voice_story: bool = Field(default=True)  # True to generate TTS audio narration
    enable_illustrated_story: bool = Field(default=True)  # True to generate cover & scenes illustrations

    @property
    def base_dir(self) -> Path:
        """Returns the project base directory path."""
        return Path(__file__).resolve().parent.parent

    @property
    def assets_dir(self) -> Path:
        """Returns the project assets storage directory path, creating it if necessary."""
        path = self.base_dir / "assets"
        path.mkdir(parents=True, exist_ok=True)
        return path

# Global settings instance
settings = AppSettings()
