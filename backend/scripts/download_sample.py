import os
import urllib.request
import argparse

def download_sample(output_path: str):
    # Using a generic safe video (Big Buck Bunny) as a dummy feed.
    # We do NOT condone downloading real-world stampede/disaster footage for testing.
    # To trigger the alert during a demo using this safe video, enable DEMO_MODE=True in .env
    url = "https://www.w3schools.com/html/mov_bbb.mp4"
    
    print("Downloading safe generic video feed (Big Buck Bunny) for pipeline testing...")
    print("CONSTRAINT: Using real tragedy footage for testing is strictly prohibited.")
    try:
        urllib.request.urlretrieve(url, output_path)
        print(f"Successfully downloaded to {output_path}")
        print("\n--> To trigger a simulated crowd crush alert using this safe video,")
        print("--> ensure DEMO_MODE=True in your backend/.env file.")
    except Exception as e:
        print(f"Error downloading video: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="sample_feed.mp4", help="Output path for the video")
    args = parser.parse_args()
    download_sample(args.output)
