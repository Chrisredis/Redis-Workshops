#!/usr/bin/env python3
"""
Face Detection Test Tool

Quick test to verify face detection is working properly
"""

import cv2
import numpy as np
from datetime import datetime

def test_face_detection():
    """Test face detection functionality"""
    print("👤 Testing Face Detection")
    print("=" * 30)
    
    # Initialize camera
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        print("❌ Camera not available")
        return
    
    # Initialize face detection
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    if face_cascade.empty():
        print("❌ Face detection not available")
        camera.release()
        return
    
    print("✅ Camera and face detection initialized")
    print("\nControls:")
    print("  'q' - Quit")
    print("  'c' - Capture photo")
    print("\nLook at the camera - you should see green boxes around detected faces!")
    
    while True:
        ret, frame = camera.read()
        if not ret:
            break
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(100, 100)
        )
        
        # Draw rectangles around faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, "Face Detected!", (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Add status text
        cv2.putText(frame, f"Faces: {len(faces)}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Time: {datetime.now().strftime('%H:%M:%S')}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        if len(faces) > 0:
            cv2.putText(frame, "✅ Ready for capture!", (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "❌ No face detected", (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        cv2.imshow('Face Detection Test', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('c') and len(faces) > 0:
            # Save captured image
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"face_test_{timestamp}.jpg"
            cv2.imwrite(filename, frame)
            print(f"📸 Captured photo saved as: {filename}")
    
    camera.release()
    cv2.destroyAllWindows()
    print("👋 Face detection test completed")

if __name__ == "__main__":
    test_face_detection()
