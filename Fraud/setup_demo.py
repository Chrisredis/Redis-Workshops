#!/usr/bin/env python3
"""
Setup Script for Redis Active-Active Fraud Detection Demo

This script helps set up the demo environment including:
1. Redis instance configuration
2. Sample data generation
3. Demo scenario execution
"""

import subprocess
import sys
import time
import redis
import json
import threading
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DemoSetup:
    def __init__(self):
        self.redis_store_a = None
        self.redis_store_b = None
        
    def check_redis_connection(self, host, port, store_name):
        """Check if Redis instance is running and accessible"""
        try:
            client = redis.Redis(host=host, port=port, db=0, decode_responses=True)
            client.ping()
            logger.info(f"✅ {store_name} Redis is running at {host}:{port}")
            return client
        except redis.ConnectionError:
            logger.error(f"❌ {store_name} Redis is not accessible at {host}:{port}")
            return None
    
    def start_redis_containers(self):
        """Start Redis containers using Docker"""
        logger.info("🐳 Starting Redis containers...")
        
        try:
            # Start Store A Redis (port 6379)
            subprocess.run([
                "docker", "run", "-d", 
                "--name", "redis-store-a",
                "-p", "6379:6379",
                "redis/redis-stack:latest"
            ], check=True, capture_output=True)
            logger.info("✅ Started Redis Store A container (port 6379)")
        except subprocess.CalledProcessError as e:
            if "already in use" in str(e.stderr):
                logger.info("ℹ️ Redis Store A container already exists")
            else:
                logger.error(f"❌ Failed to start Redis Store A: {e}")
        
        try:
            # Start Store B Redis (port 6380)
            subprocess.run([
                "docker", "run", "-d",
                "--name", "redis-store-b", 
                "-p", "6380:6379",
                "redis/redis-stack:latest"
            ], check=True, capture_output=True)
            logger.info("✅ Started Redis Store B container (port 6380)")
        except subprocess.CalledProcessError as e:
            if "already in use" in str(e.stderr):
                logger.info("ℹ️ Redis Store B container already exists")
            else:
                logger.error(f"❌ Failed to start Redis Store B: {e}")
        
        # Wait for containers to be ready
        logger.info("⏳ Waiting for Redis containers to be ready...")
        time.sleep(5)
        
        # Test connections
        self.redis_store_a = self.check_redis_connection("localhost", 6379, "Store A")
        self.redis_store_b = self.check_redis_connection("localhost", 6380, "Store B")
        
        return self.redis_store_a is not None and self.redis_store_b is not None
    
    def install_dependencies(self):
        """Install required Python packages"""
        logger.info("📦 Installing required dependencies...")
        
        packages = [
            "redis[hiredis]",
            "flask",
            "flask-socketio",
            "opencv-python",
            "numpy"
        ]
        
        for package in packages:
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", package
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logger.info(f"✅ Installed {package}")
            except subprocess.CalledProcessError:
                logger.error(f"❌ Failed to install {package}")
                return False
        
        return True
    
    def setup_sample_data(self):
        """Set up sample data for the demo"""
        logger.info("📊 Setting up sample data...")
        
        if not self.redis_store_a:
            logger.error("❌ Store A Redis not available")
            return False
        
        # Sample customer data
        customers = [
            {"id": "CUST_001", "name": "John Smith", "email": "john@example.com"},
            {"id": "CUST_002", "name": "Jane Doe", "email": "jane@example.com"},
            {"id": "CUST_003", "name": "Bob Wilson", "email": "bob@example.com"}
        ]
        
        # Sample product data
        products = [
            {"sku": "SHIRT_001", "name": "Cotton T-Shirt", "price": 29.99},
            {"sku": "SHIRT_002", "name": "Polo Shirt", "price": 45.99},
            {"sku": "JEANS_001", "name": "Blue Jeans", "price": 89.99}
        ]
        
        try:
            # Store customer data
            for customer in customers:
                key = f"customer:{customer['id']}"
                self.redis_store_a.set(key, json.dumps(customer))
            
            # Store product data
            for product in products:
                key = f"product:{product['sku']}"
                self.redis_store_a.set(key, json.dumps(product))
            
            logger.info(f"✅ Created {len(customers)} customers and {len(products)} products")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error setting up sample data: {e}")
            return False
    
    def run_demo_scenario(self):
        """Run the complete demo scenario"""
        logger.info("🎬 Starting demo scenario...")
        
        try:
            from pos_simulator import POSSimulator
            from hacked_pos import HackedPOSSimulator
            
            # Initialize simulators
            pos_store_a = POSSimulator("STORE_A", "localhost", 6379)
            hacked_pos_store_b = HackedPOSSimulator("STORE_B", "localhost", 6380)
            
            logger.info("🛒 Step 1: Customer purchases shirt at Store A...")
            purchase_result = pos_store_a.process_purchase("CUST_001", "SHIRT_001")
            
            if not purchase_result.get("success"):
                logger.error(f"❌ Purchase failed: {purchase_result.get('error')}")
                return False
            
            transaction_id = purchase_result["transaction_id"]
            logger.info(f"✅ Purchase completed: {transaction_id}")
            
            # Wait for Active-Active sync (simulated)
            logger.info("🔄 Waiting for Active-Active replication...")
            time.sleep(2)
            
            # Simulate data sync to Store B
            transaction_data = self.redis_store_a.get(f"transaction:{transaction_id}")
            if transaction_data:
                self.redis_store_b.set(f"transaction:{transaction_id}", transaction_data)
                
                # Copy photo data if exists
                photo_data = self.redis_store_a.get(f"photo:{transaction_id}")
                if photo_data:
                    self.redis_store_b.set(f"photo:{transaction_id}", photo_data)
            
            logger.info("✅ Data replicated to Store B")
            
            # Step 2: Legitimate return at Store A
            logger.info("🔄 Step 2: Customer returns item at Store A (legitimate)...")
            time.sleep(1)
            
            return_result = pos_store_a.process_return("CUST_001", transaction_id)
            if return_result.get("success"):
                logger.info(f"✅ Legitimate return processed: {return_result['transaction_id']}")
            
            # Step 3: Fraudulent return attempt at Store B
            logger.info("🚨 Step 3: Fraudulent return attempt at Store B...")
            time.sleep(0.5)  # Simulate near-simultaneous attempt
            
            fraud_result = hacked_pos_store_b.attempt_fraudulent_return(transaction_id)
            if fraud_result.get("fraud_detected"):
                logger.warning(f"🚨 Fraud detected: {fraud_result['transaction_id']}")
            
            logger.info("🎯 Demo scenario completed successfully!")
            logger.info("📊 Open the dashboard at http://localhost:8080 to see the results")
            
            return True
            
        except ImportError as e:
            logger.error(f"❌ Missing required modules: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error running demo scenario: {e}")
            return False
    
    def start_dashboard(self):
        """Start the fraud detection dashboard"""
        logger.info("🖥️ Starting fraud detection dashboard...")
        
        try:
            import fraud_dashboard
            
            # Start dashboard in a separate thread
            dashboard_thread = threading.Thread(
                target=lambda: fraud_dashboard.socketio.run(
                    fraud_dashboard.app, 
                    host='0.0.0.0', 
                    port=8080, 
                    debug=False
                )
            )
            dashboard_thread.daemon = True
            dashboard_thread.start()
            
            logger.info("✅ Dashboard started at http://localhost:8080")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error starting dashboard: {e}")
            return False
    
    def cleanup(self):
        """Clean up demo environment"""
        logger.info("🧹 Cleaning up demo environment...")
        
        try:
            # Stop and remove containers
            subprocess.run(["docker", "stop", "redis-store-a"], 
                         capture_output=True, check=False)
            subprocess.run(["docker", "rm", "redis-store-a"], 
                         capture_output=True, check=False)
            
            subprocess.run(["docker", "stop", "redis-store-b"], 
                         capture_output=True, check=False)
            subprocess.run(["docker", "rm", "redis-store-b"], 
                         capture_output=True, check=False)
            
            logger.info("✅ Cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")

