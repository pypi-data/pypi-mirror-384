# Kalibr SDK

**Multi-Model AI Integration Framework**

Write once. Deploy anywhere. Connect to any AI model.

Kalibr lets you expose Python functions as APIs that work with **GPT, Claude, Gemini, and Copilot** automatically.

[![PyPI version](https://badge.fury.io/py/kalibr.svg)](https://badge.fury.io/py/kalibr)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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

### 4. See Multi-Model Schemas

Open your browser to see all 4 AI model schemas auto-generated:

```
http://localhost:8000/                    # API info
http://localhost:8000/gpt-actions.json    # For ChatGPT
http://localhost:8000/mcp.json            # For Claude
http://localhost:8000/schemas/gemini      # For Gemini
http://localhost:8000/schemas/copilot     # For Copilot
http://localhost:8000/docs                # Interactive docs
```

**That's it!** One Python file, four AI platform schemas. 🎯

---

## 🎯 What Does This Do?

Kalibr turns your Python functions into APIs that AI assistants can call:

```python
from kalibr import Kalibr

app = Kalibr(title="My Business API")

@app.action("get_inventory", "Check product stock")
def get_inventory(product_id: str):
    # Your business logic
    return {"product_id": product_id, "stock": 42}
```

**Result:** ChatGPT, Claude, Gemini, and Copilot can all call your `get_inventory` function!

---

## 💪 Two Modes

### Function-Level (Simple)
Perfect for exposing business logic:

```python
from kalibr import Kalibr

app = Kalibr(title="My API")

@app.action("calculate_price", "Calculate product price")
def calculate_price(product_id: str, quantity: int):
    return {"total": quantity * get_price(product_id)}
```

### App-Level (Advanced)
Full framework with file uploads, sessions, streaming, workflows:

```python
from kalibr import KalibrApp
from kalibr.types import FileUpload, Session

app = KalibrApp(title="Advanced API")

@app.file_handler("analyze_doc", [".pdf", ".docx"])
async def analyze_doc(file: FileUpload):
    return {"filename": file.filename, "analysis": "..."}

@app.session_action("save_data", "Save to session")
async def save_data(session: Session, data: dict):
    session.set("my_data", data)
    return {"saved": True}

@app.stream_action("live_feed", "Stream real-time data")
async def live_feed(count: int = 10):
    for i in range(count):
        yield {"item": i, "timestamp": "..."}
```

---

## 📚 Examples Included

After running `kalibr-connect examples`, you get:

- **`basic_kalibr_example.py`** - Simple function-level example
- **`enhanced_kalibr_example.py`** - Advanced app-level example with all features

---

## 🤖 AI Platform Integration

Once your Kalibr app is running, integrate with AI platforms:

### ChatGPT (GPT Actions)
1. Copy schema from `http://localhost:8000/gpt-actions.json`
2. Go to GPT Builder → Actions → Import from URL
3. Done! ChatGPT can now call your functions

### Claude (MCP)
1. Add to Claude Desktop config:
```json
{
  "mcp": {
    "servers": {
      "my-api": {
        "url": "http://localhost:8000/mcp.json"
      }
    }
  }
}
```
2. Done! Claude can now call your functions

### Gemini & Copilot
Similar simple setup using their respective schema endpoints.

---

## 🎯 Use Cases

- **Customer Service APIs** - Let AI assistants look up orders, process refunds
- **Data Analysis APIs** - Let AI query your analytics and generate insights
- **Document Processing** - Let AI analyze uploaded documents
- **Business Automation** - Let AI trigger workflows in your systems
- **Internal Tools** - Give your team AI-powered access to internal systems

---

## 📖 Documentation

- **Quick Start**: You're reading it!
- **Full Docs**: See `KALIBR_SDK_COMPLETE.md` in the package
- **Examples**: Run `kalibr-connect examples`
- **CLI Help**: `kalibr-connect --help`

---

## 🔧 CLI Commands

```bash
kalibr-connect examples          # Copy example files to current dir
kalibr-connect serve my_app.py   # Run your app locally
kalibr-connect version           # Show version info
kalibr-connect --help            # Show all commands
```

---

## ⚡ Key Features

- ✅ **Multi-Model Support** - Works with GPT, Claude, Gemini, Copilot
- ✅ **Automatic Schemas** - No manual schema writing
- ✅ **File Uploads** - Handle document uploads
- ✅ **Sessions** - Stateful conversations
- ✅ **Streaming** - Real-time data streaming
- ✅ **Workflows** - Multi-step processes
- ✅ **Type Safe** - Full Python type hints
- ✅ **Fast** - Async/await support

---

## 🔥 Why Kalibr?

**Without Kalibr:**
- Learn 4 different API specs
- Write 4 different schemas
- Maintain 4 codebases
- = Weeks of work

**With Kalibr:**
- Write Python functions once
- Kalibr generates all 4 schemas
- Single codebase
- = One day of work

---

## 💡 Simple Example

```python
# my_app.py
from kalibr import Kalibr

app = Kalibr(title="Weather API")

@app.action("get_weather", "Get current weather")
def get_weather(city: str):
    # Your logic here
    return {"city": city, "temp": 72, "condition": "sunny"}
```

```bash
# Run it
kalibr-connect serve my_app.py

# Now ALL these work:
# ✅ ChatGPT can call get_weather()
# ✅ Claude can call get_weather()
# ✅ Gemini can call get_weather()
# ✅ Copilot can call get_weather()
```

---

## 🚀 Get Started Now

```bash
pip install kalibr
kalibr-connect examples
kalibr-connect serve kalibr_examples/basic_kalibr_example.py
```

Open http://localhost:8000 and see your multi-model API in action! 🎯

---

## 📝 License

MIT License - see LICENSE file for details.

---

**Kalibr SDK** - Transform how you build AI-integrated applications! 🚀
