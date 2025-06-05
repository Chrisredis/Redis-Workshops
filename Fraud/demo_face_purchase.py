#!/usr/bin/env python3
"""
Demo Face Purchase - Direct Transaction Processing

This script directly processes a purchase with face detection
to demonstrate the fraud detection system.
"""

import cv2
import numpy as np
import redis
import json
import time
import uuid
import base64
from datetime import datetime

def capture_face_photo(customer_id):
    """Simple face capture"""
    print(f"\n📷 Capturing photo for {customer_id}")
    print("=" * 40)
    
    # Initialize camera
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        print("⚠️ Camera not available, using demo photo")
        return generate_demo_photo(customer_id)
    
    # Initialize face detection
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    print("🎯 Look at the camera!")
    print("📸 Press 'c' when you see the green box around your face")
    print("❌ Press 'q' to cancel")
    
    while True:
        ret, frame = camera.read()
        if not ret:
            break
        
        # Detect faces
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(50, 50))
        
        # Draw face boxes
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
            cv2.putText(frame, "FACE DETECTED!", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Add overlay
        cv2.putText(frame, f"Customer: {customer_id}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, f"Faces Found: {len(faces)}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        if len(faces) > 0:
            cv2.putText(frame, "✅ READY - Press 'c' to capture!", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "👤 Position your face in camera", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        cv2.imshow('Face Detection - Press C to Capture', frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('c') and len(faces) > 0:
            # Capture!
            storage_photo = cv2.resize(frame, (320, 240))
            _, buffer = cv2.imencode('.jpg', storage_photo)
            photo_base64 = base64.b64encode(buffer).decode('utf-8')
            
            print(f"📸 Photo captured with {len(faces)} face(s)!")
            
            # Show captured photo
            cv2.imshow('✅ CAPTURED PHOTO', storage_photo)
            print("✅ Photo captured! Press any key to continue...")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            camera.release()
            
            return photo_base64
            
        elif key == ord('q'):
            print("❌ Cancelled")
            cv2.destroyAllWindows()
            camera.release()
            return None
    
    camera.release()
    cv2.destroyAllWindows()
    return None

def generate_demo_photo(customer_id):
    """Generate demo photo"""
    img = np.random.randint(100, 200, (240, 320, 3), dtype=np.uint8)
    
    # Draw simple face
    cv2.circle(img, (160, 120), 60, (220, 200, 180), -1)  # Face
    cv2.circle(img, (140, 100), 8, (0, 0, 0), -1)   # Left eye
    cv2.circle(img, (180, 100), 8, (0, 0, 0), -1)   # Right eye
    cv2.ellipse(img, (160, 140), (20, 10), 0, 0, 180, (0, 0, 0), 2)  # Mouth
    
    # Add text
    cv2.putText(img, f"Customer: {customer_id}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(img, "DEMO FACE PHOTO", (20, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.putText(img, f"Time: {datetime.now().strftime('%H:%M:%S')}", (20, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    cv2.imshow('Demo Face Photo', img)
    print("🖼️ Demo photo generated - press any key to continue")
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    _, buffer = cv2.imencode('.jpg', img)
    return base64.b64encode(buffer).decode('utf-8')

def process_purchase(customer_id, product_name, price, photo_base64):
    """Process the purchase transaction"""
    print(f"\n💳 Processing Purchase...")
    print("=" * 30)
    
    # Connect to Redis
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=False)
    
    # Create transaction
    transaction_id = f"TXN_STORE_A_{uuid.uuid4().hex[:8].upper()}"
    timestamp = int(time.time())
    
    transaction = {
        "transaction_id": transaction_id,
        "store_id": "STORE_A",
        "customer_id": customer_id,
        "transaction_type": "PURCHASE",
        "product": {
            "name": product_name,
            "price": price
        },
        "amount": price,
        "payment_method": "credit_card",
        "timestamp": timestamp,
        "datetime": datetime.fromtimestamp(timestamp).isoformat(),
        "has_photo": True,
        "face_verified": True,
        "verification_method": "FACE_DETECTION",
        "status": "COMPLETED"
    }
    
    # Store in Redis
    redis_client.set(f"transaction:{transaction_id}", json.dumps(transaction))
    redis_client.set(f"photo:{transaction_id}", photo_base64)
    
    # Add to stream
    stream_data = {
        "transaction_id": transaction_id,
        "store_id": "STORE_A",
        "customer_id": customer_id,
        "type": "PURCHASE",
        "amount": str(price),
        "product_name": product_name,
        "has_photo": "true",
        "face_verified": "true",
        "verification": "FACE_DETECTION",
        "timestamp": str(timestamp)
    }
    redis_client.xadd("transaction_stream", stream_data)
    
    print(f"✅ Purchase Completed!")
    print(f"Transaction ID: {transaction_id}")
    print(f"Customer: {customer_id}")
    print(f"Product: {product_name}")
    print(f"Amount: ${price}")
    print(f"Face Verified: ✅ YES")
    print(f"Photo Stored: ✅ YES")
    print(f"\n🎉 Check the dashboard to see your transaction!")
    
    return transaction_id

def main():
    """Main demo function"""
    print("\n🎬 Face Detection Purchase Demo")
    print("=" * 40)
    print("This demo will:")
    print("1. 📷 Capture your photo with face detection")
    print("2. 💳 Process a purchase transaction")
    print("3. 💾 Store everything in Redis")
    print("4. 📊 Show it on the fraud dashboard")
    
    # Get customer info
    customer_id = input("\nEnter your name (or press Enter for CHRIS_001): ").strip()
    if not customer_id:
        customer_id = "CHRIS_001"
    
    # Product selection
    products = {
        "1": ("Cotton T-Shirt", 29.99),
        "2": ("Polo Shirt", 45.99),
        "3": ("Dress Shirt", 79.99),
        "4": ("Blue Jeans", 89.99),
        "5": ("Leather Jacket", 199.99)
    }
    
    print(f"\nSelect a product:")
    for key, (name, price) in products.items():
        print(f"  {key}. {name} - ${price}")
    
    choice = input("\nEnter choice (1-5, or Enter for Leather Jacket): ").strip()
    if choice not in products:
        choice = "5"  # Default to leather jacket
    
    product_name, price = products[choice]
    
    print(f"\n🛒 Processing purchase:")
    print(f"Customer: {customer_id}")
    print(f"Product: {product_name}")
    print(f"Price: ${price}")
    
    # Capture photo
    photo_base64 = capture_face_photo(customer_id)
    
    if photo_base64:
        # Process purchase
        transaction_id = process_purchase(customer_id, product_name, price, photo_base64)
        
        print(f"\n🎯 Demo Complete!")
        print(f"Your transaction {transaction_id} is now visible on the dashboard")
        print(f"with your face-verified photo attached!")
        
        # Suggest next steps
        print(f"\n🔄 Next Steps:")
        print(f"1. Check the dashboard at http://localhost:8080")
        print(f"2. Try a fraudulent return from Store B")
        print(f"3. See the fraud detection in action!")
        
    else:
        print("❌ Photo capture failed - demo cancelled")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Demo cancelled")
    except Exception as e:
        print(f"\n❌ Error: {e}")
