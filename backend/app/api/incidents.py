import uuid
import os
import shutil
import json
import logging
import time
import cv2
import numpy as np
import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Optional
from pydantic import BaseModel

from app.db.database import AsyncSessionLocal
from app.db.models import Incident, FrameAssessment, Camera
from app.schemas.incident import IncidentOut, IncidentDetailOut, FrameAssessmentOut
from app.services.frame_extractor import extract_frames
from app.models.density_estimator import PersonCounter
from app.models.flow_analyzer import FlowAnalyzer
from app.services.alert_service import AlertService
from app.core.config import settings
from app.services.risk_scorer import RiskScorer, FrameRecord
from app.services.video_analysis_service import video_analyzer
import json

logger = logging.getLogger(__name__)

class UploadResponse(BaseModel):
    status: str
    message: str
    job_id: str

router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"])

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
UPLOAD_DIR = os.path.join(ROOT_DIR, "storage", "uploads")
DENSITY_MAPS_DIR = os.path.join(ROOT_DIR, "storage", "density_maps")
FLOW_MAPS_DIR = os.path.join(ROOT_DIR, "storage", "flow_maps")
ARCHIVE_DIR = os.path.join(ROOT_DIR, "storage", "archive")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DENSITY_MAPS_DIR, exist_ok=True)
os.makedirs(FLOW_MAPS_DIR, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)

density_estimator = PersonCounter(device="cpu")
flow_analyzer = FlowAnalyzer()
alert_service = AlertService()

