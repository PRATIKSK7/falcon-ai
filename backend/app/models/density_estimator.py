import cv2
import numpy as np
from typing import Tuple, Optional
from ultralytics import YOLO
import math

class PersonCounter:
    def __init__(self, weights_path: str = "yolov8n.pt", device: str = "cpu"):
        print(f"Loading YOLOv8n from {weights_path} on {device}...")
        self.model = YOLO(weights_path)
        self.device = device
        
    def estimate(self, frame: np.ndarray, max_dim: int = 640) -> Tuple[np.ndarray, float]:
        """
        Estimates the crowd density map and total count from an OpenCV frame (BGR).
        
        Uses YOLOv8n to detect people (class 0).
        The density map is a 2D grid (downscaled from original) where each cell
        contains the count of person bounding box centers.
        
        Returns:
            density_map (np.ndarray): 2D heatmap grid
            count (float): Estimated total count
            detections (list): List of dicts with bounding box data
        """
        h, w = frame.shape[:2]
        
        # Downscale for YOLO speed if needed
        scale = 1.0
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            frame_resized = cv2.resize(frame, (int(w * scale), int(h * scale)))
        else:
            frame_resized = frame

        # Run YOLO inference with tracking
        # classes=[0] filters to 'person' only
        results = self.model.track(source=frame_resized, classes=[0], device=self.device, verbose=False, persist=True)
        
        # Create a grid for the density map (e.g. 1/8th the size of the resized frame for a smooth heatmap)
        grid_h, grid_w = int(frame_resized.shape[0] / 8), int(frame_resized.shape[1] / 8)
        grid_h = max(1, grid_h)
        grid_w = max(1, grid_w)
        density_map = np.zeros((grid_h, grid_w), dtype=np.float32)
        
        count = 0
        detections = []
        if len(results) > 0:
            boxes = results[0].boxes
            for box in boxes:
                # Center of the bounding box
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
                conf = float(box.conf[0].cpu().numpy()) if box.conf is not None else 0.0
                track_id = int(box.id[0].cpu().numpy()) if box.id is not None else -1
                
                # Map coordinate to grid
                grid_x = min(grid_w - 1, max(0, int(cx / 8)))
                grid_y = min(grid_h - 1, max(0, int(cy / 8)))
                
                density_map[grid_y, grid_x] += 1.0
                count += 1
                detections.append({
                    "id": track_id,
                    "x1": float(x1), "y1": float(y1), "x2": float(x2), "y2": float(y2),
                    "cx": float(cx), "cy": float(cy),
                    "conf": conf
                })
                
        # Optional: apply slight gaussian blur to the grid so the heatmap looks smoother
        density_map = cv2.GaussianBlur(density_map, (3, 3), 0.5)

        return density_map, float(count), detections
