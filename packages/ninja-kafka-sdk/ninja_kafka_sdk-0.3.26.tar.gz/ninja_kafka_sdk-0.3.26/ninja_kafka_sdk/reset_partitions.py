#!/usr/bin/env python3
"""
Simple Kafka Partition Reset Script

Resets partition leadership by triggering preferred replica election.
This forces Kafka to reassign partition leaders to healthy brokers.

Usage:
    python reset_partitions.py                    # Reset ninja-results and ninja-tasks
    python reset_partitions.py --topics topic1   # Reset specific topic
    python reset_partitions.py --force            # Force reset even if topics seem healthy
"""

import json
import subprocess
import sys
import argparse
import time
from typing import List

def run_kafka_command(cmd: List[str]) -> bool:
    """Run a kafka command and return success status."""
    try:
        print(f"🔧 Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"✅ Success")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Failed (exit code: {result.returncode})")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print(f"❌ Command timed out")
        return False
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False

def trigger_leader_election(topics: List[str], kafka_servers: str = "localhost:9092") -> bool:
    """Trigger preferred replica election for topics."""
    print(f"⚡ Triggering leader election for topics: {', '.join(topics)}")
    
    # Create partition JSON for leader election
    partitions_data = {"partitions": []}
    
    for topic in topics:
        # Get partition count for topic
        describe_cmd = [
            "kafka-topics", "--bootstrap-server", kafka_servers,
            "--describe", "--topic", topic
        ]
        
        print(f"📊 Getting partition info for {topic}...")
        try:
            result = subprocess.run(describe_cmd, capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                partition_lines = [line for line in lines if f"Topic: {topic}" in line and "Partition:" in line]
                
                for line in partition_lines:
                    # Extract partition number
                    parts = line.split()
                    partition_idx = parts.index("Partition:")
                    partition_num = int(parts[partition_idx + 1])
                    
                    partitions_data["partitions"].append({
                        "topic": topic,
                        "partition": partition_num
                    })
                    
                print(f"   Found {len(partition_lines)} partitions")
            else:
                print(f"   ⚠️ Could not describe topic {topic}")
        except Exception as e:
            print(f"   ⚠️ Error describing topic {topic}: {e}")
    
    if not partitions_data["partitions"]:
        print("❌ No partitions found to reset")
        return False
    
    # Write partition data to temp file
    partition_file = "/tmp/partitions_to_elect.json"
    try:
        with open(partition_file, 'w') as f:
            json.dump(partitions_data, f)
        print(f"📁 Created partition file: {partition_file}")
    except Exception as e:
        print(f"❌ Failed to create partition file: {e}")
        return False
    
    # Trigger leader election
    elect_cmd = [
        "kafka-leader-election", "--bootstrap-server", kafka_servers,
        "--election-type", "preferred", "--path-to-json-file", partition_file
    ]
    
    success = run_kafka_command(elect_cmd)
    
    # Cleanup
    try:
        import os
        os.remove(partition_file)
    except:
        pass
    
    return success

def restart_kafka_if_local() -> bool:
    """Restart local Kafka if running."""
    print("🔄 Checking if we can restart local Kafka...")
    
    # Check if kafka is running locally
    try:
        result = subprocess.run(["pgrep", "-f", "kafka"], capture_output=True)
        if result.returncode != 0:
            print("   ℹ️ Kafka not running locally - skipping restart")
            return True
    except:
        print("   ℹ️ Cannot check Kafka process - skipping restart")
        return True
    
    print("⚠️ Local Kafka detected - restart requires manual intervention")
    print("   For MSK clusters, restart brokers via AWS console")
    print("   For local Kafka, restart the Kafka service")
    return False

def main():
    parser = argparse.ArgumentParser(description="Reset Kafka partition leadership")
    parser.add_argument('--topics', nargs='+', default=['ninja-results', 'ninja-tasks'], help='Topics to reset')
    parser.add_argument('--servers', default='localhost:9092', help='Kafka servers')
    parser.add_argument('--force', action='store_true', help='Force reset without health check')
    
    args = parser.parse_args()
    
    print("🔧 KAFKA PARTITION RESET TOOL")
    print("="*50)
    print(f"Topics: {', '.join(args.topics)}")
    print(f"Servers: {args.servers}")
    print()
    
    if not args.force:
        print("🧪 Testing current partition health...")
        # Quick test with our existing tester
        try:
            from simple_partition_tester import SimplePartitionTester
            tester = SimplePartitionTester(args.servers)
            tester.connect()
            
            needs_reset = False
            for topic in args.topics:
                results = tester.test_topic_partitions(topic)
                failed = [p for p, (success, _) in results.items() if not success]
                if failed:
                    print(f"   ❌ {topic}: broken partitions {failed}")
                    needs_reset = True
                else:
                    print(f"   ✅ {topic}: all partitions healthy")
            
            tester.disconnect()
            
            if not needs_reset:
                print("\n✅ All partitions healthy - no reset needed")
                return
        except Exception as e:
            print(f"   ⚠️ Health check failed: {e}")
            print("   Proceeding with reset anyway...")
    
    print("\n⚡ RESETTING PARTITIONS...")
    
    # Method 1: Preferred replica election
    print("\n1️⃣ Trying preferred replica election...")
    if trigger_leader_election(args.topics, args.servers):
        print("✅ Leader election completed")
        
        # Wait a bit for election to take effect
        print("⏱️ Waiting 10 seconds for election to take effect...")
        time.sleep(10)
        
        # Test if it worked
        try:
            from simple_partition_tester import SimplePartitionTester
            print("🧪 Testing after reset...")
            tester = SimplePartitionTester(args.servers)
            tester.connect()
            
            all_healthy = True
            for topic in args.topics:
                results = tester.test_topic_partitions(topic)
                failed = [p for p, (success, _) in results.items() if not success]
                if failed:
                    print(f"   ❌ {topic}: still broken partitions {failed}")
                    all_healthy = False
                else:
                    print(f"   ✅ {topic}: all partitions now healthy")
            
            tester.disconnect()
            
            if all_healthy:
                print("\n🎉 PARTITION RESET SUCCESSFUL!")
                return
        except Exception as e:
            print(f"   ⚠️ Post-reset test failed: {e}")
    
    # Method 2: Suggest manual intervention
    print("\n2️⃣ Manual intervention required:")
    print("   For MSK: Restart brokers in AWS console")
    print("   For local: Restart Kafka service")
    print("   Alternative: Delete and recreate topics (DATA LOSS!)")

if __name__ == "__main__":
    main()