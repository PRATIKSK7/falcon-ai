import requests
import os
import time

API_URL = "http://localhost:8000/api/v1"

def create_corrupt_file():
    path = "corrupt.mp4"
    with open(path, "w") as f:
        f.write("This is not a video file")
    return path

def test_corrupt_file():
    print("--- Testing Corrupt File ---")
    path = create_corrupt_file()
    try:
        with open(path, "rb") as f:
            res = requests.post(f"{API_URL}/incidents/upload", data={"camera_id": 1}, files={"file": ("corrupt.mp4", f, "video/mp4")})
        print(f"Status: {res.status_code}")
        print(f"Response: {res.text}")
    finally:
        os.remove(path)

def test_pipeline(demo_mode: bool):
    print(f"\n--- Testing Pipeline (DEMO_MODE={demo_mode}) ---")
    # Toggle demo mode safely using backend's config if possible? 
    # Can't dynamically toggle from API unless we have an endpoint. 
    # For now, rely on .env (It's set to True currently)
    path = "sample_feed.mp4"
    if not os.path.exists(path):
        print(f"Please run download_sample.py first.")
        return

    with open(path, "rb") as f:
        res = requests.post(f"{API_URL}/incidents/upload", data={"camera_id": 1}, files={"file": ("sample_feed.mp4", f, "video/mp4")})
        
    if res.status_code != 200:
        print(f"Upload Failed: {res.text}")
        return
        
    job_id = res.json()["id"]
    print(f"Uploaded! Job ID: {job_id}")
    
    # Poll
    while True:
        status_res = requests.get(f"{API_URL}/incidents/{job_id}")
        if status_res.status_code != 200:
            print(f"Error fetching status: {status_res.status_code} - {status_res.text}")
            break
        data = status_res.json()
        print(f"Status: {data['status']}, Frames Processed: {len(data.get('frames', []))}")
        if data["status"] in ["COMPLETED", "FAILED"]:
            print(f"Final Peak Severity: {data.get('peak_severity')}")
            break
        time.sleep(2)

if __name__ == "__main__":
    test_corrupt_file()
    # Ensure sample_feed.mp4 exists
    if not os.path.exists("sample_feed.mp4"):
        print("Downloading sample...")
        os.system("python3 scripts/download_sample.py")
    test_pipeline(demo_mode=True)
