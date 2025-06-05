#!/usr/bin/env python3
"""
Quick Demo Runner for Redis Active-Active Fraud Detection

This script provides a simple way to run the fraud detection demo with
pre-configured scenarios and automatic setup.
"""

import subprocess
import sys
import time
import threading
import webbrowser
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FraudDemo:
    def __init__(self):
        self.processes = []
        self.dashboard_started = False
        
    def check_dependencies(self):
        """Check if required dependencies are available"""
        logger.info("🔍 Checking dependencies...")
        
        required_modules = [
            'redis', 'flask', 'flask_socketio', 'cv2', 'numpy'
        ]
        
        missing_modules = []
        for module in required_modules:
            try:
                __import__(module)
                logger.info(f"✅ {module} is available")
            except ImportError:
                missing_modules.append(module)
                logger.warning(f"❌ {module} is missing")
        
        if missing_modules:
            logger.error(f"Missing modules: {', '.join(missing_modules)}")
            logger.info("Run: pip install -r requirements.txt")
            return False
        
        return True
    
    def start_redis_containers(self):
        """Start Redis containers if not already running"""
        logger.info("🐳 Starting Redis containers...")
        
        # Check if containers are already running
        try:
            result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
            if 'redis-store-a' in result.stdout and 'redis-store-b' in result.stdout:
                logger.info("✅ Redis containers are already running")
                return True
        except:
            pass
        
        # Start containers
        commands = [
            ['docker', 'run', '-d', '--name', 'redis-store-a', '-p', '6379:6379', 'redis/redis-stack:latest'],
            ['docker', 'run', '-d', '--name', 'redis-store-b', '-p', '6380:6379', 'redis/redis-stack:latest']
        ]
        
        for cmd in commands:
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                logger.info(f"✅ Started {cmd[3]}")
            except subprocess.CalledProcessError:
                logger.info(f"ℹ️ {cmd[3]} may already exist")
        
        # Wait for containers to be ready
        time.sleep(5)
        return True
    
    def start_dashboard(self):
        """Start the fraud detection dashboard"""
        logger.info("🖥️ Starting fraud detection dashboard...")
        
        try:
            # Start dashboard process
            dashboard_process = subprocess.Popen([
                sys.executable, 'fraud_dashboard.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes.append(dashboard_process)
            
            # Wait a moment for dashboard to start
            time.sleep(3)
            
            # Check if dashboard is running
            if dashboard_process.poll() is None:
                logger.info("✅ Dashboard started successfully")
                self.dashboard_started = True
                
                # Open browser
                try:
                    webbrowser.open('http://localhost:8080')
                    logger.info("🌐 Opened dashboard in browser")
                except:
                    logger.info("📊 Dashboard available at: http://localhost:8080")
                
                return True
            else:
                logger.error("❌ Dashboard failed to start")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error starting dashboard: {e}")
            return False
    
    def run_purchase_scenario(self):
        """Run a sample purchase scenario"""
        logger.info("🛒 Running purchase scenario...")
        
        try:
            from pos_simulator import POSSimulator
            
            pos = POSSimulator("STORE_A", "localhost", 6379)
            
            # Process a sample purchase
            result = pos.process_purchase("CUST_001", "SHIRT_001")
            
            if result.get("success"):
                logger.info(f"✅ Purchase successful: {result['transaction_id']}")
                return result['transaction_id']
            else:
                logger.error(f"❌ Purchase failed: {result.get('error')}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error in purchase scenario: {e}")
            return None
    
    def run_fraud_scenario(self, target_transaction_id):
        """Run fraud detection scenario"""
        logger.info("🚨 Running fraud scenario...")
        
        try:
            from pos_simulator import POSSimulator
            from hacked_pos import HackedPOSSimulator
            
            # Initialize both systems
            legitimate_pos = POSSimulator("STORE_A", "localhost", 6379)
            hacked_pos = HackedPOSSimulator("STORE_B", "localhost", 6380)
            
            # Simulate data replication (in real Active-Active, this would be automatic)
            self.simulate_active_active_sync(target_transaction_id)
            
            # Start fraud scenario in separate threads
            def legitimate_return():
                time.sleep(1)  # Small delay
                logger.info("✅ Processing legitimate return at Store A...")
                result = legitimate_pos.process_return("CUST_001", target_transaction_id)
                if result.get("success"):
                    logger.info(f"✅ Legitimate return: {result['transaction_id']}")
            
            def fraudulent_return():
                time.sleep(1.5)  # Slightly later to simulate near-simultaneous
                logger.info("🚨 Attempting fraudulent return at Store B...")
                result = hacked_pos.attempt_fraudulent_return(target_transaction_id)
                if result.get("fraud_detected"):
                    logger.warning(f"🚨 Fraud detected: {result['transaction_id']}")
            
            # Run both scenarios
            thread1 = threading.Thread(target=legitimate_return)
            thread2 = threading.Thread(target=fraudulent_return)
            
            thread1.start()
            thread2.start()
            
            thread1.join()
            thread2.join()
            
            logger.info("🎯 Fraud scenario completed!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in fraud scenario: {e}")
            return False
    
    def simulate_active_active_sync(self, transaction_id):
        """Simulate Active-Active replication between Redis instances"""
        logger.info("🔄 Simulating Active-Active replication...")
        
        try:
            import redis
            
            # Connect to both instances
            redis_a = redis.Redis(host='localhost', port=6379, db=0, decode_responses=False)
            redis_b = redis.Redis(host='localhost', port=6380, db=0, decode_responses=False)
            
            # Copy transaction data
            transaction_data = redis_a.get(f"transaction:{transaction_id}")
            if transaction_data:
                redis_b.set(f"transaction:{transaction_id}", transaction_data)
            
            # Copy photo data
            photo_data = redis_a.get(f"photo:{transaction_id}")
            if photo_data:
                redis_b.set(f"photo:{transaction_id}", photo_data)
            
            # Copy customer data
            customer_data = redis_a.get("customer:CUST_001")
            if customer_data:
                redis_b.set("customer:CUST_001", customer_data)
            
            logger.info("✅ Data replicated to Store B")
            
        except Exception as e:
            logger.error(f"❌ Error in replication simulation: {e}")
    
    def run_interactive_demo(self):
        """Run interactive demo with user choices"""
        print("\n🛡️ Redis Active-Active Fraud Detection Demo")
        print("=" * 50)
        
        while True:
            print("\nDemo Options:")
            print("1. Run Complete Fraud Scenario")
            print("2. Start POS Simulator (Store A)")
            print("3. Start Hacked POS (Store B)")
            print("4. Open Dashboard")
            print("5. View Demo Status")
            print("6. Exit")
            
            choice = input("\nSelect option (1-6): ").strip()
            
            if choice == "1":
                # Run complete scenario
                transaction_id = self.run_purchase_scenario()
                if transaction_id:
                    time.sleep(2)
                    self.run_fraud_scenario(transaction_id)
                    print("\n🎉 Complete fraud scenario executed!")
                    print("📊 Check the dashboard to see the results")
            
            elif choice == "2":
                print("🏪 Starting POS Simulator for Store A...")
                subprocess.Popen([sys.executable, 'pos_simulator.py'])
                print("✅ POS Simulator started in new window")
            
            elif choice == "3":
                print("🔓 Starting Hacked POS for Store B...")
                subprocess.Popen([sys.executable, 'hacked_pos.py'])
                print("✅ Hacked POS started in new window")
            
            elif choice == "4":
                if not self.dashboard_started:
                    self.start_dashboard()
                else:
                    webbrowser.open('http://localhost:8080')
                    print("🌐 Dashboard opened in browser")
            
            elif choice == "5":
                self.show_status()
            
            elif choice == "6":
                break
            
            else:
                print("Invalid option. Please try again.")
    
    def show_status(self):
        """Show current demo status"""
        print("\n📊 Demo Status:")
        print(f"Dashboard: {'Running' if self.dashboard_started else 'Not started'}")
        print(f"Active processes: {len(self.processes)}")
        
        # Check Redis containers
        try:
            result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
            if 'redis-store-a' in result.stdout:
                print("Redis Store A: Running")
            else:
                print("Redis Store A: Not running")
                
            if 'redis-store-b' in result.stdout:
                print("Redis Store B: Running")
            else:
                print("Redis Store B: Not running")
        except:
            print("Docker status: Unknown")
    
    def cleanup(self):
        """Clean up demo processes and containers"""
        logger.info("🧹 Cleaning up demo...")
        
        # Terminate processes
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
        
        # Stop containers (optional)
        try:
            subprocess.run(['docker', 'stop', 'redis-store-a', 'redis-store-b'], 
                         capture_output=True, check=False)
        except:
            pass

def main():
    """Main demo function"""
    demo = FraudDemo()
    
    try:
        # Check dependencies
        if not demo.check_dependencies():
            print("\n❌ Missing dependencies. Please run:")
            print("pip install -r requirements.txt")
            return
        
        # Start Redis containers
        if not demo.start_redis_containers():
            print("\n❌ Failed to start Redis containers")
            return
        
        # Start dashboard
        if not demo.start_dashboard():
            print("\n❌ Failed to start dashboard")
            return
        
        print("\n🎉 Demo environment ready!")
        print("📊 Dashboard: http://localhost:8080")
        
        # Run interactive demo
        demo.run_interactive_demo()
        
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down demo...")
    except Exception as e:
        logger.error(f"❌ Demo error: {e}")
    finally:
        demo.cleanup()

if __name__ == "__main__":
    main()