async def run_process_video(job_id: str, video_path: str, camera_id: int):
    # Fetch camera details
    async with AsyncSessionLocal() as session:
        cam_result = await session.execute(select(Camera).where(Camera.id == camera_id))
        camera = cam_result.scalar_one_or_none()
        if not camera:
            logger.error(f"Camera {camera_id} not found for job {job_id}")
            return
            
        location_name = camera.location_name
        risk_scorer = RiskScorer(venue_area_sqm=50.0) # We could map this to camera.safe_density_threshold logic if desired

        # Update Incident status
        inc_result = await session.execute(select(Incident).where(Incident.id == job_id))
        incident = inc_result.scalar_one_or_none()
        if incident:
            incident.status = "PROCESSING"
            await session.commit()
    
    job_density_dir = os.path.join(DENSITY_MAPS_DIR, job_id)
    job_flow_dir = os.path.join(FLOW_MAPS_DIR, job_id)
    os.makedirs(job_density_dir, exist_ok=True)
    os.makedirs(job_flow_dir, exist_ok=True)
    
    prev_frame = None
    rolling_window = []
    previous_severity = "LOW"
    peak_score = 0
    peak_severity = "LOW"
    
    total_frames = 0
    t_extract_total = 0
    t_density_total = 0
    t_flow_total = 0
    t_risk_total = 0
    start_wall = time.time()
    
    try:
        t_extract_start = time.time()
        # Optimization: Run at 5 FPS since YOLO is fast enough.
        for frame_index, frame in extract_frames(video_path, sample_fps=5):
            t_extract_total += time.time() - t_extract_start
            total_frames += 1
            timestamp = float(frame_index) / 30.0 
            
            # Density
            t_density_start = time.time()
            density_map, count, detections = density_estimator.estimate(frame)
            if np.max(density_map) > 0:
                normalized_map = (density_map / np.max(density_map) * 255).astype(np.uint8)
            else:
                normalized_map = np.zeros_like(density_map, dtype=np.uint8)
            heatmap = cv2.applyColorMap(normalized_map, cv2.COLORMAP_JET)
            heatmap_path = os.path.join(job_density_dir, f"frame_{frame_index}.png")
            cv2.imwrite(heatmap_path, heatmap)
            t_density_total += time.time() - t_density_start
            
            # Flow
            t_flow_start = time.time()
            mean_magnitude = 0.0
            mean_divergence = 0.0
            convergence_hotspots = []
            flow_path = ""
            
            if prev_frame is not None:
                flow_metrics = flow_analyzer.compute_flow(prev_frame, frame)
                mean_magnitude = round(flow_metrics["mean_magnitude"], 4)
                mean_divergence = round(flow_metrics["mean_divergence"], 4)
                convergence_hotspots = flow_metrics["convergence_hotspots"]
                
                flow_img = flow_analyzer.draw_flow_overlay(frame, flow_metrics["raw_flow"])
                flow_path = os.path.join(job_flow_dir, f"frame_{frame_index}.png")
                cv2.imwrite(flow_path, flow_img)
            t_flow_total += time.time() - t_flow_start
            
            # Risk Scoring
            t_risk_start = time.time()
            record = FrameRecord(
                frame_index=frame_index,
                timestamp=timestamp,
                crowd_count=round(count, 2),
                mean_flow_magnitude=mean_magnitude,
                mean_divergence=mean_divergence,
                convergence_hotspots=convergence_hotspots
            )
            
            # --- DEBUG LOGGING ---
            with open(os.path.join(ROOT_DIR, "debug_cv_outputs.log"), "a") as f:
                f.write(f"Job: {job_id} | Frame: {frame_index} | Raw Crowd Count: {count:.2f} | Raw Flow Mag: {mean_magnitude:.4f}\n")
            
            # --- DEMO MODE INJECTION ---
            if settings.DEMO_MODE and frame_index >= 25:
                record.crowd_count = camera.safe_density_threshold * 50.0 * 1.5
                record.mean_flow_magnitude = 0.05
                record.mean_divergence = -1.5
                record.convergence_hotspots = [(100, 100, -1.5)]
            # ---------------------------
            
            rolling_window.append(record)
            if len(rolling_window) > 15:
                rolling_window.pop(0)
                
            assessment = risk_scorer.score_window(rolling_window)
            
            # Track peaks
            if assessment.score > peak_score:
                peak_score = assessment.score
                peak_severity = assessment.severity
            
            # Escalation check (legacy alert triggers are removed from here if desired, but prompt says "Keep existing functionality intact." so we leave it)
            if assessment.severity in ["HIGH", "CRITICAL"] and previous_severity not in ["HIGH", "CRITICAL"]:
                print(f"[ALERT TRIGGER] Job {job_id} Crowd risk escalated to {assessment.severity} at frame {frame_index}!")
                dashboard_url = f"http://localhost:3000/incidents/{job_id}"
                # Alert service now uses generic trigger_alert, we'll keep the legacy trigger format if it existed,
                # but wait, the prompt for the previous step changed alert_service to remove videomae ones, and the legacy ones might still be there. 
                # Yes, trigger_voice_call and trigger_whatsapp_alert were not removed from alert_service.py.
                alert_service.trigger_all(
                    job_id=job_id,
                    assessment=assessment,
                    location=f"{location_name} (Lat: {camera.latitude}, Lng: {camera.longitude})",
                    snapshot_url="",
                    dashboard_url=dashboard_url
                )
                
            previous_severity = assessment.severity
            
            # DB Write
            async with AsyncSessionLocal() as session:
                frame_db = FrameAssessment(
                    incident_id=job_id,
                    frame_index=frame_index,
                    timestamp=timestamp,
                    crowd_count=record.crowd_count,
                    mean_flow_magnitude=record.mean_flow_magnitude,
                    mean_divergence=record.mean_divergence,
                    risk_score=assessment.score,
                    severity=assessment.severity,
                    contributing_factors=json.dumps(assessment.contributing_factors),
                    detections_json=json.dumps(detections),
                    density_map_path=heatmap_path,
                    flow_map_path=flow_path
                )
                session.add(frame_db)
                await session.commit()
                print(f"[Handoff] Frame {frame_index} committed to DB for job {job_id}")
            
            t_risk_total += time.time() - t_risk_start
            prev_frame = frame
            t_extract_start = time.time()
            
        async with AsyncSessionLocal() as session:
            inc_result = await session.execute(select(Incident).where(Incident.id == job_id))
            incident = inc_result.scalar_one_or_none()
            if incident:
                incident.status = "COMPLETED"
                incident.completed_at = datetime.now(timezone.utc)
                incident.peak_score = peak_score
                incident.peak_severity = peak_severity
                await session.commit()
                
        total_wall = time.time() - start_wall
        print("\n====== PROCESSING SUMMARY ======")
        print(f"Total Frames: {total_frames}")
        print(f"Total Wall Time: {total_wall:.2f}s")
        if total_frames > 0:
            print(f"Avg Extraction: {(t_extract_total/total_frames)*1000:.2f}ms")
            print(f"Avg Density: {(t_density_total/total_frames)*1000:.2f}ms")
            print(f"Avg Flow: {(t_flow_total/total_frames)*1000:.2f}ms")
            print(f"Avg Risk & DB: {(t_risk_total/total_frames)*1000:.2f}ms")
            print(f"Avg Total Latency/Frame: {(total_wall/total_frames)*1000:.2f}ms")
        print("================================\n")
                
    except Exception as e:
        logger.error(f"Error processing video {job_id}: {e}")
        async with AsyncSessionLocal() as session:
            inc_result = await session.execute(select(Incident).where(Incident.id == job_id))
            incident = inc_result.scalar_one_or_none()
            if incident:
                incident.status = "FAILED"
                await session.commit()

