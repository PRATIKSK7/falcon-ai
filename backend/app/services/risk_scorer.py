import numpy as np
from typing import List, Tuple
from pydantic import BaseModel

class FrameRecord(BaseModel):
    frame_index: int
    timestamp: float
    crowd_count: float
    mean_flow_magnitude: float
    mean_divergence: float
    # List of (x, y, divergence_value)
    convergence_hotspots: List[Tuple[int, int, float]]

class RiskAssessment(BaseModel):
    score: int
    severity: str
    contributing_factors: List[str]
    timestamp: float
    frame_index: int

class RiskScorer:
    def __init__(self, venue_area_sqm: float = 50.0):
        self.venue_area_sqm = venue_area_sqm
        # Weights for the final score out of 100
        self.w_threshold = 0.35
        self.w_trend = 0.25
        self.w_convergence = 0.25
        self.w_anomaly = 0.15

    def score_window(self, window: List[FrameRecord]) -> RiskAssessment:
        if not window:
            return RiskAssessment(
                score=0, severity="LOW", contributing_factors=[], 
                timestamp=0.0, frame_index=0
            )

        latest = window[-1]
        factors = []
        
        # --- 1. Density Threshold (0 to 100) ---
        # > 4 people/m^2 is critical (100 score on this metric)
        current_density = latest.crowd_count / self.venue_area_sqm
        density_score_raw = (current_density / 4.0) * 100
        score_threshold = min(100.0, max(0.0, density_score_raw))
        if current_density > 4.0:
            factors.append(f"Critical crowd density exceeded: {current_density:.1f} people/m² (Safe limit: 4.0).")
        elif current_density > 2.0:
            factors.append(f"High crowd density detected: {current_density:.1f} people/m².")

        # --- 2. Density Trend (0 to 100) ---
        score_trend = 0.0
        if len(window) >= 2:
            first = window[0]
            dt = latest.timestamp - first.timestamp
            if dt > 0:
                # rate of change (people per second)
                dCount = latest.crowd_count - first.crowd_count
                rate = dCount / dt
                # If rate > 5 people/sec into the zone, that's max risk
                trend_score_raw = (rate / 5.0) * 100
                score_trend = min(100.0, max(0.0, trend_score_raw))
                if rate > 2.0:
                    factors.append(f"Rapid crowd influx detected: +{rate:.1f} people/sec.")

        # --- 3. Convergence Intensity (0 to 100) ---
        score_convergence = 0.0
        if latest.convergence_hotspots:
            # Most negative divergence means strongest convergence.
            max_convergence = min([hs[2] for hs in latest.convergence_hotspots])
            # Map -1.0 to 100 score, 0.0 to 0 score
            conv_score_raw = (abs(max_convergence) / 1.0) * 100
            score_convergence = min(100.0, max(0.0, conv_score_raw))
            if score_convergence > 50.0:
                factors.append("Strong flow convergence detected (people moving toward a single point).")

        # --- 4. Flow Magnitude Anomaly (0 to 100) ---
        score_anomaly = 0.0
        if len(window) >= 5:
            magnitudes = [rec.mean_flow_magnitude for rec in window[:-1]]
            mean_mag = np.mean(magnitudes)
            std_mag = np.std(magnitudes)
            current_mag = latest.mean_flow_magnitude
            
            if std_mag > 0.01:
                z_score = (current_mag - mean_mag) / std_mag
                # If flow suddenly stops (z_score < -2), it's a huge stampede signature
                if z_score < -2.0:
                    score_anomaly = 100.0
                    factors.append("Sudden stop in crowd movement (classic crush precursor).")
                elif z_score > 3.0:
                    # Sudden spike in movement (running/fleeing)
                    score_anomaly = 80.0
                    factors.append("Sudden spike in crowd movement speed.")

        # --- Weighted Final Score ---
        final_score_raw = (
            self.w_threshold * score_threshold +
            self.w_trend * score_trend +
            self.w_convergence * score_convergence +
            self.w_anomaly * score_anomaly
        )
        
        final_score = int(round(final_score_raw))
        
        # --- Mapping to Severity ---
        if final_score <= 30:
            severity = "LOW"
        elif final_score <= 55:
            severity = "MODERATE"
        elif final_score <= 75:
            severity = "HIGH"
        else:
            severity = "CRITICAL"
            
        if not factors and severity != "LOW":
            factors.append("General elevated risk metrics.")

        return RiskAssessment(
            score=final_score,
            severity=severity,
            contributing_factors=factors,
            timestamp=latest.timestamp,
            frame_index=latest.frame_index
        )
