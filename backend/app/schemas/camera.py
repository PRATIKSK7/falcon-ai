from pydantic import BaseModel

class CameraCreate(BaseModel):
    name: str
    location_name: str
    latitude: float
    longitude: float
    safe_density_threshold: float = 4.0

class CameraOut(CameraCreate):
    id: int
    class Config:
        from_attributes = True
