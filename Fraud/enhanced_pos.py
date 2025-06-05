#!/usr/bin/env python3
"""
Enhanced POS Simulator with Photo Preview

This enhanced version shows the customer photo before processing
the transaction, demonstrating the photo verification process.
"""

import redis
import json
import time
import uuid
import base64
import cv2
import numpy as np
from datetime import datetime
from typing import Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedPOSSimulator:
    def __init__(self, store_id: str = "STORE_A", redis_host: str = "localhost", redis_port: int = 6379):
        """Initialize Enhanced POS Simulator"""
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
        
        # Product catalog
        self.products = {
            "SHIRT_001": {"name": "Cotton T-Shirt", "price": 29.99, "sku": "SHIRT_001"},
            "SHIRT_002": {"name": "Polo Shirt", "price": 45.99, "sku": "SHIRT_002"},
            "SHIRT_003": {"name": "Dress Shirt", "price": 79.99, "sku": "SHIRT_003"},
            "JEANS_001": {"name": "Blue Jeans", "price": 89.99, "sku": "JEANS_001"},
            "JACKET_001": {"name": "Leather Jacket", "price": 199.99, "sku": "JACKET_001"}
        }
    
    def init_camera(self):
        """Initialize camera for photo capture"""
        try:
            self.camera = cv2.VideoCapture(0)
            if self.camera.isOpened():
                logger.info("📷 Camera initialized successfully")
            else:
                logger.warning("⚠️ Camera not available, will use demo photos")
                self.camera = None
        except Exception as e:
            logger.warning(f"⚠️ Camera initialization failed: {e}")
            self.camera = None
    
    def show_camera_preview_and_capture(self, customer_id: str) -> Optional[str]:
        """Show camera preview and capture photo with confirmation"""
        if not self.camera or not self.camera.isOpened():
            print("⚠️ Camera not available, generating demo photo...")
            return self.generate_demo_photo(customer_id)
        
        print(f"\n📷 Camera Preview for Customer: {customer_id}")
        print("=" * 50)
        print("Controls:")
        print("  'c' - Capture photo")
        print("  'r' - Retake photo")
        print("  'a' - Accept and continue")
        print("  'q' - Cancel transaction")
        
        captured_photo = None
        photo_base64 = None
        
        while True:
            ret, frame = self.camera.read()
            if not ret:
                print("❌ Failed to read from camera")
                break
            
            # Create display frame
            display_frame = cv2.resize(frame, (640, 480))
            
            # Add overlay information
            cv2.putText(display_frame, f"Customer: {customer_id}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(display_frame, f"Store: {self.store_id}", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(display_frame, f"Time: {datetime.now().strftime('%H:%M:%S')}", 
                       (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            if captured_photo is not None:
                cv2.putText(display_frame, "Photo Captured! Press 'a' to accept", 
                           (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                cv2.putText(display_frame, "or 'r' to retake", 
                           (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            else:
                cv2.putText(display_frame, "Press 'c' to capture photo", 
                           (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imshow(f'{self.store_id} - Customer Photo Capture', display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('c'):
                # Capture photo
                captured_photo = frame.copy()
                
                # Resize for storage
                storage_photo = cv2.resize(captured_photo, (320, 240))
                
                # Convert to base64
                _, buffer = cv2.imencode('.jpg', storage_photo)
                photo_base64 = base64.b64encode(buffer).decode('utf-8')
                
                print("📸 Photo captured!")
                print(f"📊 Photo size: {len(photo_base64)} characters")
                
                # Show captured photo in separate window
                capture_display = cv2.resize(captured_photo, (320, 240))
                cv2.putText(capture_display, "CAPTURED", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(capture_display, customer_id, 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.imshow('Captured Customer Photo', capture_display)
            
            elif key == ord('r'):
                # Retake photo
                captured_photo = None
                photo_base64 = None
                cv2.destroyWindow('Captured Customer Photo')
                print("🔄 Ready to retake photo...")
            
            elif key == ord('a') and captured_photo is not None:
                # Accept photo and continue
                print("✅ Photo accepted for transaction!")
                break
            
            elif key == ord('q'):
                # Cancel transaction
                print("❌ Transaction cancelled by user")
                cv2.destroyAllWindows()
                return None
        
        cv2.destroyAllWindows()
        return photo_base64
    
    def generate_demo_photo(self, customer_id: str) -> str:
        """Generate a demo photo when camera is not available"""
        # Create a demo image with customer info
        img = np.random.randint(80, 180, (240, 320, 3), dtype=np.uint8)
        
        # Add customer information
        cv2.putText(img, f"Customer: {customer_id}", 
                   (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(img, f"Store: {self.store_id}", 
                   (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(img, f"Time: {datetime.now().strftime('%H:%M:%S')}", 
                   (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        cv2.putText(img, "DEMO PHOTO", 
                   (20, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(img, "Photo Verified", 
                   (20, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Show the demo photo
        cv2.imshow(f'Demo Photo - {customer_id}', img)
        print(f"🖼️ Generated demo photo for {customer_id}")
        print("Press any key to continue...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        # Convert to base64
        _, buffer = cv2.imencode('.jpg', img)
        photo_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return photo_base64
    
    def process_purchase_with_preview(self, customer_id: str, product_sku: str, payment_method: str = "credit_card") -> Dict:
        """Process purchase with photo preview and confirmation"""
        if product_sku not in self.products:
            return {"error": f"Product {product_sku} not found"}
        
        product = self.products[product_sku]
        
        print(f"\n🛒 Processing Purchase")
        print("=" * 30)
        print(f"Customer: {customer_id}")
        print(f"Product: {product['name']}")
        print(f"Price: ${product['price']}")
        print(f"Payment: {payment_method}")
        
        # Step 1: Capture customer photo with preview
        print(f"\n📷 Step 1: Customer Photo Verification")
        customer_photo = self.show_camera_preview_and_capture(customer_id)
        
        if not customer_photo:
            return {"error": "Photo capture cancelled or failed"}
        
        # Step 2: Process transaction
        print(f"\n💳 Step 2: Processing Payment...")
        transaction_id = f"TXN_{self.store_id}_{uuid.uuid4().hex[:8].upper()}"
        timestamp = int(time.time())
        
        # Create transaction record
        transaction = {
            "transaction_id": transaction_id,
            "store_id": self.store_id,
            "customer_id": customer_id,
            "transaction_type": "PURCHASE",
            "product": {
                "sku": product_sku,
                "name": product["name"],
                "price": product["price"]
            },
            "amount": product["price"],
            "payment_method": payment_method,
            "timestamp": timestamp,
            "datetime": datetime.fromtimestamp(timestamp).isoformat(),
            "has_photo": True,
            "photo_verified": True,
            "status": "COMPLETED"
        }
        
        try:
            # Store transaction data
            transaction_key = f"transaction:{transaction_id}"
            self.redis_client.set(transaction_key, json.dumps(transaction))
            
            # Store customer photo
            photo_key = f"photo:{transaction_id}"
            self.redis_client.set(photo_key, customer_photo)
            
            # Add to transaction stream
            stream_data = {
                "transaction_id": transaction_id,
                "store_id": self.store_id,
                "customer_id": customer_id,
                "type": "PURCHASE",
                "amount": str(product["price"]),
                "product_sku": product_sku,
                "has_photo": "true",
                "photo_verified": "true",
                "timestamp": str(timestamp)
            }
            self.redis_client.xadd("transaction_stream", stream_data)
            
            print(f"\n✅ Purchase Completed Successfully!")
            print(f"Transaction ID: {transaction_id}")
            print(f"Amount: ${product['price']}")
            print(f"Photo Verified: ✅ Yes")
            print(f"Stored in Redis: ✅ Yes")
            
            return {
                "success": True,
                "transaction_id": transaction_id,
                "product": product,
                "amount": product["price"],
                "has_photo": True,
                "photo_verified": True,
                "timestamp": timestamp
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
    pos = EnhancedPOSSimulator()
    
    try:
        print("\n🏪 Enhanced Store A POS System")
        print("=" * 40)
        print("📷 Photo verification enabled")
        print("🔒 Secure transactions with visual confirmation")
        
        while True:
            print("\nOptions:")
            print("1. Process Purchase (with Photo Preview)")
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
                    result = pos.process_purchase_with_preview(customer_id, product_sku)
                    
                    if result.get("success"):
                        print(f"\n🎉 Transaction successful!")
                        print(f"Check the dashboard to see the transaction with photo!")
                    else:
                        print(f"\n❌ Transaction failed: {result.get('error')}")
                else:
                    print("❌ Invalid product SKU")
            
            elif choice == "2":
                if pos.camera and pos.camera.isOpened():
                    print("📷 Testing camera...")
                    ret, frame = pos.camera.read()
                    if ret:
                        cv2.imshow('Camera Test', cv2.resize(frame, (320, 240)))
                        print("✅ Camera working! Press any key to close...")
                        cv2.waitKey(0)
                        cv2.destroyAllWindows()
                    else:
                        print("❌ Cannot capture from camera")
                else:
                    print("❌ Camera not available")
            
            elif choice == "3":
                break
            
            else:
                print("Invalid option. Please try again.")
    
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down Enhanced POS system...")
    
    finally:
        pos.cleanup()

if __name__ == "__main__":
    main()
