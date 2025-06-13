#!/usr/bin/env python3
"""
Unified Demo Launcher
Starts the complete fraud detection demo with unified POS interface
"""

import subprocess
import time
import webbrowser
import os
import sys
import redis

def check_redis():
    """Check if Redis stores are running"""
    try:
        redis_a = redis.Redis(host='localhost', port=6379)
        redis_b = redis.Redis(host='localhost', port=6380)
        
        redis_a.ping()
        redis_b.ping()
        
        print("✅ Redis stores are running")
        return True
    except Exception as e:
        print(f"❌ Redis connection error: {e}")
        print("\n🔧 To start Redis containers:")
        print("docker run -d --name redis-store-a -p 6379:6379 redis:latest")
        print("docker run -d --name redis-store-b -p 6380:6379 redis:latest")
        return False

def check_dependencies():
    """Check if required Python packages are installed"""
    required_packages = [
        'redis', 'opencv-python', 'pillow', 'flask', 'flask-socketio'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print(f"\n📦 Install with: pip install {' '.join(missing)}")
        return False
    
    print("✅ All dependencies installed")
    return True

def main():
    print("🚀 Redis Fraud Detection - Unified Demo Launcher")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Check Redis
    if not check_redis():
        return
    
    print("\n🎯 Starting Unified POS System...")
    print("This will open a single window with:")
    print("  📱 Product selection")
    print("  📷 Camera capture with face detection")
    print("  💳 Transaction processing")
    print("  🚨 Fraud detection")
    print("  🌐 Dashboard integration")
    
    try:
        # Start the unified POS
        subprocess.run([sys.executable, "unified_pos.py"], check=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Demo stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting demo: {e}")

if __name__ == "__main__":
    main()
