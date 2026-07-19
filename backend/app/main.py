import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.api.incidents import router as incidents_router
from app.api.cameras import router as cameras_router
from app.api.analytics import router as analytics_router
from app.api.ai import router as ai_router
from app.db.database import init_db, AsyncSessionLocal
from sqlalchemy.future import select
from app.db.models import Incident, Camera
from app.api.incidents import run_ai_pipeline
import asyncio
import logging
import shutil
import sys
import os

# Add backend directory to sys.path so we can import from config and services
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from services.model_loader import model_loader_instance

logger = logging.getLogger(__name__)

async def recover_pending_videos():
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    STORAGE_DIR = os.path.join(ROOT_DIR, "storage")
    uploads_dir = os.path.join(STORAGE_DIR, "uploads")
    archive_dir = os.path.join(STORAGE_DIR, "archive")
    
    recovered_count = 0

    async with AsyncSessionLocal() as session:
        cam_result = await session.execute(select(Camera).limit(1))
        fallback_cam = cam_result.scalar_one_or_none()
        fallback_camera_id = fallback_cam.id if fallback_cam else 1

        for folder in [uploads_dir, archive_dir]:
            if not os.path.exists(folder):
                continue
            for f in os.listdir(folder):
                if not f.endswith(('.mp4', '.avi')):
                    continue
                video_path = os.path.join(folder, f)
                job_id, _ = os.path.splitext(f)
                
                result = await session.execute(select(Incident).where(Incident.id == job_id))
                incident = result.scalar_one_or_none()
                
                if incident:
                    if incident.status == "COMPLETED":
                        logger.info(f"Skipping completed Incident {job_id}.")
                    else:
                        logger.info(f"Retrying Incident {job_id}.")
                        if folder == archive_dir:
                            new_path = os.path.join(uploads_dir, f)
                            shutil.move(video_path, new_path)
                            video_path = new_path
                        asyncio.create_task(run_ai_pipeline(job_id, video_path, incident.camera_id))
                        recovered_count += 1
                else:
                    if folder == uploads_dir:
                        logger.info(f"Resuming AI analysis for video {job_id}.")
                        asyncio.create_task(run_ai_pipeline(job_id, video_path, fallback_camera_id))
                        recovered_count += 1

    if recovered_count > 0:
        logger.info(f"Recovered {recovered_count} pending videos.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    await init_db()
    
    logger.info("Loading AI models...")
    model_loaded = model_loader_instance.load_model()
    if not model_loaded:
        logger.warning("Failed to load Keras model on startup. It will be retried on first request.")
        
    logger.info("Recovering pending videos...")
    await recover_pending_videos()
    yield

app = FastAPI(title="FALCON AI API", lifespan=lifespan)

# Configure CORS for local Next.js/Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(cameras_router)
app.include_router(incidents_router)
app.include_router(analytics_router)
app.include_router(ai_router)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORAGE_DIR = os.path.join(ROOT_DIR, "storage")
os.makedirs(STORAGE_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STORAGE_DIR), name="static")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {
        "name": "FALCON AI API",
        "status": "operational",
        "docs_url": "/docs"
    }
