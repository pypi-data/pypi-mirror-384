#!/usr/bin/env python3
"""
Basic usage examples for versionIO.

This script demonstrates the core features of versionIO including
automatic versioning, version listing, and restoration.
"""

from pathlib import Path
import tempfile
import time

# Import versionIO - drop-in replacement for open()
from versionio import open, VersionedFile, VersionPolicy


def example_simple_versioning():
    """Demonstrate basic automatic versioning."""
    print("=== Simple Versioning Example ===")
    
    # Use a temporary directory for the demo
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "config.json"
        
        # Write initial version
        with open(file_path, 'w') as f:
            f.write('{"setting": "value1", "debug": false}')
        print(f"Created file: {file_path}")
        
        # Update the file - automatic backup is created
        time.sleep(0.1)  # Small delay to ensure different timestamps
        with open(file_path, 'w') as f:
            f.write('{"setting": "value2", "debug": true}')
        print("Updated file (backup created automatically)")
        
        # Check versions directory
        versions_dir = Path(tmpdir) / ".versions" / "config.json"
        if versions_dir.exists():
            backups = list(versions_dir.glob("*.json"))
            print(f"Found {len(backups)} backup(s) in {versions_dir}")
            for backup in backups:
                print(f"  - {backup.name}: {backup.stat().st_size} bytes")
        
        print()


def example_versioned_file_class():
    """Demonstrate the VersionedFile high-level interface."""
    print("=== VersionedFile Class Example ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "document.txt"
        
        # Create a VersionedFile instance
        vf = VersionedFile(file_path)
        
        # Write multiple versions
        print("Creating multiple versions...")
        for i in range(1, 4):
            vf.write(f"Document version {i}\nUpdated on iteration {i}")
            time.sleep(0.1)
            print(f"  Created version {i}")
        
        # List all versions
        print("\nAvailable versions (newest first):")
        versions = vf.versions()
        for i, version in enumerate(versions):
            print(f"  {i}: {version.timestamp} - {version.size} bytes")
        
        # Read current content
        print("\nCurrent content:")
        print(f"  {vf.read()}")
        
        # Restore an older version
        if len(versions) > 0:
            print(f"\nRestoring to oldest version...")
            vf.restore(versions[-1])
            print(f"Restored content:")
            print(f"  {vf.read()}")
        
        print()


def example_retention_policy():
    """Demonstrate retention policy to limit number of backups."""
    print("=== Retention Policy Example ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "log.txt"
        
        # Create a policy that keeps only last 3 versions
        policy = VersionPolicy(max_versions=3)
        print("Using policy: max_versions=3")
        
        # Create many versions
        print("\nCreating 10 versions...")
        for i in range(10):
            with open(file_path, 'w', policy=policy) as f:
                f.write(f"Log entry {i}")
            time.sleep(0.01)
        
        # Check how many backups were kept
        versions_dir = Path(tmpdir) / ".versions" / "log.txt"
        if versions_dir.exists():
            backups = sorted(versions_dir.glob("*.txt"))
            print(f"\nKept {len(backups)} backup(s) (policy limit: 3)")
            for backup in backups:
                content = backup.read_text()
                print(f"  - {backup.name}: '{content}'")
        
        print()


def example_disable_versioning():
    """Demonstrate how to disable versioning for specific files."""
    print("=== Disable Versioning Example ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "temp.txt"
        
        # Write without versioning
        print("Writing with versioning=False...")
        with open(file_path, 'w', versioning=False) as f:
            f.write("Temporary content - no backup needed")
        
        # Update without versioning
        with open(file_path, 'w', versioning=False) as f:
            f.write("Updated temporary content")
        
        # Check that no versions were created
        versions_dir = Path(tmpdir) / ".versions"
        if not versions_dir.exists():
            print("✓ No .versions directory created (as expected)")
        else:
            print("✗ .versions directory exists (unexpected)")
        
        print()


def example_append_mode():
    """Demonstrate versioning with append mode."""
    print("=== Append Mode Example ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "activity.log"
        
        # Create initial file
        with open(file_path, 'w') as f:
            f.write("=== Activity Log ===\n")
        print(f"Created log file: {file_path}")
        
        # Append in first session (creates backup)
        time.sleep(0.1)
        with open(file_path, 'a') as f:
            f.write("Session 1: User logged in\n")
            f.write("Session 1: Action performed\n")
        print("Appended session 1 (backup created)")
        
        # Append in second session (creates another backup)
        time.sleep(0.1)
        with open(file_path, 'a') as f:
            f.write("Session 2: User logged out\n")
        print("Appended session 2 (backup created)")
        
        # Show backups
        versions_dir = Path(tmpdir) / ".versions" / "activity.log"
        if versions_dir.exists():
            backups = list(versions_dir.glob("*.log"))
            print(f"\nCreated {len(backups)} backup(s)")
        
        # Show final content
        print("\nFinal file content:")
        print(file_path.read_text())
        
        print()


if __name__ == "__main__":
    print("versionIO - Basic Usage Examples\n")
    print("This script demonstrates the core features of versionIO.\n")
    
    example_simple_versioning()
    example_versioned_file_class()
    example_retention_policy()
    example_disable_versioning()
    example_append_mode()
    
    print("=== Examples Complete ===")
    print("\nKey Takeaways:")
    print("• versionIO.open() is a drop-in replacement for built-in open()")
    print("• Backups are created automatically before write operations")
    print("• Use VersionedFile class for high-level operations")
    print("• Set max_versions in VersionPolicy to limit backup count")
    print("• Disable versioning with versioning=False when needed")