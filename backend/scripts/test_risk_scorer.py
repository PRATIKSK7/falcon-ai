import sys
import os

# Ensure backend directory is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.risk_scorer import RiskScorer, FrameRecord

def main():
    scorer = RiskScorer(venue_area_sqm=50.0)
    
    print("--- Test 1: Normal Walking Window ---")
    normal_window = []
    for i in range(15):
        normal_window.append(FrameRecord(
            frame_index=i,
            timestamp=i * 0.2, # 5 fps
            crowd_count=20.0 + (i * 0.1), # Very slow increase
            mean_flow_magnitude=0.5,
            mean_divergence=0.0,
            convergence_hotspots=[]
        ))
        
    assessment1 = scorer.score_window(normal_window)
    print(f"Score: {assessment1.score}")
    print(f"Severity: {assessment1.severity}")
    print(f"Factors: {assessment1.contributing_factors}")
    assert assessment1.severity == "LOW"
    
    print("\n--- Test 2: Stampede Signature Window ---")
    stampede_window = []
    for i in range(15):
        # Density increases rapidly up to 250 people (5 per sqm)
        count = 50.0 + (i * 14.0)
        # Flow magnitude is high then suddenly drops at the end
        flow = 1.0 if i < 13 else 0.1
        # Divergence is highly negative (convergence)
        hotspots = [(10, 10, -0.8)] if i > 10 else []
        
        stampede_window.append(FrameRecord(
            frame_index=i,
            timestamp=i * 0.2,
            crowd_count=count,
            mean_flow_magnitude=flow,
            mean_divergence=-0.5 if i > 10 else 0.0,
            convergence_hotspots=hotspots
        ))

    assessment2 = scorer.score_window(stampede_window)
    print(f"Score: {assessment2.score}")
    print(f"Severity: {assessment2.severity}")
    print(f"Factors: {assessment2.contributing_factors}")
    assert assessment2.severity in ["HIGH", "CRITICAL"]

    print("\nSuccess! Risk scorer behaves as expected.")

if __name__ == "__main__":
    main()
