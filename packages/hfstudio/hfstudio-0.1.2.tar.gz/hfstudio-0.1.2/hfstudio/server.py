from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, Any
import base64
import io
import numpy as np
import soundfile as sf
import httpx
import os
from pathlib import Path
from huggingface_hub import InferenceClient, get_token, whoami

app = FastAPI(title="HFStudio API", version="0.1.0")

# Get the static files directory
static_dir = Path(__file__).parent / "static"

# Mount static files
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    app.mount("/_app", StaticFiles(directory=str(static_dir / "_app")), name="app")
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")
    app.mount("/samples", StaticFiles(directory=str(static_dir / "samples")), name="samples")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:7860", 
        "http://localhost:11111", 
        "http://localhost:11112",  # Add the current frontend port
        "http://localhost:3000",
        "*"  # Allow all origins for Spaces deployment
    ],
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
    access_token: Optional[str] = None

class TTSResponse(BaseModel):
    audio_url: Optional[str] = None
    duration: Optional[float] = None
    format: str = "wav"
    error: Optional[str] = None
    success: bool = True

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
    """Serve the SvelteKit single-page application"""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path), media_type="text/html")
    else:
        return {"message": "HFStudio API is running"}

@app.get("/api/status")
async def get_status():
    return {
        "mode": "api",
        "local_available": False,
        "api_configured": True
    }

@app.get("/api/auth/oauth-config")
async def get_oauth_config():
    """Get OAuth configuration for the frontend"""
    # Get scopes from environment variable or use default
    scopes = os.getenv("OAUTH_SCOPES", "read-repos write-repos manage-repos inference-api")
    
    return {
        "client_id": os.getenv("OAUTH_CLIENT_ID", "cdf32a17-e40f-4a84-b683-f66aa1105793"),
        "scopes": scopes,
        "is_spaces": bool(os.getenv("SPACE_HOST"))
    }

