import sys
import os
import cv2
import numpy as np

# Ensure backend directory is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.density_estimator import DensityEstimator

def main():
    weights_path = os.path.join(os.path.dirname(__file__), '..', '0model_best.pth.tar')
    if not os.path.exists(weights_path):
        weights_path = None
        print("Warning: Weights not found. Using randomly initialized weights.")
        
    print("Initializing model...")
    estimator = DensityEstimator(weights_path=weights_path, device="cpu")
    
    dummy_img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    print("Running inference on dummy image...")
    
    density_map, count = estimator.estimate(dummy_img)
    
    print(f"Estimated count: {count:.2f}")
    print(f"Density map shape: {density_map.shape}")
    print("Success!")

if __name__ == "__main__":
    main()
