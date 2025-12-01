import requests
import os
import time

def test_yolo():
    url = "http://localhost:8005/api/yolo/analyze"
    
    # Create a dummy video file (just text content, YOLO will fail to read it but the flow should work)
    # Ideally we need a real video. 
    # Let's try to use the one from previous test if it exists, or create a minimal one?
    # Actually, cv2.VideoCapture might fail on text file.
    # I'll create a dummy file and expect "processing_started".
    # The background task will fail on cv2.VideoCapture but that's okay for API testing.
    # If I want to verify full flow, I need a valid video.
    
    with open("test_yolo.mp4", "wb") as f:
        f.write(b"dummy video content")
        
    files = {"file": ("test_yolo.mp4", open("test_yolo.mp4", "rb"), "video/mp4")}
    data = {"conf_threshold": 0.4, "frame_skip": 1}
    
    try:
        print(f"Sending POST request to {url}...")
        response = requests.post(url, files=files, data=data)
        
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")
        
        if response.status_code == 200:
            print("YOLO API Test SUCCESS!")
        else:
            print("YOLO API Test FAILED!")
            
    except Exception as e:
        print(f"Test FAILED: {e}")
    finally:
        if os.path.exists("test_yolo.mp4"):
            os.remove("test_yolo.mp4")

if __name__ == "__main__":
    test_yolo()