@app.get("/api/auth/local-token")
async def get_local_token():
    """Get local HF token if available (for local development)"""
    try:
        # Check if we're running on Spaces
        if os.getenv("SPACE_HOST"):
            return {"available": False, "reason": "running_on_spaces"}
        
        # Try to get local token
        token = get_token()
        if not token:
            return {"available": False, "reason": "no_local_token"}
        
        # Try to validate token by getting user info, but handle rate limiting gracefully
        try:
            user_info = whoami(token=token)
            if user_info.get("type") != "user":
                return {"available": False, "reason": "invalid_token_type"}
            
            return {
                "available": True,
                "token": token,
                "user_info": {
                    "name": user_info.get("name"),
                    "fullname": user_info.get("fullname"),
                    "avatarUrl": user_info.get("avatarUrl")
                }
            }
        except Exception as api_error:
            # If API validation fails (e.g., rate limiting), still return the token
            # The frontend can validate it when needed
            if "429" in str(api_error) or "rate limit" in str(api_error).lower():
                return {
                    "available": True,
                    "token": token,
                    "user_info": {
                        "name": "Local User",
                        "fullname": "Local User",
                        "avatarUrl": None
                    },
                    "warning": "Token validation skipped due to rate limiting"
                }
            else:
                return {"available": False, "reason": f"token_validation_error: {str(api_error)}"}
        
    except Exception as e:
        return {"available": False, "reason": f"error: {str(e)}"}

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
        print(f"Received TTS request: mode={request.mode}, has_token={bool(request.access_token)}")
        if request.access_token:
            print(f"Token preview: {request.access_token[:10]}...")
        
        # Check if we have an access token for API mode
        if request.mode == "api" and request.access_token:
            print("Using Chatterbox API...")
            try:
                # Use Chatterbox API via HuggingFace InferenceClient
                client = InferenceClient(
                    provider="fal-ai",
                    api_key=request.access_token,
                )
                
                print(f"Calling text_to_speech with text: '{request.text[:50]}...'")
                print(f"Using token: {request.access_token}")
                print(f"Model: ResembleAI/chatterbox")
                print(f"Provider: fal-ai")
                
                # Print the equivalent Python command for testing
                print("=" * 80)
                print("EQUIVALENT PYTHON CODE:")
                print("You can test this locally with:")
                print(f"""
from huggingface_hub import InferenceClient

client = InferenceClient(
    provider="fal-ai",
    api_key="{request.access_token}",
)

audio_bytes = client.text_to_speech(
    "{request.text}",
    model="ResembleAI/chatterbox",
)

print(f"Success! Generated {{len(audio_bytes)}} bytes of audio")
                """.strip())
                print("=" * 80)
                
                # Generate audio using Chatterbox
                audio_bytes = client.text_to_speech(
                    request.text,
                    model="ResembleAI/chatterbox",
                )
                
                print(f"Received audio bytes: {len(audio_bytes)} bytes")
                
                # Convert audio bytes to base64 for data URL
                audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                audio_url = f"data:audio/wav;base64,{audio_base64}"
                
                # Estimate duration (rough calculation)
                duration = len(request.text) * 0.05  # ~0.05 seconds per character
                
                print("Successfully generated audio via Chatterbox API")
                return TTSResponse(
                    audio_url=audio_url,
                    duration=duration,
                    format="wav"
                )
            except Exception as api_error:
                error_str = str(api_error)
                print(f"Chatterbox API error: {error_str}")
                
                # Provide specific error messages based on the error type
                if "403 Forbidden" in error_str and "permissions" in error_str:
                    return TTSResponse(
                        success=False,
                        error="Your HuggingFace token doesn't have permission to use Inference Providers. Please create a new token with 'Inference API' permissions at https://huggingface.co/settings/tokens"
                    )
                elif "authentication" in error_str.lower():
                    return TTSResponse(
                        success=False,
                        error="Authentication failed. Please check your HuggingFace token or log in again."
                    )
                else:
                    return TTSResponse(
                        success=False,
                        error=f"Chatterbox API error: {error_str}"
                    )
        
        # No token provided
        if request.mode == "api":
            return TTSResponse(
                success=False,
                error="Please log in to HuggingFace to use the Chatterbox API."
            )
        else:
            return TTSResponse(
                success=False,
                error="Local mode not yet implemented."
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/token")
async def exchange_oauth_token(request: OAuthTokenRequest, http_request: Request):
    """Exchange OAuth authorization code for access token"""
    try:
        # HuggingFace OAuth token endpoint
        token_url = "https://huggingface.co/oauth/token"
        
        # OAuth app credentials - use environment variables on Spaces, fallback to hardcoded for local dev
        client_id = os.getenv("OAUTH_CLIENT_ID", "cdf32a17-e40f-4a84-b683-f66aa1105793")
        client_secret = os.getenv("OAUTH_CLIENT_SECRET", "f590cb2d-6eac-4cef-a0cb-d0116825295c")
        
        # Determine redirect URI based on environment
        if os.getenv("SPACE_HOST"):
            # On Spaces, use the Space URL
            space_host = os.getenv("SPACE_HOST").split(",")[0]  # Handle custom domains
            redirect_uri = f"https://{space_host}/auth/callback"
        else:
            # Local development - try to determine from referer header
            referer = http_request.headers.get("referer", "")
            if referer:
                from urllib.parse import urlparse
                parsed = urlparse(referer)
                redirect_uri = f"{parsed.scheme}://{parsed.netloc}/auth/callback"
            else:
                # Final fallback for development
                redirect_uri = "http://localhost:7860/auth/callback"
        
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

@app.get("/auth/callback")
async def oauth_callback(code: str = None, state: str = None, request: Request = None):
    """Handle OAuth callback and redirect to frontend with token"""
    if not code:
        return HTMLResponse("""
        <html>
            <head><title>OAuth Error</title></head>
            <body>
                <h1>OAuth Error</h1>
                <p>No authorization code received.</p>
                <script>window.close();</script>
            </body>
        </html>
        """, status_code=400)
    
    try:
        # Exchange code for token using the same logic as the API endpoint
        token_url = "https://huggingface.co/oauth/token"
        
        client_id = os.getenv("OAUTH_CLIENT_ID", "cdf32a17-e40f-4a84-b683-f66aa1105793")
        client_secret = os.getenv("OAUTH_CLIENT_SECRET", "f590cb2d-6eac-4cef-a0cb-d0116825295c")
        
        # Determine redirect URI based on environment
        if os.getenv("SPACE_HOST"):
            # On Spaces, use the Space URL
            space_host = os.getenv("SPACE_HOST").split(",")[0]  # Handle custom domains
            redirect_uri = f"https://{space_host}/auth/callback"
        else:
            # Local development
            redirect_uri = "http://localhost:7860/auth/callback"
        
        token_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data=token_data,
                headers={"Accept": "application/json"}
            )
            
            if response.status_code == 200:
                token_response = response.json()
                access_token = token_response["access_token"]
                
                # Return HTML page that stores token and closes popup/redirects
                return HTMLResponse(f"""
                <html>
                    <head><title>OAuth Success</title></head>
                    <body>
                        <h1>Sign in successful!</h1>
                        <p>Redirecting...</p>
                        <script>
                            localStorage.setItem('hf_access_token', '{access_token}');
                            window.location.href = '/';
                        </script>
                    </body>
                </html>
                """)
            else:
                return HTMLResponse(f"""
                <html>
                    <head><title>OAuth Error</title></head>
                    <body>
                        <h1>OAuth Error</h1>
                        <p>Token exchange failed: {response.text}</p>
                        <a href="/">Return to app</a>
                    </body>
                </html>
                """, status_code=400)
                
    except Exception as e:
        return HTMLResponse(f"""
        <html>
            <head><title>OAuth Error</title></head>
            <body>
                <h1>OAuth Error</h1>
                <p>Error: {str(e)}</p>
                <a href="/">Return to app</a>
            </body>
        </html>
        """, status_code=500)

# Catch-all route to serve the SvelteKit app (excluding API routes)
@app.get("/{path:path}")
async def serve_spa(path: str):
    """Serve the SvelteKit single-page application for non-API routes"""
    # Skip API routes
    if path.startswith("api/") or path.startswith("docs") or path.startswith("openapi.json"):
        raise HTTPException(status_code=404, detail="Not found")
    
    # For any non-API route, serve the index.html
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path), media_type="text/html")
    else:
        # Fallback if no built frontend
        return HTMLResponse("""
        <html>
            <head><title>HFStudio</title></head>
            <body>
                <h1>HFStudio Backend</h1>
                <p>The backend is running, but the frontend hasn't been built yet.</p>
                <p>Visit <a href="/docs">/docs</a> for the API documentation.</p>
            </body>
        </html>
        """)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)