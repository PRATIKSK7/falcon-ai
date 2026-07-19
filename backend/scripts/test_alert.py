import sys
import os

# Ensure backend directory is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.alert_service import AlertService
from app.services.risk_scorer import RiskAssessment
import asyncio

def main():
    print("Testing Dual-Channel Alert System...")
    alert_service = AlertService()
    
    if not alert_service.client:
        print("Warning: Twilio client not configured. Make sure TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN are set in .env")
        print("The test will just log to console and fail gracefully.")
        
    assessment = RiskAssessment(
        score=85,
        severity="CRITICAL",
        contributing_factors=["Crowd density exceeded 4.2 people/m²", "Sudden stop in crowd movement (classic crush precursor)"],
        timestamp=12.5,
        frame_index=375
    )
    
    print("\nAttempting to trigger alerts (this will hit the DB and Twilio API)...")
    
    # We need an event loop running for the async DB logging to work gracefully
    async def run_test():
        from app.db.database import init_db
        await init_db()
        
        alert_service.trigger_all(
            job_id="test-job-uuid-1234",
            assessment=assessment,
            location="Camera 1 - Station Platform",
            snapshot_url="https://images.unsplash.com/photo-1507676184212-d0330a151f15?w=500",
            dashboard_url="http://localhost:3000/incidents/test-job-uuid-1234"
        )
        print("\nAlert trigger function completed.")
        
    asyncio.run(run_test())

if __name__ == "__main__":
    main()
