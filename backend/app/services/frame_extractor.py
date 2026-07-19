import cv2
import numpy as np
from typing import Generator, Tuple

def extract_frames(video_path: str, sample_fps: int = 5) -> Generator[Tuple[int, np.ndarray], None, None]:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file {video_path}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0 or np.isnan(fps):
        fps = 30.0  # Fallback if unable to read FPS
        
    frame_interval = int(round(fps / sample_fps))
    if frame_interval < 1:
        frame_interval = 1
        
    frame_index = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        if frame_index % frame_interval == 0:
            yield (frame_index, frame)
            
        frame_index += 1
        
    cap.release()
