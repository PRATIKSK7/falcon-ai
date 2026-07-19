from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.database import Base

class Camera(Base):
    __tablename__ = "cameras"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location_name = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    safe_density_threshold = Column(Float, default=4.0)

class Incident(Base):
    __tablename__ = "incidents"
    id = Column(String, primary_key=True, index=True) # UUID
    camera_id = Column(Integer, ForeignKey("cameras.id"))
    video_path = Column(String)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    peak_severity = Column(String, default="LOW")
    peak_score = Column(Integer, default=0)
    
    camera = relationship("Camera")

class FrameAssessment(Base):
    __tablename__ = "frame_assessments"
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String, ForeignKey("incidents.id"), index=True)
    frame_index = Column(Integer)
    timestamp = Column(Float)
    crowd_count = Column(Float)
    mean_flow_magnitude = Column(Float)
    mean_divergence = Column(Float)
    risk_score = Column(Integer)
    severity = Column(String)
    contributing_factors = Column(Text) # JSON string
    detections_json = Column(Text) # JSON string array of dicts
    density_map_path = Column(String)
    flow_map_path = Column(String)

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String, ForeignKey("incidents.id"), index=True)
    channel = Column(String) # "VOICE" or "WHATSAPP"
    status = Column(String)
    external_sid = Column(String)
    sent_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
