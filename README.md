# 🤖 BlackRoad AI - Ollama Runtime

**Multi-model AI runtime with [MEMORY] integration**

## 🎯 Overview

BlackRoad's deployment of Ollama - a runtime for running multiple AI models with:
- 🧠 **[MEMORY] Integration** - Context from BlackRoad memory system
- 🎨 **Emoji Enhancement** - Automatic emoji support
- 🔄 **Multi-Model** - Run Qwen, DeepSeek, Llama, Mistral, etc.
- 🌐 **Cluster Ready** - Deploy across Pi network
- ⚡ **Action Support** - Execute commands via models

## 📦 Included Models

Automatically pulls on startup:
- **Qwen2.5:7b** - Apache 2.0 language model
- **DeepSeek-R1:7b** - Reasoning model
- **Llama3.2:3b** - Meta's compact model
- **Mistral:7b** - Mistral AI model

## 🚀 Quick Start

### Docker Deployment
```bash
# Build and start
docker-compose up -d

# Check logs
docker logs -f blackroad-ai-ollama

# List models
curl http://localhost:11434/api/tags
```

### Using BlackRoad Wrapper
```bash
# Chat with Qwen via wrapper (includes [MEMORY])
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "message": "Explain quantum entanglement",
    "use_memory": true,
    "session_id": "user-123"
  }'
```

### Direct Ollama API
```bash
# Chat without wrapper
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:7b",
  "prompt": "Why is the sky blue?",
  "stream": false
}'
```

## 🏗️ Architecture

```
┌────────────────────────────────────────┐
│     BlackRoad Wrapper (Port 8001)     │
│   ┌──────────────┐  ┌──────────────┐  │
│   │  [MEMORY]    │  │   Emoji      │  │
│   │  Bridge      │  │   Enhancer   │  │
│   └──────┬───────┘  └──────┬───────┘  │
│          └──────────────────┘          │
└──────────────────┬─────────────────────┘
                   │
       ┌───────────▼───────────┐
       │   Ollama (Port 11434) │
       ├───────────────────────┤
       │  • qwen2.5:7b         │
       │  • deepseek-r1:7b     │
       │  • llama3.2:3b        │
       │  • mistral:7b         │
       └───────────────────────┘
```

## 🧠 [MEMORY] Integration

The BlackRoad wrapper adds memory capabilities:
```python
# Automatically includes conversation history
# Saves all interactions
# Collaborates with other Claude instances
```

## 🌐 Cluster Deployment

Deploy to all Pis:
```bash
./deploy-ollama-cluster.sh
```

This deploys to:
- lucidia (192.168.4.38)
- aria (192.168.4.64)
- alice (192.168.4.49)
- octavia (192.168.4.74)

## 📊 API Endpoints

### BlackRoad Wrapper (Port 8001)
- `GET /` - Service info
- `GET /health` - Health check (no auth required)
- `GET /models` - List models
- `POST /chat` - Chat with [MEMORY] integration

### OpenAI-Compatible Proxy (Port 8001 · prefix `/v1`)

Point **any** OpenAI SDK or tool at `http://<host>:8001/v1` and all traffic
is served locally — no calls leave your infrastructure.

```python
import openai
client = openai.OpenAI(
    base_url="http://localhost:8001/v1",
    api_key="<BLACKROAD_API_KEY>",   # or any string when auth is disabled
)
response = client.chat.completions.create(
    model="gpt-4",          # auto-mapped → qwen2.5:7b
    messages=[{"role": "user", "content": "Hello!"}],
)
```

- `GET  /v1/models` - List models (OpenAI format)
- `POST /v1/chat/completions` - Chat completions (OpenAI format)

**Default model aliases** (overridable via `BLACKROAD_MODEL_MAP` env var):

| OpenAI / Anthropic name | Local Ollama model |
|---|---|
| `gpt-4`, `gpt-4o` | `qwen2.5:7b` |
| `gpt-4o-mini`, `claude-3-haiku-*` | `llama3.2:3b` |
| `gpt-3.5-turbo` | `mistral:7b` |
| `claude-3-opus-*`, `claude-3-5-sonnet-*` | `deepseek-r1:7b` |

### Ollama Direct (Port 11434)
- `GET /api/tags` - List models
- `POST /api/generate` - Generate completion
- `POST /api/chat` - Chat completion
- `POST /api/pull` - Pull new model

## 🔒 Authentication (OAuth / API Key)

Set the `BLACKROAD_API_KEY` environment variable to enable Bearer-token auth on
all protected endpoints. When the variable is absent the server runs in
open/LAN mode (suitable for Pi-local deployment behind Tailscale/Cloudflare).

```bash
# Enable auth
export BLACKROAD_API_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
docker-compose up -d
```

Clients send the key as a standard Bearer token:

```
Authorization: Bearer <BLACKROAD_API_KEY>
```

## 🎨 Models You Can Add

```bash
# Pull any Ollama model
docker exec blackroad-ai-ollama ollama pull <model-name>

# Popular models:
ollama pull codellama:7b      # Code generation
ollama pull phi:2.7b          # Microsoft Phi
ollama pull neural-chat:7b    # Intel's model
```

## 📄 License

- **Ollama Runtime**: MIT License
- **Models**: Various (Apache 2.0, MIT, etc.)
- **BlackRoad Wrapper**: BlackRoad Proprietary

---

🌌 **Built with the BlackRoad Vision** - One runtime, infinite models

---

## 🖤 BlackRoad OS

This repository is part of the **BlackRoad OS** ecosystem - the operating system for AI-first companies.

### 🌟 The Vision

BlackRoad OS enables entire companies to operate exclusively by AI while serving as the API layer above Google, OpenAI, and Anthropic, managing their AI model memory and continuity.

- **OS in a Window**: [os.blackroad.io](https://os.blackroad.io)
- **3D AI Models**: [products.blackroad.io](https://products.blackroad.io)
- **Agent Orchestration**: 30,000 AI agents coordinated via memory system

### 🤖 GitHub Integration

Need help? Mention **@blackroad** in any issue or PR to summon our intelligent agent cascade!

### 📊 Repository Stats

- **Organization**: Part of 15 BlackRoad organizations
- **Total Repos**: 144+ across the empire
- **AI Agents**: 30,000+ available for assistance

### 🔗 Links

- [BlackRoad OS](https://blackroad.io)
- [Documentation](https://docs.blackroad.io)
- [Status](https://status.blackroad.io)
- [GitHub Organizations](https://github.com/BlackRoad-OS)

### 📧 Contact

- Email: blackroad.systems@gmail.com
- Primary: amundsonalexa@gmail.com

### ⚖️ License

Copyright © 2026 BlackRoad OS, Inc. - All Rights Reserved

See [LICENSE](./LICENSE) for details.

---

🖤🛣️ **The road is the destination.**
