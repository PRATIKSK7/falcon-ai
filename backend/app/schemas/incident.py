from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json

class FrameAssessmentOut(BaseModel):
    frame_index: int
    timestamp: float
    crowd_count: float
    mean_flow_magnitude: float
    mean_divergence: float
    risk_score: int
    severity: str
    contributing_factors: List[str]
    detections: List[dict]
    density_map_path: str
    flow_map_path: str

    @classmethod
    def from_orm_obj(cls, obj):
        factors = json.loads(obj.contributing_factors) if obj.contributing_factors else []
        return cls(
            frame_index=obj.frame_index,
            timestamp=obj.timestamp,
            crowd_count=obj.crowd_count,
            mean_flow_magnitude=obj.mean_flow_magnitude,
            mean_divergence=obj.mean_divergence,
            risk_score=obj.risk_score,
            severity=obj.severity,
            contributing_factors=factors,
            detections=json.loads(obj.detections_json) if obj.detections_json else [],
            density_map_path=obj.density_map_path or "",
            flow_map_path=obj.flow_map_path or ""
        )

class IncidentOut(BaseModel):
    id: str
    camera_id: int
    video_path: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    peak_severity: str
    peak_score: int
    prediction: str = "Pending"
    progress: int = 0
    class Config:
        from_attributes = True

class IncidentDetailOut(IncidentOut):
    frames: List[FrameAssessmentOut]
    class Config:
        from_attributes = True
