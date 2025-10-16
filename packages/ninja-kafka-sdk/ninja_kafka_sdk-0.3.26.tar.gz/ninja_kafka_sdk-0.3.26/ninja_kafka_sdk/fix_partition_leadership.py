#!/usr/bin/env python3
"""
Kafka Partition Leadership Fix Script

This script detects and fixes broken partition leadership issues by:
1. Analyzing partition health across topics
2. Identifying broken/unhealthy partitions
3. Triggering partition leader elections
4. Validating message delivery to all partitions
5. Providing recommendations for infrastructure fixes

Usage:
    python fix_partition_leadership.py --check           # Health check only
    python fix_partition_leadership.py --fix             # Attempt automatic fixes
    python fix_partition_leadership.py --test-delivery   # Test message delivery
    python fix_partition_leadership.py --monitor         # Continuous monitoring
"""

import asyncio
import json
import logging
import time
import argparse
import sys
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from datetime import datetime, timedelta

try:
    from kafka import KafkaProducer, KafkaConsumer, KafkaAdminClient
    from kafka.admin import NewPartitions, ConfigResource, ConfigResourceType
    from kafka.errors import KafkaError, NotLeaderForPartitionError, LeaderNotAvailableError
except ImportError:
    print("❌ kafka-python not installed. Run: pip install kafka-python")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class PartitionHealth:
    topic: str
    partition: int
    leader: Optional[int]
    replicas: List[int]
    in_sync_replicas: List[int]
    is_healthy: bool
    last_test_success: Optional[float]
    failure_count: int
    error_message: Optional[str]

@dataclass
class TopicHealth:
    topic: str
    total_partitions: int
    healthy_partitions: int
    broken_partitions: List[int]
    partition_details: List[PartitionHealth]
    overall_health: str  # "HEALTHY", "DEGRADED", "CRITICAL"

