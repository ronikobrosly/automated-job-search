#!/usr/bin/env python3
"""
Database migration script for the automated job search system.
This script handles running migrations and database schema updates.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def run_alembic_command(command_args):
    """Run an alembic command in the correct directory"""
    data_dir = project_root / 'data'
    original_cwd = os.getcwd()
    
    try:
        os.chdir(data_dir)
        cmd = ['uv', 'run', 'alembic'] + command_args
        print(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Command completed successfully")
            if result.stdout:
                print(result.stdout)
        else:
            print("✗ Command failed:")
            if result.stderr:
                print(result.stderr)
            return False
            
    except Exception as e:
        print(f"✗ Error running command: {e}")
        return False
    finally:
        os.chdir(original_cwd)
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Database migration utility')
    parser.add_argument('action', choices=['upgrade', 'downgrade', 'current', 'history', 'heads'], 
                       help='Migration action to perform')
    parser.add_argument('revision', nargs='?', default='head', 
                       help='Target revision (default: head)')
    parser.add_argument('--sql', action='store_true', 
                       help='Show SQL that would be executed')
    
    args = parser.parse_args()
    
    print(f"Running database migration: {args.action}")
    print("=" * 50)
    
    # Build alembic command
    command_args = [args.action]
    
    if args.action in ['upgrade', 'downgrade']:
        command_args.append(args.revision)
    
    if args.sql:
        command_args.append('--sql')
    
    # Run the command
    success = run_alembic_command(command_args)
    
    if success:
        print(f"\n✅ Migration {args.action} completed successfully!")
    else:
        print(f"\n❌ Migration {args.action} failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()