def main():
    """Main setup function"""
    print("\n🛡️ Redis Active-Active Fraud Detection Demo Setup")
    print("=" * 60)
    
    setup = DemoSetup()
    
    try:
        # Check if Docker is available
        try:
            subprocess.run(["docker", "--version"], 
                         capture_output=True, check=True)
            logger.info("✅ Docker is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("❌ Docker is not available. Please install Docker first.")
            return
        
        # Install dependencies
        if not setup.install_dependencies():
            logger.error("❌ Failed to install dependencies")
            return
        
        # Start Redis containers
        if not setup.start_redis_containers():
            logger.error("❌ Failed to start Redis containers")
            return
        
        # Set up sample data
        if not setup.setup_sample_data():
            logger.error("❌ Failed to set up sample data")
            return
        
        # Start dashboard
        if not setup.start_dashboard():
            logger.error("❌ Failed to start dashboard")
            return
        
        # Run demo scenario
        time.sleep(2)  # Give dashboard time to start
        if not setup.run_demo_scenario():
            logger.error("❌ Failed to run demo scenario")
            return
        
        print("\n🎉 Demo setup completed successfully!")
        print("=" * 60)
        print("📊 Dashboard: http://localhost:8080")
        print("🏪 Store A Redis: localhost:6379")
        print("🔓 Store B Redis: localhost:6380")
        print("\nNext steps:")
        print("1. Open the dashboard in your browser")
        print("2. Run pos_simulator.py for legitimate transactions")
        print("3. Run hacked_pos.py for fraud simulation")
        print("\nPress Ctrl+C to stop the demo")
        
        # Keep the script running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n👋 Shutting down demo...")
            setup.cleanup()
    
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        setup.cleanup()

if __name__ == "__main__":
    main()
