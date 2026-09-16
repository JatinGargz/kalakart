FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend and frontend code
COPY backend ./backend
COPY kalakart-frontend ./kalakart-frontend

# Universal cloud port fallback (Koyeb/Render/Railway/HF Spaces)
ENV PORT=8000
EXPOSE 8000

# Run FastAPI orchestrator
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --app-dir backend"]
