#!/usr/bin/env python3
"""
Setup script to configure the current MSK setup as the stage environment.

This extracts the current hardcoded MSK configuration and sets it up properly
as environment variables for the stage environment.
"""

import os
import subprocess
import sys


def setup_current_stage_config():
    """Set up current MSK configuration as stage environment."""
    
    # Current MSK configuration (extracted from old hardcoded values)
    current_msk_servers = (
        "b-1.browserninjaminimal.rkeiib.c7.kafka.us-west-2.amazonaws.com:9092,"
        "b-2.browserninjaminimal.rkeiib.c7.kafka.us-west-2.amazonaws.com:9092"
    )
    
    print("🔧 CONFIGURING CURRENT MSK AS STAGE ENVIRONMENT")
    print("=" * 55)
    
    print(f"\n📍 Current MSK Servers: {current_msk_servers}")
    print(f"📍 Setting as KAFKA_STAGE_SERVERS")
    
    # Set environment variable
    os.environ['KAFKA_STAGE_SERVERS'] = current_msk_servers
    
    print("\n✅ Configuration applied for current session")
    
    # Test the configuration
    print("\n🧪 Testing configuration...")
    try:
        from ninja_kafka_sdk.config import NinjaKafkaConfig
        
        config = NinjaKafkaConfig(environment='stage')
        print(f"✅ Stage servers: {config.kafka_servers}")
        print(f"✅ Environment: {config.environment}")
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False
    
    # Generate shell export commands
    print("\n💾 TO MAKE PERMANENT, add to your shell profile:")
    print(f"export KAFKA_STAGE_SERVERS='{current_msk_servers}'")
    
    # Generate .env file
    env_content = f"""# Ninja Kafka SDK Configuration
# Current MSK setup for stage environment
KAFKA_CONNECTION=stage
KAFKA_STAGE_SERVERS={current_msk_servers}

# For production, set up separate cluster:
# KAFKA_PROD_SERVERS=prod-msk-1:9092,prod-msk-2:9092,prod-msk-3:9092
"""
    
    env_file = "kafka_config.env"
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print(f"\n📄 Configuration saved to: {env_file}")
    print(f"   Load with: source {env_file}")
    
    return True


def show_migration_guide():
    """Show migration guide for different environments."""
    
    print("\n📚 ENVIRONMENT SETUP GUIDE")
    print("=" * 40)
    
    configs = {
        "Local Development": {
            "env_var": "KAFKA_LOCAL_SERVERS",
            "default": "localhost:9092",
            "example": "localhost:9092"
        },
        "Dev Environment": {
            "env_var": "KAFKA_DEV_SERVERS", 
            "default": "kafka-dev:9092",
            "example": "kafka-dev:9092"
        },
        "Stage Environment": {
            "env_var": "KAFKA_STAGE_SERVERS",
            "default": "⚠️  Must be configured",
            "example": "stage-msk-1:9092,stage-msk-2:9092"
        },
        "Production": {
            "env_var": "KAFKA_PROD_SERVERS",
            "default": "⚠️  Must be configured", 
            "example": "prod-msk-1:9092,prod-msk-2:9092,prod-msk-3:9092"
        }
    }
    
    for env_name, config in configs.items():
        print(f"\n🌍 {env_name}:")
        print(f"   Variable: {config['env_var']}")
        print(f"   Default:  {config['default']}")
        print(f"   Example:  export {config['env_var']}='{config['example']}'")


def main():
    """Main setup function."""
    if len(sys.argv) > 1 and sys.argv[1] == "--guide":
        show_migration_guide()
        return
    
    print("Setting up current MSK configuration...")
    
    if setup_current_stage_config():
        print("\n✅ Setup completed successfully!")
        
        # Show next steps
        print("\n🎯 NEXT STEPS:")
        print("1. Source the generated config file: source kafka_config.env")
        print("2. Set up separate production MSK cluster")
        print("3. Configure KAFKA_PROD_SERVERS for production environment")
        print("4. Test with: python -c 'from ninja_kafka_sdk import NinjaClient; NinjaClient()'")
        
        show_migration_guide()
    else:
        print("\n❌ Setup failed!")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())