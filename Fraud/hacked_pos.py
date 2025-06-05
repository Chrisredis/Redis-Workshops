#!/usr/bin/env python3
"""
Hacked POS Simulator for Store B - Fraudulent Transactions without Photo Verification

This script simulates a compromised Point of Sale system that:
1. Processes fraudulent return transactions
2. Does NOT capture customer photos (security bypass)
3. Attempts to return items purchased at other stores
4. Demonstrates fraud patterns for detection
"""

import redis
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List
import logging
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HackedPOSSimulator:
    def __init__(self, store_id: str = "STORE_B", redis_host: str = "localhost", redis_port: int = 6380):
        """Initialize Hacked POS Simulator for Store B"""
        self.store_id = store_id
        self.redis_host = redis_host
        self.redis_port = redis_port
        
        # Connect to Redis (Store B instance)
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=0,
                decode_responses=False
            )
            self.redis_client.ping()
            logger.info(f"🔓 Connected to Redis at {redis_host}:{redis_port} (Store B - Compromised)")
        except redis.ConnectionError:
            logger.error(f"❌ Failed to connect to Redis at {redis_host}:{redis_port}")
            raise
        
        # Fraudster profiles
        self.fraudster_profiles = [
            {"id": "FRAUD_001", "name": "John Doe", "method": "stolen_receipt"},
            {"id": "FRAUD_002", "name": "Jane Smith", "method": "fake_transaction_id"},
            {"id": "FRAUD_003", "name": "Bob Wilson", "method": "social_engineering"},
            {"id": "FRAUD_004", "name": "Alice Brown", "method": "system_exploit"}
        ]
    
    def scan_for_purchase_transactions(self) -> List[Dict]:
        """Scan Redis for purchase transactions to target for fraudulent returns"""
        try:
            # Get recent purchase transactions from the stream
            stream_data = self.redis_client.xrevrange("transaction_stream", count=50)
            
            purchase_transactions = []
            for stream_id, fields in stream_data:
                if fields.get(b'type', b'').decode() == 'PURCHASE':
                    transaction = {
                        "transaction_id": fields[b'transaction_id'].decode(),
                        "customer_id": fields[b'customer_id'].decode(),
                        "store_id": fields[b'store_id'].decode(),
                        "amount": fields[b'amount'].decode(),
                        "product_sku": fields.get(b'product_sku', b'').decode(),
                        "has_photo": fields[b'has_photo'].decode() == "true",
                        "timestamp": fields[b'timestamp'].decode()
                    }
                    purchase_transactions.append(transaction)
            
            logger.info(f"🔍 Found {len(purchase_transactions)} purchase transactions to target")
            return purchase_transactions
            
        except Exception as e:
            logger.error(f"❌ Error scanning for transactions: {e}")
            return []
    
    def attempt_fraudulent_return(self, target_transaction_id: str, fraudster_id: str = None) -> Dict:
        """Attempt a fraudulent return without proper verification"""
        try:
            # Get original transaction details
            transaction_key = f"transaction:{target_transaction_id}"
            original_data = self.redis_client.get(transaction_key)
            
            if not original_data:
                return {"error": "Target transaction not found", "fraud_detected": True}
            
            original_transaction = json.loads(original_data)
            
            # Select random fraudster if not specified
            if not fraudster_id:
                fraudster = random.choice(self.fraudster_profiles)
                fraudster_id = fraudster["id"]
                fraud_method = fraudster["method"]
            else:
                fraud_method = "manual_override"
            
            # Create fraudulent return transaction
            fraud_transaction_id = f"FRAUD_{self.store_id}_{uuid.uuid4().hex[:8].upper()}"
            timestamp = int(time.time())
            
            fraud_transaction = {
                "transaction_id": fraud_transaction_id,
                "original_transaction_id": target_transaction_id,
                "store_id": self.store_id,
                "customer_id": fraudster_id,  # Using fraudster ID instead of real customer
                "transaction_type": "RETURN",
                "product": original_transaction["product"],
                "amount": -original_transaction["amount"],  # Negative for return
                "timestamp": timestamp,
                "datetime": datetime.fromtimestamp(timestamp).isoformat(),
                "has_photo": False,  # NO PHOTO VERIFICATION - KEY FRAUD INDICATOR
                "verification_method": "NONE",  # No verification
                "fraud_indicators": {
                    "no_photo_verification": True,
                    "different_store": original_transaction["store_id"] != self.store_id,
                    "suspicious_customer_id": True,
                    "fraud_method": fraud_method,
                    "original_store": original_transaction["store_id"]
                },
                "status": "SUSPICIOUS"
            }
            
            # Store fraudulent transaction
            fraud_key = f"transaction:{fraud_transaction_id}"
            self.redis_client.set(fraud_key, json.dumps(fraud_transaction))
            
            # Add to transaction stream with fraud indicators
            stream_data = {
                "transaction_id": fraud_transaction_id,
                "original_transaction_id": target_transaction_id,
                "store_id": self.store_id,
                "customer_id": fraudster_id,
                "type": "RETURN",
                "amount": str(fraud_transaction["amount"]),
                "has_photo": "false",  # Critical fraud indicator
                "verification": "NONE",
                "fraud_attempt": "true",
                "fraud_method": fraud_method,
                "original_store": original_transaction["store_id"],
                "timestamp": str(timestamp)
            }
            self.redis_client.xadd("transaction_stream", stream_data)
            
            # Add to fraud alerts stream
            fraud_alert = {
                "alert_id": f"ALERT_{uuid.uuid4().hex[:8].upper()}",
                "fraud_transaction_id": fraud_transaction_id,
                "original_transaction_id": target_transaction_id,
                "fraud_type": "UNAUTHORIZED_RETURN",
                "risk_level": "HIGH",
                "indicators": json.dumps(fraud_transaction["fraud_indicators"]),
                "timestamp": str(timestamp),
                "store_id": self.store_id
            }
            self.redis_client.xadd("fraud_alerts", fraud_alert)
            
            logger.warning(f"🚨 FRAUD ATTEMPT: {fraud_transaction_id} - No photo verification")
            logger.warning(f"   Target: {target_transaction_id} from {original_transaction['store_id']}")
            logger.warning(f"   Method: {fraud_method}")
            
            return {
                "fraud_detected": True,
                "transaction_id": fraud_transaction_id,
                "original_transaction_id": target_transaction_id,
                "amount": fraud_transaction["amount"],
                "has_photo": False,
                "verification_method": "NONE",
                "fraud_indicators": fraud_transaction["fraud_indicators"],
                "timestamp": timestamp
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing fraudulent return: {e}")
            return {"error": f"Failed to process fraudulent return: {e}"}
    
    def simulate_automated_fraud_attempts(self, max_attempts: int = 5):
        """Simulate automated fraud attempts targeting recent purchases"""
        logger.info(f"🤖 Starting automated fraud simulation (max {max_attempts} attempts)")
        
        # Get target transactions
        target_transactions = self.scan_for_purchase_transactions()
        
        if not target_transactions:
            logger.warning("⚠️ No target transactions found for fraud simulation")
            return
        
        attempts = 0
        for transaction in target_transactions[:max_attempts]:
            if attempts >= max_attempts:
                break
                
            # Only target transactions from other stores
            if transaction["store_id"] != self.store_id:
                logger.info(f"🎯 Targeting transaction: {transaction['transaction_id']}")
                
                # Random delay to simulate realistic timing
                time.sleep(random.uniform(1, 3))
                
                result = self.attempt_fraudulent_return(transaction["transaction_id"])
                
                if result.get("fraud_detected"):
                    logger.warning(f"🚨 Fraud attempt completed: {result['transaction_id']}")
                    attempts += 1
                else:
                    logger.error(f"❌ Fraud attempt failed: {result.get('error')}")
        
        logger.info(f"🏁 Fraud simulation completed: {attempts} attempts made")
    
    def monitor_legitimate_returns(self):
        """Monitor for legitimate returns to create simultaneous fraud attempts"""
        logger.info("👁️ Monitoring for legitimate returns to exploit...")
        
        try:
            # Monitor transaction stream for legitimate returns
            last_id = '$'  # Start from latest
            
            while True:
                # Read new transactions from stream
                streams = self.redis_client.xread({'transaction_stream': last_id}, block=1000, count=1)
                
                for stream_name, messages in streams:
                    for message_id, fields in messages:
                        last_id = message_id
                        
                        # Check if this is a legitimate return
                        if (fields.get(b'type', b'').decode() == 'RETURN' and 
                            fields.get(b'has_photo', b'').decode() == 'true' and
                            fields.get(b'store_id', b'').decode() != self.store_id):
                            
                            original_txn_id = fields.get(b'original_transaction_id', b'').decode()
                            
                            logger.info(f"🎯 Detected legitimate return: {fields[b'transaction_id'].decode()}")
                            logger.info(f"   Attempting simultaneous fraud on: {original_txn_id}")
                            
                            # Small delay to simulate near-simultaneous attempt
                            time.sleep(random.uniform(0.5, 2.0))
                            
                            # Attempt fraudulent return on same original transaction
                            fraud_result = self.attempt_fraudulent_return(original_txn_id)
                            
                            if fraud_result.get("fraud_detected"):
                                logger.warning(f"🚨 Simultaneous fraud attempt: {fraud_result['transaction_id']}")
                
        except KeyboardInterrupt:
            logger.info("👋 Stopping fraud monitoring...")
        except Exception as e:
            logger.error(f"❌ Error in fraud monitoring: {e}")
    
    def get_fraud_statistics(self) -> Dict:
        """Get fraud attempt statistics"""
        try:
            # Count fraud attempts from alerts stream
            fraud_alerts = self.redis_client.xrevrange("fraud_alerts", count=100)
            
            total_attempts = len(fraud_alerts)
            recent_attempts = len([alert for alert in fraud_alerts 
                                 if int(alert[1][b'timestamp'].decode()) > (time.time() - 3600)])
            
            return {
                "total_fraud_attempts": total_attempts,
                "recent_attempts_1h": recent_attempts,
                "store_id": self.store_id,
                "status": "COMPROMISED"
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting fraud statistics: {e}")
            return {}

def main():
    """Main function to run hacked POS simulator"""
    hacked_pos = HackedPOSSimulator()
    
    try:
        print("\n🔓 Store B POS System - COMPROMISED (Fraud Simulation)")
        print("=" * 60)
        print("⚠️  WARNING: This system simulates fraudulent activities for demo purposes")
        
        while True:
            print("\nFraud Simulation Options:")
            print("1. Scan for Target Transactions")
            print("2. Attempt Single Fraudulent Return")
            print("3. Run Automated Fraud Simulation")
            print("4. Monitor for Legitimate Returns (Real-time)")
            print("5. View Fraud Statistics")
            print("6. Exit")
            
            choice = input("\nSelect option (1-6): ").strip()
            
            if choice == "1":
                targets = hacked_pos.scan_for_purchase_transactions()
                print(f"\n🎯 Found {len(targets)} potential targets:")
                for i, target in enumerate(targets[:10], 1):
                    print(f"  {i}. {target['transaction_id']} - ${target['amount']} - Store: {target['store_id']}")
            
            elif choice == "2":
                transaction_id = input("Target Transaction ID: ").strip()
                if transaction_id:
                    result = hacked_pos.attempt_fraudulent_return(transaction_id)
                    if result.get("fraud_detected"):
                        print(f"🚨 Fraud attempt completed: {result['transaction_id']}")
                        print(f"   No photo verification: {not result['has_photo']}")
                    else:
                        print(f"❌ Fraud attempt failed: {result.get('error')}")
            
            elif choice == "3":
                max_attempts = input("Max fraud attempts (default 5): ").strip()
                max_attempts = int(max_attempts) if max_attempts.isdigit() else 5
                hacked_pos.simulate_automated_fraud_attempts(max_attempts)
            
            elif choice == "4":
                print("👁️ Starting real-time monitoring... (Press Ctrl+C to stop)")
                hacked_pos.monitor_legitimate_returns()
            
            elif choice == "5":
                stats = hacked_pos.get_fraud_statistics()
                print(f"\n📊 Fraud Statistics:")
                print(f"   Total attempts: {stats.get('total_fraud_attempts', 0)}")
                print(f"   Recent (1h): {stats.get('recent_attempts_1h', 0)}")
                print(f"   Store status: {stats.get('status', 'UNKNOWN')}")
            
            elif choice == "6":
                break
            
            else:
                print("Invalid option. Please try again.")
    
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down hacked POS system...")

if __name__ == "__main__":
    main()
