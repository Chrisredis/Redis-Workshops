#!/usr/bin/env python3
"""
Unified Web-Based POS System
A clean web interface for the fraud detection demo that handles:
1. Product selection
2. Customer identification  
3. Photo capture with face detection
4. Transaction processing
5. Real-time fraud detection
"""

from flask import Flask, render_template, request, jsonify, Response
import cv2
import numpy as np
import redis
import json
import time
import uuid
import base64
import threading
from datetime import datetime
import os

app = Flask(__name__)

class UnifiedWebPOS:
    def __init__(self):
        # Redis connections
        self.redis_store_a = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.redis_store_b = redis.Redis(host='localhost', port=6380, decode_responses=True)
        
        # Camera
        self.camera = None
        self.camera_active = False
        self.captured_photo = None
        self.photo_base64 = None
        
        # Products catalog
        self.products = {
            "LAPTOP_001": {"name": "Gaming Laptop", "price": 2499.99, "category": "Electronics"},
            "WATCH_001": {"name": "Luxury Watch", "price": 1299.99, "category": "Accessories"},
            "PHONE_001": {"name": "Smartphone", "price": 899.99, "category": "Electronics"},
            "JACKET_001": {"name": "Leather Jacket", "price": 299.99, "category": "Clothing"},
            "SHOES_001": {"name": "Running Shoes", "price": 159.99, "category": "Footwear"},
            "TABLET_001": {"name": "Tablet Pro", "price": 799.99, "category": "Electronics"},
            "HEADPHONES_001": {"name": "Wireless Headphones", "price": 249.99, "category": "Electronics"},
            "JEANS_001": {"name": "Designer Jeans", "price": 189.99, "category": "Clothing"}
        }
        
        self.check_redis_connection()
        
    def check_redis_connection(self):
        """Check Redis connection"""
        try:
            self.redis_store_a.ping()
            self.redis_store_b.ping()
            print("✅ Connected to Redis stores")
            return True
        except Exception as e:
            print(f"❌ Redis connection error: {e}")
            return False
    
    def detect_faces(self, frame):
        """Detect faces in the frame and draw rectangles"""
        try:
            # Load face cascade
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            # Convert to grayscale for detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            # Draw rectangles around faces
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, "Face Detected", (x, y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # Add face count
            cv2.putText(frame, f"Faces: {len(faces)}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            return frame, len(faces)
            
        except Exception as e:
            # If face detection fails, return original frame
            cv2.putText(frame, "Face detection unavailable", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            return frame, 0
    
    def generate_camera_frames(self):
        """Generate camera frames for streaming"""
        while self.camera_active and self.camera and self.camera.isOpened():
            ret, frame = self.camera.read()
            if ret:
                # Resize frame
                frame = cv2.resize(frame, (640, 480))
                
                # Add face detection
                frame_with_faces, face_count = self.detect_faces(frame)
                
                # Encode frame
                _, buffer = cv2.imencode('.jpg', frame_with_faces)
                frame_bytes = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                break
    
    def capture_photo_from_camera(self):
        """Capture a photo from the camera"""
        if self.camera and self.camera.isOpened():
            ret, frame = self.camera.read()
            if ret:
                # Resize for storage
                self.captured_photo = cv2.resize(frame, (320, 240))

                # Convert to base64
                _, buffer = cv2.imencode('.jpg', self.captured_photo)
                self.photo_base64 = base64.b64encode(buffer).decode('utf-8')

                # Save photo file for reference
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"customer_photo_{timestamp}.jpg"
                cv2.imwrite(filename, self.captured_photo)

                return True
        return False

    def generate_fake_fraud_photo(self):
        """Generate a fake photo for fraud simulation"""
        try:
            # Create a simple fake image (red rectangle with "FRAUD" text)
            import numpy as np
            fake_image = np.zeros((240, 320, 3), dtype=np.uint8)
            fake_image[:, :] = [0, 0, 128]  # Dark red background

            # Add "FRAUD" text
            cv2.putText(fake_image, "FRAUDSTER", (50, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
            cv2.putText(fake_image, "FAKE PHOTO", (60, 180),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            # Convert to base64
            _, buffer = cv2.imencode('.jpg', fake_image)
            return base64.b64encode(buffer).decode('utf-8')

        except Exception as e:
            print(f"Error generating fake photo: {e}")
            return None

    def generate_different_fraud_photo(self):
        """Generate a different fake photo for photo hash mismatch fraud"""
        try:
            # Create a different fake image (blue background with different text)
            import numpy as np
            fake_image = np.zeros((240, 320, 3), dtype=np.uint8)
            fake_image[:, :] = [128, 0, 0]  # Dark blue background (different from red)

            # Add different text
            cv2.putText(fake_image, "IMPOSTER", (40, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 0), 3)
            cv2.putText(fake_image, "WRONG PERSON", (30, 180),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            # Convert to base64
            _, buffer = cv2.imencode('.jpg', fake_image)
            return base64.b64encode(buffer).decode('utf-8')

        except Exception as e:
            print(f"Error generating different fraud photo: {e}")
            return None

# Global POS instance
pos_system = UnifiedWebPOS()

@app.route('/')
def index():
    """Main POS interface"""
    return render_template('unified_pos.html', products=pos_system.products)

@app.route('/dashboard')
def simple_dashboard():
    """Simple dashboard for viewing transactions"""
    return render_template('simple_dashboard.html')

@app.route('/test')
def test_system():
    """Test endpoint to verify system is working"""
    try:
        # Test Redis connection
        store_a_ping = pos_system.redis_store_a.ping()
        store_b_ping = pos_system.redis_store_b.ping()

        # Count transactions
        store_a_count = len(list(pos_system.redis_store_a.scan_iter(match="transaction:*")))
        store_b_count = len(list(pos_system.redis_store_b.scan_iter(match="transaction:*")))

        return f"""
        <h1>System Test Results</h1>
        <p>✅ Store A Redis: {'Connected' if store_a_ping else 'Failed'}</p>
        <p>✅ Store B Redis: {'Connected' if store_b_ping else 'Failed'}</p>
        <p>📊 Store A Transactions: {store_a_count}</p>
        <p>📊 Store B Transactions: {store_b_count}</p>
        <p>🎯 System Status: All Good!</p>
        <a href="/">← Back to POS</a>
        """
    except Exception as e:
        return f"❌ Error: {e}"

@app.route('/api/products')
def get_products():
    """Get products list"""
    return jsonify(pos_system.products)

@app.route('/api/start_camera', methods=['POST'])
def start_camera():
    """Start camera"""
    try:
        pos_system.camera = cv2.VideoCapture(0)
        if pos_system.camera.isOpened():
            pos_system.camera_active = True
            return jsonify({"success": True, "message": "Camera started"})
        else:
            return jsonify({"success": False, "message": "Camera not available"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Camera error: {e}"})

@app.route('/api/stop_camera', methods=['POST'])
def stop_camera():
    """Stop camera"""
    pos_system.camera_active = False
    if pos_system.camera:
        pos_system.camera.release()
        pos_system.camera = None
    return jsonify({"success": True, "message": "Camera stopped"})

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    if pos_system.camera_active:
        return Response(pos_system.generate_camera_frames(),
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return "Camera not active", 404

@app.route('/api/capture_photo', methods=['POST'])
def capture_photo():
    """Capture photo from camera"""
    if pos_system.capture_photo_from_camera():
        return jsonify({
            "success": True,
            "message": "Photo captured successfully",
            "photo_data": pos_system.photo_base64[:100] + "..." if pos_system.photo_base64 else None
        })
    else:
        return jsonify({"success": False, "message": "Failed to capture photo"})

@app.route('/api/process_transaction', methods=['POST'])
def process_transaction():
    """Process a transaction with replication monitoring"""
    try:
        data = request.json

        # Validate inputs
        customer_id = data.get('customer_id', '').strip()
        product_sku = data.get('product_sku', '')
        store_id = data.get('store_id', 'STORE_A')
        transaction_type = data.get('transaction_type', 'PURCHASE')

        if not customer_id or not product_sku:
            return jsonify({"success": False, "message": "Missing customer ID or product"})

        if product_sku not in pos_system.products:
            return jsonify({"success": False, "message": "Invalid product selected"})

        # Create transaction
        transaction_id = f"TXN_{store_id}_{uuid.uuid4().hex[:8].upper()}"
        product = pos_system.products[product_sku]

        # Generate photo hash for fraud detection
        photo_hash = None
        if pos_system.photo_base64:
            import hashlib
            photo_hash = hashlib.md5(pos_system.photo_base64.encode()).hexdigest()[:16]

        # Create detailed timestamp
        now = datetime.now()
        timestamp_iso = now.isoformat()
        timestamp_readable = now.strftime("%Y-%m-%d %H:%M:%S")

        transaction_data = {
            "transaction_id": transaction_id,
            "store_id": store_id,
            "customer_id": customer_id,
            "product_sku": product_sku,
            "product_name": product["name"],
            "price": product["price"],
            "transaction_type": transaction_type,
            "timestamp": timestamp_iso,
            "timestamp_readable": timestamp_readable,
            "has_photo": bool(pos_system.photo_base64),
            "photo_hash": photo_hash,
            "is_fraudulent": False,
            "processed_at": timestamp_readable
        }

        # Get Redis clients
        source_redis = pos_system.redis_store_a if store_id == "STORE_A" else pos_system.redis_store_b
        target_redis = pos_system.redis_store_b if store_id == "STORE_A" else pos_system.redis_store_a

        # Store in source store
        source_redis.set(f"transaction:{transaction_id}", json.dumps(transaction_data))

        # Store photo if available
        photo_data_for_response = None
        if pos_system.photo_base64:
            source_redis.set(f"photo:{transaction_id}", pos_system.photo_base64)
            photo_data_for_response = pos_system.photo_base64

        # Add to transaction stream
        source_redis.xadd("transaction_stream", {
            "transaction_id": transaction_id,
            "store_id": store_id,
            "customer_id": customer_id,
            "amount": product["price"],
            "type": transaction_type,
            "has_photo": "true" if pos_system.photo_base64 else "false"
        })

        # Simulate replication with timing
        import time
        replication_start = time.perf_counter()

        # Replicate to other store
        target_redis.set(f"transaction:{transaction_id}", json.dumps(transaction_data))
        if pos_system.photo_base64:
            target_redis.set(f"photo:{transaction_id}", pos_system.photo_base64)

        target_redis.xadd("transaction_stream", {
            "transaction_id": transaction_id,
            "store_id": store_id,
            "customer_id": customer_id,
            "amount": product["price"],
            "type": transaction_type,
            "has_photo": "true" if pos_system.photo_base64 else "false",
            "replicated": "true"
        })

        replication_time = (time.perf_counter() - replication_start) * 1000  # Convert to ms

        # Clear captured photo before response
        pos_system.photo_base64 = None
        pos_system.captured_photo = None

        return jsonify({
            "success": True,
            "message": "Transaction processed and replicated successfully",
            "transaction_id": transaction_id,
            "details": {
                "customer": customer_id,
                "product": product["name"],
                "amount": product["price"],
                "photo_verified": bool(photo_data_for_response),
                "photo_hash": photo_hash,
                "photo_data": photo_data_for_response,
                "replication_time_ms": round(replication_time, 2),
                "source_store": store_id,
                "target_store": "STORE_B" if store_id == "STORE_A" else "STORE_A"
            }
        })

    except Exception as e:
        return jsonify({"success": False, "message": f"Transaction failed: {e}"})

@app.route('/api/simulate_fraud', methods=['POST'])
def simulate_fraud():
    """Simulate a fraudulent transaction with photo analysis"""
    try:
        transaction_id = f"TXN_FRAUD_{uuid.uuid4().hex[:8].upper()}"
        fraud_product_sku = "LAPTOP_001"
        product = pos_system.products[fraud_product_sku]

        # Generate fake photo for fraud attempt (different from legitimate customer)
        fake_photo_data = pos_system.generate_fake_fraud_photo()
        fake_photo_hash = None

        if fake_photo_data:
            import hashlib
            fake_photo_hash = hashlib.md5(fake_photo_data.encode()).hexdigest()[:16]

        # Check for existing legitimate transactions to compare against
        legitimate_transactions = []
        try:
            # Look for recent legitimate transactions
            for key in pos_system.redis_store_a.scan_iter(match="transaction:TXN_STORE_A_*"):
                txn_data = pos_system.redis_store_a.get(key)
                if txn_data:
                    txn = json.loads(txn_data)
                    if not txn.get('is_fraudulent', False) and txn.get('has_photo', False):
                        legitimate_transactions.append(txn)
        except:
            pass

        transaction_data = {
            "transaction_id": transaction_id,
            "store_id": "STORE_B",
            "customer_id": "FRAUDSTER_001",
            "product_sku": fraud_product_sku,
            "product_name": product["name"],
            "price": product["price"],
            "transaction_type": "RETURN",
            "timestamp": datetime.now().isoformat(),
            "has_photo": bool(fake_photo_data),
            "photo_hash": fake_photo_hash,
            "is_fraudulent": True,
            "fraud_indicators": ["suspicious_customer", "high_value_return", "photo_hash_mismatch"]
        }

        # Store fraudulent transaction
        pos_system.redis_store_b.set(f"transaction:{transaction_id}", json.dumps(transaction_data))

        # Store fake photo if generated
        if fake_photo_data:
            pos_system.redis_store_b.set(f"photo:{transaction_id}", fake_photo_data)

        # Create fraud alert with detailed analysis
        fraud_score = 85
        risk_indicators = ["High-value return", "Known fraudster"]

        # Add photo-related fraud indicators
        if fake_photo_data and legitimate_transactions:
            risk_indicators.append("Photo hash mismatch with legitimate customer")
            fraud_score += 10
        elif not fake_photo_data:
            risk_indicators.append("Missing photo verification")
            fraud_score += 5

        fraud_alert = {
            "alert_id": f"FRAUD_{uuid.uuid4().hex[:8].upper()}",
            "transaction_id": transaction_id,
            "fraud_score": min(fraud_score, 100),
            "risk_level": "HIGH" if fraud_score > 80 else "MEDIUM",
            "indicators": risk_indicators,
            "timestamp": datetime.now().isoformat(),
            "action_taken": "TRANSACTION_BLOCKED",
            "photo_analysis": {
                "fraud_photo_hash": fake_photo_hash,
                "legitimate_comparison": legitimate_transactions[0].get('photo_hash') if legitimate_transactions else None,
                "hash_match": False
            }
        }

        pos_system.redis_store_b.set(f"fraud_alert:{transaction_id}", json.dumps(fraud_alert))

        # Add to transaction stream
        pos_system.redis_store_b.xadd("transaction_stream", {
            "transaction_id": transaction_id,
            "store_id": "STORE_B",
            "customer_id": "FRAUDSTER_001",
            "amount": product["price"],
            "type": "RETURN",
            "has_photo": "true" if fake_photo_data else "false",
            "fraud_detected": "true",
            "fraud_score": str(fraud_score)
        })

        return jsonify({
            "success": True,
            "message": "Fraud attempt detected and blocked",
            "fraud_details": {
                "transaction_id": transaction_id,
                "fraud_score": fraud_score,
                "risk_level": fraud_alert["risk_level"],
                "action": "TRANSACTION_BLOCKED",
                "indicators": risk_indicators,
                "photo_analysis": fraud_alert["photo_analysis"],
                "fake_photo_data": fake_photo_data,
                "legitimate_comparison": legitimate_transactions[0] if legitimate_transactions else None
            }
        })

    except Exception as e:
        return jsonify({"success": False, "message": f"Fraud simulation failed: {e}"})

@app.route('/api/simulate_photo_fraud', methods=['POST'])
def simulate_photo_fraud():
    """Simulate fraud with different photo (hash mismatch)"""
    try:
        transaction_id = f"TXN_PHOTO_FRAUD_{uuid.uuid4().hex[:8].upper()}"
        fraud_product_sku = "WATCH_001"  # High-value item
        product = pos_system.products[fraud_product_sku]

        # Generate a different fake photo for the fraudster
        different_fake_photo = pos_system.generate_different_fraud_photo()
        different_photo_hash = None

        if different_fake_photo:
            import hashlib
            different_photo_hash = hashlib.md5(different_fake_photo.encode()).hexdigest()[:16]

        # Get a legitimate customer's photo hash for comparison
        legitimate_photo_hash = None
        legitimate_customer = None
        try:
            for key in pos_system.redis_store_a.scan_iter(match="transaction:TXN_STORE_A_*"):
                txn_data = pos_system.redis_store_a.get(key)
                if txn_data:
                    txn = json.loads(txn_data)
                    if not txn.get('is_fraudulent', False) and txn.get('photo_hash'):
                        legitimate_photo_hash = txn.get('photo_hash')
                        legitimate_customer = txn.get('customer_id')
                        break
        except:
            pass

        transaction_data = {
            "transaction_id": transaction_id,
            "store_id": "STORE_B",
            "customer_id": legitimate_customer or "CHRIS_001",  # Claiming to be legitimate customer
            "product_sku": fraud_product_sku,
            "product_name": product["name"],
            "price": product["price"],
            "transaction_type": "RETURN",
            "timestamp": datetime.now().isoformat(),
            "has_photo": True,
            "photo_hash": different_photo_hash,
            "is_fraudulent": True,
            "fraud_indicators": ["photo_hash_mismatch", "identity_theft", "high_value_return"]
        }

        # Store fraudulent transaction
        pos_system.redis_store_b.set(f"transaction:{transaction_id}", json.dumps(transaction_data))

        # Store the different fake photo
        if different_fake_photo:
            pos_system.redis_store_b.set(f"photo:{transaction_id}", different_fake_photo)

        # Create detailed fraud alert
        fraud_alert = {
            "alert_id": f"PHOTO_FRAUD_{uuid.uuid4().hex[:8].upper()}",
            "transaction_id": transaction_id,
            "fraud_score": 95,
            "risk_level": "CRITICAL",
            "indicators": [
                "Photo hash mismatch with known customer",
                "Identity theft attempt",
                "High-value return with wrong photo"
            ],
            "timestamp": datetime.now().isoformat(),
            "action_taken": "TRANSACTION_BLOCKED",
            "photo_analysis": {
                "fraudster_photo_hash": different_photo_hash,
                "legitimate_photo_hash": legitimate_photo_hash,
                "hash_match": False,
                "fraud_type": "PHOTO_SUBSTITUTION"
            }
        }

        pos_system.redis_store_b.set(f"fraud_alert:{transaction_id}", json.dumps(fraud_alert))

        return jsonify({
            "success": True,
            "message": "Photo fraud simulation completed",
            "fraud_details": {
                "transaction_id": transaction_id,
                "fraud_score": 95,
                "risk_level": "CRITICAL",
                "fraud_type": "PHOTO_HASH_MISMATCH",
                "action": "TRANSACTION_BLOCKED",
                "indicators": fraud_alert["indicators"],
                "photo_analysis": fraud_alert["photo_analysis"],
                "fraudster_photo_data": different_fake_photo,
                "legitimate_customer": legitimate_customer
            }
        })

    except Exception as e:
        return jsonify({"success": False, "message": f"Photo fraud simulation failed: {e}"})

@app.route('/api/replication_status')
def get_replication_status():
    """Get current replication status between stores"""
    try:
        # Get recent transactions from both stores
        store_a_count = len(list(pos_system.redis_store_a.scan_iter(match="transaction:*")))
        store_b_count = len(list(pos_system.redis_store_b.scan_iter(match="transaction:*")))

        # Get recent stream entries
        try:
            stream_a = pos_system.redis_store_a.xrevrange("transaction_stream", count=5)
            stream_b = pos_system.redis_store_b.xrevrange("transaction_stream", count=5)
        except:
            stream_a = []
            stream_b = []

        return jsonify({
            "success": True,
            "replication_status": {
                "store_a_transactions": store_a_count,
                "store_b_transactions": store_b_count,
                "sync_status": "SYNCED" if store_a_count == store_b_count else "SYNCING",
                "recent_stream_a": len(stream_a),
                "recent_stream_b": len(stream_b)
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Error getting replication status: {e}"})

@app.route('/api/dashboard_data')
def get_dashboard_data():
    """Get transaction data for dashboard"""
    try:
        # Get all transactions from both stores
        store_a_transactions = []
        store_b_transactions = []

        # Get Store A transactions
        for key in pos_system.redis_store_a.scan_iter(match="transaction:*"):
            try:
                txn_data = pos_system.redis_store_a.get(key)
                if txn_data:
                    txn = json.loads(txn_data)

                    # Normalize transaction data format
                    normalized_txn = {
                        "transaction_id": txn.get("transaction_id", ""),
                        "store_id": txn.get("store_id", "STORE_A"),
                        "customer_id": txn.get("customer_id", ""),
                        "product_name": txn.get("product_name") or txn.get("product", {}).get("name", "Unknown"),
                        "price": txn.get("price") or txn.get("amount", 0),
                        "transaction_type": txn.get("transaction_type", "PURCHASE"),
                        "timestamp": txn.get("timestamp") or txn.get("datetime", ""),
                        "has_photo": txn.get("has_photo", False),
                        "photo_hash": txn.get("photo_hash", ""),
                        "is_fraudulent": txn.get("is_fraudulent", False)
                    }

                    # Get photo if available
                    photo_key = f"photo:{txn['transaction_id']}"
                    photo_data = pos_system.redis_store_a.get(photo_key)
                    if photo_data:
                        normalized_txn['has_photo'] = True
                        normalized_txn['photo_preview'] = "📷"  # Just show icon for dashboard

                    store_a_transactions.append(normalized_txn)
            except Exception as e:
                print(f"Error processing Store A transaction {key}: {e}")

        # Get Store B transactions
        for key in pos_system.redis_store_b.scan_iter(match="transaction:*"):
            try:
                txn_data = pos_system.redis_store_b.get(key)
                if txn_data:
                    txn = json.loads(txn_data)

                    # Normalize transaction data format
                    normalized_txn = {
                        "transaction_id": txn.get("transaction_id", ""),
                        "store_id": txn.get("store_id", "STORE_B"),
                        "customer_id": txn.get("customer_id", ""),
                        "product_name": txn.get("product_name") or txn.get("product", {}).get("name", "Unknown"),
                        "price": txn.get("price") or txn.get("amount", 0),
                        "transaction_type": txn.get("transaction_type", "PURCHASE"),
                        "timestamp": txn.get("timestamp") or txn.get("datetime", ""),
                        "has_photo": txn.get("has_photo", False),
                        "photo_hash": txn.get("photo_hash", ""),
                        "is_fraudulent": txn.get("is_fraudulent", False)
                    }

                    # Get photo if available
                    photo_key = f"photo:{txn['transaction_id']}"
                    photo_data = pos_system.redis_store_b.get(photo_key)
                    if photo_data:
                        normalized_txn['has_photo'] = True
                        normalized_txn['photo_preview'] = "📷"  # Just show icon for dashboard

                    store_b_transactions.append(normalized_txn)
            except Exception as e:
                print(f"Error processing Store B transaction {key}: {e}")

        # Sort by transaction_id (most recent first) to avoid timestamp issues
        store_a_transactions.sort(key=lambda x: x.get('transaction_id', ''), reverse=True)
        store_b_transactions.sort(key=lambda x: x.get('transaction_id', ''), reverse=True)

        return jsonify({
            "success": True,
            "store_a_transactions": store_a_transactions[:10],  # Last 10
            "store_b_transactions": store_b_transactions[:10],  # Last 10
            "total_a": len(store_a_transactions),
            "total_b": len(store_b_transactions)
        })

    except Exception as e:
        return jsonify({"success": False, "message": f"Error getting dashboard data: {e}"})

if __name__ == "__main__":
    print("🚀 Starting Unified Web POS System...")
    print("📱 Access at: http://localhost:5001")
    print("📷 Real camera capture enabled")
    print("🔄 Real-time replication monitoring enabled")
    print("🚨 Enhanced fraud detection with photo analysis")
    app.run(host='0.0.0.0', port=5001, debug=True, threaded=True)

@app.route('/api/process_transaction', methods=['POST'])
def process_transaction():
    """Process a transaction"""
    try:
        data = request.json

        # Validate inputs
        customer_id = data.get('customer_id', '').strip()
        product_sku = data.get('product_sku', '')
        store_id = data.get('store_id', 'STORE_A')
        transaction_type = data.get('transaction_type', 'PURCHASE')

        if not customer_id or not product_sku:
            return jsonify({"success": False, "message": "Missing customer ID or product"})

        if product_sku not in pos_system.products:
            return jsonify({"success": False, "message": "Invalid product selected"})

        # Check for photo if it's a purchase
        if transaction_type == "PURCHASE" and not pos_system.photo_base64:
            return jsonify({"success": False, "message": "Photo required for purchases"})

        # Create transaction
        transaction_id = f"TXN_{store_id}_{uuid.uuid4().hex[:8].upper()}"
        product = pos_system.products[product_sku]

        transaction_data = {
            "transaction_id": transaction_id,
            "store_id": store_id,
            "customer_id": customer_id,
            "product_sku": product_sku,
            "product_name": product["name"],
            "price": product["price"],
            "transaction_type": transaction_type,
            "timestamp": datetime.now().isoformat(),
            "has_photo": bool(pos_system.photo_base64),
            "is_fraudulent": False
        }

        # Get Redis client for the store
        redis_client = pos_system.redis_store_a if store_id == "STORE_A" else pos_system.redis_store_b

        # Store transaction
        redis_client.set(f"transaction:{transaction_id}", json.dumps(transaction_data))

        # Store photo if available
        if pos_system.photo_base64:
            redis_client.set(f"photo:{transaction_id}", pos_system.photo_base64)

        # Add to transaction stream
        redis_client.xadd("transaction_stream", {
            "transaction_id": transaction_id,
            "store_id": store_id,
            "customer_id": customer_id,
            "amount": product["price"],
            "type": transaction_type,
            "has_photo": "true" if pos_system.photo_base64 else "false"
        })

        # Clear captured photo
        pos_system.photo_base64 = None
        pos_system.captured_photo = None

        return jsonify({
            "success": True,
            "message": "Transaction processed successfully",
            "transaction_id": transaction_id,
            "details": {
                "customer": customer_id,
                "product": product["name"],
                "amount": product["price"],
                "photo_verified": bool(pos_system.photo_base64)
            }
        })

    except Exception as e:
        return jsonify({"success": False, "message": f"Transaction failed: {e}"})

@app.route('/api/simulate_fraud', methods=['POST'])
def simulate_fraud():
    """Simulate a fraudulent transaction"""
    try:
        # Create fraudulent transaction (return without photo)
        transaction_id = f"TXN_FRAUD_{uuid.uuid4().hex[:8].upper()}"

        # Use high-value product
        fraud_product_sku = "LAPTOP_001"  # Gaming Laptop
        product = pos_system.products[fraud_product_sku]

        transaction_data = {
            "transaction_id": transaction_id,
            "store_id": "STORE_B",
            "customer_id": "FRAUDSTER_001",
            "product_sku": fraud_product_sku,
            "product_name": product["name"],
            "price": product["price"],
            "transaction_type": "RETURN",
            "timestamp": datetime.now().isoformat(),
            "has_photo": False,
            "is_fraudulent": True,
            "fraud_indicators": ["no_photo", "high_value_return", "suspicious_customer"]
        }

        # Store in Redis Store B
        pos_system.redis_store_b.set(f"transaction:{transaction_id}", json.dumps(transaction_data))

        # Add fraud alert
        fraud_alert = {
            "alert_id": f"FRAUD_{uuid.uuid4().hex[:8].upper()}",
            "transaction_id": transaction_id,
            "fraud_score": 85,
            "risk_level": "HIGH",
            "indicators": ["Missing photo verification", "High-value return", "Known fraudster"],
            "timestamp": datetime.now().isoformat(),
            "action_taken": "TRANSACTION_BLOCKED"
        }

        pos_system.redis_store_b.set(f"fraud_alert:{transaction_id}", json.dumps(fraud_alert))

        # Add to transaction stream
        pos_system.redis_store_b.xadd("transaction_stream", {
            "transaction_id": transaction_id,
            "store_id": "STORE_B",
            "customer_id": "FRAUDSTER_001",
            "amount": product["price"],
            "type": "RETURN",
            "has_photo": "false",
            "fraud_detected": "true"
        })

        return jsonify({
            "success": True,
            "message": "Fraud simulation completed",
            "fraud_details": {
                "transaction_id": transaction_id,
                "fraud_score": 85,
                "risk_level": "HIGH",
                "action": "TRANSACTION_BLOCKED"
            }
        })

    except Exception as e:
        return jsonify({"success": False, "message": f"Fraud simulation failed: {e}"})

if __name__ == "__main__":
    print("🚀 Starting Unified Web POS System...")
    print("📱 Access at: http://localhost:5001")
    print("📷 Real camera capture enabled")
    print("🚨 Fraud detection active")
    app.run(host='0.0.0.0', port=5001, debug=True, threaded=True)
