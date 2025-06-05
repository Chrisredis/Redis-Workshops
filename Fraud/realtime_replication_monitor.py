#!/usr/bin/env python3
"""
Real-time Redis Replication Monitor

Shows live data synchronization between Redis instances with precise timing.
"""

import redis
import json
import time
import threading
from datetime import datetime
from typing import Dict, Any
import sys

class RealtimeReplicationMonitor:
    def __init__(self):
        """Initialize the real-time monitor"""
        # Redis connections
        self.redis_a = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.redis_b = redis.Redis(host='localhost', port=6380, db=0, decode_responses=True)
        
        # Monitoring state
        self.running = False
        self.last_stream_id_a = "0-0"
        self.last_stream_id_b = "0-0"
        
        # Statistics
        self.stats = {
            "total_replications": 0,
            "a_to_b_count": 0,
            "b_to_a_count": 0,
            "total_time": 0.0,
            "min_time": float('inf'),
            "max_time": 0.0,
            "data_volume": 0,
            "errors": 0
        }
        
        self.test_connections()
    
    def test_connections(self):
        """Test Redis connections"""
        try:
            self.redis_a.ping()
            print("✅ Connected to Store A (Redis port 6379)")
        except Exception as e:
            print(f"❌ Store A connection failed: {e}")
            raise
        
        try:
            self.redis_b.ping()
            print("✅ Connected to Store B (Redis port 6380)")
        except Exception as e:
            print(f"❌ Store B connection failed: {e}")
            raise
    
    def replicate_data(self, source_redis, target_redis, key: str, value: Any) -> float:
        """Replicate data and measure precise timing"""
        start_time = time.perf_counter()
        
        try:
            target_redis.set(key, value)
            end_time = time.perf_counter()
            
            replication_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            # Update statistics
            self.stats["total_replications"] += 1
            self.stats["total_time"] += replication_time
            self.stats["min_time"] = min(self.stats["min_time"], replication_time)
            self.stats["max_time"] = max(self.stats["max_time"], replication_time)
            
            # Estimate data size
            if isinstance(value, str):
                self.stats["data_volume"] += len(value.encode('utf-8'))
            elif isinstance(value, bytes):
                self.stats["data_volume"] += len(value)
            
            return replication_time
            
        except Exception as e:
            print(f"❌ Replication error: {e}")
            self.stats["errors"] += 1
            return -1
    
    def replicate_stream_entry(self, source_redis, target_redis, fields: Dict) -> float:
        """Replicate stream entry with timing"""
        start_time = time.perf_counter()
        
        try:
            target_redis.xadd("transaction_stream", fields)
            end_time = time.perf_counter()
            
            replication_time = (end_time - start_time) * 1000
            
            # Update statistics
            self.stats["total_replications"] += 1
            self.stats["total_time"] += replication_time
            self.stats["min_time"] = min(self.stats["min_time"], replication_time)
            self.stats["max_time"] = max(self.stats["max_time"], replication_time)
            
            # Estimate data size
            data_size = sum(len(str(k)) + len(str(v)) for k, v in fields.items())
            self.stats["data_volume"] += data_size
            
            return replication_time
            
        except Exception as e:
            print(f"❌ Stream replication error: {e}")
            self.stats["errors"] += 1
            return -1
    
    def monitor_stream_a_to_b(self):
        """Monitor Store A → Store B replication"""
        while self.running:
            try:
                # Read new entries from Store A
                entries = self.redis_a.xread(
                    {"transaction_stream": self.last_stream_id_a},
                    count=1,
                    block=1000
                )
                
                for stream_name, messages in entries:
                    for message_id, fields in messages:
                        self.last_stream_id_a = message_id
                        
                        # Replicate stream entry
                        replication_time = self.replicate_stream_entry(
                            self.redis_a, self.redis_b, fields
                        )
                        
                        if replication_time > 0:
                            self.stats["a_to_b_count"] += 1
                            self.print_replication_event(
                                "A → B", "STREAM", message_id, fields, replication_time
                            )
                        
                        # Replicate associated data
                        if "transaction_id" in fields:
                            self.replicate_associated_data(
                                fields["transaction_id"], self.redis_a, self.redis_b, "A → B"
                            )
            
            except redis.ResponseError:
                time.sleep(0.1)
            except Exception as e:
                if self.running:
                    print(f"❌ Error in A→B monitor: {e}")
                time.sleep(1)
    
    def monitor_stream_b_to_a(self):
        """Monitor Store B → Store A replication"""
        while self.running:
            try:
                # Read new entries from Store B
                entries = self.redis_b.xread(
                    {"transaction_stream": self.last_stream_id_b},
                    count=1,
                    block=1000
                )
                
                for stream_name, messages in entries:
                    for message_id, fields in messages:
                        self.last_stream_id_b = message_id
                        
                        # Replicate stream entry
                        replication_time = self.replicate_stream_entry(
                            self.redis_b, self.redis_a, fields
                        )
                        
                        if replication_time > 0:
                            self.stats["b_to_a_count"] += 1
                            self.print_replication_event(
                                "B → A", "STREAM", message_id, fields, replication_time
                            )
                        
                        # Replicate associated data
                        if "transaction_id" in fields:
                            self.replicate_associated_data(
                                fields["transaction_id"], self.redis_b, self.redis_a, "B → A"
                            )
            
            except redis.ResponseError:
                time.sleep(0.1)
            except Exception as e:
                if self.running:
                    print(f"❌ Error in B→A monitor: {e}")
                time.sleep(1)
    
    def replicate_associated_data(self, transaction_id: str, source_redis, target_redis, direction: str):
        """Replicate transaction and photo data"""
        try:
            # Replicate transaction data
            transaction_key = f"transaction:{transaction_id}"
            transaction_data = source_redis.get(transaction_key)
            
            if transaction_data:
                replication_time = self.replicate_data(
                    source_redis, target_redis, transaction_key, transaction_data
                )
                if replication_time > 0:
                    self.print_replication_event(
                        direction, "TRANSACTION", transaction_key, 
                        f"{len(transaction_data)} bytes", replication_time
                    )
            
            # Replicate photo data
            photo_key = f"photo:{transaction_id}"
            photo_data = source_redis.get(photo_key)
            
            if photo_data:
                replication_time = self.replicate_data(
                    source_redis, target_redis, photo_key, photo_data
                )
                if replication_time > 0:
                    self.print_replication_event(
                        direction, "PHOTO", photo_key, 
                        f"{len(photo_data)} bytes", replication_time
                    )
        
        except Exception as e:
            print(f"❌ Error replicating associated data: {e}")
    
    def print_replication_event(self, direction: str, data_type: str, key: str, data_info: Any, replication_time: float):
        """Print replication event with detailed timing"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # Direction indicators
        if direction == "A → B":
            arrow = "🔵 ➡️"
        else:
            arrow = "🟠 ⬅️"
        
        # Data type icons
        icons = {"STREAM": "📊", "TRANSACTION": "💳", "PHOTO": "📷"}
        icon = icons.get(data_type, "📄")
        
        # Time color coding
        if replication_time < 1:
            time_indicator = "🟢"  # Very fast
        elif replication_time < 5:
            time_indicator = "🟡"  # Fast
        else:
            time_indicator = "🔴"  # Slow
        
        print(f"\n{timestamp} {arrow} {icon} {data_type}")
        print(f"  Key: {key}")
        print(f"  Data: {data_info}")
        print(f"  {time_indicator} Replication Time: {replication_time:.3f}ms")
        
        # Show running statistics
        if self.stats["total_replications"] > 0:
            avg_time = self.stats["total_time"] / self.stats["total_replications"]
            print(f"  📈 Total: {self.stats['total_replications']} | Avg: {avg_time:.3f}ms | Volume: {self.stats['data_volume']:,} bytes")
    
    def print_status_header(self):
        """Print monitoring header"""
        print("\n" + "=" * 80)
        print("🔄 REAL-TIME REDIS ACTIVE-ACTIVE REPLICATION MONITOR")
        print("=" * 80)
        print("🔵 Store A (port 6379) ↔️ Store B (port 6380)")
        print("⏱️  Microsecond-precision timing measurements")
        print("📊 Live data volume and performance tracking")
        print("🛑 Press Ctrl+C to stop")
        print("=" * 80)
    
    def print_periodic_stats(self):
        """Print detailed periodic statistics"""
        while self.running:
            time.sleep(15)  # Every 15 seconds
            
            if self.stats["total_replications"] > 0:
                avg_time = self.stats["total_time"] / self.stats["total_replications"]
                
                print(f"\n📊 REPLICATION PERFORMANCE - {datetime.now().strftime('%H:%M:%S')}")
                print("-" * 60)
                print(f"🔄 Total Replications: {self.stats['total_replications']}")
                print(f"🔵 A → B: {self.stats['a_to_b_count']}")
                print(f"🟠 B → A: {self.stats['b_to_a_count']}")
                print(f"⏱️  Average Time: {avg_time:.3f}ms")
                print(f"🟢 Fastest: {self.stats['min_time']:.3f}ms")
                print(f"🔴 Slowest: {self.stats['max_time']:.3f}ms")
                print(f"📊 Data Volume: {self.stats['data_volume']:,} bytes")
                print(f"📈 Throughput: {self.stats['data_volume']/1024:.1f} KB/total")
                print(f"❌ Errors: {self.stats['errors']}")
                print("-" * 60)
    
    def start_monitoring(self):
        """Start real-time monitoring"""
        self.print_status_header()
        self.running = True
        
        # Start monitoring threads
        thread_a_to_b = threading.Thread(target=self.monitor_stream_a_to_b, daemon=True)
        thread_b_to_a = threading.Thread(target=self.monitor_stream_b_to_a, daemon=True)
        stats_thread = threading.Thread(target=self.print_periodic_stats, daemon=True)
        
        thread_a_to_b.start()
        thread_b_to_a.start()
        stats_thread.start()
        
        print("🔄 Real-time monitoring active... Waiting for transactions...")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping real-time monitor...")
            self.running = False
            
            # Final comprehensive statistics
            if self.stats["total_replications"] > 0:
                avg_time = self.stats["total_time"] / self.stats["total_replications"]
                throughput = self.stats["data_volume"] / max(self.stats["total_time"] / 1000, 0.001)  # bytes per second
                
                print(f"\n📊 FINAL PERFORMANCE REPORT")
                print("=" * 40)
                print(f"Total Replications: {self.stats['total_replications']}")
                print(f"A → B: {self.stats['a_to_b_count']}")
                print(f"B → A: {self.stats['b_to_a_count']}")
                print(f"Average Time: {avg_time:.3f}ms")
                print(f"Fastest: {self.stats['min_time']:.3f}ms")
                print(f"Slowest: {self.stats['max_time']:.3f}ms")
                print(f"Total Data: {self.stats['data_volume']:,} bytes ({self.stats['data_volume']/1024:.1f} KB)")
                print(f"Throughput: {throughput:.0f} bytes/sec")
                print(f"Errors: {self.stats['errors']}")
                
                # Performance rating
                if avg_time < 1:
                    rating = "🟢 EXCELLENT"
                elif avg_time < 5:
                    rating = "🟡 GOOD"
                else:
                    rating = "🔴 NEEDS OPTIMIZATION"
                
                print(f"Performance: {rating}")
            
            print("👋 Monitor stopped")

def main():
    """Main function"""
    try:
        monitor = RealtimeReplicationMonitor()
        monitor.start_monitoring()
    except Exception as e:
        print(f"❌ Failed to start monitor: {e}")

if __name__ == "__main__":
    main()
