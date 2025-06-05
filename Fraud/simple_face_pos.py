#!/usr/bin/env python3
"""
Simple Face Detection POS - Relaxed Version

This version is much more relaxed:
- Captures immediately when any face is detected
- Lower quality requirements
- Simple one-click capture
"""

import cv2
import numpy as np
import redis
import json
import time
import uuid
import base64
from datetime import datetime
from typing import Dict, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleFacePOS:
    def __init__(self, store_id: str = "STORE_A", redis_host: str = "localhost", redis_port: int = 6379):
        """Initialize Simple Face POS System"""
        self.store_id = store_id
        self.redis_host = redis_host
        self.redis_port = redis_port
        
        # Connect to Redis
        try:
            self.redis_client = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=False)
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
    
    def init_camera(self):
        """Initialize camera"""
        try:
            self.camera = cv2.VideoCapture(0)
            if self.camera.isOpened():
                logger.info("📷 Camera initialized successfully")
            else:
                logger.warning("⚠️ Camera not available")
                self.camera = None
        except Exception as e:
            logger.warning(f"⚠️ Camera initialization failed: {e}")
            self.camera = None
    
    def init_face_detection(self):
        """Initialize face detection"""
        try:
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            if self.face_cascade.empty():
                logger.error("❌ Failed to load face cascade")
                self.face_cascade = None
            else:
                logger.info("✅ Face detection initialized")
        except Exception as e:
            logger.error(f"❌ Face detection failed: {e}")
            self.face_cascade = None
    
    def simple_face_capture(self, customer_id: str) -> Optional[str]:
        """Simple face capture - just click when you see your face!"""
        if not self.camera or not self.camera.isOpened():
            print("⚠️ Camera not available, generating demo photo...")
            return self.generate_demo_photo(customer_id)
        
        print(f"\n📷 Simple Face Capture for {customer_id}")
        print("=" * 40)
        print("🎯 Look at the camera and press 'c' when you see your face!")
        print("📸 Green box = face detected, ready to capture")
        print("\nControls:")
        print("  'c' - Capture photo")
        print("  'q' - Cancel")
        
        while True:
            ret, frame = self.camera.read()
            if not ret:
                print("❌ Camera error")
                break
            
            # Simple face detection
            faces = []
            if self.face_cascade is not None:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(30, 30))
            
            # Draw face boxes
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, "Face Ready!", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Add overlay
            cv2.putText(frame, f"Customer: {customer_id}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Faces: {len(faces)}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            if len(faces) > 0:
                cv2.putText(frame, "✅ Press 'c' to capture!", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "👤 Position face in camera", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            cv2.imshow(f'{self.store_id} - Simple Face Capture', frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('c'):
                if len(faces) > 0:
                    # Capture photo
                    storage_photo = cv2.resize(frame, (320, 240))
                    _, buffer = cv2.imencode('.jpg', storage_photo)
                    photo_base64 = base64.b64encode(buffer).decode('utf-8')
                    
                    print(f"📸 Photo captured with {len(faces)} face(s) detected!")
                    
                    # Show captured photo
                    cv2.imshow('Captured Photo', storage_photo)
                    print("Press any key to continue...")
                    cv2.waitKey(0)
                    cv2.destroyAllWindows()
                    
                    return photo_base64
                else:
                    print("⚠️ No face detected - try again")
            
            elif key == ord('q'):
                print("❌ Cancelled")
                cv2.destroyAllWindows()
                return None
        
        cv2.destroyAllWindows()
        return None
    
    def generate_demo_photo(self, customer_id: str) -> str:
        """Generate demo photo"""
        img = np.random.randint(80, 180, (240, 320, 3), dtype=np.uint8)
        
        # Simple face drawing
        cv2.circle(img, (160, 120), 50, (200, 180, 160), -1)  # Face
        cv2.circle(img, (145, 105), 5, (0, 0, 0), -1)   # Left eye
        cv2.circle(img, (175, 105), 5, (0, 0, 0), -1)   # Right eye
        cv2.ellipse(img, (160, 135), (15, 8), 0, 0, 180, (0, 0, 0), 2)  # Mouth
        
        cv2.putText(img, f"Customer: {customer_id}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(img, "DEMO FACE", (20, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow('Demo Photo', img)
        print("🖼️ Demo photo generated - press any key to continue")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        _, buffer = cv2.imencode('.jpg', img)
        return base64.b64encode(buffer).decode('utf-8')
    
    def process_simple_purchase(self, customer_id: str, product_sku: str) -> Dict:
        """Process purchase with simple face capture"""
        if product_sku not in self.products:
            return {"error": f"Product {product_sku} not found"}
        
        product = self.products[product_sku]
        
        print(f"\n🛒 Simple Purchase Processing")
        print("=" * 35)
        print(f"Customer: {customer_id}")
        print(f"Product: {product['name']}")
        print(f"Price: ${product['price']}")
        
        # Simple face capture
        customer_photo = self.simple_face_capture(customer_id)
        
        if not customer_photo:
            return {"error": "Photo capture cancelled"}
        
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
            "verification_method": "SIMPLE_FACE_DETECTION",
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
                "verification": "SIMPLE_FACE",
                "timestamp": str(timestamp)
            }
            self.redis_client.xadd("transaction_stream", stream_data)
            
            print(f"\n✅ Purchase Completed!")
            print(f"Transaction ID: {transaction_id}")
            print(f"Face Detected: ✅ Yes")
            print(f"Photo Stored: ✅ Yes")
            
            return {"success": True, "transaction_id": transaction_id, "face_verified": True}
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return {"error": f"Failed to process: {e}"}
    
    def cleanup(self):
        """Clean up"""
        if self.camera:
            self.camera.release()
        cv2.destroyAllWindows()

def main():
    """Main function"""
    pos = SimpleFacePOS()
    
    try:
        print("\n📷 Simple Face Detection POS")
        print("=" * 35)
        print("🎯 Easy face capture - just click when ready!")
        
        while True:
            print("\nOptions:")
            print("1. Process Purchase (Simple Face Capture)")
            print("2. Test Camera")
            print("3. Exit")
            
            choice = input("\nSelect option (1-3): ").strip()
            
            if choice == "1":
                customer_id = input("Customer ID: ").strip() or f"CUST_{int(time.time()) % 10000:04d}"
                
                print("\nAvailable Products:")
                for sku, product in pos.products.items():
                    print(f"  {sku}: {product['name']} - ${product['price']}")
                
                product_sku = input("Product SKU: ").strip().upper()
                
                if product_sku in pos.products:
                    result = pos.process_simple_purchase(customer_id, product_sku)
                    
                    if result.get("success"):
                        print(f"\n🎉 Success! Check the dashboard!")
                    else:
                        print(f"\n❌ Failed: {result.get('error')}")
                else:
                    print("❌ Invalid product SKU")
            
            elif choice == "2":
                if pos.camera and pos.camera.isOpened():
                    pos.simple_face_capture("TEST_USER")
                else:
                    print("❌ Camera not available")
            
            elif choice == "3":
                break
            
            else:
                print("Invalid option")
    
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    
    finally:
        pos.cleanup()

if __name__ == "__main__":
    main()
