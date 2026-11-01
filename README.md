# 🛒 AI Shopping Assistant

A full-stack demo that recognises products through your camera, checks the packaging for damage, reads
Manufacturing / Expiry dates from the label, and uses generative AI to explain what you are buying.


---

## 📌 Overview

When I shop, I often wonder: *Is this packet damaged? When does it expire? What is this product actually used for?* Expiry dates are printed in tiny text, and it is easy to miss them.

So I built an assistant that does this in one camera scan:

1. Detects the product live using **YOLOv8**
2. Checks the packaging for damage using **OpenCV**
3. Reads manufacturing and expiry dates using **OCR**
4. Generates a description, uses, nutrition, storage tips, and shopping advice using an **LLM API (Groq)**

There is no database and no IoT or sensors. Everything runs from the camera image.

---

## ✨ Features

- Live camera product detection with bounding boxes, product name, and confidence score
- Damage detection for torn packets, crushed boxes, and dented packaging (demo level)
- Manufacturing and expiry date extraction with a Fresh / Expiring soon / Expired status
- AI-generated description, main uses, basic nutrition, storage tips, and short shopping advice
- Image upload mode, so you can test without a camera
- Manual product name box, for items the default YOLO model does not know
- Works with many LLM providers (Groq, Gemini, OpenAI, Claude, Ollama, and more) by changing one config file
- Responsive UI that works on laptop and phone screens

---

## 🎯 Use Case: Problem This Solves

| Problem in real life | How this project helps |
|---|---|
| Packaging damage is easy to miss | Camera scan flags visible damage |
| Expiry dates are tiny and hard to read | OCR reads them and shows the status |
| People do not know how to store or use a product | AI gives uses, storage tips, and nutrition |
| Hard to decide whether to buy | AI gives a short shopping advice |

It can especially help elderly people, people with weak eyesight, and anyone buying in bulk.

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, React Router, plain CSS |
| Backend | FastAPI (Python) |
| Object detection | YOLOv8 (Ultralytics) |
| Image processing | OpenCV |
| OCR | EasyOCR (Tesseract optional) |
| Generative AI | Groq API (also supports Gemini, OpenAI, Claude, Ollama, and OpenAI-compatible servers) |
| Database | None |

---

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
#   then edit .env and past use your key

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


--- 



## 🔄 How It Works

```
Camera (React)  ──frame──►  FastAPI backend
                              │
                              ├─ YOLOv8   → product name + bounding box
                              ├─ OpenCV   → damage score
                              ├─ EasyOCR  → text → date parser → MFD / EXP / status
                              └─ LLM API  → description, uses, nutrition, tips, advice
                              │
Result Panel (React) ◄────────┘
```

- The live view sends a small frame about every 0.6 seconds to `/api/detect` for fast boxes.
- When I press **Analyze product**, a higher resolution frame goes to `/api/analyze`, which runs damage check, OCR, and the LLM.

---

## 📁 Project Folder

```
smart-shopping-assistant/
├── README.md
├── backend/
│   ├── requirements.txt
│   ├── .env.example            # copy to .env and add your key
│   ├── app/
│   │   ├── main.py             # FastAPI routes
│   │   ├── config.py           # reads settings from .env
│   │   ├── schemas.py          # response models
│   │   └── services/
│   │       ├── detector.py     # YOLOv8 wrapper
│   │       ├── damage.py       # OpenCV damage heuristics
│   │       ├── ocr.py          # EasyOCR + image preprocessing
│   │       ├── dates.py        # MFD / EXP date parser
│   │       └── llm.py          # multi-provider LLM client
│   └── tests/                  # unit tests
├── frontend/
│   ├── package.json
│   ├── vite.config.js          # proxies /api to the backend
│   └── src/
│       ├── main.jsx, App.jsx, api.js, utils.js, styles.css
│       ├── pages/              # Home.jsx, Detect.jsx
│       └── components/         # Navbar.jsx, ResultPanel.jsx
└── sample_data/                # test images and video
```

---


## ▶️ How to Run the Full Project

Open **two terminals**.

**Terminal 1: Backend**
```powershell
cd backend
.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --port 8000
```
Check `http://127.0.0.1:8000/api/health`. You should see your provider, your model, and `"llm_configured": true`.

**Terminal 2: Frontend**
```bash
cd frontend
npm run dev
```
Open **http://localhost:5173**.

**Using the app**
1. Go to **Live Detection** and click **Start camera** (allow permission), or **Upload image**.
2. Pick the detected product, or type a product name in the manual box.
3. Click **Analyze product**.
4. Read the result panel.

Test files are in `sample_data/` (good label, expired label, damaged box, and a video).

