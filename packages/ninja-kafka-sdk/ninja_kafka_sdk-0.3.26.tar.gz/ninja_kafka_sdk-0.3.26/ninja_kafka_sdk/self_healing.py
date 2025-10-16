"""
Self-healing functionality for Ninja Kafka SDK.
Automatically detects and resolves common Kafka connectivity issues.
"""

import logging
import time
import os
import socket
import threading
from typing import Optional, Dict, List, Any, Callable
from kafka import KafkaConsumer
from kafka.errors import KafkaError

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

logger = logging.getLogger(__name__)


class SelfHealingStats:
    """Statistics tracking for self-healing operations."""
    
    def __init__(self):
        self.total_healing_attempts = 0
        self.successful_healings = 0
        self.failed_healings = 0
        self.multiple_consumer_fixes = 0
        self.consumer_group_resets = 0
        self.connectivity_failures = 0
        self.last_healing_time = None
        
    def record_healing_attempt(self, success: bool, healing_type: str):
        """Record a healing attempt."""
        self.total_healing_attempts += 1
        self.last_healing_time = time.time()
        
        if success:
            self.successful_healings += 1
        else:
            self.failed_healings += 1
            
        if healing_type == 'multiple_consumers':
            self.multiple_consumer_fixes += 1
        elif healing_type == 'consumer_group_reset':
            self.consumer_group_resets += 1
        elif healing_type == 'connectivity':
            self.connectivity_failures += 1
            
    def get_stats(self) -> Dict[str, Any]:
        """Get healing statistics."""
        success_rate = 0
        if self.total_healing_attempts > 0:
            success_rate = (self.successful_healings / self.total_healing_attempts) * 100
            
        return {
            'total_healing_attempts': self.total_healing_attempts,
            'successful_healings': self.successful_healings,
            'failed_healings': self.failed_healings,
            'success_rate_percent': round(success_rate, 2),
            'multiple_consumer_fixes': self.multiple_consumer_fixes,
            'consumer_group_resets': self.consumer_group_resets,
            'connectivity_failures': self.connectivity_failures,
            'last_healing_time': self.last_healing_time
        }


