import os
import cv2
import logging
import numpy as np
from typing import List, Generator, Tuple
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def load_video_frames(video_path: str) -> Generator[np.ndarray, None, None]:
    """
    Lazily loads frames from a video file.

    Args:
        video_path (str): The absolute or relative path to the video file.

    Yields:
        np.ndarray: An individual video frame in BGR format.

    Raises:
        FileNotFoundError: If the video file does not exist.
        IOError: If the video file cannot be opened.
        ValueError: If an empty frame is encountered unexpectedly.
    """
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        raise FileNotFoundError(f"Video file not found: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Failed to open video file: {video_path}")
        raise IOError(f"Failed to open video file: {video_path}")

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    logger.info(f"Opened video {video_path} with {frame_count} frames.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame is None or frame.size == 0:
                logger.error("Encountered an empty frame during video decoding.")
                raise ValueError("Encountered an empty frame during video decoding.")
                
            yield frame
    finally:
        cap.release()


def resize_frame(frame: np.ndarray, target_size: Tuple[int, int] = (224, 224)) -> np.ndarray:
    """
    Resizes a single OpenCV frame to the specified target dimensions.

    Args:
        frame (np.ndarray): The input image frame.
        target_size (Tuple[int, int], optional): The (width, height) to resize to. Defaults to (224, 224).

    Returns:
        np.ndarray: The resized frame.
        
    Raises:
        ValueError: If the input frame is empty or invalid.
    """
    if frame is None or frame.size == 0:
        raise ValueError("Cannot resize an empty or invalid frame.")
        
    return cv2.resize(frame, target_size, interpolation=cv2.INTER_LINEAR)


def prepare_clip(frames: List[np.ndarray], target_size: Tuple[int, int] = (224, 224)) -> List[np.ndarray]:
    """
    Prepares a batch of frames for VideoMAE inference by resizing and converting BGR to RGB.

    Args:
        frames (List[np.ndarray]): A list of BGR image frames.
        target_size (Tuple[int, int], optional): The (width, height) to resize to. Defaults to (224, 224).

    Returns:
        List[np.ndarray]: A list of RGB, resized image frames.

    Raises:
        ValueError: If the input list is empty.
    """
    if not frames:
        raise ValueError("The provided clip contains no frames.")

    processed_clip = []
    for frame in frames:
        resized_frame = resize_frame(frame, target_size)
        rgb_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
        processed_clip.append(rgb_frame)
        
    return processed_clip


def generate_clips_from_frames(
    frames_generator: Generator[np.ndarray, None, None], 
    clip_length: int = settings.VIDEO_CLIP_LENGTH, 
    stride: int = settings.VIDEO_STRIDE
) -> Generator[List[np.ndarray], None, None]:
    """
    Creates a sliding window over a generator of frames to produce fixed-length clips.

    Args:
        frames_generator (Generator[np.ndarray, None, None]): A generator yielding individual frames.
        clip_length (int, optional): The exact number of frames required per clip. Defaults to 16.
        stride (int, optional): The number of frames to advance the sliding window. Defaults to 8.

    Yields:
        List[np.ndarray]: A list of exactly `clip_length` preprocessed RGB frames.

    Raises:
        ValueError: If the total available frames are less than `clip_length`.
    """
    buffer = []
    clip_count = 0
    total_frames_processed = 0

    for frame in frames_generator:
        buffer.append(frame)
        total_frames_processed += 1

        if len(buffer) == clip_length:
            yield prepare_clip(buffer)
            clip_count += 1
            
            # Slide the window forward by dropping the oldest `stride` frames
            buffer = buffer[stride:]

    if total_frames_processed < clip_length:
        logger.error(f"Insufficient frames: Found {total_frames_processed}, but require at least {clip_length}.")
        raise ValueError(f"Video contains {total_frames_processed} frames, which is less than the required clip length of {clip_length}.")

    logger.info(f"Generated {clip_count} clips from {total_frames_processed} total frames.")


def generate_clips(
    video_path: str, 
    clip_length: int = settings.VIDEO_CLIP_LENGTH, 
    stride: int = settings.VIDEO_STRIDE
) -> Generator[List[np.ndarray], None, None]:
    """
    Streams a video file and generates sliding-window clips formatted for VideoMAE inference.

    Args:
        video_path (str): The absolute or relative path to the video file.
        clip_length (int, optional): The exact number of frames required per clip. Defaults to 16.
        stride (int, optional): The number of frames to advance the sliding window. Defaults to 8.

    Yields:
        List[np.ndarray]: A list of exactly `clip_length` preprocessed RGB frames.
    """
    logger.info(f"Starting sliding window clip generation for {video_path} (clip_length={clip_length}, stride={stride})")
    frames_generator = load_video_frames(video_path)
    yield from generate_clips_from_frames(frames_generator, clip_length=clip_length, stride=stride)
