# llm-only

### 🧠 Conditionally serve content only to AI crawlers (LLMs) using Python.

This lightweight library detects LLM user agents and allows you to render or expose certain HTML blocks exclusively for them.

---

## ⚙️ Installation

```bash
pip install llm-only
```

---

## 🚀 Usage (FastAPI)

```python
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from llm_only.fastapi_middleware import LLMOnlyMiddleware

app = FastAPI()
app.add_middleware(LLMOnlyMiddleware)

@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    if request.state.is_llm:
        return "<h1>Pricing: 50 credits for $100/mo</h1>"
    return "<h1>Your React slider here</h1>"
```

---

## 🧩 Usage (Flask)

```python
from flask import Flask
from llm_only.flask_decorator import llm_only

app = Flask(__name__)

@app.route("/")
def homepage():
    @llm_only
    def llm_content():
        return "<h3>Pricing: 50 credits for $100/mo</h3>"

    html = f"""
    <html><body>
        <div id='ui'>[React slider here]</div>
        {llm_content()}
    </body></html>
    """
    return html
```

---

## 📜 License

MIT License © Amal Alexander
