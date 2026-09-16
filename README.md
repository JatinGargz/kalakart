# 🏛️ KALAKART (कलाकार्ट) / SHILP AI
### AI-Powered Digital Marketplace & Business Manager for Indian Artisans | SIH 2026

[![Deploy to Koyeb](https://www.koyeb.com/static/images/deploy/button.svg)](https://app.koyeb.com/deploy?type=git&repository=github.com/JatinGargz/kalakart&name=kalakart&ports=8000;http;/)

A unified, voice-first digital marketplace and enterprise AI copilot designed for Indian master artisans, handloom weavers, and craft clusters under **PM Vishwakarma** and **PM-DAKSH**.

---

## 🌟 Key Features

1. **🤖 Random Forest Fair Pricing ML Engine**:
   - 300-estimator Scikit-Learn model calculating living wage floors (MoSJE ₹100/hr mandate), raw material costs, and retail/B2B margins.
2. **🛡️ Anti-Bargaining Shield ("सौदा रक्षक")**:
   - Evaluates buyer and tourist discount offers in real-time, flashing protection against exploitative rates and generating polite, firm Hindi counter-dialogue.
3. **📸 Vision Studio 1080p Canvas & MoSJE Digital Authenticity Seal**:
   - Upgrades raw mobile workshop photos into 1080x1080px e-commerce assets watermarked with the official Ministry of Social Justice & Empowerment seal.
4. **📄 Dynamic Mela Standee PDF with Live UPI QR**:
   - Generates high-resolution printable A4 posters with cluster attribution, GI tag badges, and scan-to-pay UPI QR codes for physical exhibitions, melas, and haats.
5. **🌐 Official ONDC Beckn Protocol v1.2 Export**:
   - Generates schema-compliant Beckn v1.2 catalog JSON for discoverability on buyer apps (Paytm, Pincode, Mystore).
6. **🎙️ Speech-to-Catalog NLP Engine & Shilpi Assistant**:
   - Bilingual voice recording in Hindi/English with AI attribute extraction into structured listings.
7. **🛍️ 16 Authentic GI-Certified Products Pre-Seeded**:
   - Jaipur Blue Pottery, Banarasi Silk, Kashmiri Pashmina, Bastar Dokra, Madhubani Art, Tanjore Gold Paintings, Channapatna Toys, and more.

---

## 🚀 1-Click Deploy to Koyeb (100% Free, No Credit Card Required)

Deploy this full-stack application to Koyeb in seconds:

[![Deploy to Koyeb](https://www.koyeb.com/static/images/deploy/button.svg)](https://app.koyeb.com/deploy?type=git&repository=github.com/JatinGargz/kalakart&name=kalakart&ports=8000;http;/)

1. Click the button above to launch Koyeb.
2. Sign in with GitHub (`JatinGargz`).
3. Koyeb automatically detects `Dockerfile` and configures port `8000`.
4. Choose the **Free Nano** tier (no credit card required).
5. Click **Deploy**. Your permanent HTTPS URL (e.g. `https://kalakart-<org>.koyeb.app`) is generated!

---

## ☁️ Alternative: Deploy to Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/JatinGargz/kalakart)

---

## 💻 Local Quickstart

### Prerequisites
- Python 3.10+
- `pip install -r requirements.txt`

### Run Prototype
```bash
# Windows
run_prototype.bat

# Or manual terminal
uvicorn main:app --host 0.0.0.0 --port 8000 --app-dir backend
```
Access the application at `http://127.0.0.1:8000`.
