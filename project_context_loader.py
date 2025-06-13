#!/usr/bin/env python3
"""
Project Context Loader
Quickly loads project context from Redis memory for seamless thread continuity
"""

from redis_memory_manager import RedisMemoryManager
import json

def load_fraud_detection_context():
    """Load fraud detection project context from Redis"""
    manager = RedisMemoryManager()
    
    print("🔄 Loading fraud detection project context from Redis...")
    
    # Test connection
    if not manager.test_connection():
        print("❌ Cannot connect to Redis Cloud - using local context only")
        return None
    
    # Get fraud detection memories
    fraud_context = manager.get_all_project_memories("fraud_detection")
    
    if not fraud_context:
        print("⚠️  No stored context found - this might be a fresh start")
        return None
    
    # Display context summary
    if "status" in fraud_context:
        status = fraud_context["status"]
        print("\n📊 Fraud Detection Project Status:")
        print(f"   Last Updated: {status.get('_timestamp', 'Unknown')}")
        
        if "performance" in status:
            perf = status["performance"]
            print(f"   💰 Value Protected: ${perf.get('value_protected', 0)}")
            print(f"   🚨 Fraud Detection Rate: {perf.get('fraud_detection_rate', 0)}%")
            print(f"   ⚡ Avg Replication Time: {perf.get('avg_replication_time_ms', 0)}ms")
        
        if "components" in status:
            print(f"   🛠️  Key Components: {len(status['components'])} files")
        
        if "features" in status:
            print(f"   ✅ Features: {len(status['features'])} implemented")
    
    print("\n🎯 Context loaded successfully!")
    return fraud_context

def load_project_context(project_name: str):
    """Load any project context from Redis"""
    manager = RedisMemoryManager()
    
    print(f"🔄 Loading {project_name} project context from Redis...")
    
    if not manager.test_connection():
        return None
    
    context = manager.get_all_project_memories(project_name)
    
    if context:
        print(f"✅ Loaded context for {project_name}")
        return context
    else:
        print(f"⚠️  No stored context found for {project_name}")
        return None

def list_all_projects():
    """List all projects with stored context"""
    manager = RedisMemoryManager()
    
    if not manager.test_connection():
        return []
    
    projects = manager.list_projects()
    
    print("📁 Projects with stored context:")
    for project in projects:
        memories = manager.get_all_project_memories(project)
        memory_types = list(memories.keys())
        print(f"   - {project}: {len(memory_types)} memory types")
    
    return projects

def store_workshop_progress(workshop_name: str, progress_data: dict):
    """Store progress for any workshop"""
    manager = RedisMemoryManager()
    
    if not manager.test_connection():
        return False
    
    return manager.store_project_memory(workshop_name, "progress", progress_data)

def main():
    """Interactive context loader"""
    print("🚀 Redis Workshops Context Loader")
    print("=" * 50)
    
    # List all projects
    projects = list_all_projects()
    
    if not projects:
        print("No projects found with stored context.")
        return
    
    print(f"\nFound {len(projects)} projects with stored context.")
    
    # Load fraud detection context as example
    if "fraud_detection" in projects:
        print("\n" + "=" * 50)
        load_fraud_detection_context()

if __name__ == "__main__":
    main()
