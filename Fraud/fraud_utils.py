"""
Fraud Detection Utilities for Redis Workshop

This module provides utility functions for the fraud detection demo including
data generation, feature engineering, and visualization helpers.
"""

import redis
import json
import time
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RedisConnectionManager:
    """Manages Redis connections and provides helper methods"""
    
    def __init__(self, host='localhost', port=6379, db=0):
        self.host = host
        self.port = port
        self.db = db
        self.client = None
        
    def connect(self):
        """Establish Redis connection"""
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True
            )
            self.client.ping()
            logger.info("✅ Connected to Redis successfully")
            return True
        except redis.ConnectionError as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            return False
    
    def check_modules(self):
        """Check if required Redis modules are available"""
        if not self.client:
            return False
            
        try:
            modules = self.client.module_list()
            module_names = [module[1] for module in modules]
            
            required_modules = ['search', 'ReJSON', 'timeseries']
            missing_modules = []
            
            for module in required_modules:
                if module in module_names:
                    logger.info(f"✅ {module} module is available")
                else:
                    logger.warning(f"❌ {module} module is NOT available")
                    missing_modules.append(module)
            
            return len(missing_modules) == 0
            
        except Exception as e:
            logger.error(f"Error checking modules: {e}")
            return False
    
    def flush_fraud_data(self):
        """Clean up fraud detection data"""
        if not self.client:
            return False
            
        try:
            # Delete all fraud-related keys
            patterns = ['transaction:*', 'user:*', 'merchant:*', 'fraud_stream']
            
            for pattern in patterns:
                keys = self.client.keys(pattern)
                if keys:
                    self.client.delete(*keys)
                    logger.info(f"Deleted {len(keys)} keys matching {pattern}")
            
            # Drop indexes
            try:
                self.client.ft('idx:transactions').dropindex()
                self.client.ft('idx:users').dropindex()
                self.client.ft('idx:merchants').dropindex()
                logger.info("Dropped existing indexes")
            except:
                pass
                
            return True
            
        except Exception as e:
            logger.error(f"Error flushing data: {e}")
            return False


class FraudMetrics:
    """Calculate and track fraud detection metrics"""
    
    def __init__(self, redis_client):
        self.r = redis_client
        
    def calculate_confusion_matrix(self, predictions: List[Dict]) -> Dict:
        """Calculate confusion matrix from predictions"""
        tp = fp = tn = fn = 0
        
        for pred in predictions:
            actual = pred.get('actual_fraud', False)
            predicted = pred.get('predicted_fraud', False)
            
            if actual and predicted:
                tp += 1
            elif not actual and predicted:
                fp += 1
            elif not actual and not predicted:
                tn += 1
            else:
                fn += 1
        
        return {
            'true_positives': tp,
            'false_positives': fp,
            'true_negatives': tn,
            'false_negatives': fn,
            'total': len(predictions)
        }
    
    def calculate_metrics(self, confusion_matrix: Dict) -> Dict:
        """Calculate precision, recall, F1-score from confusion matrix"""
        tp = confusion_matrix['true_positives']
        fp = confusion_matrix['false_positives']
        tn = confusion_matrix['true_negatives']
        fn = confusion_matrix['false_negatives']
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        accuracy = (tp + tn) / (tp + fp + tn + fn) if (tp + fp + tn + fn) > 0 else 0
        
        return {
            'precision': round(precision, 3),
            'recall': round(recall, 3),
            'f1_score': round(f1_score, 3),
            'accuracy': round(accuracy, 3)
        }
    
    def get_fraud_statistics(self) -> Dict:
        """Get fraud detection statistics from Redis"""
        try:
            # Query all transactions
            result = self.r.ft('idx:transactions').search('*')
            
            total_transactions = result.total
            fraud_transactions = 0
            total_fraud_score = 0
            
            for doc in result.docs:
                transaction_data = self.r.json().get(f"transaction:{doc.transaction_id}")
                if transaction_data:
                    if transaction_data.get('is_fraud', False):
                        fraud_transactions += 1
                    total_fraud_score += transaction_data.get('fraud_score', 0)
            
            fraud_rate = (fraud_transactions / total_transactions * 100) if total_transactions > 0 else 0
            avg_fraud_score = (total_fraud_score / total_transactions) if total_transactions > 0 else 0
            
            return {
                'total_transactions': total_transactions,
                'fraud_transactions': fraud_transactions,
                'fraud_rate_percent': round(fraud_rate, 2),
                'average_fraud_score': round(avg_fraud_score, 3)
            }
            
        except Exception as e:
            logger.error(f"Error getting fraud statistics: {e}")
            return {}