> The first request is slow because the models load once. After that it is fast.
> Important: after changing `.env`, always restart the backend.

---

## 🔌 How the Frontend Calls the Backend APIs

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Backend status and LLM config check |
| POST | `/api/detect` | YOLO detection and damage check for one frame |
| POST | `/api/analyze` | Full analysis: damage, OCR dates, and AI insights |

In development, Vite proxies `/api/*` to `http://127.0.0.1:8000`, so I did not need to fight CORS.

**Frontend call (`src/api.js`):**
```javascript
const form = new FormData();
form.append("file", blob, "frame.jpg");
const res = await fetch("/api/detect", { method: "POST", body: form });
const data = await res.json();
```

**Test from the terminal:**
```bash
curl -X POST http://127.0.0.1:8000/api/detect -F "file=@sample_data/sample_good_label.jpg"

curl -X POST http://127.0.0.1:8000/api/analyze \
  -F "file=@sample_data/sample_good_label.jpg" \
  -F "product_name=Snack chips"
```
On Windows PowerShell, use `curl.exe` instead of `curl`. You can also try every endpoint at `http://127.0.0.1:8000/docs`.

**Sample `/api/analyze` response (shortened):**
```json
{
  "product": { "name": "Snack chips", "confidence": null },
  "damage": { "is_damaged": false, "score": 0.09, "reasons": [] },
  "dates": {
    "manufacturing_date": "2026-03-12",
    "expiry_date": "2027-03-11",
    "status": "ok",
    "days_left": 130
  },
  "ai": {
    "description": "...",
    "main_uses": ["..."],
    "nutrition": null,
    "storage_tips": ["..."],
    "shopping_advice": "..."
  }
}
```
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

---



---

## 🛠️ Configuration

All settings are in `backend/.env`.

| Variable | Default | Meaning |
|---|---|---|
| `LLM_PROVIDER` | `gemini` | `gemini`, `openai`, `anthropic`, `groq`, `openrouter`, `deepseek`, `mistral`, `ollama`, `custom` |
| `LLM_API_KEY` | none | Your secret API key (not needed for `ollama`) |
| `LLM_MODEL` | provider default | Model name override |
| `LLM_BASE_URL` | provider default | Only needed for `custom` servers |
| `YOLO_MODEL` | `yolov8n.pt` | YOLO weights file (use your own `best.pt` for custom training) |
| `YOLO_CONF` | `0.35` | Minimum detection confidence |
| `OCR_ENGINE` | `easyocr` | `easyocr` or `tesseract` |
| `CORS_ORIGINS` | localhost:5173 | Allowed frontend origins |

---

## 🔤 OCR Explained

OCR (Optical Character Recognition) converts text in an image into real text the program can read.

My pipeline:
1. **EasyOCR** reads all text in the frame.
2. If no date is found, I **pre-process the image** (grayscale, contrast boost with CLAHE, sharpening) and try again.
3. A custom **date parser** (`dates.py`) finds the dates in that text.

The parser understands keywords like `MFD`, `MFG`, `PKD`, `EXP`, `Use by`, and `Best before`, and formats like `12/03/2026`, `12-03-26`, `12 MAR 2026`, and `MAR 2026`. It assumes day-first dates. If there are no keywords, the earlier date is treated as the manufacturing date and the later one as the expiry date.

Then it calculates the status: **Fresh**, **Expiring soon** (30 days or less), or **Expired**.

OCR accuracy depends on light, focus, and print quality, so glare and blur reduce results.

---

## 👁️ Computer Vision: YOLO and OpenCV Explained

### YOLOv8 (object detection)
YOLO ("You Only Look Once") finds objects in an image in one pass and returns a box, a class name, and a confidence score. I used the small `yolov8n.pt` model for speed on a normal laptop CPU.

The default model is trained on 80 everyday COCO classes (bottle, cup, banana, book, person...). It does **not** know packaged grocery brands. For that, the model needs to be fine-tuned on a grocery dataset. I added a manual product name box as a workaround.

### OpenCV (damage detection, demo level)
For the cropped product region, I calculate three signals:
- **Edge density**: crumpled or torn surfaces have many irregular edges
- **Solidity**: area divided by convex hull area; dents and tears make the outline irregular
- **Laplacian variance**: creases and cracks increase texture energy

These are combined into a score from 0 to 1, and a score of 0.5 or higher is flagged as damaged. I tuned the thresholds using synthetic test images, so real-world results can vary. A properly trained model would be more accurate.

---

## 🤖 Generative AI: LLM API (Groq) Explained

After vision and OCR, the app sends a short JSON message to an LLM containing the product name, the damage result, and the date status. A system prompt forces the model to reply only in JSON with these keys: `description`, `main_uses`, `nutrition`, `storage_tips`, `shopping_advice`.

