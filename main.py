from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import io

app = FastAPI(title="Text to Speech Service", version="0.1.0")

class TextToSpeechRequest(BaseModel):
    text: str
    voice: str = "default"
    speed: float = 1.0

@app.get("/")
async def root():
    return {"message": "Text to Speech Service"}

@app.post("/text-to-speech")
async def text_to_speech(request: TextToSpeechRequest):
    # Placeholder implementation - return a simple response
    audio_data = f"Audio for: {request.text} with voice: {request.voice}".encode()
    
    return StreamingResponse(
        io.BytesIO(audio_data),
        media_type="audio/wav",
        headers={"Content-Disposition": "attachment; filename=speech.wav"}
    )

@app.get("/health")
async def health():
    return {"status": "healthy"}