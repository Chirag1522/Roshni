"""
Voice narration endpoints
Generate Rachel voice audio for billing and allocation results
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import logging
from app.services.voice_service import generate_voice, get_audio_file_path

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/narrate")
async def narrate_text(request_data: dict):
    """
    Generate voice narration for given text.

    Expected request body:
    {
        "text": "आपने आज सौर ऊर्जा से 250.00 रुपये कमाए।"
    }

    Returns:
        URL to generated audio file: "/voice/latest"
    """
    try:
        text = request_data.get("text", "").strip()

        if not text:
            raise HTTPException(status_code=400, detail="Text is required")

        logger.info(f"Generating voice for: {text[:50]}...")

        # Generate voice using ElevenLabs
        file_path = generate_voice(text)

        logger.info(f"Voice generated successfully: {file_path}")

        return {
            "status": "success",
            "message": "Voice generated successfully",
            "audio_url": "/voice/latest",
        }

    except Exception as e:
        logger.error(f"Voice generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest")
async def get_latest_voice():
    """
    Serve the latest generated voice audio file.

    Returns:
        MP3 audio file
    """
    try:
        audio_file_path = get_audio_file_path()
        return FileResponse(audio_file_path, media_type="audio/mpeg", filename="audio.mp3")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No voice file generated yet")
    except Exception as e:
        logger.error(f"Error serving voice file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))