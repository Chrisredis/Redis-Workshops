#!/usr/bin/env python3
"""
Camera Manager - Proper camera lifecycle management

Opens camera, captures photo, closes camera immediately.
"""

import cv2
import numpy as np
import base64
from datetime import datetime
import time

class CameraManager:
    def __init__(self):
        """Initialize camera manager"""
        self.camera = None
        self.face_cascade = None
        self.init_face_detection()
    
    def init_face_detection(self):
        """Initialize face detection"""
        try:
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            if self.face_cascade.empty():
                print("⚠️ Face detection not available")
                self.face_cascade = None
            else:
                print("✅ Face detection ready")
        except Exception as e:
            print(f"⚠️ Face detection error: {e}")
            self.face_cascade = None
    
    def open_camera(self):
        """Open camera"""
        try:
            self.camera = cv2.VideoCapture(0)
            if self.camera.isOpened():
                # Set camera properties
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                print("📷 Camera opened")
                return True
            else:
                print("❌ Camera not available")
                return False
        except Exception as e:
            print(f"❌ Camera error: {e}")
            return False
    
    def close_camera(self):
        """Close camera and cleanup"""
        if self.camera:
            self.camera.release()
            self.camera = None
        cv2.destroyAllWindows()
        print("📷 Camera closed")
    
    def capture_photo_with_face_detection(self, customer_id: str, timeout_seconds: int = 30) -> str:
        """
        Capture photo with face detection
        Opens camera, captures when face detected, closes camera
        """
        print(f"\n📷 Capturing photo for {customer_id}")
        print("=" * 40)
        
        # Open camera
        if not self.open_camera():
            return self.generate_demo_photo(customer_id)
        
        print("🎯 Position your face in the camera")
        print("📸 Press 'c' when you see the green box around your face")
        print("⏰ Auto-timeout in 30 seconds")
        print("❌ Press 'q' to cancel")
        
        start_time = time.time()
        captured_photo = None
        
        try:
            while True:
                # Check timeout
                if time.time() - start_time > timeout_seconds:
                    print("⏰ Timeout - using last frame")
                    ret, frame = self.camera.read()
                    if ret:
                        captured_photo = frame
                    break
                
                ret, frame = self.camera.read()
                if not ret:
                    print("❌ Camera read failed")
                    break
                
                # Detect faces
                faces = []
                if self.face_cascade is not None:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = self.face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(50, 50))
                
                # Draw face boxes
                display_frame = frame.copy()
                for (x, y, w, h) in faces:
                    cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
                    cv2.putText(display_frame, "FACE DETECTED!", (x, y-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Add overlay
                cv2.putText(display_frame, f"Customer: {customer_id}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                cv2.putText(display_frame, f"Faces: {len(faces)}", (10, 70), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                
                remaining_time = int(timeout_seconds - (time.time() - start_time))
                cv2.putText(display_frame, f"Timeout: {remaining_time}s", (10, 110), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                
                if len(faces) > 0:
                    cv2.putText(display_frame, "✅ READY - Press 'c' to capture!", (10, 150), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                else:
                    cv2.putText(display_frame, "👤 Position face in camera", (10, 150), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                
                cv2.imshow('Face Detection - Press C to Capture', display_frame)
                
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('c') and len(faces) > 0:
                    captured_photo = frame.copy()
                    print(f"📸 Photo captured with {len(faces)} face(s)!")
                    break
                elif key == ord('q'):
                    print("❌ Cancelled by user")
                    break
        
        finally:
            # Always close camera
            self.close_camera()
        
        if captured_photo is not None:
            # Process and encode photo
            storage_photo = cv2.resize(captured_photo, (320, 240))
            _, buffer = cv2.imencode('.jpg', storage_photo)
            photo_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Show captured photo briefly
            cv2.imshow('✅ CAPTURED PHOTO', storage_photo)
            print("✅ Photo captured successfully!")
            print("Press any key to continue...")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            
            return photo_base64
        else:
            print("❌ No photo captured")
            return self.generate_demo_photo(customer_id)
    
    def generate_demo_photo(self, customer_id: str) -> str:
        """Generate demo photo when camera not available"""
        print("🖼️ Generating demo photo...")
        
        img = np.random.randint(100, 200, (240, 320, 3), dtype=np.uint8)
        
        # Draw simple face
        cv2.circle(img, (160, 120), 60, (220, 200, 180), -1)  # Face
        cv2.circle(img, (140, 100), 8, (0, 0, 0), -1)   # Left eye
        cv2.circle(img, (180, 100), 8, (0, 0, 0), -1)   # Right eye
        cv2.ellipse(img, (160, 140), (20, 10), 0, 0, 180, (0, 0, 0), 2)  # Mouth
        
        # Add text
        cv2.putText(img, f"Customer: {customer_id}", (20, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(img, "DEMO FACE PHOTO", (20, 200), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(img, f"Time: {datetime.now().strftime('%H:%M:%S')}", (20, 220), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        cv2.imshow('Demo Face Photo', img)
        print("🖼️ Demo photo generated - press any key to continue")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        _, buffer = cv2.imencode('.jpg', img)
        return base64.b64encode(buffer).decode('utf-8')

# Example usage
if __name__ == "__main__":
    camera_mgr = CameraManager()
    
    print("📷 Camera Manager Test")
    print("=" * 30)
    
    customer_id = input("Enter customer ID (or press Enter for TEST): ").strip()
    if not customer_id:
        customer_id = "TEST"
    
    photo_data = camera_mgr.capture_photo_with_face_detection(customer_id)
    
    if photo_data:
        print(f"✅ Photo captured! Size: {len(photo_data)} characters")
    else:
        print("❌ Photo capture failed")
