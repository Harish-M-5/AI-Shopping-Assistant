# 🛒 AI Smart Shopping Assistant

A full-stack demo that recognises products through your camera, checks the packaging for damage, reads
Manufacturing / Expiry dates from the label, and uses generative AI to explain what you are buying.

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite + React Router (plain CSS, responsive, dark-mode aware) |
| Backend | FastAPI (Python) |
| Object detection | YOLOv8 (`ultralytics`) |
| Image processing / damage check | OpenCV |
| OCR | EasyOCR (default) or Tesseract |
| Generative AI | **Any provider**: Gemini, ChatGPT, Claude, Groq, OpenRouter, DeepSeek, Mistral, Ollama (local) or custom – plain HTTPS |
| Storage | None – no database, no IoT, no sensors |

---

# Output:
<img width="1920" height="1080" alt="Screenshot 2026-11-01 192804" src="https://github.com/user-attachments/assets/0e377063-5636-48f2-bda4-5c0c60c69c22" />

<img width="1920" height="1080" alt="Screenshot 2026-11-01 192813" src="https://github.com/user-attachments/assets/bc3b0cba-2a62-4b0d-ac25-1b40d0dc0ceb" />

<img width="1920" height="1080" alt="Screenshot 2026-11-01 192858" src="https://github.com/user-attachments/assets/7329e41e-8ad4-4527-b0f7-922ef33296c5" />



<img width="1920" height="1080" alt="Screenshot 2026-11-01 193000" src="https://github.com/user-attachments/assets/a69426a0-8ae2-4d3d-b2ce-ed5f5ea9fe97" />



<img width="1920" height="1080" alt="Screenshot 2026-11-01 193012" src="https://github.com/user-attachments/assets/16c97510-eb62-4f84-a234-718a552fc843" />




---

## ✨ Features

1. **Live camera detection** – frames are sent to YOLOv8 ~1.5×/second.
2. **Bounding boxes** with product name + confidence (green = OK, red = damaged).
3. **Damage detection (demo level)** – OpenCV heuristics for torn / crushed / dented packaging.
4. **OCR date extraction** – Manufacturing & Expiry dates, with Fresh / Expiring soon / Expired status.
5. **Generative AI insights** – description, main uses, basic nutrition (food only), storage tips, shopping advice.
6. **Pages** – Home, Live Camera Detection, AI Result Panel. Also supports **image upload** for testing without a camera.

## 🧭 How it works

```
 Browser (React)                          FastAPI backend
 ┌────────────────────┐   /api/detect    ┌─────────────────────────────┐
 │ <video> camera     │ ───────────────► │ YOLOv8 → boxes              │
 │ canvas overlay     │ ◄─────────────── │ OpenCV → damage score/crop  │
 │                    │                  └─────────────────────────────┘
 │ [Analyze] button   │   /api/analyze   ┌─────────────────────────────┐
 │ AI Result Panel    │ ───────────────► │ YOLO + damage + OCR + dates │
 │                    │ ◄─────────────── │ → LLM (Claude / OpenAI)     │
 └────────────────────┘                  └─────────────────────────────┘
```

* **`/api/detect`** is lightweight and runs continuously on the live feed.
* **`/api/analyze`** runs once when you press *Analyze product*, using a higher-resolution frame so small
  date text is readable by OCR, then calls the LLM.

## 📁 Project structure

```
smart-shopping-assistant/
├── README.md
├── backend/
│   ├── requirements.txt
│   ├── .env.example               # copy to .env and add your API key
│   ├── app/
│   │   ├── main.py                # FastAPI routes
│   │   ├── config.py              # settings from .env
│   │   ├── schemas.py             # response models
│   │   └── services/
│   │       ├── detector.py        # YOLOv8 wrapper
│   │       ├── damage.py          # OpenCV damage heuristics
│   │       ├── ocr.py             # EasyOCR / Tesseract + preprocessing
│   │       ├── dates.py           # MFD / EXP parser (pure Python)
│   │       └── llm.py             # multi-provider LLM client + offline fallback
│   └── tests/test_dates.py, test_llm.py
├── frontend/
│   ├── package.json
│   ├── vite.config.js             # dev proxy: /api → localhost:8000
│   ├── index.html
│   └── src/
│       ├── main.jsx, App.jsx, api.js, utils.js, styles.css
│       ├── pages/Home.jsx, pages/Detect.jsx
│       └── components/Navbar.jsx, components/ResultPanel.jsx
└── sample_data/
    ├── generate_samples.py        # regenerates the files below
    ├── sample_good_label.jpg      # valid MFD/EXP
    ├── sample_expired_label.jpg   # expired dates
    ├── sample_damaged_box.jpg     # crumpled pack
    └── sample_video.mp4           # moving pack with dates
```

---

## ✅ Prerequisites

