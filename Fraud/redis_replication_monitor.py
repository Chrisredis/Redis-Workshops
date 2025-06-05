#!/usr/bin/env python3
"""
Redis Active-Active Replication Monitor

Shows real-time data synchronization between Redis instances
with precise timing measurements.
"""

import redis
import json
import time
import threading
from datetime import datetime
from typing import Dict, Any
import sys

class RedisReplicationMonitor:
    def __init__(self):
        """Initialize the replication monitor"""
        # Redis connections
        self.redis_a = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.redis_b = redis.Redis(host='localhost', port=6380, db=0, decode_responses=True)
        
        # Monitoring state
        self.running = False
        self.last_stream_id_a = "0-0"
        self.last_stream_id_b = "0-0"
        self.replication_stats = {
            "total_replicated": 0,
            "avg_replication_time": 0.0,
            "last_replication_time": 0.0,
            "errors": 0
        }
        
        # Test connections
        self.test_connections()
    
    def test_connections(self):
        """Test Redis connections"""
        try:
            self.redis_a.ping()
            print("✅ Connected to Redis Store A (port 6379)")
        except Exception as e:
            print(f"❌ Failed to connect to Store A: {e}")
            raise

        try:
            self.redis_b.ping()
            print("✅ Connected to Redis Store B (port 6380)")
        except Exception as e:
            print(f"❌ Failed to connect to Store B: {e}")
            raise
    
    def replicate_data(self, source_redis, target_redis, data_type: str, key: str, value: Any) -> float:
        """Replicate data from source to target and return replication time"""
        start_time = time.time()
        
        try:
            if data_type == "string":
                target_redis.set(key, value)
            elif data_type == "hash":
                target_redis.hset(key, mapping=value)
            elif data_type == "stream":
                # For streams, we add the entry
                target_redis.xadd("transaction_stream", value)
            
            replication_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Update stats
            self.replication_stats["total_replicated"] += 1
            self.replication_stats["last_replication_time"] = replication_time
            
            # Calculate running average
            total = self.replication_stats["total_replicated"]
            current_avg = self.replication_stats["avg_replication_time"]
            self.replication_stats["avg_replication_time"] = (
                (current_avg * (total - 1) + replication_time) / total
            )
            
            return replication_time
            
        except Exception as e:
            logger.error(f"❌ Replication error: {e}")
            self.replication_stats["errors"] += 1
            return -1
    
    def monitor_stream_a_to_b(self):
        """Monitor Store A stream and replicate to Store B"""
        while self.running:
            try:
                # Read new entries from Store A stream
                entries = self.redis_a.xread(
                    {"transaction_stream": self.last_stream_id_a},
                    count=1,
                    block=1000  # Block for 1 second
                )
                
                for stream_name, messages in entries:
                    for message_id, fields in messages:
                        # Update last processed ID
                        self.last_stream_id_a = message_id
                        
                        # Replicate to Store B
                        replication_time = self.replicate_data(
                            self.redis_a, self.redis_b, "stream", "transaction_stream", fields
                        )
                        
                        if replication_time > 0:
                            self.print_replication_event(
                                "A → B", "STREAM", message_id, fields, replication_time
                            )
                        
                        # Also replicate associated transaction and photo data
                        if "transaction_id" in fields:
                            self.replicate_transaction_data(
                                fields["transaction_id"], self.redis_a, self.redis_b, "A → B"
                            )
            
            except redis.ResponseError:
                # Stream doesn't exist yet, continue
                time.sleep(0.1)
            except Exception as e:
                if self.running:  # Only log if we're still supposed to be running
                    logger.error(f"Error monitoring A→B: {e}")
                time.sleep(1)
    
    def monitor_stream_b_to_a(self):
        """Monitor Store B stream and replicate to Store A"""
        while self.running:
            try:
                # Read new entries from Store B stream
                entries = self.redis_b.xread(
                    {"transaction_stream": self.last_stream_id_b},
                    count=1,
                    block=1000  # Block for 1 second
                )
                
                for stream_name, messages in entries:
                    for message_id, fields in messages:
                        # Update last processed ID
                        self.last_stream_id_b = message_id
                        
                        # Replicate to Store A
                        replication_time = self.replicate_data(
                            self.redis_b, self.redis_a, "stream", "transaction_stream", fields
                        )
                        
                        if replication_time > 0:
                            self.print_replication_event(
                                "B → A", "STREAM", message_id, fields, replication_time
                            )
                        
                        # Also replicate associated transaction and photo data
                        if "transaction_id" in fields:
                            self.replicate_transaction_data(
                                fields["transaction_id"], self.redis_b, self.redis_a, "B → A"
                            )
            
            except redis.ResponseError:
                # Stream doesn't exist yet, continue
                time.sleep(0.1)
            except Exception as e:
                if self.running:  # Only log if we're still supposed to be running
                    logger.error(f"Error monitoring B→A: {e}")
                time.sleep(1)
    
    def replicate_transaction_data(self, transaction_id: str, source_redis, target_redis, direction: str):
        """Replicate transaction and photo data"""
        try:
            # Replicate transaction data
            transaction_key = f"transaction:{transaction_id}"
            transaction_data = source_redis.get(transaction_key)
            
            if transaction_data:
                replication_time = self.replicate_data(
                    source_redis, target_redis, "string", transaction_key, transaction_data
                )
                if replication_time > 0:
                    self.print_replication_event(
                        direction, "TRANSACTION", transaction_key, 
                        f"Transaction data ({len(transaction_data)} bytes)", replication_time
                    )
            
            # Replicate photo data
            photo_key = f"photo:{transaction_id}"
            photo_data = source_redis.get(photo_key)
            
            if photo_data:
                replication_time = self.replicate_data(
                    source_redis, target_redis, "string", photo_key, photo_data
                )
                if replication_time > 0:
                    self.print_replication_event(
                        direction, "PHOTO", photo_key, 
                        f"Photo data ({len(photo_data)} bytes)", replication_time
                    )
        
        except Exception as e:
            logger.error(f"Error replicating transaction data: {e}")
    
    def print_replication_event(self, direction: str, data_type: str, key: str, data_summary: Any, replication_time: float):
        """Print a replication event with timing"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # Include milliseconds
        
        # Color coding for direction
        if direction == "A → B":
            direction_color = "🔵"  # Blue for A to B
        else:
            direction_color = "🟠"  # Orange for B to A
        
        # Data type icons
        type_icons = {
            "STREAM": "📊",
            "TRANSACTION": "💳",
            "PHOTO": "📷"
        }
        icon = type_icons.get(data_type, "📄")
        
        # Format replication time with color coding
        if replication_time < 1:
            time_color = "🟢"  # Green for very fast
        elif replication_time < 10:
            time_color = "🟡"  # Yellow for fast
        else:
            time_color = "🔴"  # Red for slow
        
        print(f"{timestamp} {direction_color} {direction} {icon} {data_type}")
        print(f"    Key: {key}")
        print(f"    Data: {data_summary}")
        print(f"    {time_color} Replication Time: {replication_time:.2f}ms")
        print(f"    📈 Total Replicated: {self.replication_stats['total_replicated']}")
        print(f"    ⏱️  Average Time: {self.replication_stats['avg_replication_time']:.2f}ms")
        print("-" * 60)
    
    def print_status(self):
        """Print current status"""
        while self.running:
            time.sleep(5)  # Print status every 5 seconds
            
            print(f"\n📊 REPLICATION STATUS - {datetime.now().strftime('%H:%M:%S')}")
            print("=" * 60)
            print(f"🔄 Total Replications: {self.replication_stats['total_replicated']}")
            print(f"⏱️  Average Time: {self.replication_stats['avg_replication_time']:.2f}ms")
            print(f"🕐 Last Replication: {self.replication_stats['last_replication_time']:.2f}ms")
            print(f"❌ Errors: {self.replication_stats['errors']}")
            
            # Show current stream positions
            try:
                stream_info_a = self.redis_a.xinfo_stream("transaction_stream")
                stream_info_b = self.redis_b.xinfo_stream("transaction_stream")
                print(f"📊 Store A Stream Length: {stream_info_a.get('length', 0)}")
                print(f"📊 Store B Stream Length: {stream_info_b.get('length', 0)}")
            except:
                print("📊 Streams not yet created")
            
            print("=" * 60)
    
    def start_monitoring(self):
        """Start the replication monitoring"""
        print("\n🔄 Starting Redis Active-Active Replication Monitor")
        print("=" * 60)
        print("🔵 Store A (port 6379) ↔️ Store B (port 6380)")
        print("📊 Monitoring real-time data synchronization...")
        print("⏱️  Showing replication timing for each operation")
        print("🛑 Press Ctrl+C to stop")
        print("=" * 60)
        
        self.running = True
        
        # Start monitoring threads
        thread_a_to_b = threading.Thread(target=self.monitor_stream_a_to_b, daemon=True)
        thread_b_to_a = threading.Thread(target=self.monitor_stream_b_to_a, daemon=True)
        status_thread = threading.Thread(target=self.print_status, daemon=True)
        
        thread_a_to_b.start()
        thread_b_to_a.start()
        status_thread.start()
        
        try:
            # Keep main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping replication monitor...")
            self.running = False
            
            # Final stats
            print(f"\n📊 FINAL STATISTICS")
            print("=" * 30)
            print(f"Total Replications: {self.replication_stats['total_replicated']}")
            print(f"Average Time: {self.replication_stats['avg_replication_time']:.2f}ms")
            print(f"Errors: {self.replication_stats['errors']}")
            print("👋 Monitor stopped")

def main():
    """Main function"""
    try:
        monitor = RedisReplicationMonitor()
        monitor.start_monitoring()
    except Exception as e:
        logger.error(f"❌ Failed to start monitor: {e}")

if __name__ == "__main__":
    main()
