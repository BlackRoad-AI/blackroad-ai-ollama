"""
🤖 BlackRoad AI - Ollama Wrapper Server
Adds [MEMORY] integration, emoji support, actions, OAuth, and vendor proxy to Ollama
"""

import os
import secrets
import subprocess
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Any, Dict
import httpx

app = FastAPI(
    title="BlackRoad AI - Ollama Wrapper",
    description="Ollama with [MEMORY] integration and BlackRoad enhancements",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ollama client
OLLAMA_URL = "http://localhost:11434"

# ── Bearer token / API-key authentication ───────────────────────────────────
# Set BLACKROAD_API_KEY env var to enable auth; omit to run open (dev mode).
_REQUIRED_KEY: Optional[str] = os.getenv("BLACKROAD_API_KEY")
_bearer = HTTPBearer(auto_error=False)


async def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> None:
    """Validate Bearer token when BLACKROAD_API_KEY is configured."""
    if not _REQUIRED_KEY:
        return  # auth disabled – development / LAN mode
    if credentials is None or not secrets.compare_digest(
        credentials.credentials, _REQUIRED_KEY
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )


class ChatRequest(BaseModel):
    model: str
    message: str
    max_tokens: int = 512
    temperature: float = 0.7
    use_memory: bool = True
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    model: str
    memory_context_used: bool = False
    emoji_enhanced: bool = True


@app.get("/")
async def root():
    return {
        "service": "BlackRoad AI - Ollama Wrapper",
        "status": "online",
        "features": ["oauth", "memory_integration", "emoji_support", "multi_model", "openai_proxy"]
    }


@app.get("/health")
async def health():
    """Health check"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            return {
                "status": "healthy",
                "ollama_running": response.status_code == 200
            }
    except:
        return {"status": "unhealthy", "ollama_running": False}


@app.get("/models", dependencies=[Depends(require_auth)])
async def list_models():
    """List available models"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse, dependencies=[Depends(require_auth)])
async def chat(request: ChatRequest):
    """
    Chat with Ollama model + BlackRoad enhancements
    """
    prompt = request.message
    memory_used = False

    # Add memory context
    if request.use_memory and request.session_id:
        try:
            result = subprocess.run(
                ["/host-home/memory-system.sh", "check", f"ollama-{request.session_id}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout:
                prompt = f"[Context]\n{result.stdout}\n\n{request.message}"
                memory_used = True
        except:
            pass

    # Call Ollama
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": request.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": request.temperature,
                        "num_predict": request.max_tokens
                    }
                }
            )
            result = response.json()
            response_text = result.get("response", "")

            # Enhance with emojis
            response_text = enhance_with_emojis(response_text)

            # Save to memory
            if request.session_id:
                try:
                    subprocess.run(
                        [
                            "/host-home/memory-system.sh", "log", "interaction",
                            f"ollama-{request.session_id}",
                            f"Q: {request.message}\nA: {response_text}",
                            f"ai,ollama,{request.model}"
                        ],
                        timeout=5
                    )
                except:
                    pass

            return ChatResponse(
                response=response_text,
                model=request.model,
                memory_context_used=memory_used,
                emoji_enhanced=True
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── OpenAI-compatible vendor proxy ──────────────────────────────────────────
# Clients configured to point at http://<host>:8001/v1 (with any API key)
# will have their requests served entirely by the local Ollama instance.
# This replaces OpenAI / Anthropic / Copilot routing with your own infra.

# Default model mapping: OpenAI model names → local Ollama equivalents
_MODEL_MAP: Dict[str, str] = {
    "gpt-4": "qwen2.5:7b",
    "gpt-4o": "qwen2.5:7b",
    "gpt-4o-mini": "llama3.2:3b",
    "gpt-3.5-turbo": "mistral:7b",
    "claude-3-opus-20240229": "deepseek-r1:7b",
    "claude-3-sonnet-20240229": "qwen2.5:7b",
    "claude-3-haiku-20240307": "llama3.2:3b",
    "claude-3-5-sonnet-20241022": "qwen2.5:7b",
}

# Environment overrides, e.g. BLACKROAD_MODEL_MAP='{"gpt-4":"deepseek-r1:7b"}'
import json as _json
import uuid as _uuid
try:
    _MODEL_MAP.update(_json.loads(os.getenv("BLACKROAD_MODEL_MAP", "{}")))
except Exception:
    pass


class _OAIMessage(BaseModel):
    role: str
    content: str


class _OAIChatRequest(BaseModel):
    model: str
    messages: List[_OAIMessage]
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False


@app.get("/v1/models", dependencies=[Depends(require_auth)])
async def oai_list_models():
    """OpenAI-compatible model list – returns locally available Ollama models."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{OLLAMA_URL}/api/tags")
            tags = resp.json().get("models", [])
        data = [
            {"id": m["name"], "object": "model", "owned_by": "blackroad"}
            for m in tags
        ]
        # Also surface the alias names so existing client configs work unchanged
        for alias, local in _MODEL_MAP.items():
            data.append({"id": alias, "object": "model", "owned_by": "blackroad"})
        return {"object": "list", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/chat/completions", dependencies=[Depends(require_auth)])
async def oai_chat_completions(request: _OAIChatRequest):
    """
    OpenAI-compatible chat completions endpoint.

    Point any SDK / tool that supports a custom base URL at
    ``http://<host>:8001/v1`` and all traffic will be served by the local
    Ollama instance — no calls leave your infrastructure.

    Example (Python openai SDK):
        import openai
        client = openai.OpenAI(
            base_url="http://localhost:8001/v1",
            api_key="<BLACKROAD_API_KEY>",
        )
    """
    # Resolve model alias → local Ollama model name
    local_model = _MODEL_MAP.get(request.model, request.model)

    # Convert OpenAI messages to Ollama chat format
    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": local_model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": request.temperature or 0.7,
                        "num_predict": request.max_tokens or 512,
                    },
                },
            )
            resp.raise_for_status()
            data = resp.json()

        content = data.get("message", {}).get("content", "")
        content = enhance_with_emojis(content)

        return {
            "id": f"chatcmpl-{_uuid.uuid4().hex}",
            "object": "chat.completion",
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
                "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def enhance_with_emojis(text: str) -> str:
    """Add contextual emojis"""
    emoji_map = {
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️",
        "blackroad": "🖤🛣️",
        "ai": "🤖",
        "quantum": "⚛️"
    }

    for keyword, emoji in emoji_map.items():
        if keyword.lower() in text.lower() and emoji not in text:
            text = text.replace(keyword, f"{emoji} {keyword}", 1)

    return text


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
