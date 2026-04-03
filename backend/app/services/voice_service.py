"""
ElevenLabs Voice Generation Service
Generates realistic Hindi/English narration with Rachel voice
"""

import logging
import os
import tempfile
from elevenlabs.client import ElevenLabs
from config import settings

logger = logging.getLogger(__name__)

# Get the backend directory for storing audio files
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUDIO_DIR = os.path.join(BACKEND_DIR, "audio_cache")

# Create audio directory if it doesn't exist
os.makedirs(AUDIO_DIR, exist_ok=True)
logger.info(f"Audio cache directory: {AUDIO_DIR}")

# Initialize ElevenLabs client
try:
    client = ElevenLabs(api_key=settings.elevenlabs_api_key)
    ELEVENLABS_ENABLED = True
    logger.info("ElevenLabs client initialized successfully")
except Exception as e:
    ELEVENLABS_ENABLED = False
    logger.warning(f"ElevenLabs initialization failed: {e}")
    client = None


def get_audio_file_path() -> str:
    """Get the full path to the latest audio file."""
    return os.path.join(AUDIO_DIR, "latest.mp3")


def generate_voice(text: str, voice_id: str = "21m00Tcm4TlvDq8ikWAM") -> str:
    """
    Generate voice narration using ElevenLabs.

    Args:
        text: Text to convert to speech
        voice_id: ElevenLabs voice ID (default: Rachel - 21m00Tcm4TlvDq8ikWAM)

    Returns:
        Path to generated MP3 file

    Raises:
        Exception: If ElevenLabs API fails
    """
    if not ELEVENLABS_ENABLED or not client:
        raise Exception("ElevenLabs is not configured. Please set ELEVENLABS_API_KEY in .env")

    try:
        logger.info(f"Generating voice for text: {text[:50]}...")

        # Call ElevenLabs API
        audio_stream = client.text_to_speech.convert(
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",
            text=text,
        )

        # Save to file with absolute path
        file_path = get_audio_file_path()

        with open(file_path, "wb") as f:
            for chunk in audio_stream:
                f.write(chunk)

        file_size = os.path.getsize(file_path)
        logger.info(f"Voice generated successfully: {file_path} ({file_size} bytes)")

        return file_path

    except Exception as e:
        logger.error(f"Voice generation error: {str(e)}")
        raise
