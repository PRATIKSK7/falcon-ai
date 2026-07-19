import os
import cv2
import torch
import logging
import numpy as np
from typing import List, Dict, Any
from pathlib import Path
from transformers import VideoMAEImageProcessor, VideoMAEForVideoClassification
from torch.nn.functional import softmax
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class VideoMAEInference:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(VideoMAEInference, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, checkpoint_path: str = None):
        if self._initialized:
            return
            
        # Default checkpoint path assuming backend/app/services/videomae_inference.py
        if checkpoint_path is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            checkpoint_path = str(base_dir / "models" / "falcon_v1_checkpoint.pth")
            
        self.checkpoint_path = checkpoint_path
        self.device = self._get_device()
        self.model = None
        self.processor = None
        
        # Default fallback values
        self.class_names = ["Normal", "Stampede"]
        self.clip_length = settings.VIDEO_CLIP_LENGTH
        self.image_size = 224
        
        self._load_model()
        self._initialized = True

    def _get_device(self) -> torch.device:
        if torch.cuda.is_available():
            device = torch.device("cuda")
            logger.info("VideoMAEInference: Using CUDA device.")
        elif torch.backends.mps.is_available():
            device = torch.device("mps")
            logger.info("VideoMAEInference: Using MPS (Apple Silicon) device.")
        else:
            device = torch.device("cpu")
            logger.info("VideoMAEInference: Using CPU device.")
        return device

    def _load_model(self) -> None:
        try:
            logger.info(f"VideoMAEInference: Loading checkpoint from {self.checkpoint_path}...")
            
            if not os.path.exists(self.checkpoint_path):
                logger.error(f"VideoMAEInference: Checkpoint not found at {self.checkpoint_path}. Model will not be loaded.")
                return
                
            checkpoint = torch.load(self.checkpoint_path, map_location=self.device)
            
            # Restore metadata
            if "class_names" in checkpoint:
                self.class_names = checkpoint["class_names"]
            if "clip_length" in checkpoint:
                self.clip_length = checkpoint["clip_length"]
            if "image_size" in checkpoint:
                self.image_size = checkpoint["image_size"]
            
            logger.info(f"VideoMAEInference: Restored metadata: Classes={self.class_names}, Clip Length={self.clip_length}, Image Size={self.image_size}")
            
            # Load processor
            self.processor = VideoMAEImageProcessor.from_pretrained(
                "MCG-NJU/videomae-base",
                size={"shortest_edge": self.image_size}
            )
            
            # Load model architecture
            self.model = VideoMAEForVideoClassification.from_pretrained(
                "MCG-NJU/videomae-base",
                num_labels=len(self.class_names),
                ignore_mismatched_sizes=True
            )
            
            # Load state dict
            if "model_state_dict" in checkpoint:
                self.model.load_state_dict(checkpoint["model_state_dict"])
            else:
                raise KeyError("Checkpoint does not contain 'model_state_dict'")
                
            self.model.to(self.device)
            self.model.eval()
            
            logger.info("VideoMAEInference: Model loaded and initialized successfully.")
            
        except Exception as e:
            logger.error(f"VideoMAEInference: Failed to load VideoMAE model: {str(e)}")
            raise

    def predict(self, frames: List[np.ndarray]) -> Dict[str, Any]:
        """
        Predicts the class of a video clip given exactly 'clip_length' BGR frames.
        """
        try:
            if self.model is None or self.processor is None:
                if getattr(settings, "DEMO_MODE", False):
                    if getattr(settings, "SIMULATE_STAMPEDE", False):
                        logger.info("VideoMAEInference: DEMO_MODE=True and SIMULATE_STAMPEDE=True. Mocking 'Stampede' prediction.")
                        return {
                            "prediction": "Stampede",
                            "confidence": 0.99,
                            "probabilities": {"Stampede": 0.99, "Normal": 0.01}
                        }
                    else:
                        logger.info("VideoMAEInference: DEMO_MODE=True. Mocking 'Normal' prediction.")
                        return {
                            "prediction": "Normal",
                            "confidence": 0.99,
                            "probabilities": {"Normal": 0.99, "Stampede": 0.01}
                        }
                raise RuntimeError("VideoMAE model is not loaded. Cannot perform prediction.")

            if not isinstance(frames, list):
                raise ValueError("Input frames must be a list of numpy arrays.")
                
            if len(frames) != self.clip_length:
                raise ValueError(f"Expected exactly {self.clip_length} frames, but got {len(frames)}.")
                
            # Convert BGR (OpenCV) to RGB (PIL/Transformers)
            rgb_frames = [cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) for frame in frames]
            
            # Preprocess
            inputs = self.processor(list(rgb_frames), return_tensors="pt")
            pixel_values = inputs["pixel_values"].to(self.device)
            
            # Inference
            with torch.no_grad():
                outputs = self.model(pixel_values)
                logits = outputs.logits
                
                # Apply softmax
                probs = softmax(logits, dim=1).squeeze(0).cpu().numpy()
                
            # Extract results
            probabilities = {self.class_names[i]: float(probs[i]) for i in range(len(self.class_names))}
            pred_idx = int(np.argmax(probs))
            prediction = self.class_names[pred_idx]
            confidence = float(probs[pred_idx])
            
            return {
                "prediction": prediction,
                "confidence": round(confidence, 4),
                "probabilities": {k: round(v, 4) for k, v in probabilities.items()}
            }
            
        except Exception as e:
            logger.error(f"VideoMAEInference: Prediction failed: {str(e)}")
            raise

# Expose singleton instance
videomae_model = VideoMAEInference()
