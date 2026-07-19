import logging
from typing import List
from fastapi import APIRouter, HTTPException, File, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import sys
import os
import tempfile
import cv2
import numpy as np
import json
import time
from collections import deque
import asyncio
from twilio.rest import Client

backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from app.services.videomae_inference import videomae_model
from services.model_loader import predict as keras_predict
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])

class AIHealthResponse(BaseModel):
    backend_running: bool
    tensorflow_loaded: bool
    model_loaded: bool
    opencv_available: bool
    twilio_configured: bool
    gpu_cpu_status: str
    api_version: str

@router.get("/health", response_model=AIHealthResponse)
async def ai_health():
    import psutil
    try:
        from services.model_loader import model_loader_instance
        import tensorflow as tf
        
        tf_version = tf.__version__ if tf else "Not Installed"
        
        opencv_available = hasattr(cv2, '__version__')
        
        twilio_configured = bool(settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN)
        
        # Simple GPU check for TF
        gpu_cpu_status = "GPU" if tf.config.list_physical_devices('GPU') else "CPU"
        
        return AIHealthResponse(
            backend_running=True,
            tensorflow_loaded=True,
            model_loaded=model_loader_instance._model is not None,
            opencv_available=opencv_available,
            twilio_configured=twilio_configured,
            gpu_cpu_status=gpu_cpu_status,
            api_version="v2.1.0"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking AI health: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while checking AI health.")


def trigger_twilio_alert(mse=0.0):
    """Triggers an actual Twilio call"""
    print("\n" + "="*50)
    print(f"[✓] Triggering Twilio (Reconstruction Error: {mse:.4f})")
    print("="*50 + "\n")
    
    # 1. Verify Configuration
    missing = []
    if not settings.TWILIO_ACCOUNT_SID: missing.append("TWILIO_ACCOUNT_SID")
    if not settings.TWILIO_AUTH_TOKEN: missing.append("TWILIO_AUTH_TOKEN")
    if not settings.TWILIO_PHONE_NUMBER: missing.append("TWILIO_PHONE_NUMBER")
    if not settings.TWILIO_DESTINATION_NUMBER: missing.append("DESTINATION_PHONE_NUMBER")
    
    if missing:
        error_msg = f"Missing Twilio Variables: {', '.join(missing)}"
        print(f"[X] {error_msg}")
        return False, error_msg

    try:
        # 2. Authenticate
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        # 3. Voice Message (Inline TwiML)
        twiml = f"""
        <Response>
            <Say voice="Polly.Aditi">
                Attention. This is an automated emergency alert from FALCON AI. A potential stampede has been detected. Immediate police response is recommended.
            </Say>
        </Response>
        """
        
        print(f"Calling Number: {settings.TWILIO_PHONE_NUMBER}")
        print(f"Destination Number: {settings.TWILIO_DESTINATION_NUMBER}")
        
        # 4. Create Call
        call = client.calls.create(
            twiml=twiml,
            to=settings.TWILIO_DESTINATION_NUMBER,
            from_=settings.TWILIO_PHONE_NUMBER
        )
        
        # 5. Success Log
        print("✓ Twilio authenticated")
        print("✓ Call created")
        print(f"✓ Call SID: {call.sid}")
        print(f"✓ Call Status: {call.status}")
        
        return True, {"sid": call.sid, "status": call.status}

    except Exception as e:
        # 6. Error Logging
        from twilio.base.exceptions import TwilioRestException
        if isinstance(e, TwilioRestException):
            error_details = (f"Twilio Error Code: {e.code}\n"
                             f"HTTP Status: {e.status}\n"
                             f"Error Message: {e.msg}")
            print(f"[X] TwilioRestException:\n{error_details}")
            
            if "unverified" in e.msg.lower():
                print("Suggested Fix: Destination number must be verified in the Twilio Console.")
            return False, error_details
        else:
            print(f"[X] Failed to trigger Twilio call: {e}")
            return False, str(e)


@router.post("/test-call")
async def test_twilio_call():
    """Standalone endpoint to place a test voice call immediately."""
    success, result = trigger_twilio_alert()
    if not success:
        raise HTTPException(status_code=500, detail=result)
    return {"message": "Test call successfully initiated", "details": result}


@router.post("/predict_stream")
async def predict_stream_endpoint(file: UploadFile = File(...)):
    """
    Robust Streaming endpoint using Server-Sent Events (SSE).
    """
    print(f"\n[✓] Video uploaded: {file.filename}")
    
    # Save upload to a temp file
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            content = await file.read()
            tmp.write(content)
            temp_path = tmp.name
        print(f"[✓] File saved to {temp_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File save failed: {str(e)}")

    async def event_generator():
        try:
            # 4. Open video using OpenCV
            cap = cv2.VideoCapture(temp_path)
            if not cap.isOpened():
                error_msg = "Video could not be opened using OpenCV."
                print(f"[X] {error_msg}")
                yield f"data: {json.dumps({'status': 'error', 'message': error_msg})}\n\n"
                return
            
            print("[✓] Video opened successfully")
            
            frame_buffer = deque(maxlen=10)
            frame_count = 0
            twilio_triggered = False
            
            while True:
                ret, frame = cap.read()
                
                # 5. Read first frame verification
                if not ret:
                    if frame_count == 0:
                        error_msg = "Frame 1 read failed. Video may be empty."
                        print(f"[X] {error_msg}")
                        yield f"data: {json.dumps({'status': 'error', 'message': error_msg})}\n\n"
                    else:
                        print(f"[✓] End of video reached after {frame_count} frames")
                    break
                
                if frame_count == 0:
                    print("[✓] Frame 1 read successfully")
                
                # 7. Preprocessing exactly to model specifications
                try:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    resized = cv2.resize(gray, (96, 96))
                    normalized = resized / 255.0
                    frame_buffer.append(normalized)
                except Exception as e:
                    error_msg = f"Optical Flow / Preprocessing failed: {str(e)}"
                    print(f"[X] {error_msg}")
                    yield f"data: {json.dumps({'status': 'error', 'message': error_msg})}\n\n"
                    break

                frame_count += 1
                
                # 10. Perform inference every sliding window (e.g., every 5 frames once buffer is full)
                if len(frame_buffer) == 10 and frame_count % 5 == 0:
                    try:
                        # 9. Verify input tensor shape exactly matches (1, 10, 96, 96, 1)
                        window_np = np.array(frame_buffer, dtype=np.float32)
                        window_np = np.expand_dims(window_np, axis=-1)
                        batch_np = np.expand_dims(window_np, axis=0)
                        
                        # AI inference
                        result = keras_predict(batch_np)
                        
                        # Add tracking fields for SSE
                        result['frame'] = frame_count
                        result['is_stream'] = True
                        
                        mse = result.get('reconstruction_error', 0)
                        print(f"[✓] AI inference complete (Frame {frame_count}). Anomaly score = {mse:.4f}")
                        
                        # 6, 12. If threshold exceeded, immediately call Twilio ONE time
                        if result.get("prediction") == "Stampede Detected":
                            print(f"[✓] Threshold exceeded!")
                            if not twilio_triggered:
                                twilio_triggered = True
                                # Trigger without blocking the video pipeline
                                asyncio.create_task(asyncio.to_thread(trigger_twilio_alert, mse))
                        
                        # 11. Return prediction immediately to UI
                        yield f"data: {json.dumps(result)}\n\n"
                        
                        # Small sleep to allow other async tasks to run and yield to the network buffer
                        await asyncio.sleep(0.01)
                        
                    except Exception as e:
                        error_msg = f"TensorFlow inference failed: {str(e)}"
                        print(f"[X] {error_msg}")
                        yield f"data: {json.dumps({'status': 'error', 'message': error_msg})}\n\n"
                        break
                        
            # Final cleanup
            cap.release()
            print("[✓] Sequence ready, cleaning up resources.")
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    return StreamingResponse(event_generator(), media_type="text/event-stream")
