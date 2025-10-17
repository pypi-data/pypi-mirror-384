from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import base64
import io
import numpy as np
import soundfile as sf
import httpx

app = FastAPI(title="HFStudio API", version="0.1.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:11111", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class TTSRequest(BaseModel):
    text: str
    voice_id: str = "default"
    model_id: str = "coqui-tts"
    parameters: Dict[str, Any] = {}
    mode: str = "api"  # "api" or "local"

class TTSResponse(BaseModel):
    audio_url: str
    duration: float
    format: str = "wav"

class Voice(BaseModel):
    id: str
    name: str
    preview_url: Optional[str] = None
    supported_models: list[str] = []

class Model(BaseModel):
    id: str
    name: str
    type: str  # "local" or "api"
    status: str  # "available", "downloadable", "api-only"

class OAuthTokenRequest(BaseModel):
    code: str

class OAuthTokenResponse(BaseModel):
    access_token: str
    token_type: str
    scope: str

# Routes
@app.get("/")
async def root():
    return {"message": "HFStudio API is running"}

@app.get("/api/status")
async def get_status():
    return {
        "mode": "api",
        "local_available": False,
        "api_configured": True
    }

@app.get("/api/voices")
async def get_voices():
    voices = [
        Voice(id="liam", name="Liam", supported_models=["coqui-tts", "bark"]),
        Voice(id="sarah", name="Sarah", supported_models=["coqui-tts", "bark"]),
        Voice(id="alex", name="Alex", supported_models=["coqui-tts", "bark"]),
        Voice(id="emma", name="Emma", supported_models=["coqui-tts", "bark"]),
    ]
    return {"voices": voices}

@app.get("/api/models")
async def get_models():
    models = [
        Model(id="eleven-multilingual-v2", name="Eleven Multilingual v2", type="api", status="api-only"),
        Model(id="coqui-tts", name="Coqui TTS", type="local", status="available"),
        Model(id="bark", name="Bark", type="local", status="downloadable"),
    ]
    return {"models": models}

@app.post("/api/tts/generate")
async def generate_tts(request: TTSRequest):
    try:
        # For now, generate a simple sine wave as placeholder audio
        duration = min(len(request.text) * 0.05, 10)  # Rough estimate
        sample_rate = 22050
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Generate a simple tone
        frequency = 440  # A4 note
        audio = np.sin(2 * np.pi * frequency * t) * 0.3
        
        # Add some variation
        audio += np.sin(2 * np.pi * frequency * 1.5 * t) * 0.1
        audio += np.sin(2 * np.pi * frequency * 2 * t) * 0.05
        
        # Convert to int16
        audio = (audio * 32767).astype(np.int16)
        
        # Create WAV in memory
        buffer = io.BytesIO()
        sf.write(buffer, audio, sample_rate, format='WAV')
        buffer.seek(0)
        
        # Convert to base64
        audio_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        audio_url = f"data:audio/wav;base64,{audio_base64}"
        
        return TTSResponse(
            audio_url=audio_url,
            duration=duration,
            format="wav"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/token")
async def exchange_oauth_token(request: OAuthTokenRequest):
    """Exchange OAuth authorization code for access token"""
    try:
        # HuggingFace OAuth token endpoint
        token_url = "https://huggingface.co/oauth/token"
        
        # OAuth app credentials
        client_id = "cdf32a17-e40f-4a84-b683-f66aa1105793"
        client_secret = "f590cb2d-6eac-4cef-a0cb-d0116825295c"
        redirect_uri = "http://localhost:11111/auth/callback"
        
        # Prepare token exchange request
        token_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": request.code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
        
        # Exchange code for token
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data=token_data,
                headers={"Accept": "application/json"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Token exchange failed: {response.text}"
                )
            
            token_response = response.json()
            
            return OAuthTokenResponse(
                access_token=token_response["access_token"],
                token_type=token_response.get("token_type", "Bearer"),
                scope=token_response.get("scope", "")
            )
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=11110)