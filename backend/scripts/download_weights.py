import os
import sys
import requests

WEIGHTS_URL = "https://huggingface.co/muasifk/CSRNet/resolve/main/0model_best.pth.tar?download=true"
WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), "..", "0model_best.pth.tar")

def main():
    print(f"Downloading CSRNet weights from {WEIGHTS_URL} ...")
    try:
        response = requests.get(WEIGHTS_URL, stream=True)
        response.raise_for_status()
        
        with open(WEIGHTS_PATH, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    
        print(f"Weights successfully downloaded to {os.path.abspath(WEIGHTS_PATH)}")
    except Exception as e:
        print(f"Failed to download weights: {e}")
        print("Please manually download the weights from a CSRNet repository (e.g. ShanghaiTech A) and place the .pth.tar file in the backend/ directory.")
        sys.exit(1)

if __name__ == "__main__":
    main()
