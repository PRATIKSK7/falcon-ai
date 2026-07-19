import os
import threading
import logging
import time
from datetime import datetime

try:
    import tensorflow as tf
    import numpy as np
except ImportError:
    tf = None
    np = None

import sys
# Make sure config can be imported if running from backend root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings

logger = logging.getLogger(__name__)

class ModelLoader:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ModelLoader, cls).__new__(cls)
                cls._instance._model = None
                cls._instance._initialized = False
        return cls._instance
        
    def load_model(self):
        if self._initialized:
            return True
            
        with self._lock:
            if self._initialized:
                return True
                
            if tf is None:
                logger.error("TensorFlow is not installed. Cannot load model.")
                return False
                
            try:
                logger.info(f"Loading Keras model from {settings.MODEL_PATH}...")
                
                if settings.DEVICE == "cpu":
                    tf.config.set_visible_devices([], 'GPU')
                
                self._model = tf.keras.models.load_model(settings.MODEL_PATH)
                self._initialized = True
                logger.info("Keras model loaded successfully and cached in memory.")
                return True
            except Exception as e:
                logger.error(f"Failed to load Keras model: {str(e)}")
                return False
                
    def get_model(self):
        if not self._initialized:
            self.load_model()
        return self._model
        
    def predict(self, input_data):
        if not self._initialized:
            if not self.load_model():
                raise RuntimeError("Model could not be loaded for prediction.")
                
        if tf is None:
            raise RuntimeError("TensorFlow is not installed.")
            
        try:
            start_time = time.time()
            
            if not isinstance(input_data, (np.ndarray, tf.Tensor)):
                raise ValueError("Input data must be a numpy array or tensor.")
                
            # Predict and calculate MSE
            predictions = self._model.predict(input_data, verbose=0)
            processing_time = time.time() - start_time
            
            # Compute reconstruction error (MSE) per window
            mse_per_window = np.mean(np.square(input_data - predictions), axis=(1, 2, 3, 4))
            
            max_error = float(np.max(mse_per_window))
            
            label = "Stampede Detected" if max_error > settings.RECONSTRUCTION_THRESHOLD else "Normal"
            
            return {
                "status": "success",
                "prediction": label,
                "reconstruction_error": round(max_error, 5),
                "threshold": settings.RECONSTRUCTION_THRESHOLD,
                "processing_time": f"{round(processing_time * 1000, 2)} ms",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "model_version": "1.0"
            }
        except Exception as e:
            logger.error(f"Inference error: {str(e)}")
            raise

model_loader_instance = ModelLoader()

def get_model():
    return model_loader_instance.get_model()

def predict(input_data):
    return model_loader_instance.predict(input_data)
