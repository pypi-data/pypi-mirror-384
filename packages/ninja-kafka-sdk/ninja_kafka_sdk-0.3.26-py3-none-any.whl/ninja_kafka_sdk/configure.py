#!/usr/bin/env python3
"""
Ninja Kafka SDK Configuration Utility

Easy way to configure Kafka providers for different environments.

Usage:
    python configure.py --help
    python configure.py show
    python configure.py set-local localhost:9093
    python configure.py set-stage stage-msk.amazonaws.com:9092
    python configure.py set-confluent pkc-xxx.confluent.cloud:9092
"""

import os
import argparse
from typing import Dict, Optional


class KafkaConfigManager:
    """Utility to manage Kafka configuration."""
    
    def __init__(self):
        self.env_vars = {
            'local': 'KAFKA_LOCAL_SERVERS',
            'dev': 'KAFKA_DEV_SERVERS', 
            'stage': 'KAFKA_STAGE_SERVERS',
            'prod': 'KAFKA_PROD_SERVERS',
            'msk': 'KAFKA_MSK_SERVERS',
            'confluent': 'KAFKA_CONFLUENT_SERVERS',
            'docker': 'KAFKA_DOCKER_SERVERS',
            'explicit': 'KAFKA_BOOTSTRAP_SERVERS'
        }
    
    def show_config(self):
        """Show current configuration."""
        print("🔧 CURRENT KAFKA CONFIGURATION")
        print("=" * 50)
        
        # Show environment variables
        print("\n📝 Environment Variables:")
        found_any = False
        for name, env_var in self.env_vars.items():
            value = os.getenv(env_var)
            if value:
                print(f"  ✅ {env_var} = {value}")
                found_any = True
        
        if not found_any:
            print("  ℹ️  No Kafka environment variables set (using defaults)")
        
        # Show what each environment would use
        print("\n🌍 Environment Resolution:")
        try:
            from ninja_kafka_sdk.config import NinjaKafkaConfig
            for env in ['local', 'dev', 'stage', 'prod']:
                try:
                    config = NinjaKafkaConfig(environment=env)
                    servers = config.kafka_servers
                    broker_count = len(servers.split(','))
                    provider = self._detect_provider(servers)
                    print(f"  {env:>5}: {provider} ({broker_count} brokers)")
                    print(f"         {servers}")
                except Exception as e:
                    print(f"  {env:>5}: Error - {e}")
        except ImportError:
            print("  ⚠️  SDK not available in current directory")
    
    def _detect_provider(self, servers: str) -> str:
        """Detect Kafka provider from server string."""
        if 'localhost' in servers:
            return 'Local'
        elif 'confluent.cloud' in servers:
            return 'Confluent Cloud'
        elif 'amazonaws.com' in servers:
            return 'AWS MSK'
        elif 'kafka-dev' in servers:
            return 'Docker/Dev'
        else:
            return 'Custom'
    
    def set_config(self, config_type: str, servers: str):
        """Set configuration for a specific type."""
        if config_type not in self.env_vars:
            print(f"❌ Invalid config type: {config_type}")
            print(f"   Valid types: {', '.join(self.env_vars.keys())}")
            return False
        
        env_var = self.env_vars[config_type]
        os.environ[env_var] = servers
        
        print(f"✅ Configuration set:")
        print(f"   {env_var} = {servers}")
        print(f"\n💡 To make permanent, add to your .env file:")
        print(f"   export {env_var}='{servers}'")
        
        return True
    
    def test_connection(self, environment: str = None):
        """Test connection to configured Kafka."""
        print(f"🧪 Testing Kafka connection...")
        
        try:
            from ninja_kafka_sdk import NinjaClient
            
            if environment:
                client = NinjaClient(environment=environment)
                print(f"   Environment: {environment}")
            else:
                client = NinjaClient()
                print(f"   Environment: {client.config.environment} (auto-detected)")
            
            print(f"   Servers: {client.config.kafka_servers}")
            print(f"   Consumer Group: {client.config.consumer_group}")
            print(f"   Topics: {client.config.tasks_topic} → {client.config.results_topic}")
            
            # Try to create producer (this validates connection)
            client._start_producer()
            print("✅ Connection successful!")
            client.stop()
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
        
        return True


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Ninja Kafka SDK Configuration Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s show                              # Show current configuration
  %(prog)s set-local localhost:9093          # Set local Kafka port
  %(prog)s set-stage stage-msk:9092          # Set stage MSK cluster
  %(prog)s set-prod prod-msk-1:9092,prod-msk-2:9092  # Set prod cluster
  %(prog)s set-confluent pkc-xxx.confluent.cloud:9092  # Use Confluent
  %(prog)s test                              # Test current configuration
  %(prog)s test --env stage                  # Test specific environment
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Show command
    subparsers.add_parser('show', help='Show current configuration')
    
    # Set commands
    for config_type in ['local', 'dev', 'stage', 'prod', 'msk', 'confluent', 'docker', 'explicit']:
        set_parser = subparsers.add_parser(f'set-{config_type}', help=f'Set {config_type} servers')
        set_parser.add_argument('servers', help='Comma-separated list of broker:port')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test Kafka connection')
    test_parser.add_argument('--env', help='Test specific environment')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = KafkaConfigManager()
    
    if args.command == 'show':
        manager.show_config()
    
    elif args.command.startswith('set-'):
        config_type = args.command[4:]  # Remove 'set-' prefix
        manager.set_config(config_type, args.servers)
    
    elif args.command == 'test':
        manager.test_connection(args.env)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()