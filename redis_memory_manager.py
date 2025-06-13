#!/usr/bin/env python3
"""
Redis Memory Manager for Redis Workshops
Stores and retrieves project context, progress, and memories across conversation threads
"""

import redis
import json
import datetime
from typing import Dict, List, Any, Optional

class RedisMemoryManager:
    def __init__(self):
        """Initialize connection to Redis Cloud instance"""
        self.redis_client = redis.Redis(
            host='redis-15306.c329.us-east4-1.gce.redns.redis-cloud.com',
            port=15306,
            username='default',
            password='ftswOcgMB8dLCnjbKMMDBg3DNnpi1KO5',
            decode_responses=True
        )
        self.base_key = "workshops:memory"
        
    def test_connection(self) -> bool:
        """Test Redis connection"""
        try:
            self.redis_client.ping()
            print("✅ Redis Cloud connection successful!")
            return True
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            return False
    
    def store_project_memory(self, project_name: str, memory_type: str, data: Dict[str, Any]) -> bool:
        """
        Store project memory in Redis
        
        Args:
            project_name: Name of project (e.g., 'fraud_detection', 'vector_search')
            memory_type: Type of memory (e.g., 'status', 'config', 'progress', 'notes')
            data: Dictionary of data to store
        """
        try:
            key = f"{self.base_key}:{project_name}:{memory_type}"
            
            # Add timestamp
            data['_timestamp'] = datetime.datetime.now().isoformat()
            data['_project'] = project_name
            data['_type'] = memory_type
            
            # Store as JSON
            self.redis_client.set(key, json.dumps(data, indent=2))
            
            # Add to project index
            index_key = f"{self.base_key}:{project_name}:_index"
            self.redis_client.sadd(index_key, memory_type)
            
            print(f"✅ Stored {memory_type} memory for {project_name}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to store memory: {e}")
            return False
    
    def get_project_memory(self, project_name: str, memory_type: str) -> Optional[Dict[str, Any]]:
        """Retrieve specific project memory"""
        try:
            key = f"{self.base_key}:{project_name}:{memory_type}"
            data = self.redis_client.get(key)
            
            if data:
                return json.loads(data)
            return None
            
        except Exception as e:
            print(f"❌ Failed to retrieve memory: {e}")
            return None
    
    def get_all_project_memories(self, project_name: str) -> Dict[str, Any]:
        """Get all memories for a project"""
        try:
            index_key = f"{self.base_key}:{project_name}:_index"
            memory_types = self.redis_client.smembers(index_key)
            
            memories = {}
            for memory_type in memory_types:
                memory_data = self.get_project_memory(project_name, memory_type)
                if memory_data:
                    memories[memory_type] = memory_data
            
            return memories
            
        except Exception as e:
            print(f"❌ Failed to retrieve all memories: {e}")
            return {}
    
    def list_projects(self) -> List[str]:
        """List all projects with stored memories"""
        try:
            pattern = f"{self.base_key}:*:_index"
            keys = self.redis_client.keys(pattern)
            
            projects = []
            for key in keys:
                # Extract project name from key
                parts = key.split(':')
                if len(parts) >= 3:
                    project_name = parts[2]
                    projects.append(project_name)
            
            return sorted(list(set(projects)))
            
        except Exception as e:
            print(f"❌ Failed to list projects: {e}")
            return []
    
    def store_fraud_detection_status(self):
        """Store current fraud detection project status"""
        fraud_status = {
            "redis_cloud_config": {
                "host": "redis-15306.c329.us-east4-1.gce.redns.redis-cloud.com",
                "port": 15306,
                "username": "default",
                "status": "using_redis_cloud_for_data_persistence"
            },
            "redis_containers": {
                "store_a": "redis-store-a:6379",
                "store_b": "redis-store-b:6380",
                "status": "running_for_active_active_demo",
                "note": "Local containers for Active-Active replication demo, data stored in Redis Cloud"
            },
            "components": {
                "fraud_dashboard": "fraud_dashboard.py",
                "visual_pos": "visual_pos.py", 
                "comprehensive_demo": "comprehensive_demo.py",
                "face_detection": "face_detection_pos.py"
            },
            "features": [
                "Real-time photo verification with face detection",
                "Cross-store fraud detection and prevention", 
                "Sub-10ms replication between Redis instances",
                "Live web dashboard with real-time updates",
                "Visual confirmation of photo attachment",
                "Automated fraud blocking with AI scoring"
            ],
            "performance": {
                "legitimate_transactions": 14,
                "fraud_attempts": 9,
                "fraud_detected": 4,
                "fraud_prevented": 4,
                "value_protected": 11299.91,
                "avg_replication_time_ms": 5.69,
                "fraud_detection_rate": 44.4
            },
            "next_steps": [
                "Add more sophisticated ML fraud detection models",
                "Implement customer facial recognition",
                "Add mobile app integration", 
                "Scale to multiple store locations",
                "Add fraud pattern analysis and reporting"
            ]
        }
        
        return self.store_project_memory("fraud_detection", "status", fraud_status)
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get Redis memory usage statistics"""
        try:
            info = self.redis_client.info('memory')
            
            used_memory_mb = info.get('used_memory', 0) / (1024 * 1024)
            max_memory_mb = 250  # Your current limit
            
            return {
                "used_memory_mb": round(used_memory_mb, 2),
                "max_memory_mb": max_memory_mb,
                "usage_percentage": round((used_memory_mb / max_memory_mb) * 100, 2),
                "available_mb": round(max_memory_mb - used_memory_mb, 2)
            }
            
        except Exception as e:
            print(f"❌ Failed to get memory usage: {e}")
            return {}

    def store_workshop_memories(self):
        """Store memories for various workshops"""

        # Vector Search Workshop
        vector_search = {
            "workshop_path": "02-Vector_Similarity_Search",
            "notebooks": ["02.01_RedisVL.ipynb", "02.02_Redis_py.ipynb"],
            "data_files": ["Labelled_Tweets.csv"],
            "topics": ["Vector embeddings", "Similarity search", "RedisVL", "Tweet analysis"],
            "status": "available",
            "description": "Vector similarity search using Redis with tweet data analysis"
        }
        self.store_project_memory("vector_search", "config", vector_search)

        # LangChain Workshop
        langchain = {
            "workshop_path": "05-LangChain_Redis",
            "notebooks": [
                "05.01_OpenAI_LangChain_Redis.ipynb",
                "05.02_Dolly_v2_LangChain_Redis.ipynb",
                "05.03_Google_Gemini_LangChain_Redis.ipynb",
                "05.10_LangChain_RedisSemanticCache.ipynb",
                "05.11_LangChain_RedisChatMemory.ipynb"
            ],
            "topics": ["LangChain integration", "Semantic caching", "Chat memory", "Multiple LLM providers"],
            "status": "available",
            "description": "LangChain integration with Redis for caching and memory"
        }
        self.store_project_memory("langchain_redis", "config", langchain)

        # RedisJSON Search
        redisjson = {
            "workshop_path": "01-RedisJSON_Search",
            "notebooks": ["01-RedisJSON_Search.ipynb"],
            "topics": ["JSON documents", "Search capabilities", "RedisJSON module"],
            "status": "available",
            "description": "JSON document storage and search with Redis"
        }
        self.store_project_memory("redisjson_search", "config", redisjson)

def main():
    """Test the Redis Memory Manager"""
    print("🚀 Testing Redis Memory Manager...")

    manager = RedisMemoryManager()

    # Test connection
    if not manager.test_connection():
        return

    # Store fraud detection status
    print("\n📊 Storing fraud detection project status...")
    manager.store_fraud_detection_status()

    # Store other workshop memories
    print("\n📚 Storing workshop memories...")
    manager.store_workshop_memories()

    # Store Redis Cloud migration status
    print("\n☁️ Storing Redis Cloud migration status...")
    migration_status = {
        "migration_completed": True,
        "notebooks_updated": 12,
        "workshops_migrated": [
            "01-RedisJSON_Search",
            "02-Vector_Similarity_Search",
            "03-Advanced_RedisSearch",
            "05-LangChain_Redis",
            "06-LlamaIndex_Redis"
        ],
        "benefits": [
            "Persistent data across sessions",
            "Shared data between workshops",
            "No local Redis setup required",
            "250MB storage capacity",
            "Consistent configuration across all projects"
        ],
        "redis_cloud_config": {
            "host": "redis-15306.c329.us-east4-1.gce.redns.redis-cloud.com",
            "port": 15306,
            "username": "default"
        }
    }
    manager.store_project_memory("redis_cloud_migration", "status", migration_status)

    # Test retrieval
    print("\n🔍 Testing memory retrieval...")
    fraud_memory = manager.get_project_memory("fraud_detection", "status")
    if fraud_memory:
        print(f"✅ Retrieved fraud detection status (last updated: {fraud_memory.get('_timestamp')})")
        print(f"   - Legitimate transactions: {fraud_memory['performance']['legitimate_transactions']}")
        print(f"   - Value protected: ${fraud_memory['performance']['value_protected']}")

    # List projects
    print("\n📁 Projects with stored memories:")
    projects = manager.list_projects()
    for project in projects:
        print(f"   - {project}")

    # Memory usage
    print("\n💾 Redis memory usage:")
    usage = manager.get_memory_usage()
    if usage:
        print(f"   - Used: {usage['used_memory_mb']} MB")
        print(f"   - Available: {usage['available_mb']} MB")
        print(f"   - Usage: {usage['usage_percentage']}%")

    print("\n🎉 Redis Memory Manager is ready!")
    print("Now you can use 'Continue with the Redis fraud detection project' in new threads!")
    print("Or try: 'Continue with vector search', 'Continue with LangChain', etc.")

if __name__ == "__main__":
    main()
