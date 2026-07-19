import cv2
import numpy as np
from typing import Dict, Any

class FlowAnalyzer:
    def __init__(self):
        # Parameters for Farneback dense optical flow
        self.pyr_scale = 0.5
        self.levels = 3
        self.winsize = 15
        self.iterations = 3
        self.poly_n = 5
        self.poly_sigma = 1.2
        self.flags = 0

    def compute_flow(self, prev_frame: np.ndarray, curr_frame: np.ndarray, top_n_hotspots: int = 5) -> Dict[str, Any]:
        prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)

        flow = cv2.calcOpticalFlowFarneback(
            prev_gray, curr_gray, None,
            self.pyr_scale, self.levels, self.winsize,
            self.iterations, self.poly_n, self.poly_sigma, self.flags
        )

        u = flow[..., 0]
        v = flow[..., 1]

        # Magnitude
        magnitude, _ = cv2.cartToPolar(u, v)
        mean_magnitude = float(np.mean(magnitude))

        # Divergence: dU/dx + dV/dy
        du_dy, du_dx = np.gradient(u)
        dv_dy, dv_dx = np.gradient(v)
        divergence = du_dx + dv_dy

        mean_divergence = float(np.mean(divergence))

        # Find hotspots (most negative divergence)
        div_flat = divergence.flatten()
        
        # Sort and take the top N smallest (most negative)
        smallest_idx = np.argsort(div_flat)[:top_n_hotspots]
        
        hotspots = []
        for idx in smallest_idx:
            val = div_flat[idx]
            if val < -0.01:  # Threshold to only consider actual convergence
                y, x = np.unravel_index(idx, divergence.shape)
                hotspots.append((int(x), int(y), float(val)))

        return {
            "mean_magnitude": mean_magnitude,
            "mean_divergence": mean_divergence,
            "convergence_hotspots": hotspots,
            "raw_flow": flow # Keep for drawing arrows
        }

    def draw_flow_overlay(self, frame: np.ndarray, flow: np.ndarray, step: int = 16) -> np.ndarray:
        h, w = frame.shape[:2]
        y, x = np.mgrid[step//2:h:step, step//2:w:step].reshape(2,-1).astype(int)
        fx, fy = flow[y,x].T
        
        lines = np.vstack([x, y, x+fx, y+fy]).T.reshape(-1, 2, 2)
        lines = np.int32(lines + 0.5)
        
        vis = frame.copy()
        for (x1, y1), (x2, y2) in lines:
            cv2.arrowedLine(vis, (x1, y1), (x2, y2), (0, 255, 0), 1, tipLength=0.3)
            
        return vis
