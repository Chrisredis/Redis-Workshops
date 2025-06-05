#!/usr/bin/env python3
"""
Real-time Fraud Detection Dashboard

This web dashboard provides:
1. Side-by-side view of legitimate vs fraudulent transactions
2. Real-time monitoring of both Redis instances
3. Visual fraud detection alerts
4. Photo verification comparison
5. Transaction timeline and analytics
"""

import redis
import json
import time
import base64
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fraud_detection_demo_2024'
socketio = SocketIO(app, cors_allowed_origins="*")

class FraudDashboard:
    def __init__(self):
        """Initialize fraud detection dashboard"""
        # Connect to both Redis instances
        self.redis_store_a = self.connect_redis("localhost", 6379, "Store A")
        self.redis_store_b = self.connect_redis("localhost", 6380, "Store B")
        
        self.monitoring = False
        self.monitor_thread = None
        
    def connect_redis(self, host: str, port: int, store_name: str):
        """Connect to Redis instance"""
        try:
            client = redis.Redis(host=host, port=port, db=0, decode_responses=False)
            client.ping()
            logger.info(f"✅ Connected to {store_name} Redis at {host}:{port}")
            return client
        except redis.ConnectionError:
            logger.error(f"❌ Failed to connect to {store_name} Redis at {host}:{port}")
            return None
    
    def get_transaction_data(self, redis_client, transaction_id: str):
        """Get complete transaction data including photo"""
        try:
            # Get transaction details
            transaction_key = f"transaction:{transaction_id}"
            transaction_data = redis_client.get(transaction_key)
            
            if not transaction_data:
                return None
            
            transaction = json.loads(transaction_data)
            
            # Get photo if available
            photo_key = f"photo:{transaction_id}"
            photo_data = redis_client.get(photo_key)
            
            if photo_data:
                transaction['photo_base64'] = photo_data.decode('utf-8')
            
            return transaction
            
        except Exception as e:
            logger.error(f"Error getting transaction data: {e}")
            return None
    
    def get_recent_transactions(self, redis_client, limit: int = 20):
        """Get recent transactions from Redis stream"""
        try:
            if not redis_client:
                return []
                
            stream_data = redis_client.xrevrange("transaction_stream", count=limit)
            
            transactions = []
            for stream_id, fields in stream_data:
                transaction = {
                    "stream_id": stream_id.decode(),
                    "transaction_id": fields[b'transaction_id'].decode(),
                    "store_id": fields[b'store_id'].decode(),
                    "customer_id": fields[b'customer_id'].decode(),
                    "type": fields[b'type'].decode(),
                    "amount": fields[b'amount'].decode(),
                    "has_photo": fields[b'has_photo'].decode() == "true",
                    "timestamp": int(fields[b'timestamp'].decode()),
                    "verification": fields.get(b'verification', b'').decode(),
                    "fraud_attempt": fields.get(b'fraud_attempt', b'false').decode() == "true"
                }
                
                # Get full transaction details
                full_data = self.get_transaction_data(redis_client, transaction["transaction_id"])
                if full_data:
                    transaction.update(full_data)
                
                transactions.append(transaction)
            
            return transactions
            
        except Exception as e:
            logger.error(f"Error getting recent transactions: {e}")
            return []
    
    def get_fraud_alerts(self, redis_client):
        """Get recent fraud alerts"""
        try:
            if not redis_client:
                return []
                
            alerts_data = redis_client.xrevrange("fraud_alerts", count=10)
            
            alerts = []
            for stream_id, fields in alerts_data:
                alert = {
                    "alert_id": fields[b'alert_id'].decode(),
                    "fraud_transaction_id": fields[b'fraud_transaction_id'].decode(),
                    "original_transaction_id": fields[b'original_transaction_id'].decode(),
                    "fraud_type": fields[b'fraud_type'].decode(),
                    "risk_level": fields[b'risk_level'].decode(),
                    "timestamp": int(fields[b'timestamp'].decode()),
                    "store_id": fields[b'store_id'].decode(),
                    "indicators": json.loads(fields[b'indicators'].decode())
                }
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting fraud alerts: {e}")
            return []
    
    def detect_simultaneous_returns(self):
        """Detect simultaneous return attempts on the same original transaction"""
        try:
            # Get recent returns from both stores
            store_a_transactions = self.get_recent_transactions(self.redis_store_a, 50)
            store_b_transactions = self.get_recent_transactions(self.redis_store_b, 50)
            
            # Filter for returns only
            store_a_returns = [t for t in store_a_transactions if t.get('type') == 'RETURN']
            store_b_returns = [t for t in store_b_transactions if t.get('type') == 'RETURN']
            
            simultaneous_attempts = []
            
            # Check for returns on the same original transaction
            for a_return in store_a_returns:
                original_id_a = a_return.get('original_transaction_id')
                if not original_id_a:
                    continue
                    
                for b_return in store_b_returns:
                    original_id_b = b_return.get('original_transaction_id')
                    
                    if (original_id_a == original_id_b and 
                        abs(a_return['timestamp'] - b_return['timestamp']) < 300):  # Within 5 minutes
                        
                        fraud_detected = {
                            "original_transaction_id": original_id_a,
                            "legitimate_return": a_return,
                            "fraudulent_return": b_return,
                            "time_difference": abs(a_return['timestamp'] - b_return['timestamp']),
                            "fraud_indicators": {
                                "simultaneous_attempts": True,
                                "photo_verification_mismatch": a_return.get('has_photo', False) != b_return.get('has_photo', False),
                                "different_stores": a_return['store_id'] != b_return['store_id'],
                                "no_photo_verification": not b_return.get('has_photo', False)
                            }
                        }
                        simultaneous_attempts.append(fraud_detected)
            
            return simultaneous_attempts
            
        except Exception as e:
            logger.error(f"Error detecting simultaneous returns: {e}")
            return []
    
    def start_monitoring(self):
        """Start real-time monitoring thread"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_transactions)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            logger.info("🔍 Started real-time fraud monitoring")
    
    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        logger.info("⏹️ Stopped fraud monitoring")
    
    def _monitor_transactions(self):
        """Monitor transactions in real-time and emit updates"""
        last_check = time.time()
        
        while self.monitoring:
            try:
                current_time = time.time()
                
                # Get recent transactions from both stores
                store_a_data = self.get_recent_transactions(self.redis_store_a, 10)
                store_b_data = self.get_recent_transactions(self.redis_store_b, 10)
                
                # Get fraud alerts
                fraud_alerts = self.get_fraud_alerts(self.redis_store_b)
                
                # Detect simultaneous returns
                simultaneous_attempts = self.detect_simultaneous_returns()
                
                # Emit updates to connected clients
                socketio.emit('transaction_update', {
                    'store_a_transactions': store_a_data,
                    'store_b_transactions': store_b_data,
                    'fraud_alerts': fraud_alerts,
                    'simultaneous_attempts': simultaneous_attempts,
                    'timestamp': current_time
                })
                
                last_check = current_time
                time.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)

# Initialize dashboard
dashboard = FraudDashboard()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/transactions')
def get_transactions():
    """API endpoint to get current transaction data"""
    store_a_data = dashboard.get_recent_transactions(dashboard.redis_store_a, 20)
    store_b_data = dashboard.get_recent_transactions(dashboard.redis_store_b, 20)
    fraud_alerts = dashboard.get_fraud_alerts(dashboard.redis_store_b)
    simultaneous_attempts = dashboard.detect_simultaneous_returns()
    
    return jsonify({
        'store_a_transactions': store_a_data,
        'store_b_transactions': store_b_data,
        'fraud_alerts': fraud_alerts,
        'simultaneous_attempts': simultaneous_attempts,
        'timestamp': time.time()
    })

@app.route('/api/transaction/<transaction_id>')
def get_transaction_details(transaction_id):
    """Get detailed transaction information"""
    # Try both Redis instances
    transaction_data = (dashboard.get_transaction_data(dashboard.redis_store_a, transaction_id) or
                       dashboard.get_transaction_data(dashboard.redis_store_b, transaction_id))
    
    if transaction_data:
        return jsonify(transaction_data)
    else:
        return jsonify({"error": "Transaction not found"}), 404

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info("Client connected to fraud dashboard")
    dashboard.start_monitoring()
    emit('status', {'message': 'Connected to fraud detection dashboard'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info("Client disconnected from fraud dashboard")

@socketio.on('request_update')
def handle_update_request():
    """Handle manual update request"""
    store_a_data = dashboard.get_recent_transactions(dashboard.redis_store_a, 20)
    store_b_data = dashboard.get_recent_transactions(dashboard.redis_store_b, 20)
    fraud_alerts = dashboard.get_fraud_alerts(dashboard.redis_store_b)
    simultaneous_attempts = dashboard.detect_simultaneous_returns()
    
    emit('transaction_update', {
        'store_a_transactions': store_a_data,
        'store_b_transactions': store_b_data,
        'fraud_alerts': fraud_alerts,
        'simultaneous_attempts': simultaneous_attempts,
        'timestamp': time.time()
    })

if __name__ == '__main__':
    try:
        print("\n🖥️ Starting Fraud Detection Dashboard")
        print("=" * 50)
        print("📊 Dashboard URL: http://localhost:8080")
        print("🔍 Real-time monitoring: Active")
        print("⚠️ Fraud detection: Enabled")
        print("\nPress Ctrl+C to stop the dashboard")
        
        socketio.run(app, host='0.0.0.0', port=8080, debug=False)
        
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down fraud dashboard...")
        dashboard.stop_monitoring()
    except Exception as e:
        logger.error(f"Error starting dashboard: {e}")
        dashboard.stop_monitoring()