class KafkaPartitionFixer:
    """Kafka partition leadership diagnostic and fix tool."""
    
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.bootstrap_servers = bootstrap_servers
        self.admin_client = None
        self.producer = None
        self.topics_to_check = ['ninja-results', 'ninja-tasks']
        self.partition_health_cache = {}
        
    def __enter__(self):
        self._connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._disconnect()
        
    def _connect(self):
        """Initialize Kafka connections."""
        try:
            logger.info(f"🔌 Connecting to Kafka: {self.bootstrap_servers}")
            
            self.admin_client = KafkaAdminClient(
                bootstrap_servers=self.bootstrap_servers,
                client_id='partition-fixer',
                request_timeout_ms=30000
            )
            
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                client_id='partition-fixer-producer',
                acks='all',
                retries=0,  # No retries for testing
                request_timeout_ms=10000,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            
            logger.info("✅ Connected to Kafka successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Kafka: {e}")
            raise
    
    def _disconnect(self):
        """Clean up Kafka connections."""
        if self.producer:
            self.producer.close()
        if self.admin_client:
            self.admin_client.close()
        logger.info("🔌 Disconnected from Kafka")
    
    def get_topic_metadata(self, topics: List[str]) -> Dict[str, TopicHealth]:
        """Get detailed metadata for specified topics."""
        logger.info(f"📊 Analyzing topics: {', '.join(topics)}")
        
        try:
            # Get cluster metadata to access topic information
            cluster_metadata = self.producer.partitions_for(topics[0])  # Test connectivity first
            
            topic_health = {}
            
            for topic_name in topics:
                try:
                    # Get partition metadata for this topic
                    partitions = self.producer.partitions_for(topic_name)
                    if partitions is None:
                        logger.error(f"Topic {topic_name} not found")
                        continue
                    
                    # Use producer metadata to get partition info
                    cluster_meta = self.producer._metadata
                    cluster_meta.request_update()
                    time.sleep(1)  # Wait for metadata update
                    
                    topic_metadata = cluster_meta.cluster.topics.get(topic_name)
                    if not topic_metadata:
                        logger.error(f"No metadata for topic {topic_name}")
                        continue
                    partition_details = []
                    healthy_count = 0
                    broken_partitions = []
                    
                    # Create partition details from available partitions
                    for partition_id in sorted(partitions):
                        partition_info = cluster_meta.cluster.partition_metadata(topic_name, partition_id)
                        
                        leader = partition_info.leader if partition_info else None
                        replicas = list(partition_info.replicas) if partition_info and partition_info.replicas else []
                        in_sync_replicas = list(partition_info.isr) if partition_info and partition_info.isr else []
                        
                        # Determine partition health
                        is_healthy = (
                            leader is not None and 
                            leader in in_sync_replicas and
                            len(in_sync_replicas) >= len(replicas) // 2 + 1
                        ) if replicas else (leader is not None)
                        
                        if is_healthy:
                            healthy_count += 1
                        else:
                            broken_partitions.append(partition_id)
                        
                        partition_health = PartitionHealth(
                            topic=topic_name,
                            partition=partition_id,
                            leader=leader,
                            replicas=replicas,
                            in_sync_replicas=in_sync_replicas,
                            is_healthy=is_healthy,
                            last_test_success=None,
                            failure_count=0,
                            error_message=None
                        )
                        partition_details.append(partition_health)
                
                    # Determine overall topic health
                    total_partitions = len(partition_details)
                    if healthy_count == total_partitions:
                        overall_health = "HEALTHY"
                    elif healthy_count >= total_partitions // 2:
                        overall_health = "DEGRADED"
                    else:
                        overall_health = "CRITICAL"
                    
                    topic_health[topic_name] = TopicHealth(
                        topic=topic_name,
                        total_partitions=total_partitions,
                        healthy_partitions=healthy_count,
                        broken_partitions=broken_partitions,
                        partition_details=partition_details,
                        overall_health=overall_health
                    )
                    
                except Exception as e:
                    logger.error(f"❌ Failed to analyze topic {topic_name}: {e}")
            
            return topic_health
            
        except Exception as e:
            logger.error(f"❌ Failed to get topic metadata: {e}")
            raise
    
    def test_partition_delivery(self, topic: str, partition: int) -> Tuple[bool, Optional[str]]:
        """Test message delivery to a specific partition."""
        test_message = {
            'test': True,
            'partition': partition,
            'timestamp': time.time(),
            'fixer': 'partition-leadership-fix'
        }
        
        try:
            logger.debug(f"📤 Testing delivery to {topic}:{partition}")
            
            future = self.producer.send(
                topic,
                value=test_message,
                partition=partition
            )
            
            # Wait for delivery with timeout
            record_metadata = future.get(timeout=10)
            
            logger.debug(f"✅ Delivery successful to {topic}:{partition} (offset: {record_metadata.offset})")
            return True, None
            
        except NotLeaderForPartitionError as e:
            error_msg = f"No leader for partition {partition}"
            logger.warning(f"⚠️ {topic}:{partition} - {error_msg}")
            return False, error_msg
            
        except LeaderNotAvailableError as e:
            error_msg = f"Leader not available for partition {partition}"
            logger.warning(f"⚠️ {topic}:{partition} - {error_msg}")
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Delivery failed: {str(e)}"
            logger.warning(f"⚠️ {topic}:{partition} - {error_msg}")
            return False, error_msg
    
    def test_all_partitions(self, topics: List[str]) -> Dict[str, TopicHealth]:
        """Test message delivery to all partitions of specified topics."""
        logger.info("🧪 Testing message delivery to all partitions...")
        
        topic_health = self.get_topic_metadata(topics)
        
        for topic_name, health in topic_health.items():
            logger.info(f"📤 Testing topic: {topic_name}")
            
            for partition_detail in health.partition_details:
                success, error = self.test_partition_delivery(
                    topic_name, 
                    partition_detail.partition
                )
                
                partition_detail.last_test_success = time.time() if success else None
                partition_detail.failure_count = 0 if success else 1
                partition_detail.error_message = error
                
                # Update health status based on actual delivery test
                if not success and partition_detail.is_healthy:
                    logger.warning(f"⚠️ Metadata says healthy but delivery failed: {topic_name}:{partition_detail.partition}")
                    partition_detail.is_healthy = False
                    if partition_detail.partition not in health.broken_partitions:
                        health.broken_partitions.append(partition_detail.partition)
                        health.healthy_partitions -= 1
        
        return topic_health
    
    def trigger_leader_election(self, topic: str, partitions: List[int]) -> bool:
        """Trigger leader election for specific partitions."""
        logger.info(f"⚡ Triggering leader election for {topic} partitions: {partitions}")
        
        try:
            from kafka.admin import NewPartitions
            from kafka.protocol.admin import ElectLeadersRequest
            
            # Note: Leader election API is complex and may require newer kafka-python
            # For now, we'll use a workaround approach
            
            logger.warning("🔧 Leader election API not fully implemented in this version")
            logger.info("💡 Manual intervention required:")
            logger.info(f"   1. Check MSK cluster health in AWS console")
            logger.info(f"   2. Consider restarting Kafka brokers during maintenance window")
            logger.info(f"   3. Monitor CloudWatch metrics for partition leadership")
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Leader election failed: {e}")
            return False
    
    def generate_fix_recommendations(self, topic_health: Dict[str, TopicHealth]) -> List[str]:
        """Generate actionable recommendations to fix partition issues."""
        recommendations = []
        
        for topic_name, health in topic_health.items():
            if health.overall_health == "HEALTHY":
                continue
            
            recommendations.append(f"\n🔧 FIXES FOR TOPIC: {topic_name}")
            recommendations.append(f"   Status: {health.overall_health}")
            recommendations.append(f"   Healthy: {health.healthy_partitions}/{health.total_partitions}")
            recommendations.append(f"   Broken partitions: {health.broken_partitions}")
            
            # Immediate workarounds
            if health.healthy_partitions > 0:
                healthy_partitions = [
                    p.partition for p in health.partition_details if p.is_healthy
                ]
                recommendations.append(f"\n   ⚡ IMMEDIATE WORKAROUND:")
                recommendations.append(f"      Force messages to healthy partitions: {healthy_partitions}")
                recommendations.append(f"      Code: producer.send('{topic_name}', message, partition={healthy_partitions[0]})")
            
            # Infrastructure fixes
            recommendations.append(f"\n   🏗️ INFRASTRUCTURE FIXES:")
            
            if health.overall_health == "CRITICAL":
                recommendations.append(f"      🚨 URGENT: More than half partitions are broken!")
                recommendations.append(f"      1. Check MSK cluster health immediately")
                recommendations.append(f"      2. Verify broker connectivity")
                recommendations.append(f"      3. Consider emergency broker restart")
            
            recommendations.append(f"      4. Monitor MSK CloudWatch metrics:")
            recommendations.append(f"         - PartitionLag")
            recommendations.append(f"         - LeaderElectionRateAndTimeMs") 
            recommendations.append(f"         - OfflinePartitionsCount")
            
            # Long-term solutions
            recommendations.append(f"\n   📈 LONG-TERM SOLUTIONS:")
            recommendations.append(f"      1. Increase replication factor to 3")
            recommendations.append(f"      2. Set min.in.sync.replicas=2")
            recommendations.append(f"      3. Implement partition health monitoring")
            recommendations.append(f"      4. Add automatic failover logic to application")
        
        return recommendations
    
    def print_health_report(self, topic_health: Dict[str, TopicHealth]):
        """Print detailed health report."""
        print("\n" + "="*80)
        print("📊 KAFKA PARTITION LEADERSHIP HEALTH REPORT")
        print("="*80)
        print(f"🕐 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔌 Cluster: {self.bootstrap_servers}")
        
        overall_healthy = all(h.overall_health == "HEALTHY" for h in topic_health.values())
        
        print(f"\n🎯 OVERALL STATUS: {'✅ HEALTHY' if overall_healthy else '❌ ISSUES DETECTED'}")
        
        for topic_name, health in topic_health.items():
            status_emoji = {
                "HEALTHY": "✅",
                "DEGRADED": "⚠️", 
                "CRITICAL": "🚨"
            }[health.overall_health]
            
            print(f"\n{status_emoji} TOPIC: {topic_name}")
            print(f"   Status: {health.overall_health}")
            print(f"   Partitions: {health.healthy_partitions}/{health.total_partitions} healthy")
            
            if health.broken_partitions:
                print(f"   🔴 Broken partitions: {health.broken_partitions}")
            
            print(f"   📝 Partition Details:")
            for partition in health.partition_details:
                status = "✅" if partition.is_healthy else "❌"
                leader_info = f"leader={partition.leader}" if partition.leader is not None else "NO LEADER"
                isr_info = f"ISR={len(partition.in_sync_replicas)}/{len(partition.replicas)}"
                
                print(f"      {status} Partition {partition.partition}: {leader_info}, {isr_info}")
                
                if partition.error_message:
                    print(f"         💥 Error: {partition.error_message}")
                if partition.last_test_success:
                    success_time = datetime.fromtimestamp(partition.last_test_success)
                    print(f"         ✅ Last successful delivery: {success_time.strftime('%H:%M:%S')}")
        
        # Print recommendations
        recommendations = self.generate_fix_recommendations(topic_health)
        if recommendations:
            print("\n" + "="*80)
            print("🔧 RECOMMENDED ACTIONS")
            print("="*80)
            for rec in recommendations:
                print(rec)
        
        print("\n" + "="*80)
    
    def continuous_monitor(self, interval: int = 30):
        """Continuously monitor partition health."""
        logger.info(f"🔍 Starting continuous monitoring (interval: {interval}s)")
        logger.info("Press Ctrl+C to stop")
        
        try:
            while True:
                logger.info("\n" + "="*50)
                logger.info(f"🔍 Health check at {datetime.now().strftime('%H:%M:%S')}")
                
                topic_health = self.test_all_partitions(self.topics_to_check)
                
                # Quick summary
                issues = []
                for topic_name, health in topic_health.items():
                    if health.overall_health != "HEALTHY":
                        issues.append(f"{topic_name}({health.overall_health})")
                
                if issues:
                    logger.warning(f"⚠️ Issues detected: {', '.join(issues)}")
                else:
                    logger.info("✅ All topics healthy")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Monitoring stopped by user")

