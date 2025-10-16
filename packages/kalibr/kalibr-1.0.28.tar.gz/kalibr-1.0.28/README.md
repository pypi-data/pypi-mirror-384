# Kalibr SDK v1.0.28
### Multi-Model AI Integration Framework

**Write once. Deploy anywhere. Connect to any AI model.**

Kalibr turns your Python functions into APIs that automatically work with **GPT Actions**, **Claude MCP**, **Gemini Extensions**, and **Copilot Plugins** — all from one codebase.  
It’s the unified SDK layer for building, packaging, and deploying AI-ready endpoints.

---

## 🧠 Core Purpose

Kalibr is a **multi-model integration SDK** that converts simple Python functions into fully MCP-compatible APIs for every major AI model ecosystem.

> One function → Four schemas → Deploy anywhere.

---

## ⚙️ What It Does

### 1. Unified Schema Generation

Kalibr automatically generates and serves schemas for:
- `/openapi.json` → GPT Actions
- `/mcp.json` → Claude MCP
- `/schemas/gemini` → Gemini Extensions
- `/schemas/copilot` → Copilot Plugins
- `/models/supported` → List of supported integrations

No manual YAML or JSON schema creation needed.

---

### 2. Environment-Aware Base URLs

Kalibr auto-detects where it's running and sets the correct base URL automatically:

| Environment | Example Base URL |
|--------------|------------------|
| Local | `http://localhost:8000` |
| Fly.io | `https://<app>.fly.dev` |
| Render | `https://<app>.onrender.com` |
| Custom | Set via `KALIBR_BASE_URL` |

---

### 3. Deployment & Runtime Abstraction

Kalibr provides a single CLI entrypoint for local and hosted runtime deployment:

```bash
kalibr serve my_app.py
kalibr deploy my_app.py --runtime fly|render|local
kalibr version
```

Each runtime automatically generates valid schema URLs and deployment bundles (`Dockerfile`, `fly.toml`, etc).

---

### 4. Two Development Modes

#### Simple Mode (Function-Level)
For lightweight APIs and test integrations.

```python
from kalibr import Kalibr

app = Kalibr(title="Weather API")

@app.action("get_weather", "Fetch weather data")
def get_weather(city: str):
    return {"city": city, "temp": 72, "condition": "sunny"}
```

#### Advanced Mode (Full App)

```python
from kalibr import KalibrApp
from kalibr.types import FileUpload, Session

app = KalibrApp(title="Document API")

@app.file_handler("analyze_doc", [".pdf", ".docx"])
async def analyze_doc(file: FileUpload):
    return {"filename": file.filename, "result": "parsed"}

@app.session_action("save_data")
async def save_data(session: Session, data: dict):
    session.set("data", data)
    return {"saved": True}
```

Includes:
- Async/await support  
- File uploads  
- Session persistence  
- Streaming responses  
- Workflow scaffolding  

---

### 5. Built-in Routes

| Endpoint | Purpose |
|-----------|----------|
| `/health` | Health + version check |
| `/docs` | Swagger UI |
| `/models/supported` | Shows model compatibility |
| `/openapi.json`, `/mcp.json`, etc. | Model schemas |

---

### 6. CLI Reference

```
kalibr serve my_app.py        # Run locally
kalibr deploy my_app.py       # Deploy to Fly/Render
kalibr examples               # Copy examples
kalibr version                # Show SDK version
```

---

### 7. Value Proposition

For developers or MCP infrastructure projects:

- **Instant MCP onboarding** — one file → all model schemas  
- **Zero config** — no schema or deployment setup required  
- **Multi-runtime support** — local, Fly, Render, or custom hosts  
- **Unified interface layer** — consistent schema output for all AI platforms  

---

### 8. Upcoming Additions

- Observability + tracing hooks  
- Usage metering and billing  
- Schema diffing / auto-validation  
- Multi-runtime load routing  

---

### License

MIT License © 2025 Kalibr Team  

---

**Kalibr SDK** — the unified layer between AI models and the real world.  
Write once. Deploy anywhere. Integrate everything.