async def run_ai_pipeline(job_id: str, video_path: str, camera_id: int):
    """
    Background task to run VideoMAE analysis asynchronously, create an incident
    if a Stampede is detected, and trigger alerts.
    """
    try:
        logger.info(f"Running background VideoMAE analysis on {video_path}")
        
        # Offload synchronous AI inference to a background thread to prevent event loop blocking
        analysis_results = await asyncio.to_thread(video_analyzer.analyze_video, video_path)
        
        async with AsyncSessionLocal() as session:
            inc_result = await session.execute(select(Incident).where(Incident.id == job_id))
            existing_incident = inc_result.scalar_one_or_none()
            
            if existing_incident:
                existing_incident.status = "PROCESSING"
                await session.commit()
                
        if analysis_results["prediction"] == "Stampede":
            async with AsyncSessionLocal() as session:
                cam_result = await session.execute(select(Camera).where(Camera.id == camera_id))
                camera = cam_result.scalar_one_or_none()
                
                # Trigger AI alerts using the generic trigger_alert
                if camera:
                    dashboard_url = f"http://localhost:3000/incidents/{job_id}"
                    location_str = f"{camera.location_name} (Lat: {camera.latitude}, Lng: {camera.longitude})"
                    alert_service.trigger_alert(
                        event_type="Stampede",
                        confidence=analysis_results["confidence"],
                        message="AI surveillance system detected a potential stampede.",
                        metadata={
                            "job_id": job_id,
                            "location": location_str,
                            "dashboard_url": dashboard_url
                        }
                    )
                    
        # Always submit to existing legacy processing to generate density/flow maps for the dashboard
        await run_process_video(job_id, video_path, camera_id)
        
        if analysis_results["prediction"] != "Stampede":
            # Prediction is Normal. Archive the video instead of deleting.
            try:
                filename = os.path.basename(video_path)
                archive_path = os.path.join(ARCHIVE_DIR, filename)
                shutil.move(video_path, archive_path)
            except OSError as e:
                logger.error(f"Failed to archive video {video_path}: {e}")
    except Exception as e:
        logger.error(f"Error in background AI pipeline for {job_id}: {e}")

def process_video_sync_wrapper(job_id: str, video_path: str, camera_id: int):
    asyncio.run(run_process_video(job_id, video_path, camera_id))

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@router.post("/upload", response_model=UploadResponse)
async def upload_incident(
    background_tasks: BackgroundTasks, 
    camera_id: int = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.endswith((".mp4", ".avi")):
        raise HTTPException(status_code=400, detail="Only .mp4 and .avi files are supported.")
        
    # Verify camera exists
    cam_result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = cam_result.scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found.")
        
    job_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    video_path = os.path.join(UPLOAD_DIR, f"{job_id}{ext}")
    
    with open(video_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
        
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened() or cap.get(cv2.CAP_PROP_FRAME_COUNT) <= 0:
        cap.release()
        os.remove(video_path)
        raise HTTPException(status_code=400, detail="Corrupt or invalid video file.")
    cap.release()
        
    # Insert incident synchronously into the DB
    new_incident = Incident(
        id=job_id,
        camera_id=camera_id,
        video_path=video_path,
        status="PENDING"
    )
    db.add(new_incident)
    await db.commit()
        
    # Schedule the AI pipeline in the background
    background_tasks.add_task(run_ai_pipeline, job_id, video_path, camera_id)
    
    return UploadResponse(
        status="processing",
        message="Video uploaded successfully. Analysis started.",
        job_id=job_id
    )

@router.get("", response_model=List[IncidentOut])
async def list_incidents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Incident).order_by(Incident.created_at.desc()))
    incidents = result.scalars().all()
    return [
        {
            "id": incident.id,
            "camera_id": incident.camera_id,
            "video_path": incident.video_path,
            "status": incident.status,
            "created_at": incident.created_at,
            "completed_at": incident.completed_at,
            "peak_severity": incident.peak_severity,
            "peak_score": incident.peak_score,
            "prediction": "Stampede" if incident.peak_severity in ["HIGH", "CRITICAL"] else "Normal",
            "progress": 100 if incident.status == "COMPLETED" else 50
        }
        for incident in incidents
    ]

@router.get("/{job_id}", response_model=IncidentDetailOut)
async def get_incident(job_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Incident).where(Incident.id == job_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    frame_result = await db.execute(select(FrameAssessment).where(FrameAssessment.incident_id == job_id).order_by(FrameAssessment.frame_index.asc()))
    frames = frame_result.scalars().all()
    
    out_dict = {
        "id": incident.id,
        "camera_id": incident.camera_id,
        "video_path": incident.video_path,
        "status": incident.status,
        "created_at": incident.created_at,
        "completed_at": incident.completed_at,
        "peak_severity": incident.peak_severity,
        "peak_score": incident.peak_score,
        "prediction": "Stampede" if incident.peak_severity in ["HIGH", "CRITICAL"] else "Normal",
        "progress": 100 if incident.status == "COMPLETED" else min(99, len(frames) * 2),
        "frames": [FrameAssessmentOut.from_orm_obj(f) for f in frames]
    }
    return out_dict
