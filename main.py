from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
import io
import logging
from datetime import datetime
import wave
import struct
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Creole Text-to-Speech Service",
    description="Text-to-Speech API for Haitian Creole and other languages",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class SynthesisRequest(BaseModel):
    text: str
    language: str = "ht"
    voice: str = "default"
    speed: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0
    
class BatchSynthesisRequest(BaseModel):
    texts: List[str]
    language: str = "ht"
    voice: str = "default"
    speed: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0

class SynthesisResponse(BaseModel):
    audio_url: str
    duration: float
    language: str
    voice: str
    
class Voice(BaseModel):
    id: str
    name: str
    language: str
    gender: str
    age: str
    description: str
    
class VoicesResponse(BaseModel):
    voices: List[Voice]
    
class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str

# Mock audio generation function
async def generate_audio(text: str, language: str, voice: str, speed: float, pitch: float, volume: float) -> bytes:
    """Mock audio generation function - replace with actual TTS model"""
    await asyncio.sleep(0.3)  # Simulate processing time
    
    # Generate a simple sine wave as mock audio
    sample_rate = 22050
    duration = max(1.0, len(text) * 0.1)  # Rough duration estimate
    
    # Generate sine wave
    frames = []
    for i in range(int(sample_rate * duration)):
        # Create a simple tone that varies with text content
        frequency = 440 + (hash(text) % 200)  # Base frequency with text-based variation
        amplitude = 0.3 * volume
        
        # Apply speed and pitch modifications
        adjusted_frequency = frequency * pitch
        time_factor = speed
        
        sample = amplitude * math.sin(2 * math.pi * adjusted_frequency * i / sample_rate / time_factor)
        frames.append(struct.pack('<h', int(sample * 32767)))
    
    # Create WAV file in memory
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b''.join(frames))
    
    return buffer.getvalue()

# Available voices
AVAILABLE_VOICES = [
    Voice(
        id="default",
        name="Default Voice",
        language="ht",
        gender="neutral",
        age="adult",
        description="Standard Haitian Creole voice"
    ),
    Voice(
        id="marie",
        name="Marie",
        language="ht",
        gender="female",
        age="adult",
        description="Friendly female Haitian Creole voice"
    ),
    Voice(
        id="jean",
        name="Jean",
        language="ht",
        gender="male",
        age="adult",
        description="Clear male Haitian Creole voice"
    ),
    Voice(
        id="english-default",
        name="English Default",
        language="en",
        gender="neutral",
        age="adult",
        description="Standard English voice"
    ),
    Voice(
        id="french-default",
        name="French Default",
        language="fr",
        gender="neutral",
        age="adult",
        description="Standard French voice"
    )
]

# Routes
@app.get("/", response_model=dict)
async def root():
    return {
        "message": "Creole Text-to-Speech Service",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        service="text-to-speech",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat()
    )

@app.post("/api/v1/synthesize")
async def synthesize(request: SynthesisRequest):
    """Synthesize text to speech"""
    try:
        logger.info(f"Synthesizing text: {request.text[:50]}... (language: {request.language}, voice: {request.voice})")
        
        # Validate voice
        valid_voices = [voice.id for voice in AVAILABLE_VOICES if voice.language == request.language]
        if request.voice not in valid_voices:
            raise HTTPException(
                status_code=400, 
                detail=f"Voice '{request.voice}' not available for language '{request.language}'"
            )
        
        # Validate parameters
        if not (0.5 <= request.speed <= 2.0):
            raise HTTPException(status_code=400, detail="Speed must be between 0.5 and 2.0")
        if not (0.5 <= request.pitch <= 2.0):
            raise HTTPException(status_code=400, detail="Pitch must be between 0.5 and 2.0")
        if not (0.1 <= request.volume <= 1.0):
            raise HTTPException(status_code=400, detail="Volume must be between 0.1 and 1.0")
        
        # Generate audio
        audio_data = await generate_audio(
            request.text, 
            request.language, 
            request.voice, 
            request.speed, 
            request.pitch, 
            request.volume
        )
        
        # Return audio as streaming response
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"attachment; filename=synthesis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav",
                "X-Duration": str(len(audio_data) / 44100),  # Approximate duration
                "X-Language": request.language,
                "X-Voice": request.voice
            }
        )
        
    except Exception as e:
        logger.error(f"Synthesis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")

