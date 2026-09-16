@echo off
REM SHILP AI — one-click prototype launcher (Windows)
echo === SHILP AI prototype ===
cd /d "%~dp0backend"
python -m pip install -r requirements.txt
echo --- Starting FastAPI gateway on http://127.0.0.1:8000 ---
start "SHILP AI backend" python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
timeout /t 3 >nul
cd /d "%~dp0kalakart-frontend"
echo --- Starting frontend on http://127.0.0.1:8080 ---
start http://127.0.0.1:8080
python -m http.server 8080
