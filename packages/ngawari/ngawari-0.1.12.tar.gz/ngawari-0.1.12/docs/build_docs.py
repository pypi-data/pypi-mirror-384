#!/usr/bin/env python3
"""
Script to build and manage Ngawari documentation.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run a command and return the result."""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error running command: {cmd}")
            print(f"Error: {result.stderr}")
            return False
        print(result.stdout)
        return True
    except Exception as e:
        print(f"Exception running command: {cmd}")
        print(f"Error: {e}")
        return False


def build_docs():
    """Build the documentation."""
    print("Building documentation...")
    return run_command("make html", cwd="docs")


def clean_docs():
    """Clean the documentation build directory."""
    print("Cleaning documentation...")
    return run_command("make clean", cwd="docs")


def serve_docs():
    """Serve the documentation locally."""
    print("Serving documentation at http://localhost:8000")
    return run_command("make serve", cwd="docs")


def check_docs():
    """Check for documentation issues."""
    print("Checking documentation...")
    return run_command("make html", cwd="docs")


def main():
    parser = argparse.ArgumentParser(description="Build and manage Ngawari documentation")
    parser.add_argument("command", choices=["build", "clean", "serve", "check", "all"],
                       help="Command to run")
    
    args = parser.parse_args()
    
    # Ensure we're in the right directory
    if not os.path.exists("docs/conf.py"):
        print("Error: docs/conf.py not found. Please run this script from the project root.")
        sys.exit(1)
    
    if args.command == "build":
        success = build_docs()
    elif args.command == "clean":
        success = clean_docs()
    elif args.command == "serve":
        success = serve_docs()
    elif args.command == "check":
        success = check_docs()
    elif args.command == "all":
        success = clean_docs() and build_docs()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main() 