@app.post("/api/v1/synthesize/batch")
async def synthesize_batch(request: BatchSynthesisRequest):
    """Synthesize multiple texts to speech"""
    try:
        logger.info(f"Batch synthesizing {len(request.texts)} texts")
        
        if len(request.texts) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 texts per batch request")
        
        # Generate audio for each text
        audio_files = []
        for i, text in enumerate(request.texts):
            audio_data = await generate_audio(
                text, 
                request.language, 
                request.voice, 
                request.speed, 
                request.pitch, 
                request.volume
            )
            
            # Store audio with metadata
            audio_files.append({
                "index": i,
                "text": text,
                "audio_size": len(audio_data),
                "duration": len(audio_data) / 44100  # Approximate duration
            })
        
        # For batch requests, return metadata (in real implementation, you'd store files and return URLs)
        return {
            "batch_id": f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "total_files": len(audio_files),
            "files": audio_files,
            "message": "Batch synthesis completed. In production, this would return download URLs."
        }
        
    except Exception as e:
        logger.error(f"Batch synthesis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch synthesis failed: {str(e)}")

@app.get("/api/v1/voices", response_model=VoicesResponse)
async def get_voices():
    """Get all available voices"""
    return VoicesResponse(voices=AVAILABLE_VOICES)

@app.get("/api/v1/voices/{language}", response_model=VoicesResponse)
async def get_voices_by_language(language: str):
    """Get voices for a specific language"""
    language_voices = [voice for voice in AVAILABLE_VOICES if voice.language == language]
    
    if not language_voices:
        raise HTTPException(status_code=404, detail=f"No voices available for language: {language}")
    
    return VoicesResponse(voices=language_voices)

@app.get("/api/v1/voices/{language}/{voice_id}", response_model=Voice)
async def get_voice(language: str, voice_id: str):
    """Get information about a specific voice"""
    for voice in AVAILABLE_VOICES:
        if voice.language == language and voice.id == voice_id:
            return voice
    
    raise HTTPException(status_code=404, detail=f"Voice {voice_id} not found for language {language}")

@app.get("/api/v1/languages")
async def get_languages():
    """Get supported languages"""
    languages = {}
    for voice in AVAILABLE_VOICES:
        if voice.language not in languages:
            languages[voice.language] = {
                "code": voice.language,
                "name": voice.language.title(),
                "voice_count": 0
            }
        languages[voice.language]["voice_count"] += 1
    
    return {
        "supported_languages": [
            {"code": "ht", "name": "Haitian Creole", "native_name": "Kreyòl Ayisyen"},
            {"code": "en", "name": "English", "native_name": "English"},
            {"code": "fr", "name": "French", "native_name": "Français"},
            {"code": "es", "name": "Spanish", "native_name": "Español"}
        ]
    }

@app.post("/api/v1/preview")
async def preview_voice(
    voice_id: str,
    language: str = "ht",
    text: str = "Bonjou, koman ou ye?"
):
    """Preview a voice with sample text"""
    try:
        # Validate voice
        voice = None
        for v in AVAILABLE_VOICES:
            if v.id == voice_id and v.language == language:
                voice = v
                break
        
        if not voice:
            raise HTTPException(status_code=404, detail=f"Voice {voice_id} not found for language {language}")
        
        # Generate preview audio
        audio_data = await generate_audio(text, language, voice_id, 1.0, 1.0, 0.8)
        
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"attachment; filename=preview_{voice_id}.wav",
                "X-Voice": voice_id,
                "X-Language": language,
                "X-Text": text
            }
        )
        
    except Exception as e:
        logger.error(f"Preview error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")

@app.get("/api/v1/formats")
async def get_supported_formats():
    """Get supported audio formats"""
    return {
        "supported_formats": [
            {
                "format": "wav",
                "mime_type": "audio/wav",
                "description": "WAV audio format",
                "quality": "high",
                "file_size": "large"
            },
            {
                "format": "mp3",
                "mime_type": "audio/mpeg",
                "description": "MP3 audio format",
                "quality": "good",
                "file_size": "medium"
            },
            {
                "format": "ogg",
                "mime_type": "audio/ogg",
                "description": "OGG audio format",
                "quality": "good",
                "file_size": "small"
            }
        ]
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)