* **Python 3.10 – 3.12** (PyTorch support for 3.13 may lag)
* **Node.js 18+** and npm
* A webcam (optional – you can upload images instead)
* ~3 GB free disk (PyTorch + models) and an internet connection for the first run
  (downloads `yolov8n.pt` and EasyOCR models automatically)

## 🚀 Install & run

Open **two terminals**.

### Terminal 1 – Backend

```bash
cd smart-shopping-assistant/backend

# 1) create & activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate           # Windows (PowerShell / cmd)

# 2) install dependencies
pip install --upgrade pip
pip install -r requirements.txt
#   (CPU-only PyTorch, smaller download – optional, run BEFORE the line above:)
#   pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# 3) configure environment (see "Choose your AI provider" below)
cp .env.example .env               # Windows: copy .env.example .env
#   then edit .env and paste your key

# 4) start the API  →  http://127.0.0.1:8000  (interactive docs at /docs)
uvicorn app.main:app --reload --port 8000
```

### Terminal 2 – Frontend

```bash
cd smart-shopping-assistant/frontend
npm install
npm run dev                        # → http://localhost:5173
```

Open **http://localhost:5173**, go to **Live Detection**, click **Start camera** and allow permission.

> The camera API only works on `http://localhost` or HTTPS. Use `localhost`, not your LAN IP.

### Production build (optional)

```bash
cd frontend && npm run build       # outputs frontend/dist
# Serve dist/ with any static host and set VITE_API_URL to your backend URL before building.
# Add that host to CORS_ORIGINS in backend/.env.
```

### Run tests

```bash
cd backend && pytest -q            # date-parser + LLM provider tests (no network needed)
```

---

## 🔑 Choose your AI provider (any API works)

You are **not tied to Claude**. Set `LLM_PROVIDER` and `LLM_API_KEY` in `backend/.env`, then **restart the backend**.
The app also runs with no key at all (the AI panel shows basic offline text).

| `LLM_PROVIDER` | Service | Get a key at | Default model |
|---|---|---|---|
| `gemini` | Google Gemini | https://aistudio.google.com/apikey | `gemini-2.5-flash` |
| `openai` | ChatGPT / OpenAI | https://platform.openai.com/api-keys | `gpt-4o-mini` |
| `anthropic` | Claude | https://console.anthropic.com → API Keys | `claude-sonnet-5-5` |
| `groq` | Groq (Llama, fast) | https://console.groq.com/keys | `llama-3.3-70b-versatile` |
| `openrouter` | OpenRouter (many models) | https://openrouter.ai/keys | `openai/gpt-4o-mini` |
| `deepseek` | DeepSeek | https://platform.deepseek.com | `deepseek-chat` |
| `mistral` | Mistral | https://console.mistral.ai | `mistral-small-latest` |
| `ollama` | Local models – **no key, no cost** | https://ollama.com | `llama3.2` |
| `custom` | Any OpenAI-compatible server (LM Studio, vLLM…) | – | set `LLM_MODEL` + `LLM_BASE_URL` |

Several of these (Gemini, Groq, OpenRouter) offer a free tier, and Ollama runs fully on your PC – check each
provider's current limits. Billing is separate from any chat subscription (e.g. a ChatGPT or claude.ai plan does
not include API credits).

### Examples (`backend/.env`)

```env
# Google Gemini (easy to start with)
LLM_PROVIDER=gemini
LLM_API_KEY=AIza...

# ChatGPT
LLM_PROVIDER=openai
LLM_API_KEY=sk-...

# Claude
LLM_PROVIDER=anthropic
LLM_API_KEY=sk-ant-...

# Free local model with Ollama (run once:  ollama pull llama3.2)
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2

# Any other OpenAI-compatible server
LLM_PROVIDER=custom
LLM_BASE_URL=http://localhost:1234/v1
LLM_MODEL=your-model-name
LLM_API_KEY=optional
```

Optional: `LLM_MODEL` overrides the default model. Provider-specific names (`GEMINI_API_KEY`, `OPENAI_API_KEY`,
`ANTHROPIC_API_KEY`, `GROQ_API_KEY`…) also work if you prefer them over `LLM_API_KEY`.

Verify at `http://127.0.0.1:8000/api/health` – you should see your provider, model and `"llm_configured": true`.
After analysing a product, the result panel shows "AI by <provider> · <model>".

**Adding another provider** = one new entry in `PRESETS` in `backend/app/services/llm.py` (three wire formats are
built in: `openai`, `anthropic`, `gemini`).

🔒 **Security:** the key lives only in `backend/.env` on the server. Never put it in the React code and never commit
`.env` (already in `.gitignore`). Identical requests are cached in memory to save API calls.

---

## ⚙️ Configuration reference (`backend/.env`)

