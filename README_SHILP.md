# 🏛️ SHILP AI — Prototype Runbook

Architecture implemented exactly as specified:

```
Artisan PWA (kalakart-frontend/) → FastAPI :8000 → Vision / Voice / Pricing / 5-Marketplace
```

## 1. Start backend
```powershell
cd "D:\Sentinal Chain AI\backend"
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

## 2. Start frontend (PWA dual-screen simulator)
```powershell
cd "D:\Sentinal Chain AI\kalakart-frontend"
python -m http.server 8080
# open http://127.0.0.1:8080
```

Or double-click `run_prototype.bat`.

## 2b. Go LIVE (free, one service)
The backend serves the frontend too, so one URL runs everything:
1. Push this folder to GitHub (`Sentinal Chain AI` → repo root must contain `render.yaml`, `backend/`, `kalakart-frontend/`).
2. On [render.com](https://render.com) → New → Blueprint → pick the repo. It reads `render.yaml` and deploys.
3. Open the `https://kalakart-ai.onrender.com` URL — the app auto-points its API at the same origin. No config needed. (Free tier sleeps after 15 min idle; first load takes ~1 min. DB re-seeds on restart.)
Alternative: Vercel/Netlify for `kalakart-frontend/` + Render for `backend/` — then set the gateway URL in the app's Settings tab.

## 3. Endpoints
| Method | URL | Purpose |
|---|---|---|
| GET | `/api/v1/health` | gateway check |
| POST multipart | `/api/v1/media/process-raw` | file + product_name, craft_type, material, location, story_text, language, artisan → 1080p MoSJE JPEG + listing |
| POST JSON | `/api/v1/pricing/bargain-shield` | material_cost, labour_hours, wage_per_hour, overhead_pct, profit_pct, buyer_offer → floor/suggested/verdict |
| POST JSON | `/api/v1/assistant/shilpi` | query, lang → answer + gTTS mp3 (Groq live if GROQ_API_KEY set) |
| POST JSON | `/api/v1/channels/publish-multi` | product_name, craft_type, price_inr, description, tags, location → Amazon ASIN, Flipkart FSN, GeM, Etsy USD, ONDC Beckn |

## 4. Live upgrades
- `rembg` true cutout is OPT-IN (first run downloads ~170MB and hangs offline): `$env:SHILP_REMBG="1"` then restart backend. Default is instant passthrough + 1080p seal.
- `gTTS` → `pip install gtts` for Hindi voice replies.
- Groq Llama-3 → set `$env:GROQ_API_KEY="..."` and restart backend.

## 5. Demo flow (2 min)
1. Click **Banarasi / Pottery / Dokra preset** → form autofills.
2. **Upload / Live Camera snap** + **Speak story** (Web Speech API).
3. **Generate AI Listing** → Vision Studio 1080p + MoSJE seal appears in Screen 2 + hero preview.
4. **Check Price** → सौदा रक्षक verdict (Hindi + English) with wage floor.
5. **Publish 5×** → ASIN/FSN/GeM/Etsy$/Beckn cards.
6. **Shilpi modal** → voice Q&A (PM Vishwakarma, GeM, ONDC…).
