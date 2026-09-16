from fastapi import FastAPI

from app.routers import pipeline

app = FastAPI(
    title="Artisan AI Pipeline",
    description="Voice + photo -> professional, multilingual, B2B-ready product listing",
    version="0.1.0",
)

app.include_router(pipeline.router, tags=["pipeline"])


@app.get("/health")
async def health():
    return {"status": "ok"}
