# Kalibr SDK  
### Multi-Model AI Integration Framework

**Write once. Deploy anywhere. Connect to any AI model.**

Kalibr turns Python functions into APIs that work seamlessly with GPT, Claude, Gemini, and Copilot — automatically generating model-specific schemas and endpoints.

---

## 🚀 Quick Start (2 minutes)

### 1. Install
```bash
pip install kalibr
```

### 2. Get Examples
```bash
kalibr-connect examples
```
This copies example files to `./kalibr_examples/` in your current directory.

### 3. Run Demo
```bash
kalibr-connect serve kalibr_examples/basic_kalibr_example.py
```

### 4. See All Schemas
Kalibr now **auto-detects your environment** and generates the correct base URLs.

| Environment | Example Base URL |
|--------------|------------------|
| Local Dev | `http://localhost:8000` |
| Fly.io | `https://<app-name>.fly.dev` |
| Custom Host | Use `KALIBR_BASE_URL` env var |

Then open:
```
<your-base-url>/gpt-actions.json    # ChatGPT
<your-base-url>/mcp.json            # Claude
<your-base-url>/schemas/gemini      # Gemini
<your-base-url>/schemas/copilot     # Copilot
```

---

## 🧠 What Kalibr Does

Kalibr turns your Python functions into production-ready multi-model APIs.

```python
from kalibr import Kalibr

app = Kalibr(title="Inventory API")

@app.action("get_inventory", "Fetch inventory data")
def get_inventory(product_id: str):
    return {"product_id": product_id, "stock": 42}
```

Result:  
ChatGPT, Claude, Gemini, and Copilot can all call `get_inventory()` using their native protocols — no schema work required.

---

## 💪 Two Modes

### **Function-Level (Simple)**
Ideal for one-off APIs or scripts.

```python
from kalibr import Kalibr

app = Kalibr(title="My API")

@app.action("calculate_price", "Calculate price total")
def calculate_price(product_id: str, quantity: int):
    return {"total": quantity * 19.99}
```

### **App-Level (Advanced)**
Use `KalibrApp` for complete control — file uploads, sessions, streaming, and workflows.

```python
from kalibr import KalibrApp
from kalibr.types import FileUpload, Session

app = KalibrApp(title="Advanced API")

@app.file_handler("analyze_doc", [".pdf", ".docx"])
async def analyze_doc(file: FileUpload):
    return {"filename": file.filename, "analysis": "..."}

@app.session_action("save_data", "Save session data")
async def save_data(session: Session, data: dict):
    session.set("my_data", data)
    return {"saved": True}
```

---

## 📚 Examples Included

After running `kalibr-connect examples`, you’ll get:

- `basic_kalibr_example.py` – simple function-level demo  
- `enhanced_kalibr_example.py` – full app with sessions, uploads, and streaming  

---

## 🤖 AI Platform Integration

### ChatGPT (GPT Actions)
1. Copy schema URL:  
   `https://<your-domain>/gpt-actions.json`
2. In GPT Builder → *Actions* → *Import from URL*
3. Done — ChatGPT can call your endpoints.

### Claude (MCP)
Add to Claude Desktop config:
```json
{
  "mcp": {
    "servers": {
      "my-api": {
        "url": "https://<your-domain>/mcp.json"
      }
    }
  }
}
```

### Gemini / Copilot
Use:
```
https://<your-domain>/schemas/gemini
https://<your-domain>/schemas/copilot
```

---

## 🎯 Common Use Cases

- **Customer Service APIs** — let AI handle orders or refunds  
- **Data Analysis** — query your analytics through AI  
- **Document Processing** — parse or summarize uploaded docs  
- **Business Automation** — trigger internal workflows  
- **Internal Tools** — expose secure internal logic to assistants  

---

## 🔧 CLI Reference

```bash
kalibr-connect examples          # Copy examples
kalibr-connect serve my_app.py   # Run locally
kalibr-connect version           # Show version
kalibr-connect --help            # Full CLI
```

---

## ⚡ Key Features

✅ Multi-Model Support — GPT, Claude, Gemini, Copilot  
✅ Automatic Schema Generation  
✅ Environment-Aware Base URLs (v1.0.21+)  
✅ File Uploads  
✅ Session Management  
✅ Streaming Responses  
✅ Workflow Support  
✅ Type-Safe API Generation  
✅ Async / Await Ready  

---

## 🔥 Why Kalibr?

Without Kalibr:
- Learn 4 model specs  
- Maintain 4 codebases  
- Duplicate effort  

With Kalibr:
- One Python function  
- Four schemas generated automatically  
- Deploy anywhere  

---

## 🆕 Version 1.0.21+

- **Automatic Base-URL Detection**  
  - Works with `KALIBR_BASE_URL` or `FLY_APP_NAME`  
  - Fixes all localhost references in deployed schemas  
- Ready for **MCP ecosystem production use**  
- Drop-in backwards compatibility  

---

## 🧩 License

MIT License — see `LICENSE` file for details.  

---

**Kalibr SDK — the unified layer between AI models and the real world.**  
Write once. Deploy anywhere. Integrate everything.