**Why Groq?** Groq hosts open models behind an OpenAI-compatible API, it is fast, and it has a free tier (limits can change).

**What I built around it:**
- One `llm.py` file supports three API formats (OpenAI-style, Anthropic, Gemini), so many providers work just by changing `LLM_PROVIDER`
- JSON cleaning, in case the model wraps the answer in markdown
- A small in-memory cache, to save API calls (no database)
- An offline fallback message, so the UI still works when the API fails
- Clear error messages shown in the result panel (401, 404, 429)

**Important lesson:** the AI only receives the product *name*, not the image. So for a generic label like "book" it can invent details. For better answers, type a specific product name in the manual box.

---

## 💡 Key Concepts

- Full-stack architecture (React frontend and FastAPI backend)
- REST APIs with multipart file upload
- Real-time inference from a browser camera (`getUserMedia`, canvas capture)
- Object detection and bounding boxes with normalised coordinates
- Classical image processing with OpenCV
- OCR and rule-based text parsing with regex
- Prompt engineering for structured JSON output
- Provider-agnostic design using configuration
- Environment variables and secret management
- Fallbacks and graceful error handling

---

## 🧩 Problems I Faced and How I Solved Them

| Problem | Cause | How I solved it |
|---|---|---|
| `source .venv/bin/activate` failed on Windows | That command is for Linux/macOS | Used `.venv\Scripts\Activate.ps1` |
| `uvicorn` not recognized | Install did not complete or the venv was not active | Created a fresh venv and ran `python -m uvicorn ...` |
| Heavy install errors | Python 3.14 was too new for PyTorch | Used Python 3.12 |
| Slow install and sync issues | Project was inside OneDrive | Moved it to a normal folder |
| `cp .env.example .env` error | `.env` already existed | Used `Copy-Item ... -Force` |
| "No AI provider key configured" | Backend had not reloaded `.env` | Restarted the backend after every `.env` change |
| `401 Invalid API Key` | An old backend process was still running on port 8000 | Verified the key directly with Groq (status 200), killed the old process, restarted |
| `404 model_not_found` | The default Groq model was no longer available | Set `LLM_MODEL=openai/gpt-oss-20b` in `.env` |
| AI invented book details | The LLM only got the name "book" | Used manual product names for better answers |
| Dates not found | Book has no date, and lighting was poor | Tested with clear labels and good light |
| API keys exposed in screenshots | I shared `.env` in photos | Revoked the keys and created new ones. Now I always mask secrets. |

---

## 👥 Ideal For

- College students learning AI and full-stack development
- Beginners who want a project that combines computer vision, OCR, and LLMs
- Mini-project and final-year project demos
- Developers who want a starter template with a swappable LLM provider

---

## 📚 Learning Outcomes

- How to connect a React frontend to a Python backend
- How YOLO detection works and where its limits are
- How to do basic image analysis with OpenCV
- How OCR works and why pre-processing matters
- How to use LLM APIs, handle errors, and design prompts
- How to read error messages and debug step by step
- Why secrets must never be shared or committed
- That AI output can sound confident and still be wrong, so it must be verified

---

## 🚀 Future Improvements

- Fine-tune YOLO on a grocery product dataset
- Train a dedicated damage detection model
- Barcode and QR scanning for exact product lookup
- Send the image itself to a vision-capable LLM for better descriptions
- Price comparison and shopping list
- Multi-language support, including Tamil
- Mobile app version
- Save scan history (needs a database)

---

## 🙏 Acknowledgments

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) for object detection
- [OpenCV](https://opencv.org/) for image processing
- [EasyOCR](https://github.com/JaidedAI/EasyOCR) for text recognition
- [FastAPI](https://fastapi.tiangolo.com/) and [React](https://react.dev/) / [Vite](https://vitejs.dev/)
- [Groq](https://groq.com/), plus Google, OpenAI, and Anthropic for LLM APIs
- An AI assistant (Claude) helped me with code guidance and debugging while I built and tested the project
- My college faculty and friends for feedback

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



## ✅ Conclusion

This project taught me that building with AI is not only about calling models. It is about connecting many parts (detection, OCR, rules, an LLM, and a UI), handling errors, and being honest about limitations. It is still a prototype, but it solves a real everyday problem and gave me hands-on experience with a full AI application from camera to result.

If you try it or have suggestions, I would love your feedback.

> **Disclaimer:** This is an educational project. AI-generated nutrition and storage information is approximate, so always follow the product label. Damage and expiry checks are aids, not guarantees of product safety.

---

## 👤 Author

Harish M
email - harishmurugan005arni@gmail.com

---






