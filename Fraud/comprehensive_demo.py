#!/usr/bin/env python3
"""
Comprehensive Fraud Detection Demo

This creates a complete fraud detection scenario with:
1. Automated transaction generation
2. Real-time replication monitoring
3. Fraud pattern detection
4. Face verification simulation
5. Multiple fraud scenarios
"""

import redis
import json
import time
import uuid
import base64
import threading
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
import cv2
import numpy as np

class ComprehensiveFraudDemo:
    def __init__(self):
        """Initialize the comprehensive demo"""
        # Redis connections
        self.redis_a = redis.Redis(host='localhost', port=6379, db=0, decode_responses=False)
        self.redis_b = redis.Redis(host='localhost', port=6380, db=0, decode_responses=False)
        
        # Demo state
        self.running = False
        self.transaction_counter = 0
        self.fraud_scenarios = []
        
        # Statistics
        self.stats = {
            "legitimate_transactions": 0,
            "fraudulent_attempts": 0,
            "fraud_detected": 0,
            "fraud_prevented": 0,
            "total_value_protected": 0.0,
            "replication_events": 0,
            "avg_replication_time": 0.0
        }
        
        # Product catalog
        self.products = {
            "SHIRT_001": {"name": "Cotton T-Shirt", "price": 29.99, "category": "clothing"},
            "SHIRT_002": {"name": "Designer Polo", "price": 89.99, "category": "clothing"},
            "JACKET_001": {"name": "Leather Jacket", "price": 299.99, "category": "outerwear"},
            "WATCH_001": {"name": "Luxury Watch", "price": 1299.99, "category": "jewelry"},
            "PHONE_001": {"name": "Smartphone", "price": 899.99, "category": "electronics"},
            "LAPTOP_001": {"name": "Gaming Laptop", "price": 2499.99, "category": "electronics"}
        }
        
        # Customer profiles
        self.customers = {
            "CHRIS_001": {"name": "Chris", "risk_level": "low", "purchase_history": []},
            "ALICE_002": {"name": "Alice", "risk_level": "low", "purchase_history": []},
            "BOB_003": {"name": "Bob", "risk_level": "medium", "purchase_history": []},
            "FRAUDSTER_001": {"name": "Unknown", "risk_level": "high", "purchase_history": []}
        }
        
        self.test_connections()
    
    def test_connections(self):
        """Test Redis connections"""
        try:
            self.redis_a.ping()
            print("✅ Connected to Store A (Redis port 6379)")
        except Exception as e:
            print(f"❌ Store A connection failed: {e}")
            raise
        
        try:
            self.redis_b.ping()
            print("✅ Connected to Store B (Redis port 6380)")
        except Exception as e:
            print(f"❌ Store B connection failed: {e}")
            raise
    
    def generate_fake_photo(self, customer_id: str, has_face: bool = True) -> str:
        """Generate a fake photo for demo purposes"""
        # Create a random background
        img = np.random.randint(80, 180, (240, 320, 3), dtype=np.uint8)
        
        if has_face:
            # Draw a simple face
            center_x, center_y = 160, 120
            face_radius = 50
            
            # Face circle
            cv2.circle(img, (center_x, center_y), face_radius, (220, 200, 180), -1)
            
            # Eyes
            cv2.circle(img, (center_x - 20, center_y - 15), 6, (0, 0, 0), -1)
            cv2.circle(img, (center_x + 20, center_y - 15), 6, (0, 0, 0), -1)
            
            # Nose
            cv2.circle(img, (center_x, center_y), 3, (180, 160, 140), -1)
            
            # Mouth
            cv2.ellipse(img, (center_x, center_y + 20), (15, 8), 0, 0, 180, (0, 0, 0), 2)
            
            # Add some variation based on customer
            if "CHRIS" in customer_id:
                cv2.putText(img, "CHRIS", (center_x - 30, center_y + 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            elif "ALICE" in customer_id:
                cv2.putText(img, "ALICE", (center_x - 30, center_y + 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            elif "FRAUDSTER" in customer_id:
                # Make fraudster photo look suspicious (no clear face)
                cv2.rectangle(img, (center_x - 60, center_y - 60), 
                             (center_x + 60, center_y + 60), (50, 50, 50), -1)
                cv2.putText(img, "OBSCURED", (center_x - 50, center_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        
        # Add metadata
        cv2.putText(img, f"Customer: {customer_id}", (10, 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(img, f"Time: {datetime.now().strftime('%H:%M:%S')}", (10, 45), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        cv2.putText(img, "DEMO PHOTO", (10, 220), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Convert to base64
        _, buffer = cv2.imencode('.jpg', img)
        return base64.b64encode(buffer).decode('utf-8')
    
    def create_transaction(self, store_id: str, customer_id: str, product_sku: str, 
                          transaction_type: str = "PURCHASE", has_photo: bool = True,
                          is_fraudulent: bool = False) -> Dict:
        """Create a transaction record"""
        self.transaction_counter += 1
        
        product = self.products[product_sku]
        transaction_id = f"TXN_{store_id}_{uuid.uuid4().hex[:8].upper()}"
        timestamp = int(time.time())
        
        # Determine if this is a return
        if transaction_type == "RETURN":
            # For returns, we need an original transaction
            original_txn_id = f"TXN_{store_id}_ORIGINAL_{self.transaction_counter}"
            amount = -product["price"]  # Negative for returns
        else:
            original_txn_id = None
            amount = product["price"]
        
        transaction = {
            "transaction_id": transaction_id,
            "store_id": store_id,
            "customer_id": customer_id,
            "transaction_type": transaction_type,
            "product": product,
            "amount": amount,
            "original_transaction_id": original_txn_id,
            "payment_method": "credit_card",
            "timestamp": timestamp,
            "datetime": datetime.fromtimestamp(timestamp).isoformat(),
            "has_photo": has_photo,
            "face_verified": has_photo and not is_fraudulent,
            "is_fraudulent": is_fraudulent,
            "fraud_indicators": [],
            "status": "COMPLETED"
        }
        
        # Add fraud indicators
        if is_fraudulent:
            transaction["fraud_indicators"] = [
                "no_photo_verification",
                "suspicious_timing",
                "high_value_item"
            ]
            if transaction_type == "RETURN":
                transaction["fraud_indicators"].append("return_without_receipt")
        
        return transaction
    
    def process_legitimate_transaction(self, store_id: str = "STORE_A"):
        """Process a legitimate transaction with photo"""
        customer_id = random.choice(list(self.customers.keys())[:-1])  # Exclude fraudster
        product_sku = random.choice(list(self.products.keys()))
        
        # Create transaction
        transaction = self.create_transaction(
            store_id, customer_id, product_sku, "PURCHASE", 
            has_photo=True, is_fraudulent=False
        )
        
        # Generate photo
        photo_data = self.generate_fake_photo(customer_id, has_face=True)
        
        # Store in Redis
        redis_client = self.redis_a if store_id == "STORE_A" else self.redis_b
        
        redis_client.set(f"transaction:{transaction['transaction_id']}", 
                        json.dumps(transaction))
        redis_client.set(f"photo:{transaction['transaction_id']}", photo_data)
        
        # Add to stream
        stream_data = {
            "transaction_id": transaction["transaction_id"],
            "store_id": store_id,
            "customer_id": customer_id,
            "type": "PURCHASE",
            "amount": str(transaction["amount"]),
            "product_sku": product_sku,
            "has_photo": "true",
            "face_verified": "true",
            "is_fraudulent": "false",
            "timestamp": str(transaction["timestamp"])
        }
        redis_client.xadd("transaction_stream", stream_data)
        
        self.stats["legitimate_transactions"] += 1
        
        print(f"✅ Legitimate transaction: {transaction['transaction_id']}")
        print(f"   Customer: {customer_id}")
        print(f"   Product: {transaction['product']['name']}")
        print(f"   Amount: ${transaction['amount']}")
        print(f"   Photo: ✅ Verified")
        
        return transaction
    
    def process_fraudulent_transaction(self, store_id: str = "STORE_B"):
        """Process a fraudulent transaction without proper verification"""
        customer_id = "FRAUDSTER_001"
        product_sku = random.choice([k for k, v in self.products.items() 
                                   if v["price"] > 200])  # Target high-value items
        
        # Create fraudulent transaction
        transaction = self.create_transaction(
            store_id, customer_id, product_sku, "RETURN", 
            has_photo=False, is_fraudulent=True
        )
        
        # Generate suspicious photo (or no photo)
        photo_data = self.generate_fake_photo(customer_id, has_face=False)
        
        # Store in Redis
        redis_client = self.redis_b if store_id == "STORE_B" else self.redis_a
        
        redis_client.set(f"transaction:{transaction['transaction_id']}", 
                        json.dumps(transaction))
        redis_client.set(f"photo:{transaction['transaction_id']}", photo_data)
        
        # Add to stream
        stream_data = {
            "transaction_id": transaction["transaction_id"],
            "store_id": store_id,
            "customer_id": customer_id,
            "type": "RETURN",
            "amount": str(transaction["amount"]),
            "product_sku": product_sku,
            "has_photo": "false",
            "face_verified": "false",
            "is_fraudulent": "true",
            "timestamp": str(transaction["timestamp"])
        }
        redis_client.xadd("transaction_stream", stream_data)
        
        self.stats["fraudulent_attempts"] += 1
        self.stats["total_value_protected"] += abs(transaction["amount"])
        
        print(f"🚨 FRAUD DETECTED: {transaction['transaction_id']}")
        print(f"   Fraudster: {customer_id}")
        print(f"   Attempted: {transaction['product']['name']}")
        print(f"   Value: ${abs(transaction['amount'])}")
        print(f"   Photo: ❌ Missing/Invalid")
        print(f"   Fraud Indicators: {', '.join(transaction['fraud_indicators'])}")
        
        return transaction

    def simulate_replication(self, source_store: str, target_store: str):
        """Simulate Active-Active replication between stores"""
        source_redis = self.redis_a if source_store == "STORE_A" else self.redis_b
        target_redis = self.redis_b if source_store == "STORE_A" else self.redis_a

        try:
            # Get latest transactions from source
            stream_data = source_redis.xrevrange("transaction_stream", count=1)

            if stream_data:
                for stream_id, fields in stream_data:
                    # Measure replication time
                    start_time = time.perf_counter()

                    # Replicate stream entry
                    target_redis.xadd("transaction_stream", fields)

                    # Replicate associated data
                    if b"transaction_id" in fields:
                        txn_id = fields[b"transaction_id"].decode()

                        # Replicate transaction data
                        txn_data = source_redis.get(f"transaction:{txn_id}")
                        if txn_data:
                            target_redis.set(f"transaction:{txn_id}", txn_data)

                        # Replicate photo data
                        photo_data = source_redis.get(f"photo:{txn_id}")
                        if photo_data:
                            target_redis.set(f"photo:{txn_id}", photo_data)

                    end_time = time.perf_counter()
                    replication_time = (end_time - start_time) * 1000

                    self.stats["replication_events"] += 1

                    # Update average replication time
                    total_events = self.stats["replication_events"]
                    current_avg = self.stats["avg_replication_time"]
                    self.stats["avg_replication_time"] = (
                        (current_avg * (total_events - 1) + replication_time) / total_events
                    )

                    print(f"🔄 Replication: {source_store} → {target_store}")
                    print(f"   Time: {replication_time:.2f}ms")
                    print(f"   Transaction: {txn_id}")

        except Exception as e:
            print(f"❌ Replication error: {e}")

    def run_automated_scenario(self, duration_minutes: int = 5):
        """Run automated fraud detection scenario"""
        print(f"\n🎬 Starting Automated Fraud Detection Scenario")
        print("=" * 60)
        print(f"Duration: {duration_minutes} minutes")
        print("Scenario: Mixed legitimate and fraudulent transactions")
        print("=" * 60)

        self.running = True
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)

        scenario_step = 0

        while self.running and time.time() < end_time:
            scenario_step += 1

            print(f"\n📊 Scenario Step {scenario_step}")
            print("-" * 30)

            # Generate different types of transactions
            if scenario_step % 4 == 1:
                # Legitimate purchase at Store A
                print("🛒 Generating legitimate purchase at Store A...")
                self.process_legitimate_transaction("STORE_A")
                time.sleep(2)

                # Simulate replication to Store B
                print("🔄 Replicating to Store B...")
                self.simulate_replication("STORE_A", "STORE_B")

            elif scenario_step % 4 == 2:
                # Legitimate purchase at Store B
                print("🛒 Generating legitimate purchase at Store B...")
                self.process_legitimate_transaction("STORE_B")
                time.sleep(2)

                # Simulate replication to Store A
                print("🔄 Replicating to Store A...")
                self.simulate_replication("STORE_B", "STORE_A")

            elif scenario_step % 4 == 3:
                # Fraudulent attempt at Store B
                print("🚨 Simulating fraud attempt at Store B...")
                self.process_fraudulent_transaction("STORE_B")
                time.sleep(2)

                # Simulate replication to Store A (fraud data spreads too)
                print("🔄 Replicating fraud data to Store A...")
                self.simulate_replication("STORE_B", "STORE_A")

            else:
                # Cross-store fraud detection scenario
                print("🔍 Cross-store fraud detection scenario...")

                # First, legitimate purchase at Store A
                legit_txn = self.process_legitimate_transaction("STORE_A")
                time.sleep(1)

                # Replicate to Store B
                self.simulate_replication("STORE_A", "STORE_B")
                time.sleep(1)

                # Now fraudster tries to return the same item at Store B
                print("🚨 Fraudster attempting return of replicated item...")
                fraud_txn = self.process_fraudulent_transaction("STORE_B")

                # This should trigger fraud detection
                self.detect_cross_store_fraud(legit_txn, fraud_txn)

            # Print current statistics
            self.print_current_stats()

            # Wait before next scenario step
            time.sleep(random.uniform(3, 8))

        print(f"\n🎬 Scenario Complete!")
        self.print_final_stats()

    def detect_cross_store_fraud(self, original_txn: Dict, suspicious_txn: Dict):
        """Detect fraud patterns across stores"""
        print(f"\n🔍 CROSS-STORE FRAUD ANALYSIS")
        print("-" * 40)

        fraud_score = 0
        indicators = []

        # Check if same product being returned
        if (original_txn["product"]["name"] == suspicious_txn["product"]["name"]):
            fraud_score += 30
            indicators.append("same_product_cross_store")

        # Check photo verification
        if not suspicious_txn["face_verified"]:
            fraud_score += 40
            indicators.append("no_photo_verification")

        # Check customer mismatch
        if original_txn["customer_id"] != suspicious_txn["customer_id"]:
            fraud_score += 25
            indicators.append("customer_mismatch")

        # Check timing (returns too soon)
        time_diff = suspicious_txn["timestamp"] - original_txn["timestamp"]
        if time_diff < 300:  # Less than 5 minutes
            fraud_score += 20
            indicators.append("suspicious_timing")

        print(f"Original Transaction: {original_txn['transaction_id']}")
        print(f"Suspicious Transaction: {suspicious_txn['transaction_id']}")
        print(f"Fraud Score: {fraud_score}/100")
        print(f"Indicators: {', '.join(indicators)}")

        if fraud_score >= 70:
            print("🚨 HIGH FRAUD RISK - TRANSACTION BLOCKED")
            self.stats["fraud_detected"] += 1
            self.stats["fraud_prevented"] += 1
        elif fraud_score >= 40:
            print("⚠️ MEDIUM FRAUD RISK - MANUAL REVIEW REQUIRED")
            self.stats["fraud_detected"] += 1
        else:
            print("✅ LOW FRAUD RISK - TRANSACTION APPROVED")

    def print_current_stats(self):
        """Print current statistics"""
        print(f"\n📊 Current Statistics:")
        print(f"   Legitimate Transactions: {self.stats['legitimate_transactions']}")
        print(f"   Fraudulent Attempts: {self.stats['fraudulent_attempts']}")
        print(f"   Fraud Detected: {self.stats['fraud_detected']}")
        print(f"   Fraud Prevented: {self.stats['fraud_prevented']}")
        print(f"   Value Protected: ${self.stats['total_value_protected']:.2f}")
        print(f"   Replication Events: {self.stats['replication_events']}")
        print(f"   Avg Replication Time: {self.stats['avg_replication_time']:.2f}ms")

    def print_final_stats(self):
        """Print final comprehensive statistics"""
        print(f"\n📊 FINAL FRAUD DETECTION STATISTICS")
        print("=" * 50)
        print(f"🛒 Legitimate Transactions: {self.stats['legitimate_transactions']}")
        print(f"🚨 Fraudulent Attempts: {self.stats['fraudulent_attempts']}")
        print(f"🔍 Fraud Detected: {self.stats['fraud_detected']}")
        print(f"🛡️ Fraud Prevented: {self.stats['fraud_prevented']}")
        print(f"💰 Total Value Protected: ${self.stats['total_value_protected']:.2f}")
        print(f"🔄 Replication Events: {self.stats['replication_events']}")
        print(f"⏱️ Avg Replication Time: {self.stats['avg_replication_time']:.2f}ms")

        # Calculate effectiveness
        if self.stats['fraudulent_attempts'] > 0:
            detection_rate = (self.stats['fraud_detected'] / self.stats['fraudulent_attempts']) * 100
            prevention_rate = (self.stats['fraud_prevented'] / self.stats['fraudulent_attempts']) * 100
            print(f"🎯 Fraud Detection Rate: {detection_rate:.1f}%")
            print(f"🛡️ Fraud Prevention Rate: {prevention_rate:.1f}%")

        print("=" * 50)

def main():
    """Main demo function"""
    demo = ComprehensiveFraudDemo()

    print("\n🎬 Comprehensive Fraud Detection Demo")
    print("=" * 50)
    print("This demo showcases:")
    print("1. 📷 Photo verification with face detection")
    print("2. 🔄 Redis Active-Active replication")
    print("3. 🚨 Real-time fraud detection")
    print("4. 🔍 Cross-store fraud analysis")
    print("5. 📊 Comprehensive analytics")
    print("=" * 50)

    while True:
        print("\nDemo Options:")
        print("1. Run Automated Scenario (5 minutes)")
        print("2. Generate Single Legitimate Transaction")
        print("3. Generate Single Fraud Attempt")
        print("4. Show Current Statistics")
        print("5. Exit")

        choice = input("\nSelect option (1-5): ").strip()

        if choice == "1":
            duration = input("Duration in minutes (default 5): ").strip()
            try:
                duration = int(duration) if duration else 5
            except ValueError:
                duration = 5

            try:
                demo.run_automated_scenario(duration)
            except KeyboardInterrupt:
                print("\n🛑 Scenario stopped by user")
                demo.running = False

        elif choice == "2":
            store = input("Store (A/B, default A): ").strip().upper()
            store_id = "STORE_A" if store != "B" else "STORE_B"
            demo.process_legitimate_transaction(store_id)

        elif choice == "3":
            store = input("Store (A/B, default B): ").strip().upper()
            store_id = "STORE_B" if store != "A" else "STORE_A"
            demo.process_fraudulent_transaction(store_id)

        elif choice == "4":
            demo.print_current_stats()

        elif choice == "5":
            break

        else:
            print("Invalid option. Please try again.")

    print("\n👋 Demo completed!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