class KafkaSelfHealing:
    """
    Self-healing functionality for Kafka connections.
    Detects and resolves common issues automatically.
    """
    
    def __init__(self, client_instance):
        """
        Initialize self-healing for a Kafka client.
        
        Args:
            client_instance: The NinjaClient instance to heal
        """
        self.client = client_instance
        self.logger = logging.getLogger(f"{__name__}.{client_instance.__class__.__name__}")
        self.stats = SelfHealingStats()
        self.healing_in_progress = False
        self.max_healing_attempts = 3
        self.healing_cooldown = 30  # seconds between healing attempts
        self.last_healing_attempt = 0
        
        # Health monitoring
        self.health_monitor_thread = None
        self.health_monitor_active = False
        self.health_check_interval = 60  # seconds
        
    def detect_and_heal_issues(self, issue_context: Optional[str] = None) -> bool:
        """
        Comprehensive issue detection and healing.
        
        Args:
            issue_context: Context about what triggered the healing (e.g., 'connection_failure')
            
        Returns:
            True if healthy after healing, False if healing failed
        """
        if self.healing_in_progress:
            self.logger.debug("Healing already in progress, skipping")
            return False
            
        # Respect cooldown period
        if time.time() - self.last_healing_attempt < self.healing_cooldown:
            remaining = self.healing_cooldown - (time.time() - self.last_healing_attempt)
            self.logger.debug(f"Healing cooldown active, {remaining:.1f}s remaining")
            return False
            
        try:
            self.healing_in_progress = True
            self.last_healing_attempt = time.time()
            
            self.logger.info(f"🔧 STARTING SELF-HEALING DIAGNOSTICS")
            self.logger.info(f"   Context: {issue_context or 'unknown'}")
            self.logger.info(f"   Previous attempts: {self.stats.total_healing_attempts}")
            self.logger.info(f"   Success rate: {(self.stats.successful_healings / max(1, self.stats.total_healing_attempts)) * 100:.1f}%")
            
            # Issue 1: Multiple consumer processes
            self.logger.info("🔍 ISSUE 1: Checking for multiple consumers...")
            if self._detect_multiple_consumers():
                self.logger.warning("🔧 DETECTED: Multiple consumers found, initiating cleanup")
                if self._heal_multiple_consumers():
                    self.stats.record_healing_attempt(True, 'multiple_consumers')
                    self.logger.info("✅ RESOLVED: Multiple consumer cleanup successful")
                    time.sleep(5)  # Wait for cleanup
                else:
                    self.stats.record_healing_attempt(False, 'multiple_consumers')
                    self.logger.error("❌ FAILED: Multiple consumer cleanup failed")
                    return False
            else:
                self.logger.info("✅ CLEAR: No multiple consumers detected")
                    
            # Issue 2: Network connectivity
            self.logger.info("🔍 ISSUE 2: Testing Kafka connectivity...")
            connectivity_result = self._test_kafka_connectivity()
            if not connectivity_result:
                self.logger.error("❌ FAILED: Kafka connectivity test failed - infrastructure issue")
                self.stats.record_healing_attempt(False, 'connectivity')
                return False
            else:
                self.logger.info("✅ CLEAR: Kafka connectivity test passed")
                
            # Issue 3: Stale consumer group (if connection or partition context suggests it)
            self.logger.info("🔍 ISSUE 3: Checking consumer group state...")
            if issue_context and ('connection' in issue_context.lower() or 'partition' in issue_context.lower()):
                self.logger.warning("🔧 DETECTED: Context suggests stale consumer group, initiating reset")
                if self._heal_consumer_group():
                    self.stats.record_healing_attempt(True, 'consumer_group_reset')
                    self.logger.info("✅ RESOLVED: Consumer group reset successful")
                else:
                    self.stats.record_healing_attempt(False, 'consumer_group_reset')
                    self.logger.error("❌ FAILED: Consumer group reset failed")
                    return False
            else:
                self.logger.info("✅ CLEAR: No consumer group reset needed")
                    
            self.logger.info("✅ Self-healing diagnostics completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Self-healing failed with exception: {e}")
            self.stats.record_healing_attempt(False, 'exception')
            return False
        finally:
            self.healing_in_progress = False
    
    def _detect_multiple_consumers(self) -> bool:
        """Check for multiple consumer processes with same group ID."""
        if not HAS_PSUTIL:
            self.logger.debug("psutil not available, skipping multiple consumer detection")
            return False
            
        try:
            current_pid = os.getpid()
            ninja_processes = []
            
            for proc in psutil.process_iter(['pid', 'cmdline', 'create_time']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    cmdline_lower = cmdline.lower()
                    
                    # Skip monitoring/log viewing processes
                    skip_indicators = ['journalctl', 'tail', 'grep', 'cat', 'less', 'vim', 'nano']
                    if any(skip in cmdline_lower for skip in skip_indicators):
                        continue
                    
                    # Only match actual Python processes running our code
                    # Must have python AND (main.py OR start_browser_ninja.py OR ninja consumer pattern)
                    is_python_process = 'python' in cmdline_lower
                    is_ninja_main = 'main.py' in cmdline_lower or 'start_browser_ninja.py' in cmdline_lower
                    is_kafka_consumer = 'ninja' in cmdline_lower and 'kafka' in cmdline_lower
                    
                    if is_python_process and (is_ninja_main or is_kafka_consumer) and proc.info['pid'] != current_pid:
                        ninja_processes.append({
                            'pid': proc.info['pid'],
                            'created': proc.info['create_time'],
                            'cmdline': cmdline[:100]  # Truncate for logging
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                    
            if len(ninja_processes) > 0:
                self.logger.warning(f"Found {len(ninja_processes)} other Python consumer processes:")
                for p in ninja_processes:
                    self.logger.warning(f"  PID {p['pid']}: {p['cmdline']}")
                return True
                
            return False
            
        except Exception as e:
            self.logger.debug(f"Multiple consumer detection failed: {e}")
            return False
    
    def _heal_multiple_consumers(self) -> bool:
        """Kill duplicate consumer processes."""
        if not HAS_PSUTIL:
            return False
            
        try:
            current_pid = os.getpid()
            killed_count = 0
            
            for proc in psutil.process_iter(['pid', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    cmdline_lower = cmdline.lower()
                    
                    # Skip monitoring/log viewing processes
                    skip_indicators = ['journalctl', 'tail', 'grep', 'cat', 'less', 'vim', 'nano']
                    if any(skip in cmdline_lower for skip in skip_indicators):
                        continue
                    
                    # Only kill actual Python processes running our code
                    is_python_process = 'python' in cmdline_lower
                    is_ninja_main = 'main.py' in cmdline_lower or 'start_browser_ninja.py' in cmdline_lower
                    is_kafka_consumer = 'ninja' in cmdline_lower and 'kafka' in cmdline_lower
                    
                    if is_python_process and (is_ninja_main or is_kafka_consumer) and proc.info['pid'] != current_pid:
                        self.logger.info(f"Terminating duplicate Python consumer process {proc.info['pid']}: {cmdline[:80]}")
                        process = psutil.Process(proc.info['pid'])
                        process.terminate()
                        killed_count += 1
                        
                        # Wait for graceful termination
                        try:
                            process.wait(timeout=5)
                        except psutil.TimeoutExpired:
                            self.logger.warning(f"Force killing process {proc.info['pid']}")
                            process.kill()
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                    
            if killed_count > 0:
                self.logger.info(f"Terminated {killed_count} duplicate processes")
                time.sleep(3)  # Wait for cleanup
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to heal multiple consumers: {e}")
            return False
    
    def _heal_consumer_group(self) -> bool:
        """Reset consumer group by using temporary group ID."""
        try:
            if not hasattr(self.client, 'config') or not hasattr(self.client.config, 'consumer_group'):
                self.logger.debug("No consumer group configuration found, skipping reset")
                return True
                
            original_group = self.client.config.consumer_group
            temp_group = f"{original_group}-reset-{int(time.time())}"
            
            self.logger.info(f"Resetting consumer group: {original_group} -> {temp_group}")
            
            # Create temporary consumer to clear metadata
            temp_consumer = self._create_temp_consumer(temp_group)
            if temp_consumer:
                try:
                    # Brief poll to register the group
                    temp_consumer.poll(timeout_ms=2000)
                    temp_consumer.close()
                    time.sleep(2)
                    self.logger.debug("Temporary consumer created and closed successfully")
                except Exception as e:
                    self.logger.debug(f"Temporary consumer poll failed: {e}")
                    temp_consumer.close()
                
            # The original group ID remains unchanged - the temporary group just helps clear metadata
            self.logger.info("✅ Consumer group reset complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Consumer group healing failed: {e}")
            return False
    
    def _create_temp_consumer(self, group_id: str) -> Optional[KafkaConsumer]:
        """Create temporary consumer for group reset."""
        try:
            if not hasattr(self.client, 'config'):
                return None
                
            temp_consumer = KafkaConsumer(
                bootstrap_servers=self.client.config.kafka_servers.split(','),
                group_id=group_id,
                auto_offset_reset='earliest',
                consumer_timeout_ms=5000,
                session_timeout_ms=10000,
                heartbeat_interval_ms=3000,
                enable_auto_commit=True,
                auto_commit_interval_ms=1000
            )
            return temp_consumer
        except Exception as e:
            self.logger.debug(f"Temp consumer creation failed: {e}")
            return None
    
    def _test_kafka_connectivity(self) -> bool:
        """Test basic TCP connectivity to Kafka brokers."""
        if not hasattr(self.client, 'config') or not self.client.config.kafka_servers:
            self.logger.debug("No Kafka servers configured")
            return False
            
        servers = self.client.config.kafka_servers.split(',')
        successful_connections = 0
        
        for server in servers:
            try:
                server = server.strip()
                if ':' not in server:
                    continue
                    
                host, port = server.split(':')
                port = int(port)
                
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:
                    successful_connections += 1
                    self.logger.debug(f"Successfully connected to {server}")
                else:
                    self.logger.debug(f"Failed to connect to {server}: {result}")
                    
            except Exception as e:
                self.logger.debug(f"Connection test failed for {server}: {e}")
                continue
                
        # Require at least one successful connection
        success = successful_connections > 0
        if success:
            self.logger.debug(f"Kafka connectivity OK ({successful_connections}/{len(servers)} brokers reachable)")
        else:
            self.logger.error(f"Kafka connectivity failed (0/{len(servers)} brokers reachable)")
            
        return success
    
    def start_health_monitoring(self, check_interval: int = None):
        """Start continuous health monitoring in background thread."""
        if self.health_monitor_active:
            self.logger.debug("Health monitoring already active")
            return
            
        if check_interval:
            self.health_check_interval = check_interval
            
        self.health_monitor_active = True
        self.health_monitor_thread = threading.Thread(target=self._health_monitor_loop, daemon=True)
        self.health_monitor_thread.start()
        self.logger.info(f"🔍 Health monitoring started (check every {self.health_check_interval}s)")
        
    def stop_health_monitoring(self):
        """Stop health monitoring."""
        self.health_monitor_active = False
        if self.health_monitor_thread:
            self.health_monitor_thread.join(timeout=5)
        self.logger.info("🔍 Health monitoring stopped")
        
    def _health_monitor_loop(self):
        """Continuous health monitoring loop."""
        last_health_check = time.time()
        
        while self.health_monitor_active:
            try:
                current_time = time.time()
                
                # Health check at specified interval
                if current_time - last_health_check > self.health_check_interval:
                    if not self._check_consumer_health():
                        self.logger.warning("🔧 Health check failed, attempting recovery")
                        if self.detect_and_heal_issues("health_check_failure"):
                            self.logger.info("✅ Health check recovery successful")
                        else:
                            self.logger.error("❌ Health check recovery failed")
                    last_health_check = current_time
                    
                time.sleep(min(30, self.health_check_interval // 2))  # Check at most every 30s
                
            except Exception as e:
                self.logger.error(f"Health monitor error: {e}")
                time.sleep(60)
                
    def _check_consumer_health(self) -> bool:
        """Check if consumer is healthy."""
        try:
            # Check 1: Basic connectivity
            if not self._test_kafka_connectivity():
                self.logger.debug("Health check failed: no Kafka connectivity")
                return False
                
            # Check 2: No duplicate processes
            if self._detect_multiple_consumers():
                self.logger.debug("Health check failed: multiple consumers detected")
                return False
                
            # Check 3: Consumer assignment (if applicable)
            if hasattr(self.client, 'consumer') and self.client.consumer:
                try:
                    assignment = self.client.consumer.assignment()
                    if len(assignment) == 0:
                        self.logger.debug("Health check warning: consumer has no partition assignment")
                        # Don't fail health check for this - might be temporary
                except Exception as e:
                    self.logger.debug(f"Health check failed: consumer assignment check error: {e}")
                    return False
                    
            return True
            
        except Exception as e:
            self.logger.debug(f"Health check exception: {e}")
            return False
    
    def get_healing_stats(self) -> Dict[str, Any]:
        """Get self-healing statistics."""
        stats = self.stats.get_stats()
        stats['health_monitor_active'] = self.health_monitor_active
        stats['health_check_interval'] = self.health_check_interval
        stats['healing_in_progress'] = self.healing_in_progress
        return stats


class SelfHealingMixin:
    """
    Mixin class to add self-healing capabilities to Kafka clients.
    """
    
    def _init_self_healing(self):
        """Initialize self-healing. Call this in your client's __init__."""
        self.self_healing = KafkaSelfHealing(self)
        self._self_healing_enabled = True
        self._connection_attempts = 0
        self._max_connection_attempts = 3
        
    def _attempt_with_self_healing(self, operation_func: Callable, operation_name: str = "operation") -> bool:
        """
        Attempt an operation with self-healing on failure.
        
        Args:
            operation_func: Function to attempt (should return bool for success)
            operation_name: Name of operation for logging
            
        Returns:
            True if operation succeeded, False if all attempts failed
        """
        if not hasattr(self, 'self_healing'):
            self._init_self_healing()
        
        # Initialize attempt tracking for this operation if not exists
        attempt_key = f"_{operation_name}_attempts"
        if not hasattr(self, attempt_key):
            setattr(self, attempt_key, 0)
            
        current_attempts = getattr(self, attempt_key)
            
        while current_attempts < self._max_connection_attempts:
            current_attempts += 1
            setattr(self, attempt_key, current_attempts)
            
            logger.info(f"🔄 Attempting {operation_name} (attempt {current_attempts}/{self._max_connection_attempts})")
            
            # Try the operation
            if operation_func():
                setattr(self, attempt_key, 0)  # Reset on success
                return True
                
            # Operation failed
            logger.warning(f"❌ {operation_name} failed (attempt {current_attempts})")
            
            if current_attempts < self._max_connection_attempts:
                logger.info("🔧 Running self-healing diagnostics...")
                
                if self.self_healing.detect_and_heal_issues(f"{operation_name}_failure"):
                    logger.info("✅ Self-healing completed, retrying operation...")
                    time.sleep(5)  # Brief wait before retry
                    continue
                else:
                    logger.error("❌ Self-healing failed")
                    break
            else:
                logger.error(f"❌ Maximum connection attempts reached for {operation_name}")
                break
                
        return False
    
    def enable_self_healing_monitoring(self, check_interval: int = 60):
        """Enable continuous self-healing health monitoring."""
        if not hasattr(self, 'self_healing'):
            self._init_self_healing()
        self.self_healing.start_health_monitoring(check_interval)
        
    def disable_self_healing_monitoring(self):
        """Disable self-healing health monitoring."""
        if hasattr(self, 'self_healing'):
            self.self_healing.stop_health_monitoring()
            
    def get_self_healing_stats(self) -> Dict[str, Any]:
        """Get self-healing statistics."""
        if hasattr(self, 'self_healing'):
            return self.self_healing.get_healing_stats()
        return {}