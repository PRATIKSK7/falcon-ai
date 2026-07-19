import sys
import os
import cv2
import numpy as np

# Ensure backend directory is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.flow_analyzer import FlowAnalyzer

def main():
    print("Initializing FlowAnalyzer...")
    analyzer = FlowAnalyzer()
    
    # Create two dummy images with a shift
    prev_img = np.zeros((480, 640, 3), dtype=np.uint8)
    curr_img = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Draw a square that moves
    cv2.rectangle(prev_img, (200, 200), (300, 300), (255, 255, 255), -1)
    cv2.rectangle(curr_img, (205, 205), (305, 305), (255, 255, 255), -1)
    
    print("Running optical flow on dummy shifted image...")
    
    metrics = analyzer.compute_flow(prev_img, curr_img)
    
    print(f"Mean Magnitude: {metrics['mean_magnitude']:.4f}")
    print(f"Mean Divergence: {metrics['mean_divergence']:.4f}")
    print(f"Hotspots: {metrics['convergence_hotspots']}")
    print("Success!")

if __name__ == "__main__":
    main()