class TransactionAnalyzer:
    """Analyze transaction patterns and generate insights"""
    
    def __init__(self, redis_client):
        self.r = redis_client
    
    def analyze_user_patterns(self, user_id: str) -> Dict:
        """Analyze spending patterns for a specific user"""
        try:
            # Get user profile
            user_data = self.r.json().get(f"user:{user_id}")
            if not user_data:
                return {"error": "User not found"}
            
            # Get user transactions
            query = f"@user_id:{user_id}"
            result = self.r.ft('idx:transactions').search(query)
            
            transactions = []
            for doc in result.docs:
                transaction_data = self.r.json().get(f"transaction:{doc.transaction_id}")
                if transaction_data:
                    transactions.append(transaction_data)
            
            if not transactions:
                return {"error": "No transactions found for user"}
            
            # Calculate patterns
            amounts = [t['amount'] for t in transactions]
            fraud_scores = [t['fraud_score'] for t in transactions]
            fraud_count = sum(1 for t in transactions if t['is_fraud'])
            
            return {
                'user_id': user_id,
                'transaction_count': len(transactions),
                'total_amount': round(sum(amounts), 2),
                'average_amount': round(np.mean(amounts), 2),
                'median_amount': round(np.median(amounts), 2),
                'max_amount': round(max(amounts), 2),
                'fraud_count': fraud_count,
                'fraud_rate': round((fraud_count / len(transactions)) * 100, 2),
                'average_fraud_score': round(np.mean(fraud_scores), 3),
                'max_fraud_score': round(max(fraud_scores), 3)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing user patterns: {e}")
            return {"error": str(e)}
    
    def analyze_merchant_patterns(self, merchant_id: str) -> Dict:
        """Analyze transaction patterns for a specific merchant"""
        try:
            # Get merchant data
            merchant_data = self.r.json().get(f"merchant:{merchant_id}")
            if not merchant_data:
                return {"error": "Merchant not found"}
            
            # Get merchant transactions
            query = f"@merchant_id:{merchant_id}"
            result = self.r.ft('idx:transactions').search(query)
            
            transactions = []
            for doc in result.docs:
                transaction_data = self.r.json().get(f"transaction:{doc.transaction_id}")
                if transaction_data:
                    transactions.append(transaction_data)
            
            if not transactions:
                return {"error": "No transactions found for merchant"}
            
            # Calculate patterns
            amounts = [t['amount'] for t in transactions]
            fraud_scores = [t['fraud_score'] for t in transactions]
            fraud_count = sum(1 for t in transactions if t['is_fraud'])
            unique_users = len(set(t['user_id'] for t in transactions))
            
            return {
                'merchant_id': merchant_id,
                'merchant_name': merchant_data['name'],
                'category': merchant_data['category'],
                'risk_level': merchant_data['risk_level'],
                'transaction_count': len(transactions),
                'unique_customers': unique_users,
                'total_volume': round(sum(amounts), 2),
                'average_transaction': round(np.mean(amounts), 2),
                'fraud_count': fraud_count,
                'fraud_rate': round((fraud_count / len(transactions)) * 100, 2),
                'average_fraud_score': round(np.mean(fraud_scores), 3)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing merchant patterns: {e}")
            return {"error": str(e)}
    
    def get_high_risk_transactions(self, threshold: float = 0.7, limit: int = 10) -> List[Dict]:
        """Get transactions with fraud scores above threshold"""
        try:
            query = f"@fraud_score:[{threshold} +inf]"
            result = self.r.ft('idx:transactions').search(
                redis.commands.search.Query(query)
                .sort_by('fraud_score', asc=False)
                .paging(0, limit)
            )
            
            high_risk_transactions = []
            for doc in result.docs:
                transaction_data = self.r.json().get(f"transaction:{doc.transaction_id}")
                if transaction_data:
                    high_risk_transactions.append({
                        'transaction_id': transaction_data['transaction_id'],
                        'user_id': transaction_data['user_id'],
                        'merchant_id': transaction_data['merchant_id'],
                        'amount': transaction_data['amount'],
                        'fraud_score': transaction_data['fraud_score'],
                        'is_fraud': transaction_data['is_fraud'],
                        'timestamp': transaction_data['timestamp'],
                        'reasons': transaction_data.get('fraud_reasons', [])
                    })
            
            return high_risk_transactions
            
        except Exception as e:
            logger.error(f"Error getting high-risk transactions: {e}")
            return []


def format_currency(amount: float, currency: str = 'USD') -> str:
    """Format amount as currency"""
    return f"${amount:,.2f}" if currency == 'USD' else f"{amount:,.2f} {currency}"


def format_timestamp(timestamp: int) -> str:
    """Format Unix timestamp as readable string"""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points using Haversine formula"""
    import math
    
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * 
         math.sin(delta_lon / 2) ** 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c
