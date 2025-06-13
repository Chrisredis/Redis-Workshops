#!/usr/bin/env python3
"""
Redis Cloud Configuration for All Workshops
Centralized configuration for Redis Cloud connection across all Redis workshops
"""

import os
import redis

# Redis Cloud Configuration
# Your persistent Redis Cloud instance for all workshops
REDIS_CLOUD_CONFIG = {
    'host': 'redis-15306.c329.us-east4-1.gce.redns.redis-cloud.com',
    'port': 15306,
    'username': 'default',
    'password': 'ftswOcgMB8dLCnjbKMMDBg3DNnpi1KO5',
    'decode_responses': True,
    'socket_timeout': 5,
    'socket_connect_timeout': 5,
    'retry_on_timeout': True,
    'health_check_interval': 30
}

# Environment variable overrides (for flexibility)
REDIS_HOST = os.getenv("REDIS_HOST", REDIS_CLOUD_CONFIG['host'])
REDIS_PORT = int(os.getenv("REDIS_PORT", REDIS_CLOUD_CONFIG['port']))
REDIS_USERNAME = os.getenv("REDIS_USERNAME", REDIS_CLOUD_CONFIG['username'])
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", REDIS_CLOUD_CONFIG['password'])

# Redis URL for libraries that need it
REDIS_URL = f"redis://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}"

# Redis CLI connection string
REDIS_CONN = f"-h {REDIS_HOST} -p {REDIS_PORT} -a {REDIS_PASSWORD} --no-auth-warning"

def get_redis_client(**kwargs):
    """
    Get a Redis client with the cloud configuration
    
    Args:
        **kwargs: Additional Redis client parameters to override defaults
    
    Returns:
        redis.Redis: Configured Redis client
    """
    config = REDIS_CLOUD_CONFIG.copy()
    config.update(kwargs)
    
    return redis.Redis(**config)

def test_redis_connection():
    """Test Redis Cloud connection"""
    try:
        client = get_redis_client()
        client.ping()
        print("✅ Redis Cloud connection successful!")
        
        # Get server info
        info = client.info()
        print(f"   Redis version: {info.get('redis_version', 'Unknown')}")
        print(f"   Used memory: {info.get('used_memory_human', 'Unknown')}")
        
        # Check for Redis modules
        try:
            modules = client.module_list()
            if modules:
                print("   Available modules:")
                for module in modules:
                    print(f"     - {module[1]} v{module[3]}")
            else:
                print("   No additional modules loaded")
        except:
            print("   Module info not available")
        
        return True
        
    except Exception as e:
        print(f"❌ Redis Cloud connection failed: {e}")
        return False

def get_workshop_namespace(workshop_name):
    """
    Get a namespaced key prefix for workshop data
    
    Args:
        workshop_name (str): Name of the workshop (e.g., 'fraud_detection', 'vector_search')
    
    Returns:
        str: Namespaced prefix for Redis keys
    """
    return f"workshop:{workshop_name}"

def clear_workshop_data(workshop_name):
    """
    Clear all data for a specific workshop
    
    Args:
        workshop_name (str): Name of the workshop to clear
    
    Returns:
        int: Number of keys deleted
    """
    client = get_redis_client()
    namespace = get_workshop_namespace(workshop_name)
    
    # Find all keys with this namespace
    keys = client.keys(f"{namespace}:*")
    
    if keys:
        deleted = client.delete(*keys)
        print(f"🗑️  Cleared {deleted} keys for workshop '{workshop_name}'")
        return deleted
    else:
        print(f"ℹ️  No data found for workshop '{workshop_name}'")
        return 0

def list_workshop_data():
    """List all workshop data in Redis"""
    client = get_redis_client()
    
    # Get all workshop keys
    workshop_keys = client.keys("workshop:*")
    
    if not workshop_keys:
        print("ℹ️  No workshop data found in Redis")
        return {}
    
    # Group by workshop
    workshops = {}
    for key in workshop_keys:
        parts = key.split(":", 2)
        if len(parts) >= 2:
            workshop_name = parts[1]
            if workshop_name not in workshops:
                workshops[workshop_name] = []
            workshops[workshop_name].append(key)
    
    print("📊 Workshop data in Redis:")
    for workshop, keys in workshops.items():
        print(f"   {workshop}: {len(keys)} keys")
        
    return workshops

# Configuration for specific workshops
WORKSHOP_CONFIGS = {
    'fraud_detection': {
        'namespace': 'workshop:fraud_detection',
        'indexes': ['idx:transactions', 'idx:users', 'idx:merchants'],
        'streams': ['fraud_events', 'replication_events']
    },
    'vector_search': {
        'namespace': 'workshop:vector_search',
        'indexes': ['idx:tweets', 'idx:embeddings'],
        'data_prefix': 'tweet'
    },
    'langchain_redis': {
        'namespace': 'workshop:langchain',
        'indexes': ['idx:documents', 'idx:cache'],
        'cache_prefix': 'llm_cache'
    },
    'redisjson_search': {
        'namespace': 'workshop:redisjson',
        'indexes': ['idx:json_docs'],
        'data_prefix': 'doc'
    }
}

def get_workshop_config(workshop_name):
    """Get configuration for a specific workshop"""
    return WORKSHOP_CONFIGS.get(workshop_name, {
        'namespace': f'workshop:{workshop_name}',
        'indexes': [],
        'data_prefix': 'data'
    })

def main():
    """Test the Redis Cloud configuration"""
    print("🚀 Testing Redis Cloud Configuration")
    print("=" * 50)
    
    # Test connection
    if test_redis_connection():
        print("\n📊 Current workshop data:")
        list_workshop_data()
        
        print(f"\n🔗 Connection details:")
        print(f"   Host: {REDIS_HOST}")
        print(f"   Port: {REDIS_PORT}")
        print(f"   URL: {REDIS_URL}")
        
        print(f"\n📁 Available workshop configs:")
        for workshop in WORKSHOP_CONFIGS.keys():
            print(f"   - {workshop}")
    
    print("\n✅ Redis Cloud configuration ready!")
    print("Import this module in your notebooks and Python files:")
    print("from redis_cloud_config import get_redis_client, REDIS_URL, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD")

if __name__ == "__main__":
    main()
