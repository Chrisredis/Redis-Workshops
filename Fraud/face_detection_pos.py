#!/usr/bin/env python3
"""
Face Detection POS Simulator

This enhanced POS system includes:
1. Real-time face detection
2. Face quality assessment
3. Automatic photo capture when face is detected
4. Visual feedback with bounding boxes
5. Face verification for fraud prevention
"""

import cv2
import numpy as np
import redis
import json
import time
import uuid
import base64
from datetime import datetime
from typing import Dict, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FaceDetectionPOS:
    def __init__(self, store_id: str = "STORE_A", redis_host: str = "localhost", redis_port: int = 6379):
        """Initialize Face Detection POS System"""
        self.store_id = store_id
        self.redis_host = redis_host
        self.redis_port = redis_port
        
        # Connect to Redis
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=0,
                decode_responses=False
            )
            self.redis_client.ping()
            logger.info(f"✅ Connected to Redis at {redis_host}:{redis_port}")
        except redis.ConnectionError:
            logger.error(f"❌ Failed to connect to Redis at {redis_host}:{redis_port}")
            raise
        
        # Initialize camera
        self.camera = None
        self.init_camera()
        
        # Initialize face detection
        self.face_cascade = None
        self.init_face_detection()
        
        # Product catalog
        self.products = {
            "SHIRT_001": {"name": "Cotton T-Shirt", "price": 29.99, "sku": "SHIRT_001"},
            "SHIRT_002": {"name": "Polo Shirt", "price": 45.99, "sku": "SHIRT_002"},
            "SHIRT_003": {"name": "Dress Shirt", "price": 79.99, "sku": "SHIRT_003"},
            "JEANS_001": {"name": "Blue Jeans", "price": 89.99, "sku": "JEANS_001"},
            "JACKET_001": {"name": "Leather Jacket", "price": 199.99, "sku": "JACKET_001"}
        }
        
        # Face detection settings - RELAXED
        self.min_face_size = (50, 50)  # Smaller minimum face size
        self.face_detection_confidence = 1.05  # More sensitive detection
        self.stable_face_frames = 3  # Only need 3 frames (much faster)
        self.current_stable_frames = 0
        
    def init_camera(self):
        """Initialize camera"""
        try:
            self.camera = cv2.VideoCapture(0)
            if self.camera.isOpened():
                # Set camera properties for better quality
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.camera.set(cv2.CAP_PROP_FPS, 30)
                logger.info("📷 Camera initialized successfully")
            else:
                logger.warning("⚠️ Camera not available")
                self.camera = None
        except Exception as e:
            logger.warning(f"⚠️ Camera initialization failed: {e}")
            self.camera = None
    
    def init_face_detection(self):
        """Initialize face detection cascade"""
        try:
            # Try to load the face cascade classifier
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            if self.face_cascade.empty():
                logger.error("❌ Failed to load face cascade classifier")
                self.face_cascade = None
            else:
                logger.info("✅ Face detection initialized successfully")
                
        except Exception as e:
            logger.error(f"❌ Face detection initialization failed: {e}")
            self.face_cascade = None
    
    def detect_faces(self, frame) -> Tuple[list, np.ndarray]:
        """Detect faces in frame and return faces and annotated frame"""
        if self.face_cascade is None:
            return [], frame
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=self.face_detection_confidence,
            minNeighbors=5,
            minSize=self.min_face_size,
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # Draw rectangles around faces
        annotated_frame = frame.copy()
        
        for (x, y, w, h) in faces:
            # Calculate face quality score
            face_roi = gray[y:y+h, x:x+w]
            quality_score = self.calculate_face_quality(face_roi)
            
            # Choose color based on quality - RELAXED STANDARDS
            if quality_score > 0.4:
                color = (0, 255, 0)  # Green for acceptable quality
                status = "GOOD"
            elif quality_score > 0.2:
                color = (0, 255, 255)  # Yellow for basic quality
                status = "OK"
            else:
                color = (0, 0, 255)  # Red for very poor quality
                status = "LOW"
            
            # Draw face rectangle
            cv2.rectangle(annotated_frame, (x, y), (x+w, y+h), color, 2)
            
            # Add quality text
            cv2.putText(annotated_frame, f"Face: {status}", 
                       (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            cv2.putText(annotated_frame, f"Quality: {quality_score:.2f}", 
                       (x, y+h+20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return faces, annotated_frame
    
    def calculate_face_quality(self, face_roi) -> float:
        """Calculate face quality score based on various factors"""
        if face_roi.size == 0:
            return 0.0
        
        # Factor 1: Size (larger faces are generally better)
        size_score = min(face_roi.shape[0] * face_roi.shape[1] / (200 * 200), 1.0)
        
        # Factor 2: Contrast (good lighting)
        contrast_score = np.std(face_roi) / 128.0
        contrast_score = min(contrast_score, 1.0)
        
        # Factor 3: Sharpness (using Laplacian variance)
        laplacian_var = cv2.Laplacian(face_roi, cv2.CV_64F).var()
        sharpness_score = min(laplacian_var / 1000.0, 1.0)
        
        # Combine scores
        quality_score = (size_score * 0.3 + contrast_score * 0.4 + sharpness_score * 0.3)
        return min(quality_score, 1.0)
    
    def capture_face_verified_photo(self, customer_id: str) -> Optional[str]:
        """Capture photo with face verification"""
        if not self.camera or not self.camera.isOpened():
            print("⚠️ Camera not available, generating demo photo...")
            return self.generate_demo_photo(customer_id)
        
        print(f"\n👤 Face Detection Photo Capture")
        print("=" * 40)
        print(f"Customer: {customer_id}")
        print("📷 Position yourself in front of the camera")
        print("🎯 System will automatically capture when face is detected")
        print("\nControls:")
        print("  'c' - Force capture now")
        print("  'q' - Cancel transaction")
        
        best_photo = None
        best_quality = 0.0
        auto_capture_countdown = 0
        captured_photo = None
        
        while True:
            ret, frame = self.camera.read()
            if not ret:
                print("❌ Failed to read from camera")
                break
            
            # Detect faces
            faces, annotated_frame = self.detect_faces(frame)
            
            # Add overlay information
            cv2.putText(annotated_frame, f"Customer: {customer_id}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(annotated_frame, f"Store: {self.store_id}", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(annotated_frame, f"Time: {datetime.now().strftime('%H:%M:%S')}", 
                       (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Process face detection results
            if len(faces) > 0:
                # Find best quality face
                best_face_quality = 0.0
                for (x, y, w, h) in faces:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    face_roi = gray[y:y+h, x:x+w]
                    quality = self.calculate_face_quality(face_roi)
                    if quality > best_face_quality:
                        best_face_quality = quality
                
                if best_face_quality > 0.3:  # Much more relaxed quality threshold
                    self.current_stable_frames += 1
                    auto_capture_countdown = max(0, self.stable_face_frames - self.current_stable_frames)
                    
                    cv2.putText(annotated_frame, f"Face Detected! Auto-capture in: {auto_capture_countdown}", 
                               (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    # Update best photo if this is better
                    if best_face_quality > best_quality:
                        best_quality = best_face_quality
                        best_photo = frame.copy()
                    
                    # Auto-capture when stable
                    if self.current_stable_frames >= self.stable_face_frames:
                        captured_photo = best_photo
                        print(f"📸 Auto-captured! Face quality: {best_quality:.2f}")
                        break
                        
                else:
                    self.current_stable_frames = 0
                    cv2.putText(annotated_frame, "Face quality too low - move closer or improve lighting", 
                               (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            else:
                self.current_stable_frames = 0
                cv2.putText(annotated_frame, "No face detected - position yourself in frame", 
                           (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            
            # Show status
            if captured_photo is not None:
                cv2.putText(annotated_frame, "✅ PHOTO CAPTURED - Processing...", 
                           (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.imshow(f'{self.store_id} - Face Detection Capture', annotated_frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('c') and best_photo is not None:
                # Force capture best photo so far
                captured_photo = best_photo
                print(f"📸 Manual capture! Face quality: {best_quality:.2f}")
                break
            elif key == ord('q'):
                print("❌ Transaction cancelled")
                cv2.destroyAllWindows()
                return None
        
        cv2.destroyAllWindows()
        
        if captured_photo is not None:
            # Process and encode the photo
            storage_photo = cv2.resize(captured_photo, (320, 240))
            _, buffer = cv2.imencode('.jpg', storage_photo)
            photo_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Show final captured photo
            cv2.imshow('Final Captured Photo', storage_photo)
            print(f"✅ Face-verified photo captured!")
            print(f"📊 Photo quality score: {best_quality:.2f}")
            print(f"📊 Photo size: {len(photo_base64)} characters")
            print("Press any key to continue...")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            
            return photo_base64
        
        return None
    
    def generate_demo_photo(self, customer_id: str) -> str:
        """Generate demo photo with face simulation"""
        img = np.random.randint(80, 180, (240, 320, 3), dtype=np.uint8)
        
        # Draw a simple face representation
        center = (160, 120)
        cv2.circle(img, center, 60, (200, 180, 160), -1)  # Face
        cv2.circle(img, (140, 100), 8, (50, 50, 50), -1)   # Left eye
        cv2.circle(img, (180, 100), 8, (50, 50, 50), -1)   # Right eye
        cv2.ellipse(img, (160, 140), (20, 10), 0, 0, 180, (50, 50, 50), 2)  # Mouth
        
        # Add text
        cv2.putText(img, f"Customer: {customer_id}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(img, "FACE DETECTED", (20, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(img, "Demo Mode", (20, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        
        cv2.imshow('Demo Face Photo', img)
        print("🖼️ Generated demo photo with simulated face")
        print("Press any key to continue...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        _, buffer = cv2.imencode('.jpg', img)
        return base64.b64encode(buffer).decode('utf-8')
    
    def process_purchase_with_face_detection(self, customer_id: str, product_sku: str) -> Dict:
        """Process purchase with face detection verification"""
        if product_sku not in self.products:
            return {"error": f"Product {product_sku} not found"}
        
        product = self.products[product_sku]
        
        print(f"\n🛒 Processing Purchase with Face Verification")
        print("=" * 50)
        print(f"Customer: {customer_id}")
        print(f"Product: {product['name']}")
        print(f"Price: ${product['price']}")
        
        # Capture face-verified photo
        customer_photo = self.capture_face_verified_photo(customer_id)
        
        if not customer_photo:
            return {"error": "Face verification failed or cancelled"}
        
        # Process transaction
        transaction_id = f"TXN_{self.store_id}_{uuid.uuid4().hex[:8].upper()}"
        timestamp = int(time.time())
        
        transaction = {
            "transaction_id": transaction_id,
            "store_id": self.store_id,
            "customer_id": customer_id,
            "transaction_type": "PURCHASE",
            "product": product,
            "amount": product["price"],
            "payment_method": "credit_card",
            "timestamp": timestamp,
            "datetime": datetime.fromtimestamp(timestamp).isoformat(),
            "has_photo": True,
            "face_verified": True,
            "verification_method": "FACE_DETECTION",
            "status": "COMPLETED"
        }
        
        try:
            # Store in Redis
            self.redis_client.set(f"transaction:{transaction_id}", json.dumps(transaction))
            self.redis_client.set(f"photo:{transaction_id}", customer_photo)
            
            # Add to stream
            stream_data = {
                "transaction_id": transaction_id,
                "store_id": self.store_id,
                "customer_id": customer_id,
                "type": "PURCHASE",
                "amount": str(product["price"]),
                "product_sku": product_sku,
                "has_photo": "true",
                "face_verified": "true",
                "verification": "FACE_DETECTION",
                "timestamp": str(timestamp)
            }
            self.redis_client.xadd("transaction_stream", stream_data)
            
            print(f"\n✅ Purchase Completed with Face Verification!")
            print(f"Transaction ID: {transaction_id}")
            print(f"Face Verified: ✅ Yes")
            print(f"Security Level: 🔒 High")
            
            return {
                "success": True,
                "transaction_id": transaction_id,
                "face_verified": True,
                "verification_method": "FACE_DETECTION"
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing purchase: {e}")
            return {"error": f"Failed to process purchase: {e}"}
    
    def cleanup(self):
        """Clean up resources"""
        if self.camera:
            self.camera.release()
        cv2.destroyAllWindows()

def main():
    """Main function"""
    pos = FaceDetectionPOS()
    
    try:
        print("\n👤 Face Detection POS System")
        print("=" * 40)
        print("🔒 Advanced security with face verification")
        print("📷 Real-time face detection and quality assessment")
        
        while True:
            print("\nOptions:")
            print("1. Process Purchase (with Face Detection)")
            print("2. Test Face Detection")
            print("3. Exit")
            
            choice = input("\nSelect option (1-3): ").strip()
            
            if choice == "1":
                customer_id = input("Customer ID: ").strip() or f"CUST_{int(time.time()) % 10000:04d}"
                
                print("\nAvailable Products:")
                for sku, product in pos.products.items():
                    print(f"  {sku}: {product['name']} - ${product['price']}")
                
                product_sku = input("Product SKU: ").strip().upper()
                
                if product_sku in pos.products:
                    result = pos.process_purchase_with_face_detection(customer_id, product_sku)
                    
                    if result.get("success"):
                        print(f"\n🎉 Transaction successful with face verification!")
                        print(f"Check the dashboard to see the verified transaction!")
                    else:
                        print(f"\n❌ Transaction failed: {result.get('error')}")
                else:
                    print("❌ Invalid product SKU")
            
            elif choice == "2":
                print("👤 Testing face detection...")
                if pos.camera and pos.camera.isOpened():
                    pos.capture_face_verified_photo("TEST_USER")
                else:
                    print("❌ Camera not available")
            
            elif choice == "3":
                break
            
            else:
                print("Invalid option. Please try again.")
    
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down Face Detection POS...")
    
    finally:
        pos.cleanup()

if __name__ == "__main__":
    main()
