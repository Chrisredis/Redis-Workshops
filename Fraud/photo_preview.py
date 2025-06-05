#!/usr/bin/env python3
"""
Photo Preview Tool for Fraud Detection Demo

This script shows the camera feed and allows you to capture photos
to see what will be stored with transactions.
"""

import cv2
import numpy as np
import base64
import time
from datetime import datetime
import os

class PhotoPreview:
    def __init__(self):
        self.camera = None
        self.init_camera()
    
    def init_camera(self):
        """Initialize camera"""
        try:
            self.camera = cv2.VideoCapture(0)
            if self.camera.isOpened():
                print("📷 Camera initialized successfully!")
                print("Press 'c' to capture photo, 'q' to quit")
                return True
            else:
                print("⚠️ Camera not available")
                return False
        except Exception as e:
            print(f"❌ Camera error: {e}")
            return False
    
    def show_preview(self):
        """Show live camera preview"""
        if not self.camera or not self.camera.isOpened():
            print("❌ Camera not available")
            return None
        
        print("\n🎥 Starting camera preview...")
        print("Controls:")
        print("  'c' - Capture photo")
        print("  's' - Save captured photo")
        print("  'q' - Quit")
        
        captured_photo = None
        
        while True:
            ret, frame = self.camera.read()
            if not ret:
                print("❌ Failed to read from camera")
                break
            
            # Resize for display
            display_frame = cv2.resize(frame, (640, 480))
            
            # Add overlay text
            cv2.putText(display_frame, f"Fraud Detection Demo - {datetime.now().strftime('%H:%M:%S')}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            if captured_photo is not None:
                cv2.putText(display_frame, "Photo Captured! Press 's' to save", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            else:
                cv2.putText(display_frame, "Press 'c' to capture photo", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imshow('Fraud Detection - Customer Photo Preview', display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('c'):
                # Capture photo
                captured_photo = frame.copy()
                print("📸 Photo captured!")
                
                # Show captured photo in separate window
                capture_display = cv2.resize(captured_photo, (320, 240))
                cv2.putText(capture_display, "CAPTURED", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.imshow('Captured Photo', capture_display)
            
            elif key == ord('s') and captured_photo is not None:
                # Save photo
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"customer_photo_{timestamp}.jpg"
                cv2.imwrite(filename, captured_photo)
                print(f"💾 Photo saved as: {filename}")
                
                # Convert to base64 for Redis storage
                _, buffer = cv2.imencode('.jpg', cv2.resize(captured_photo, (320, 240)))
                photo_base64 = base64.b64encode(buffer).decode('utf-8')
                
                print(f"📊 Photo size: {len(photo_base64)} characters (base64)")
                print("✅ Photo ready for transaction processing!")
                
                return photo_base64
            
            elif key == ord('q'):
                break
        
        cv2.destroyAllWindows()
        return captured_photo
    
    def capture_single_photo(self):
        """Capture a single photo without preview"""
        if not self.camera or not self.camera.isOpened():
            print("❌ Camera not available")
            return None
        
        print("📸 Capturing photo...")
        ret, frame = self.camera.read()
        
        if ret:
            # Resize for storage efficiency
            frame = cv2.resize(frame, (320, 240))
            
            # Convert to base64
            _, buffer = cv2.imencode('.jpg', frame)
            photo_base64 = base64.b64encode(buffer).decode('utf-8')
            
            print("✅ Photo captured successfully!")
            return photo_base64
        else:
            print("❌ Failed to capture photo")
            return None
    
    def generate_demo_photo(self, customer_name="Demo Customer"):
        """Generate a demo photo with customer info"""
        # Create a demo image
        img = np.random.randint(50, 200, (240, 320, 3), dtype=np.uint8)
        
        # Add customer info
        cv2.putText(img, customer_name, (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(img, f"Time: {datetime.now().strftime('%H:%M:%S')}", 
                   (50, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(img, "FRAUD DETECTION DEMO", 
                   (50, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        cv2.putText(img, "Photo Verification", 
                   (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Convert to base64
        _, buffer = cv2.imencode('.jpg', img)
        photo_base64 = base64.b64encode(buffer).decode('utf-8')
        
        print(f"🖼️ Generated demo photo for {customer_name}")
        return photo_base64
    
    def cleanup(self):
        """Clean up camera resources"""
        if self.camera:
            self.camera.release()
        cv2.destroyAllWindows()

def main():
    """Main function"""
    print("\n📷 Photo Preview Tool for Fraud Detection Demo")
    print("=" * 50)
    
    preview = PhotoPreview()
    
    try:
        while True:
            print("\nOptions:")
            print("1. Show Camera Preview (Live)")
            print("2. Capture Single Photo")
            print("3. Generate Demo Photo")
            print("4. Test Camera")
            print("5. Exit")
            
            choice = input("\nSelect option (1-5): ").strip()
            
            if choice == "1":
                photo_data = preview.show_preview()
                if photo_data:
                    print("📸 Photo captured and ready for use!")
            
            elif choice == "2":
                photo_data = preview.capture_single_photo()
                if photo_data:
                    print("📸 Photo captured successfully!")
                    print(f"📊 Photo data length: {len(photo_data)} characters")
            
            elif choice == "3":
                customer_name = input("Customer name (default: Demo Customer): ").strip()
                if not customer_name:
                    customer_name = "Demo Customer"
                
                photo_data = preview.generate_demo_photo(customer_name)
                print("🖼️ Demo photo generated!")
                print(f"📊 Photo data length: {len(photo_data)} characters")
            
            elif choice == "4":
                if preview.camera and preview.camera.isOpened():
                    print("✅ Camera is working!")
                    ret, frame = preview.camera.read()
                    if ret:
                        print("✅ Can capture frames!")
                        cv2.imshow('Camera Test', cv2.resize(frame, (320, 240)))
                        print("Press any key to close test window...")
                        cv2.waitKey(0)
                        cv2.destroyAllWindows()
                    else:
                        print("❌ Cannot capture frames")
                else:
                    print("❌ Camera not available")
            
            elif choice == "5":
                break
            
            else:
                print("Invalid option. Please try again.")
    
    except KeyboardInterrupt:
        print("\n\n👋 Exiting photo preview...")
    
    finally:
        preview.cleanup()

if __name__ == "__main__":
    main()
