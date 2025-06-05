#!/usr/bin/env python3
"""
POS Simulator for Store A - Legitimate Transactions with Photo Capture

This script simulates a Point of Sale system that:
1. Processes purchase transactions
2. Captures customer photos via camera
3. Stores both transaction and photo data in Redis
4. Handles legitimate return transactions with photo verification
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

class POSSimulator:
    def __init__(self, store_id: str = "STORE_A", redis_host: str = "localhost", redis_port: int = 6379):
        """Initialize POS Simulator for Store A"""
        self.store_id = store_id
        self.redis_host = redis_host
        self.redis_port = redis_port
        
        # Connect to Redis
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=0,
                decode_responses=False  # Keep binary for images
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
            self.camera = cv2.VideoCapture(0)  # Use default camera
            if self.camera.isOpened():
                logger.info("📷 Camera initialized successfully")
            else:
                logger.warning("⚠️ Camera not available, will use placeholder images")
                self.camera = None
        except Exception as e:
            logger.warning(f"⚠️ Camera initialization failed: {e}")
            self.camera = None
    
    def capture_photo(self) -> Optional[str]:
        """Capture photo from camera and return as base64 string"""
        if self.camera and self.camera.isOpened():
            try:
                ret, frame = self.camera.read()
                if ret:
                    # Resize image for storage efficiency
                    frame = cv2.resize(frame, (320, 240))
                    
                    # Encode image to base64
                    _, buffer = cv2.imencode('.jpg', frame)
                    img_base64 = base64.b64encode(buffer).decode('utf-8')
                    
                    logger.info("📸 Photo captured successfully")
                    return img_base64
                else:
                    logger.warning("⚠️ Failed to capture frame from camera")
            except Exception as e:
                logger.error(f"❌ Error capturing photo: {e}")
        
        # Generate placeholder image if camera not available
        return self.generate_placeholder_image()
    
    def generate_placeholder_image(self) -> str:
        """Generate a placeholder image for demo purposes"""
        # Create a simple colored rectangle as placeholder
        img = np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
        
        # Add some text to make it look like a customer photo
        cv2.putText(img, f"Customer {int(time.time()) % 1000}", 
                   (50, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(img, f"Store {self.store_id}", 
                   (50, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        _, buffer = cv2.imencode('.jpg', img)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        logger.info("🖼️ Generated placeholder customer photo")
        return img_base64
    
    def process_purchase(self, customer_id: str, product_sku: str, payment_method: str = "credit_card") -> Dict:
        """Process a purchase transaction with photo capture"""
        if product_sku not in self.products:
            return {"error": f"Product {product_sku} not found"}
        
        product = self.products[product_sku]
        transaction_id = f"TXN_{self.store_id}_{uuid.uuid4().hex[:8].upper()}"
        timestamp = int(time.time())
        
        # Capture customer photo
        customer_photo = self.capture_photo()
        
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
            "has_photo": customer_photo is not None,
            "status": "COMPLETED"
        }
        
        try:
            # Store transaction data
            transaction_key = f"transaction:{transaction_id}"
            self.redis_client.set(transaction_key, json.dumps(transaction))
            
            # Store customer photo separately
            if customer_photo:
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
                "has_photo": "true" if customer_photo else "false",
                "timestamp": str(timestamp)
            }
            self.redis_client.xadd("transaction_stream", stream_data)
            
            # Store customer purchase history
            customer_key = f"customer:{customer_id}:purchases"
            purchase_record = {
                "transaction_id": transaction_id,
                "product_sku": product_sku,
                "timestamp": timestamp,
                "store_id": self.store_id
            }
            self.redis_client.lpush(customer_key, json.dumps(purchase_record))
            
            logger.info(f"✅ Purchase processed: {transaction_id} - {product['name']} - ${product['price']}")
            
            return {
                "success": True,
                "transaction_id": transaction_id,
                "product": product,
                "amount": product["price"],
                "has_photo": customer_photo is not None,
                "timestamp": timestamp
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing purchase: {e}")
            return {"error": f"Failed to process purchase: {e}"}
    
    def process_return(self, customer_id: str, original_transaction_id: str) -> Dict:
        """Process a legitimate return transaction with photo verification"""
        try:
            # Get original transaction
            transaction_key = f"transaction:{original_transaction_id}"
            original_data = self.redis_client.get(transaction_key)
            
            if not original_data:
                return {"error": "Original transaction not found"}
            
            original_transaction = json.loads(original_data)
            
            # Verify customer ID matches
            if original_transaction["customer_id"] != customer_id:
                return {"error": "Customer ID mismatch"}
            
            # Verify transaction was a purchase
            if original_transaction["transaction_type"] != "PURCHASE":
                return {"error": "Original transaction was not a purchase"}
            
            # Capture new photo for verification
            verification_photo = self.capture_photo()
            
            # Create return transaction
            return_transaction_id = f"RTN_{self.store_id}_{uuid.uuid4().hex[:8].upper()}"
            timestamp = int(time.time())
            
            return_transaction = {
                "transaction_id": return_transaction_id,
                "original_transaction_id": original_transaction_id,
                "store_id": self.store_id,
                "customer_id": customer_id,
                "transaction_type": "RETURN",
                "product": original_transaction["product"],
                "amount": -original_transaction["amount"],  # Negative for return
                "timestamp": timestamp,
                "datetime": datetime.fromtimestamp(timestamp).isoformat(),
                "has_photo": verification_photo is not None,
                "verification_method": "PHOTO_CAPTURE",
                "status": "COMPLETED"
            }
            
            # Store return transaction
            return_key = f"transaction:{return_transaction_id}"
            self.redis_client.set(return_key, json.dumps(return_transaction))
            
            # Store verification photo
            if verification_photo:
                photo_key = f"photo:{return_transaction_id}"
                self.redis_client.set(photo_key, verification_photo)
            
            # Add to transaction stream
            stream_data = {
                "transaction_id": return_transaction_id,
                "original_transaction_id": original_transaction_id,
                "store_id": self.store_id,
                "customer_id": customer_id,
                "type": "RETURN",
                "amount": str(return_transaction["amount"]),
                "has_photo": "true" if verification_photo else "false",
                "verification": "PHOTO_CAPTURE",
                "timestamp": str(timestamp)
            }
            self.redis_client.xadd("transaction_stream", stream_data)
            
            # Mark original transaction as returned
            original_transaction["return_transaction_id"] = return_transaction_id
            original_transaction["status"] = "RETURNED"
            self.redis_client.set(transaction_key, json.dumps(original_transaction))
            
            logger.info(f"✅ Return processed: {return_transaction_id} - Verified with photo")
            
            return {
                "success": True,
                "transaction_id": return_transaction_id,
                "original_transaction_id": original_transaction_id,
                "amount": return_transaction["amount"],
                "has_photo": verification_photo is not None,
                "verification_method": "PHOTO_CAPTURE",
                "timestamp": timestamp
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing return: {e}")
            return {"error": f"Failed to process return: {e}"}
    
    def get_transaction_history(self, limit: int = 10) -> list:
        """Get recent transaction history"""
        try:
            # Get recent transactions from stream
            stream_data = self.redis_client.xrevrange("transaction_stream", count=limit)
            
            transactions = []
            for stream_id, fields in stream_data:
                transaction = {
                    "stream_id": stream_id.decode(),
                    "timestamp": fields[b'timestamp'].decode(),
                    "transaction_id": fields[b'transaction_id'].decode(),
                    "store_id": fields[b'store_id'].decode(),
                    "type": fields[b'type'].decode(),
                    "amount": fields[b'amount'].decode(),
                    "has_photo": fields[b'has_photo'].decode() == "true"
                }
                transactions.append(transaction)
            
            return transactions
            
        except Exception as e:
            logger.error(f"❌ Error getting transaction history: {e}")
            return []
    
    def cleanup(self):
        """Clean up resources"""
        if self.camera:
            self.camera.release()
        cv2.destroyAllWindows()

def main():
    """Main function to run POS simulator interactively"""
    pos = POSSimulator()
    
    try:
        print("\n🏪 Store A POS System - Legitimate Transactions")
        print("=" * 50)
        
        while True:
            print("\nOptions:")
            print("1. Process Purchase")
            print("2. Process Return")
            print("3. View Transaction History")
            print("4. Exit")
            
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == "1":
                customer_id = input("Customer ID: ").strip() or f"CUST_{int(time.time()) % 10000:04d}"
                print("\nAvailable Products:")
                for sku, product in pos.products.items():
                    print(f"  {sku}: {product['name']} - ${product['price']}")
                
                product_sku = input("Product SKU: ").strip().upper()
                
                result = pos.process_purchase(customer_id, product_sku)
                if result.get("success"):
                    print(f"✅ Purchase successful: {result['transaction_id']}")
                    print(f"   Product: {result['product']['name']}")
                    print(f"   Amount: ${result['amount']}")
                    print(f"   Photo captured: {result['has_photo']}")
                else:
                    print(f"❌ Purchase failed: {result.get('error')}")
            
            elif choice == "2":
                customer_id = input("Customer ID: ").strip()
                transaction_id = input("Original Transaction ID: ").strip()
                
                result = pos.process_return(customer_id, transaction_id)
                if result.get("success"):
                    print(f"✅ Return successful: {result['transaction_id']}")
                    print(f"   Amount: ${result['amount']}")
                    print(f"   Photo verification: {result['has_photo']}")
                else:
                    print(f"❌ Return failed: {result.get('error')}")
            
            elif choice == "3":
                transactions = pos.get_transaction_history()
                print("\nRecent Transactions:")
                for txn in transactions:
                    print(f"  {txn['transaction_id']} - {txn['type']} - ${txn['amount']} - Photo: {txn['has_photo']}")
            
            elif choice == "4":
                break
            
            else:
                print("Invalid option. Please try again.")
    
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down POS system...")
    
    finally:
        pos.cleanup()

if __name__ == "__main__":
    main()