def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Kafka Partition Leadership Diagnostic and Fix Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fix_partition_leadership.py --check
  python fix_partition_leadership.py --test-delivery
  python fix_partition_leadership.py --fix
  python fix_partition_leadership.py --monitor --interval 60
        """
    )
    
    parser.add_argument(
        '--servers', 
        default='localhost:9092',
        help='Kafka bootstrap servers (default: localhost:9092)'
    )
    
    parser.add_argument(
        '--topics',
        nargs='+',
        default=['ninja-results', 'ninja-tasks'],
        help='Topics to check (default: ninja-results ninja-tasks)'
    )
    
    parser.add_argument(
        '--check',
        action='store_true',
        help='Perform health check only (metadata analysis)'
    )
    
    parser.add_argument(
        '--test-delivery',
        action='store_true',
        help='Test actual message delivery to all partitions'
    )
    
    parser.add_argument(
        '--fix',
        action='store_true', 
        help='Attempt automatic fixes (limited functionality)'
    )
    
    parser.add_argument(
        '--monitor',
        action='store_true',
        help='Continuous monitoring mode'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=30,
        help='Monitoring interval in seconds (default: 30)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Default action if none specified
    if not any([args.check, args.test_delivery, args.fix, args.monitor]):
        args.check = True
        args.test_delivery = True
    
    try:
        with KafkaPartitionFixer(args.servers) as fixer:
            fixer.topics_to_check = args.topics
            
            if args.monitor:
                fixer.continuous_monitor(args.interval)
            else:
                if args.check or args.test_delivery:
                    if args.test_delivery:
                        topic_health = fixer.test_all_partitions(args.topics)
                    else:
                        topic_health = fixer.get_topic_metadata(args.topics)
                    
                    fixer.print_health_report(topic_health)
                
                if args.fix:
                    logger.info("🔧 Running automatic fixes...")
                    # Fix logic would go here
                    logger.warning("🚧 Automatic fixes not fully implemented yet")
                    logger.info("💡 Please follow the recommendations in the report above")
    
    except KeyboardInterrupt:
        logger.info("\n🛑 Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Operation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()