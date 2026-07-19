import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import init_db, AsyncSessionLocal
from app.db.models import Camera
from sqlalchemy.future import select

async def seed():
    print("Initializing Database...")
    await init_db()
    
    async with AsyncSessionLocal() as session:
        # Check if already seeded
        result = await session.execute(select(Camera))
        if result.scalars().first():
            print("Cameras already seeded.")
            return

        c1 = Camera(name="Cam 1", location_name="Platform 3 - Central Station", latitude=40.7128, longitude=-74.0060, safe_density_threshold=4.0)
        c2 = Camera(name="Cam 2", location_name="Main Stadium Concourse", latitude=40.7129, longitude=-74.0061, safe_density_threshold=3.5)
        c3 = Camera(name="Cam 3", location_name="Subway Tunnel B", latitude=40.7130, longitude=-74.0062, safe_density_threshold=2.5)
        
        session.add_all([c1, c2, c3])
        await session.commit()
        print("Successfully seeded 3 cameras: 'Platform 3 - Central Station', 'Main Stadium Concourse', and 'Subway Tunnel B'.")

if __name__ == "__main__":
    asyncio.run(seed())
