"""
Configuration settings for the Fraud Detection Demo

This module contains all configuration parameters for the fraud detection system
including Redis settings, fraud detection thresholds, and feature parameters.
"""

import os
from typing import Dict, List

# Redis Cloud Configuration (Default)
# Using Redis Cloud for persistent fraud detection data
REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'redis-15306.c329.us-east4-1.gce.redns.redis-cloud.com'),
    'port': int(os.getenv('REDIS_PORT', 15306)),
    'username': os.getenv('REDIS_USERNAME', 'default'),
    'password': os.getenv('REDIS_PASSWORD', 'ftswOcgMB8dLCnjbKMMDBg3DNnpi1KO5'),
    'db': int(os.getenv('REDIS_DB', 0)),
    'decode_responses': True,
    'socket_timeout': 5,
    'socket_connect_timeout': 5,
    'retry_on_timeout': True,
    'health_check_interval': 30
}

# Local Redis Configuration (uncomment if needed)
# REDIS_CONFIG = {
#     'host': 'localhost',
#     'port': 6379,
#     'db': 0,
#     'password': None,
#     'socket_timeout': 5,
#     'socket_connect_timeout': 5,
#     'retry_on_timeout': True,
#     'health_check_interval': 30
# }

# Index Names
INDEX_NAMES = {
    'transactions': 'idx:transactions',
    'users': 'idx:users',
    'merchants': 'idx:merchants'
}

# Key Prefixes
KEY_PREFIXES = {
    'transaction': 'transaction:',
    'user': 'user:',
    'merchant': 'merchant:',
    'fraud_stream': 'fraud_stream',
    'alerts': 'alerts:',
    'metrics': 'metrics:'
}

# Fraud Detection Thresholds
FRAUD_THRESHOLDS = {
    'fraud_score_threshold': 0.7,  # Threshold for marking transaction as fraud
    'high_risk_threshold': 0.5,    # Threshold for high-risk transactions
    'velocity_1h_limit': 5,        # Max transactions per hour
    'velocity_24h_limit': 20,      # Max transactions per 24 hours
    'amount_multiplier_high': 5,   # Amount multiplier for high risk
    'amount_multiplier_medium': 3, # Amount multiplier for medium risk
    'distance_threshold_high': 1000, # Distance in km for high risk
    'distance_threshold_medium': 500, # Distance in km for medium risk
    'quick_transaction_seconds': 60,  # Seconds for quick successive transactions
    'amount_percentile_threshold': 95 # Percentile threshold for amount-based rules
}

# Feature Engineering Parameters
FEATURE_CONFIG = {
    'vector_dimensions': 10,
    'time_windows': {
        'velocity_1h': 3600,    # 1 hour in seconds
        'velocity_24h': 86400,  # 24 hours in seconds
        'velocity_7d': 604800   # 7 days in seconds
    },
    'normalization_factors': {
        'velocity_1h_max': 10,
        'velocity_24h_max': 50,
        'amount_max': 1000,
        'distance_max': 1000,
        'time_max': 86400
    }
}

# Merchant Categories and Risk Levels
MERCHANT_CATEGORIES = [
    'grocery',
    'gas',
    'restaurant',
    'retail',
    'online',
    'atm',
    'pharmacy',
    'entertainment',
    'travel',
    'utilities',
    'insurance',
    'healthcare'
]

MERCHANT_RISK_LEVELS = {
    'low': {
        'categories': ['grocery', 'pharmacy', 'utilities'],
        'risk_multiplier': 0.1
    },
    'medium': {
        'categories': ['restaurant', 'retail', 'gas', 'entertainment'],
        'risk_multiplier': 0.2
    },
    'high': {
        'categories': ['online', 'atm', 'travel'],
        'risk_multiplier': 0.3
    }
}

# Payment Methods
PAYMENT_METHODS = [
    'credit_card',
    'debit_card',
    'bank_transfer',
    'digital_wallet',
    'cryptocurrency',
    'cash'
]

# Geographic Regions for Data Generation
GEOGRAPHIC_REGIONS = {
    'north_america': {
        'countries': ['United States', 'Canada', 'Mexico'],
        'lat_range': (25.0, 60.0),
        'lon_range': (-140.0, -60.0)
    },
    'europe': {
        'countries': ['United Kingdom', 'Germany', 'France', 'Spain', 'Italy'],
        'lat_range': (35.0, 70.0),
        'lon_range': (-10.0, 30.0)
    },
    'asia': {
        'countries': ['Japan', 'China', 'India', 'Singapore', 'South Korea'],
        'lat_range': (10.0, 50.0),
        'lon_range': (70.0, 150.0)
    }
}

