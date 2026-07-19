from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.database import AsyncSessionLocal
from app.db.models import Camera
from app.schemas.camera import CameraCreate, CameraOut
from typing import List

router = APIRouter(prefix="/api/v1/cameras", tags=["cameras"])

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@router.post("", response_model=CameraOut)
async def create_camera(camera: CameraCreate, db: AsyncSession = Depends(get_db)):
    db_camera = Camera(**camera.model_dump())
    db.add(db_camera)
    await db.commit()
    await db.refresh(db_camera)
    return db_camera

@router.get("", response_model=List[CameraOut])
async def list_cameras(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Camera))
    return result.scalars().all()
