import logging
from typing import Dict, Any, List

from app.services.video_preprocessor import generate_clips
from app.services.videomae_inference import videomae_model
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class VideoAnalysisService:
    """
    Service responsible for orchestrating the end-to-end video analysis pipeline.
    It links the video preprocessor (generating clips) with the VideoMAE inference model.
    """

    def __init__(self, 
                 stampede_threshold: float = settings.STAMPEDE_CONFIDENCE_THRESHOLD, 
                 min_consecutive_stampede_clips: int = settings.MIN_CONSECUTIVE_STAMPEDE_CLIPS, 
                 clip_length: int = settings.VIDEO_CLIP_LENGTH, 
                 stride: int = settings.VIDEO_STRIDE):
        """
        Initializes the VideoAnalysisService.

        Args:
            stampede_threshold (float, optional): The minimum confidence score required 
                for a clip to trigger a "Stampede" classification. Defaults to 0.90.
            min_consecutive_stampede_clips (int, optional): The number of consecutive clips 
                that must predict "Stampede" above the threshold to classify the video. Defaults to 3.
            clip_length (int, optional): Number of frames per clip. Defaults to 16.
            stride (int, optional): Number of frames to advance the sliding window. Defaults to 8.
        """
        self.stampede_threshold = stampede_threshold
        self.min_consecutive_stampede_clips = min_consecutive_stampede_clips
        self.clip_length = clip_length
        self.stride = stride

    def analyze_video(self, video_path: str) -> Dict[str, Any]:
        """
        Processes a full video file, extracts sliding-window clips, runs inference 
        on each clip, and determines a final aggregated prediction for the video.

        The aggregation strategy classifies the entire video as "Stampede" if a sequence of 
        at least `min_consecutive_stampede_clips` consecutive clips predict "Stampede" 
        with a confidence greater than or equal to the configured threshold.

        Args:
            video_path (str): The absolute or relative path to the video file.

        Returns:
            Dict[str, Any]: A dictionary containing the final aggregated prediction, 
                highest confidence score, processing metrics, and detailed results 
                for every individual clip.

        Raises:
            Exception: If clip generation or model inference fails.
        """
        logger.info(f"VideoAnalysisService: Starting analysis for video: {video_path}")

        try:
            clips_generator = generate_clips(
                video_path=video_path,
                clip_length=self.clip_length,
                stride=self.stride
            )

            clips_processed = 0
            stampede_clips = 0
            normal_clips = 0
            clip_results: List[Dict[str, Any]] = []

            final_prediction = "Normal"
            highest_stampede_confidence = 0.0
            highest_normal_confidence = 0.0
            
            current_consecutive_stampede = 0
            max_consecutive_stampede = 0

            for clip_index, clip_frames in enumerate(clips_generator):
                logger.debug(f"VideoAnalysisService: Processing clip {clip_index}...")
                
                # Perform inference on the 16-frame RGB clip
                result = videomae_model.predict(clip_frames)
                
                prediction = result.get("prediction", "Normal")
                confidence = result.get("confidence", 0.0)
                probabilities = result.get("probabilities", {})

                # Record individual clip result
                clip_results.append({
                    "clip_index": clip_index,
                    "prediction": prediction,
                    "confidence": confidence,
                    "probabilities": probabilities
                })

                clips_processed += 1

                # Track statistics and highest confidence
                if prediction == "Stampede":
                    stampede_clips += 1
                    if confidence > highest_stampede_confidence:
                        highest_stampede_confidence = confidence
                else:
                    normal_clips += 1
                    if confidence > highest_normal_confidence:
                        highest_normal_confidence = confidence

                # Aggregation Strategy: Consecutive threshold checks
                if prediction == "Stampede" and confidence >= self.stampede_threshold:
                    current_consecutive_stampede += 1
                else:
                    current_consecutive_stampede = 0
                    
                if current_consecutive_stampede > max_consecutive_stampede:
                    max_consecutive_stampede = current_consecutive_stampede

            # Final decision based on consecutive clips
            if max_consecutive_stampede >= self.min_consecutive_stampede_clips:
                final_prediction = "Stampede"
                decision_reason = f"Detected {max_consecutive_stampede} consecutive stampede clips above confidence threshold."
            else:
                final_prediction = "Normal"
                decision_reason = "No sequence met the configured threshold."

            logger.info(
                f"VideoAnalysisService: Completed analysis. Processed {clips_processed} clips. "
                f"Stampede clips: {stampede_clips}, Normal clips: {normal_clips}."
            )

            # Determine final confidence based on the aggregated prediction
            final_confidence = highest_stampede_confidence if final_prediction == "Stampede" else highest_normal_confidence

            # Handle edge case where video was too short to yield any clips
            if clips_processed == 0:
                logger.warning("VideoAnalysisService: No clips were processed. Returning default Normal prediction.")
                final_confidence = 0.0
                decision_reason = "Video too short to process."

            return {
                "prediction": final_prediction,
                "confidence": round(final_confidence, 4),
                "clips_processed": clips_processed,
                "stampede_clips": stampede_clips,
                "normal_clips": normal_clips,
                "max_consecutive_stampede_clips": max_consecutive_stampede,
                "decision_reason": decision_reason,
                "clip_results": clip_results
            }

        except Exception as e:
            logger.error(f"VideoAnalysisService: Analysis failed for {video_path}. Error: {str(e)}")
            raise

# Expose a default instance for easy imports across the backend
video_analyzer = VideoAnalysisService()
