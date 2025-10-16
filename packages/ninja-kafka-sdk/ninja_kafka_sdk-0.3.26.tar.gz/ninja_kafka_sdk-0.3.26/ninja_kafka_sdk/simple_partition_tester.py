#!/usr/bin/env python3
"""
Simple Kafka Partition Tester - Tests message delivery to all partitions

This script tests message delivery to each partition and identifies broken ones.
It's simpler and more practical than the complex metadata approach.

Usage:
    python simple_partition_tester.py                    # Test default topics
    python simple_partition_tester.py --topics ninja-results ninja-tasks
    python simple_partition_tester.py --monitor          # Continuous monitoring
"""

import json
import logging
import time
import argparse
from typing import Dict, List, Tuple
from datetime import datetime
from kafka import KafkaProducer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimplePartitionTester:
    """Simple partition health tester using actual message delivery."""
    
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        
    def connect(self):
        """Connect to Kafka."""
        logger.info(f"🔌 Connecting to Kafka: {self.bootstrap_servers}")
        
        self.producer = KafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all',
            retries=0,  # No retries for testing
            request_timeout_ms=10000,
            delivery_timeout_ms=15000
        )
        
        logger.info("✅ Connected to Kafka")
    
    def disconnect(self):
        """Disconnect from Kafka."""
        if self.producer:
            self.producer.close()
            logger.info("🔌 Disconnected from Kafka")
    
    def test_topic_partitions(self, topic: str, max_partitions: int = 10) -> Dict[int, Tuple[bool, str]]:
        """Test message delivery to all partitions of a topic."""
        logger.info(f"🧪 Testing topic: {topic}")
        
        # First, discover how many partitions exist
        available_partitions = self.producer.partitions_for(topic)
        if not available_partitions:
            logger.error(f"❌ Topic {topic} not found")
            return {}
        
        logger.info(f"📊 Found {len(available_partitions)} partitions: {sorted(available_partitions)}")
        
        results = {}
        
        for partition_id in sorted(available_partitions):
            success, error = self._test_partition_delivery(topic, partition_id)
            results[partition_id] = (success, error)
            
            # Small delay between tests
            time.sleep(0.1)
        
        return results
    
    def _test_partition_delivery(self, topic: str, partition: int) -> Tuple[bool, str]:
        """Test delivery to a specific partition."""
        test_message = {
            'test': True,
            'topic': topic,
            'partition': partition,
            'timestamp': time.time(),
            'tester': 'simple-partition-tester'
        }
        
        try:
            logger.debug(f"📤 Testing {topic}:{partition}")
            
            future = self.producer.send(
                topic,
                value=test_message,
                partition=partition
            )
            
            # Wait for delivery
            record_metadata = future.get(timeout=10)
            
            success_msg = f"✅ Success (offset: {record_metadata.offset})"
            logger.debug(f"{topic}:{partition} - {success_msg}")
            return True, success_msg
            
        except Exception as e:
            error_msg = f"❌ Failed: {str(e)}"
            logger.warning(f"{topic}:{partition} - {error_msg}")
            return False, error_msg
    
    def print_results(self, topic: str, results: Dict[int, Tuple[bool, str]]):
        """Print formatted test results."""
        if not results:
            print(f"\n❌ {topic}: No partitions found or topic doesn't exist")
            return
        
        successful_partitions = [p for p, (success, _) in results.items() if success]
        failed_partitions = [p for p, (success, _) in results.items() if not success]
        
        success_rate = len(successful_partitions) / len(results) * 100
        
        print(f"\n{'='*60}")
        print(f"📊 TOPIC: {topic}")
        print(f"{'='*60}")
        print(f"📈 Success Rate: {success_rate:.1f}% ({len(successful_partitions)}/{len(results)})")
        
        if successful_partitions:
            print(f"✅ Working Partitions: {successful_partitions}")
        
        if failed_partitions:
            print(f"❌ Broken Partitions: {failed_partitions}")
            print(f"\n🔧 IMMEDIATE FIX:")
            print(f"   Use working partition in your code:")
            if successful_partitions:
                print(f"   producer.send('{topic}', message, partition={successful_partitions[0]})")
            
            print(f"\n💥 FAILURE DETAILS:")
            for partition in failed_partitions:
                _, error = results[partition]
                print(f"   Partition {partition}: {error}")
        
        if success_rate < 100:
            print(f"\n🚨 INFRASTRUCTURE ACTION REQUIRED:")
            print(f"   1. Check MSK cluster health")
            print(f"   2. Monitor CloudWatch metrics")
            print(f"   3. Consider broker restart during maintenance window")
        
        print(f"{'='*60}")
    
    def test_multiple_topics(self, topics: List[str]) -> Dict[str, Dict[int, Tuple[bool, str]]]:
        """Test multiple topics."""
        all_results = {}
        
        for topic in topics:
            results = self.test_topic_partitions(topic)
            all_results[topic] = results
            self.print_results(topic, results)
        
        return all_results
    
    def generate_fix_recommendations(self, all_results: Dict[str, Dict[int, Tuple[bool, str]]]):
        """Generate fix recommendations based on test results."""
        print(f"\n{'='*80}")
        print(f"🔧 FIX RECOMMENDATIONS")
        print(f"{'='*80}")
        
        has_issues = False
        
        for topic, results in all_results.items():
            if not results:
                continue
                
            failed_partitions = [p for p, (success, _) in results.items() if not success]
            successful_partitions = [p for p, (success, _) in results.items() if success]
            
            if failed_partitions:
                has_issues = True
                print(f"\n🎯 {topic}:")
                print(f"   Broken: {failed_partitions}")
                print(f"   Working: {successful_partitions}")
                
                if successful_partitions:
                    print(f"\n   ⚡ IMMEDIATE CODE FIX:")
                    print(f"      # Force to working partition in SDK:")
                    print(f"      future = producer.send('{topic}', message, partition={successful_partitions[0]})")
                    print(f"")
                    print(f"      # Or update ninja_kafka_sdk/client.py:")
                    print(f"      partition={successful_partitions[0]}  # Line 439")
        
        if has_issues:
            print(f"\n🏗️ INFRASTRUCTURE FIXES:")
            print(f"   1. Check Amazon MSK cluster status")
            print(f"   2. Monitor broker health via CloudWatch")  
            print(f"   3. Restart brokers during maintenance window")
            print(f"   4. Consider increasing replication factor")
            print(f"\n📊 MONITORING SETUP:")
            print(f"   - Set up alerts for partition leadership changes")
            print(f"   - Monitor OfflinePartitionsCount metric")
            print(f"   - Track message delivery success rates")
        else:
            print(f"\n✅ ALL TOPICS HEALTHY - No action needed")
        
        print(f"{'='*80}")
    
    def monitor_continuously(self, topics: List[str], interval: int = 60):
        """Monitor partition health continuously."""
        logger.info(f"🔍 Starting continuous monitoring (interval: {interval}s)")
        logger.info("Press Ctrl+C to stop")
        
        try:
            while True:
                print(f"\n🕐 Health check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                all_results = self.test_multiple_topics(topics)
                
                # Quick summary
                issues = []
                for topic, results in all_results.items():
                    failed = [p for p, (success, _) in results.items() if not success]
                    if failed:
                        issues.append(f"{topic}(partitions {failed})")
                
                if issues:
                    print(f"\n⚠️ Issues detected: {', '.join(issues)}")
                else:
                    print(f"\n✅ All topics healthy")
                
                print(f"\n⏰ Next check in {interval} seconds...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Monitoring stopped")

def main():
    parser = argparse.ArgumentParser(
        description="Simple Kafka Partition Health Tester",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--servers',
        default='localhost:9092',
        help='Kafka bootstrap servers'
    )
    
    parser.add_argument(
        '--topics',
        nargs='+',
        default=['ninja-results', 'ninja-tasks'],
        help='Topics to test'
    )
    
    parser.add_argument(
        '--monitor',
        action='store_true',
        help='Continuous monitoring mode'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Monitoring interval in seconds'
    )
    
    args = parser.parse_args()
    
    tester = SimplePartitionTester(args.servers)
    
    try:
        tester.connect()
        
        if args.monitor:
            tester.monitor_continuously(args.topics, args.interval)
        else:
            all_results = tester.test_multiple_topics(args.topics)
            tester.generate_fix_recommendations(all_results)
    
    except KeyboardInterrupt:
        logger.info("🛑 Stopped by user")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
    finally:
        tester.disconnect()

if __name__ == "__main__":
    main()