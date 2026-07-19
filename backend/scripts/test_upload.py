import sys
import time
import requests
import argparse

BASE_URL = "http://localhost:8000/api/v1/incidents"

def main():
    parser = argparse.ArgumentParser(description="Test Video Upload and Status Polling")
    parser.add_argument("video_path", help="Path to the video file to upload (.mp4 or .avi)")
    args = parser.parse_args()

    # 1. Upload the video
    print(f"Uploading {args.video_path}...")
    try:
        with open(args.video_path, "rb") as f:
            files = {"file": f}
            response = requests.post(f"{BASE_URL}/upload", files=files)
            response.raise_for_status()
    except Exception as e:
        print(f"Upload failed: {e}")
        sys.exit(1)

    data = response.json()
    job_id = data.get("job_id")
    print(f"Upload successful. Job ID: {job_id}")

    # 2. Poll for status
    while True:
        try:
            status_res = requests.get(f"{BASE_URL}/{job_id}/status")
            status_res.raise_for_status()
            status_data = status_res.json()
            status = status_data.get("status")
            print(f"Current status: {status}")
            
            if status in ["COMPLETED", "FAILED"]:
                print(f"Processing finished with status: {status}")
                break
        except Exception as e:
            print(f"Failed to check status: {e}")
            break
            
        time.sleep(2)

if __name__ == "__main__":
    main()
