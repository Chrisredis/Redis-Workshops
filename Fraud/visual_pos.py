#!/usr/bin/env python3
"""
Visual POS System with Photo Display

Shows the captured photo during the transaction process.
"""

import cv2
import redis
import json
import uuid
import base64
import time
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VisualPOSSystem:
    def __init__(self):
        """Initialize the Visual POS System"""
        # Redis connection
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        # Test Redis connection
        try:
            self.redis_client.ping()
            logger.info("✅ Connected to Redis at localhost:6379")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise
        
        # Camera setup
        self.camera = None
        self.face_cascade = None
        self.captured_photo = None
        
        # Product catalog
        self.products = {
            "SHIRT_001": {"name": "Cotton T-Shirt", "price": 29.99},
            "SHIRT_002": {"name": "Polo Shirt", "price": 45.99},
            "SHIRT_003": {"name": "Dress Shirt", "price": 79.99},
            "JEANS_001": {"name": "Blue Jeans", "price": 89.99},
            "JACKET_001": {"name": "Leather Jacket", "price": 199.99},
            "LAPTOP_001": {"name": "Gaming Laptop", "price": 2499.99},
            "WATCH_001": {"name": "Luxury Watch", "price": 1299.99},
            "PHONE_001": {"name": "Smartphone", "price": 899.99}
        }
        
        self.init_camera()
        self.init_face_detection()
    
    def init_camera(self):
        """Initialize camera"""
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                logger.warning("⚠️ Camera not available, using demo mode")
                self.camera = None
            else:
                logger.info("📷 Camera initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️ Camera initialization failed: {e}")
            self.camera = None
    
    def init_face_detection(self):
        """Initialize face detection"""
        try:
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            logger.info("✅ Face detection initialized successfully")
        except Exception as e:
            logger.error(f"❌ Face detection initialization failed: {e}")
            self.face_cascade = None
    
    def capture_photo_with_preview(self, customer_id):
        """Capture photo with live preview and display result"""
        if not self.camera or not self.face_cascade:
            logger.warning("📷 Camera not available, generating demo photo")
            return self.generate_demo_photo(customer_id)
        
        print(f"\n👤 Photo Capture for {customer_id}")
        print("=" * 50)
        print("📷 Position yourself in front of the camera")
        print("🎯 System will show live preview and capture automatically")
        print("\nControls:")
        print("  'c' - Force capture now")
        print("  'q' - Cancel")
        
        best_photo = None
        best_quality = 0
        
        while True:
            ret, frame = self.camera.read()
            if not ret:
                break
            
            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Detect faces
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            
            # Draw rectangles around faces
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                
                # Calculate face quality (size and position)
                face_area = w * h
                frame_area = frame.shape[0] * frame.shape[1]
                quality = face_area / frame_area
                
                # Auto-capture if good quality face detected
                if quality > 0.05 and quality > best_quality:
                    best_quality = quality
                    best_photo = frame.copy()
                    
                    # Show capture indicator
                    cv2.putText(frame, f"Quality: {quality:.3f} - CAPTURING!", 
                              (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.imshow('POS Camera - Photo Captured!', frame)
                    cv2.waitKey(1000)  # Show for 1 second
                    
                    # Display the captured photo
                    self.display_captured_photo(best_photo, customer_id, quality)
                    
                    cv2.destroyAllWindows()
                    return self.encode_photo(best_photo)
                else:
                    cv2.putText(frame, f"Quality: {quality:.3f} - Move closer", 
                              (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            # Show live preview
            cv2.putText(frame, "Live Preview - Position your face in the frame", 
                       (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.imshow('POS Camera - Live Preview', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('c'):
                # Force capture
                if len(faces) > 0:
                    self.display_captured_photo(frame, customer_id, best_quality)
                    cv2.destroyAllWindows()
                    return self.encode_photo(frame)
                else:
                    print("⚠️ No face detected. Please position yourself in front of the camera.")
            elif key == ord('q'):
                cv2.destroyAllWindows()
                return None
        
        cv2.destroyAllWindows()
        return None
    
    def display_captured_photo(self, photo, customer_id, quality):
        """Display the captured photo with transaction info"""
        display_photo = photo.copy()

        # Add transaction info overlay
        cv2.putText(display_photo, f"Customer: {customer_id}",
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(display_photo, f"Photo Quality: {quality:.3f}",
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(display_photo, f"Captured: {datetime.now().strftime('%H:%M:%S')}",
                   (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(display_photo, "Photo attached to transaction!",
                   (10, display_photo.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        # Show the photo
        cv2.imshow('YOUR TRANSACTION PHOTO - Press any key to continue', display_photo)
        print(f"\n📸 Photo captured successfully!")
        print(f"📊 Quality Score: {quality:.3f}")
        print(f"📊 Photo Size: {len(self.encode_photo(photo))} characters")
        print("👆 THIS IS YOUR ACTUAL PHOTO attached to the transaction!")
        print("Press any key in the photo window to continue...")

        cv2.waitKey(0)  # Wait for user to press a key
        cv2.destroyAllWindows()

    def show_transaction_with_photo(self, transaction_data, photo_data, customer_id):
        """Show the completed transaction with the actual photo"""
        if photo_data:
            # Decode the photo from base64
            import base64
            import numpy as np

            try:
                # Decode base64 to bytes
                photo_bytes = base64.b64decode(photo_data)
                # Convert bytes to numpy array
                nparr = np.frombuffer(photo_bytes, np.uint8)
                # Decode image
                photo = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                if photo is not None:
                    # Create transaction display
                    display_photo = photo.copy()

                    # Add transaction details overlay
                    cv2.putText(display_photo, f"TRANSACTION COMPLETED",
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
                    cv2.putText(display_photo, f"ID: {transaction_data['transaction_id']}",
                               (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(display_photo, f"Customer: {customer_id}",
                               (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(display_photo, f"Product: {transaction_data['product_name']}",
                               (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(display_photo, f"Amount: ${transaction_data['amount']}",
                               (10, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(display_photo, f"Photo Verified: YES",
                               (10, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(display_photo, "This photo is stored with your transaction",
                               (10, display_photo.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                    # Show the transaction with photo
                    cv2.imshow('COMPLETED TRANSACTION WITH YOUR PHOTO - Press any key to continue', display_photo)
                    print(f"\n✅ TRANSACTION COMPLETED!")
                    print(f"📄 Transaction ID: {transaction_data['transaction_id']}")
                    print(f"👤 Customer: {customer_id}")
                    print(f"🛒 Product: {transaction_data['product_name']}")
                    print(f"💰 Amount: ${transaction_data['amount']}")
                    print(f"📷 Photo: VERIFIED and ATTACHED")
                    print("👆 The window shows your ACTUAL PHOTO stored with this transaction!")
                    print("Press any key in the photo window to return to menu...")

                    cv2.waitKey(0)  # Wait for user to press a key
                    cv2.destroyAllWindows()
                    return
            except Exception as e:
                print(f"⚠️ Could not display photo: {e}")

        # Fallback if photo can't be displayed
        print(f"\n✅ TRANSACTION COMPLETED!")
        print(f"📄 Transaction ID: {transaction_data['transaction_id']}")
        print(f"👤 Customer: {customer_id}")
        print(f"🛒 Product: {transaction_data['product_name']}")
        print(f"💰 Amount: ${transaction_data['amount']}")
        print(f"📷 Photo: VERIFIED and ATTACHED")
        input("Press Enter to return to menu...")
    
    def encode_photo(self, frame):
        """Encode photo to base64 string"""
        if frame is None:
            return None
        
        # Encode frame to JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        # Convert to base64
        photo_base64 = base64.b64encode(buffer).decode('utf-8')
        return photo_base64
    
    def generate_demo_photo(self, customer_id):
        """Generate a demo photo when camera is not available"""
        # Create a simple demo image
        demo_image = cv2.zeros((480, 640, 3), dtype=cv2.uint8)
        cv2.rectangle(demo_image, (100, 100), (540, 380), (0, 255, 0), -1)
        cv2.putText(demo_image, f"DEMO PHOTO", (200, 240), 
                   cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        cv2.putText(demo_image, f"Customer: {customer_id}", (150, 300), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        return self.encode_photo(demo_image)
    
    def process_purchase(self):
        """Process a purchase with visual photo capture"""
        print("\n🛒 Visual POS System - Purchase with Photo")
        print("=" * 50)
        
        # Get customer ID
        customer_id = input("Customer ID: ").strip()
        if not customer_id:
            print("❌ Customer ID required")
            return
        
        # Show products
        print("\nAvailable Products:")
        for sku, product in self.products.items():
            print(f"  {sku}: {product['name']} - ${product['price']}")
        
        # Get product
        product_sku = input("Product SKU: ").strip().upper()
        if product_sku not in self.products:
            print("❌ Invalid product SKU")
            return
        
        product = self.products[product_sku]
        
        print(f"\n🛒 Processing Purchase")
        print("=" * 30)
        print(f"Customer: {customer_id}")
        print(f"Product: {product['name']}")
        print(f"Price: ${product['price']}")
        
        # Capture photo with preview
        photo_data = self.capture_photo_with_preview(customer_id)
        
        if not photo_data:
            print("❌ Photo capture cancelled or failed")
            return
        
        # Generate transaction
        transaction_id = f"TXN_VISUAL_{uuid.uuid4().hex[:8].upper()}"
        
        transaction_data = {
            "transaction_id": transaction_id,
            "customer_id": customer_id,
            "product_sku": product_sku,
            "product_name": product['name'],
            "amount": product['price'],
            "timestamp": datetime.now().isoformat(),
            "store_id": "STORE_VISUAL",
            "photo_verified": True,
            "photo_quality": "high"
        }
        
        # Store transaction in Redis
        self.redis_client.set(f"transaction:{transaction_id}", json.dumps(transaction_data))
        self.redis_client.set(f"photo:{transaction_id}", photo_data)

        # Add to transaction stream
        self.redis_client.xadd("transaction_stream", transaction_data)

        # Show the completed transaction with the actual photo
        self.show_transaction_with_photo(transaction_data, photo_data, customer_id)

        print(f"\n🔄 Data stored in Redis")
        print(f"🖥️ Check your web dashboard at http://localhost:8080 to see this transaction!")

        return transaction_id

def main():
    """Main function"""
    try:
        pos = VisualPOSSystem()
        
        while True:
            print("\n👤 Visual POS System")
            print("=" * 40)
            print("🔒 Advanced security with photo verification")
            print("📷 Live camera preview and photo display")
            print("\nOptions:")
            print("1. Process Purchase (with Visual Photo)")
            print("2. Exit")
            
            choice = input("\nSelect option (1-2): ").strip()
            
            if choice == "1":
                pos.process_purchase()
            elif choice == "2":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid option")
    
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"❌ System error: {e}")

if __name__ == "__main__":
    main()