# Fraud Patterns for Synthetic Data Generation
FRAUD_PATTERNS = {
    'velocity_fraud': {
        'description': 'Multiple transactions in short time',
        'probability': 0.15,
        'characteristics': {
            'transactions_per_hour': (6, 15),
            'amount_range': (50, 500),
            'time_window': 3600
        }
    },
    'amount_fraud': {
        'description': 'Unusually high transaction amounts',
        'probability': 0.10,
        'characteristics': {
            'amount_multiplier': (5, 10),
            'single_transaction': True
        }
    },
    'location_fraud': {
        'description': 'Transactions far from home location',
        'probability': 0.12,
        'characteristics': {
            'min_distance_km': 1000,
            'different_country': True
        }
    },
    'time_fraud': {
        'description': 'Transactions at unusual hours',
        'probability': 0.08,
        'characteristics': {
            'unusual_hours': [0, 1, 2, 3, 4, 5],
            'outside_pattern': True
        }
    },
    'merchant_fraud': {
        'description': 'Transactions at high-risk merchants',
        'probability': 0.10,
        'characteristics': {
            'high_risk_merchants': True,
            'amount_range': (100, 1000)
        }
    }
}

# Machine Learning Model Configuration
ML_CONFIG = {
    'isolation_forest': {
        'contamination': 0.1,
        'n_estimators': 100,
        'random_state': 42
    },
    'feature_scaling': {
        'method': 'standard',  # 'standard', 'minmax', 'robust'
        'feature_range': (0, 1)
    },
    'model_update_frequency': 3600,  # Update model every hour
    'training_data_size': 10000,     # Number of transactions for training
    'validation_split': 0.2
}

# Alert Configuration
ALERT_CONFIG = {
    'channels': {
        'email': {
            'enabled': False,
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'sender_email': '',
            'sender_password': ''
        },
        'slack': {
            'enabled': False,
            'webhook_url': '',
            'channel': '#fraud-alerts'
        },
        'redis_stream': {
            'enabled': True,
            'stream_name': 'fraud_alerts'
        }
    },
    'alert_levels': {
        'low': {
            'threshold': 0.3,
            'color': 'yellow',
            'priority': 1
        },
        'medium': {
            'threshold': 0.5,
            'color': 'orange',
            'priority': 2
        },
        'high': {
            'threshold': 0.7,
            'color': 'red',
            'priority': 3
        },
        'critical': {
            'threshold': 0.9,
            'color': 'darkred',
            'priority': 4
        }
    }
}

# Performance Monitoring
PERFORMANCE_CONFIG = {
    'metrics_retention_days': 30,
    'performance_targets': {
        'processing_time_ms': 10,      # Target processing time
        'throughput_tps': 1000,        # Target transactions per second
        'accuracy_threshold': 0.95,    # Minimum accuracy
        'false_positive_rate': 0.05    # Maximum false positive rate
    },
    'monitoring_intervals': {
        'real_time': 1,      # 1 second
        'short_term': 60,    # 1 minute
        'medium_term': 3600, # 1 hour
        'long_term': 86400   # 1 day
    }
}

# Data Generation Configuration
DATA_GENERATION = {
    'users': {
        'count': 1000,
        'account_age_range_days': (30, 730),
        'spending_patterns': {
            'avg_amount_range': (20, 500),
            'monthly_spend_range': (500, 5000),
            'preferred_merchants_count': 3,
            'typical_hours_count': (3, 8)
        }
    },
    'merchants': {
        'count': 100,
        'category_distribution': {
            'grocery': 0.15,
            'restaurant': 0.20,
            'retail': 0.25,
            'online': 0.15,
            'gas': 0.10,
            'other': 0.15
        }
    },
    'transactions': {
        'normal_amount_range': (10, 200),
        'suspicious_amount_range': (1000, 5000),
        'suspicious_probability': 0.2,
        'fraud_probability': 0.15
    }
}

# Logging Configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'handlers': {
        'console': True,
        'file': {
            'enabled': True,
            'filename': 'fraud_detection.log',
            'max_bytes': 10485760,  # 10MB
            'backup_count': 5
        }
    }
}

# API Configuration (if building REST API)
API_CONFIG = {
    'host': '0.0.0.0',
    'port': 8000,
    'debug': False,
    'rate_limiting': {
        'enabled': True,
        'requests_per_minute': 100
    },
    'authentication': {
        'enabled': False,
        'api_key_header': 'X-API-Key'
    }
}

def get_config(section: str = None) -> Dict:
    """Get configuration for a specific section or all config"""
    config_map = {
        'redis': REDIS_CONFIG,
        'fraud': FRAUD_THRESHOLDS,
        'features': FEATURE_CONFIG,
        'ml': ML_CONFIG,
        'alerts': ALERT_CONFIG,
        'performance': PERFORMANCE_CONFIG,
        'data': DATA_GENERATION,
        'logging': LOGGING_CONFIG,
        'api': API_CONFIG
    }
    
    if section:
        return config_map.get(section, {})
    
    return {
        'redis': REDIS_CONFIG,
        'fraud_thresholds': FRAUD_THRESHOLDS,
        'feature_config': FEATURE_CONFIG,
        'ml_config': ML_CONFIG,
        'alert_config': ALERT_CONFIG,
        'performance_config': PERFORMANCE_CONFIG,
        'data_generation': DATA_GENERATION,
        'logging_config': LOGGING_CONFIG,
        'api_config': API_CONFIG,
        'index_names': INDEX_NAMES,
        'key_prefixes': KEY_PREFIXES,
        'merchant_categories': MERCHANT_CATEGORIES,
        'payment_methods': PAYMENT_METHODS,
        'fraud_patterns': FRAUD_PATTERNS
    }