| Variable | Default | Meaning |
|---|---|---|
| `LLM_PROVIDER` | `gemini` | See provider table above |
| `LLM_API_KEY` | – | Your secret key (not needed for `ollama`) |
| `LLM_MODEL` | provider default | Override the model name |
| `LLM_BASE_URL` | provider default | Required only for `custom` |
| `YOLO_MODEL` | `yolov8n.pt` | Weights file. `yolov8s.pt` = more accurate, slower; or your custom `best.pt` |
| `YOLO_CONF` | `0.35` | Minimum detection confidence |
| `YOLO_IMGSZ` | `640` | Inference image size |
| `OCR_ENGINE` | `easyocr` | `easyocr` or `tesseract` |
| `OCR_LANGS` | `en` | EasyOCR languages, comma-separated |
| `USE_GPU` | `false` | Use CUDA for EasyOCR |
| `TESSERACT_CMD` | – | Path to the Tesseract binary (Windows) |
| `CORS_ORIGINS` | localhost:5173 | Allowed frontend origins |

To use **Tesseract**: install the binary (`sudo apt install tesseract-ocr`, `brew install tesseract`, or the
Windows installer), `pip install pytesseract`, and set `OCR_ENGINE=tesseract`.

---

## 🧪 Sample images & video

Located in `sample_data/` (regenerate with `python generate_samples.py`):

| File | What to test |
|---|---|
| `sample_good_label.jpg` | OCR → MFD 12 Mar 2026, EXP 11 Mar 2027 → *Fresh*; packaging OK |
| `sample_expired_label.jpg` | OCR → dates in 2024 → *Expired* badge; AI advises not to buy |
| `sample_damaged_box.jpg` | Damage check → *Damaged* with reasons |
| `sample_video.mp4` | Play full-screen on another device/monitor and point your webcam at it |

**How to test:** Live Detection → **Upload image** → pick a sample → type a product name (e.g. “Snack chips”)
→ **Analyze product**.

> ⚠️ The samples are cartoon packs made for testing OCR and damage logic. The default COCO-trained YOLO
> will *not* label them as products (type a name manually). To see YOLO boxes, use your webcam with real
> objects such as a bottle, cup, banana, apple, orange, or a phone photo.

---

## 🔍 Technical notes

**Detection.** The default `yolov8n.pt` knows 80 COCO classes (bottle, cup, banana, apple, sandwich, cake…).
For packaged groceries (chips, biscuits, cereal…), fine-tune YOLOv8 on a grocery dataset (e.g. from Roboflow
Universe) and set `YOLO_MODEL=./models/best.pt`. If you add classes named like `damaged_box` or `torn_packet`,
the backend flags them automatically.

**Damage detection (demo level).** On the cropped product: edge density (crumpled texture), solidity
(area ÷ convex hull, catches dents/tears) and Laplacian variance (creases). The weighted score ≥ 0.5 flags damage.
Thresholds are tuned on the synthetic samples; **real-world lighting and printed artwork will vary**, so treat
it as a demonstration, not quality control. Thresholds live at the top of `services/damage.py`.

**OCR dates.** Understands `MFD/MFG/PKD/Packed on/Manufactured` and `EXP/Use by/Best before` plus formats like
`12/03/2026`, `12-03-26`, `12 MAR 2026`, `12MAR26`, `MAR 2026`, `03/2026` and “best before 6 months”. Day-first
order (DD/MM) is assumed. If no keywords exist, the earlier date is treated as manufacturing and the later as
expiry. Tips for better OCR: good light, hold steady, fill the frame with the date area, avoid glare.

**API reference** (full docs at `http://127.0.0.1:8000/docs`)

| Method | Path | Body | Returns |
|---|---|---|---|
| GET | `/api/health` | – | status + config summary |
| POST | `/api/detect` | multipart `file` (image) | detections (normalised boxes, confidence, damage) |
| POST | `/api/analyze` | `file`, optional `product_name`, `bbox`, `confidence` | product, damage, dates, AI content |

## 🛠 Troubleshooting

| Problem | Fix |
|---|---|
| “Backend is offline” banner | Start uvicorn on port 8000; check `/api/health` |
| Camera does not start | Allow permission; use `localhost` or HTTPS; close other apps using the camera |
| First request is very slow | Models are downloading/loading once (YOLO + EasyOCR) – wait, then it is fast |
| “No AI provider key configured” | Set `LLM_PROVIDER` + `LLM_API_KEY` in `backend/.env`, restart the backend |
| AI service error 401 / 403 | Key is wrong, doesn't match `LLM_PROVIDER`, or billing/quota not enabled |
| AI service error 404 | Model name not available to your account – set `LLM_MODEL` |
| AI service error 429 | Free-tier rate limit hit – wait a minute or switch provider |
| Ollama: connection refused | Start Ollama (`ollama serve`) and run `ollama pull llama3.2` |
| Dates not found | Move closer, improve lighting, try `sample_good_label.jpg` to confirm setup |
| `pip` fails on PyTorch | Use Python 3.10–3.12 and the CPU wheel command above |

## ⚠️ Disclaimer

Educational demo. AI-generated nutrition and storage information is approximate; always follow the product
label. Damage and expiry checks are aids, not guarantees of product safety.
