#!/usr/bin/env python3
"""
Quick test of transaction processing
"""

import requests
import json

def test_transaction():
    """Test transaction processing"""
    
    # Test data
    transaction_data = {
        "customer_id": "TEST_001",
        "product_sku": "LAPTOP_001",
        "store_id": "STORE_A",
        "transaction_type": "PURCHASE"
    }
    
    try:
        # Test transaction processing
        response = requests.post(
            'http://localhost:5001/api/process_transaction',
            headers={'Content-Type': 'application/json'},
            json=transaction_data
        )
        
        print("Response status:", response.status_code)
        print("Response data:", response.json())
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_transaction()
