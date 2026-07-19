import sys
import os

def check_tensorflow():
    try:
        import tensorflow as tf
        print(f"TensorFlow {tf.__version__} is installed.")
        return tf
    except ImportError:
        print("TensorFlow is not installed.")
        print("Please install it by running:")
        print("pip install tensorflow")
        sys.exit(1)

def main():
    tf = check_tensorflow()
    
    # Locate the model in the backend/models directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(base_dir, "models", "anomaly_detector_ped2.keras")
    
    print(f"Loading model from {model_path}...")
    
    if not os.path.exists(model_path):
        print(f"Error: Model file not found at {model_path}")
        sys.exit(1)
        
    try:
        model = tf.keras.models.load_model(model_path)
        print("Model loaded successfully!")
        
        print("\n--- Model Summary ---")
        model.summary()
        
        print("\n--- Model Shapes ---")
        print(f"Input Shape: {model.input_shape}")
        print(f"Output Shape: {model.output_shape}")
        
    except Exception as e:
        print(f"Failed to load the model.")
        print(f"Exception: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
