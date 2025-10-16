#!/usr/bin/env python3
"""
Advanced usage scenarios for versionIO.

This script demonstrates more complex use cases including
concurrent access, batch operations, and error handling.
"""

import json
import csv
import tempfile
import time
from pathlib import Path
from datetime import datetime

from versionio import open, VersionedFile, VersionPolicy
from versionio.exceptions import VersionNotFound


def example_json_config_management():
    """Manage JSON configuration files with version history."""
    print("=== JSON Configuration Management ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "app_config.json"
        
        # Initial configuration
        config = {
            "app_name": "MyApp",
            "version": "1.0.0",
            "settings": {
                "debug": False,
                "timeout": 30,
                "max_connections": 100
            }
        }
        
        # Save initial config
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print("Saved initial configuration")
        
        # Simulate configuration updates
        vf = VersionedFile(config_file)
        
        # Update 1: Enable debug mode
        time.sleep(0.1)
        config["settings"]["debug"] = True
        config["updated_at"] = datetime.now().isoformat()
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print("Enabled debug mode")
        
        # Update 2: Change timeout
        time.sleep(0.1)
        config["settings"]["timeout"] = 60
        config["updated_at"] = datetime.now().isoformat()
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print("Updated timeout to 60")
        
        # Update 3: Increase connections
        time.sleep(0.1)
        config["settings"]["max_connections"] = 200
        config["updated_at"] = datetime.now().isoformat()
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print("Increased max connections to 200")
        
        # Show version history
        print("\n=== Configuration History ===")
        versions = vf.versions()
        for i, version in enumerate(versions):
            print(f"\nVersion {i} ({version.timestamp}):")
            content = vf.read(version)
            config_data = json.loads(content)
            settings = config_data.get("settings", {})
            print(f"  Debug: {settings.get('debug')}")
            print(f"  Timeout: {settings.get('timeout')}")
            print(f"  Max connections: {settings.get('max_connections')}")
        
        print()


def example_csv_data_updates():
    """Handle CSV file updates with automatic versioning."""
    print("=== CSV Data Management ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_file = Path(tmpdir) / "sales_data.csv"
        
        # Keep last 5 versions of sales data
        policy = VersionPolicy(max_versions=5)
        
        # Initial data
        print("Creating initial sales data...")
        with open(csv_file, 'w', newline='', policy=policy) as f:
            writer = csv.writer(f)
            writer.writerow(['Date', 'Product', 'Quantity', 'Revenue'])
            writer.writerow(['2024-01-01', 'Widget A', 10, 1000])
            writer.writerow(['2024-01-02', 'Widget B', 5, 750])
        
        # Add more data over time
        for day in range(3, 8):
            time.sleep(0.1)
            with open(csv_file, 'a', newline='', policy=policy) as f:
                writer = csv.writer(f)
                writer.writerow([f'2024-01-{day:02d}', 'Widget A', day * 2, day * 200])
            print(f"Added data for day {day}")
        
        # Show how many versions are kept
        versions_dir = Path(tmpdir) / ".versions" / "sales_data.csv"
        if versions_dir.exists():
            backups = list(versions_dir.glob("*.csv"))
            print(f"\nKept {len(backups)} backup version(s) (policy max: 5)")
        
        # Read current data
        print("\nCurrent data rows:")
        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            row_count = sum(1 for row in reader) - 1  # Subtract header
            print(f"  Total rows: {row_count}")
        
        print()


def example_safe_file_replacement():
    """Safely replace file contents with rollback capability."""
    print("=== Safe File Replacement ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        important_file = Path(tmpdir) / "critical_data.txt"
        vf = VersionedFile(important_file)
        
        # Create important file
        original_content = "This is critical data that must not be lost!"
        vf.write(original_content)
        print(f"Created file with critical data")
        
        # Attempt a risky update
        time.sleep(0.1)
        try:
            print("\nAttempting risky update...")
            new_content = "New experimental data"
            vf.write(new_content)
            
            # Simulate validation failure
            if len(new_content) < len(original_content) / 2:
                raise ValueError("New content seems corrupted (too short)!")
            
            print("Update successful")
            
        except ValueError as e:
            print(f"Update failed: {e}")
            print("Rolling back to previous version...")
            
            # Restore previous version
            versions = vf.versions()
            if versions:
                vf.restore(versions[0])
                print("Rollback complete!")
                print(f"Current content: '{vf.read()}'")
        
        print()


def example_migration_tracking():
    """Track database schema migrations with versioning."""
    print("=== Migration Tracking ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        migration_file = Path(tmpdir) / "schema_version.txt"
        vf = VersionedFile(migration_file)
        
        # Track schema versions
        migrations = [
            "v1.0.0 - Initial schema",
            "v1.1.0 - Added user_preferences table",
            "v1.2.0 - Added index on user_id",
            "v2.0.0 - Major refactoring of auth tables",
            "v2.1.0 - Added audit_log table"
        ]
        
        print("Applying migrations...")
        for migration in migrations:
            time.sleep(0.1)
            vf.write(migration)
            print(f"  Applied: {migration}")
        
        # Show migration history
        print("\n=== Migration History ===")
        versions = vf.versions()
        print(f"Total migrations tracked: {len(versions) + 1}")
        
        # Show ability to check what was in each version
        for i, version in enumerate(versions[:3]):  # Show first 3
            content = vf.read(version)
            print(f"  Version {i}: {content}")
        
        print(f"\nCurrent schema: {vf.read()}")
        print()


def example_error_recovery():
    """Demonstrate error handling and recovery."""
    print("=== Error Handling Example ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "data.txt"
        vf = VersionedFile(file_path)
        
        # Create some versions
        vf.write("Version 1")
        time.sleep(0.1)
        vf.write("Version 2")
        
        # Try to restore non-existent version
        print("Attempting to restore non-existent version...")
        fake_version_path = Path(tmpdir) / "fake.txt"
        
        try:
            from versionio.version import Version
            fake_version = Version(fake_version_path)
            vf.restore(fake_version)
        except VersionNotFound as e:
            print(f"✓ Caught expected error: {e}")
        
        # Try to read non-existent file
        print("\nAttempting to read non-existent file...")
        missing_file = VersionedFile(Path(tmpdir) / "missing.txt")
        
        try:
            content = missing_file.read()
        except FileNotFoundError as e:
            print(f"✓ Caught expected error: File not found")
        
        print("\n✓ Error handling works correctly")
        print()


if __name__ == "__main__":
    print("versionIO - Advanced Usage Scenarios\n")
    print("This script demonstrates advanced features and use cases.\n")
    
    example_json_config_management()
    example_csv_data_updates()
    example_safe_file_replacement()
    example_migration_tracking()
    example_error_recovery()
    
    print("=== Advanced Examples Complete ===")
    print("\nAdvanced Features Demonstrated:")
    print("• JSON configuration versioning")
    print("• CSV data management with retention")
    print("• Safe file replacement with rollback")
    print("• Migration tracking")
    print("• Error handling and recovery")