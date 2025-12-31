#!/usr/bin/env python3
"""
Container component for metadata update/verification.

This script runs metadata update/check inside a container.
It expects the repo workspace to be mounted at /workspace.
"""

import sys
from pathlib import Path

# Add workspace to path
sys.path.insert(0, "/workspace")

from scripts.update_graph_metadata import main as update_metadata_main


def main():
    """Run metadata update with --check flag."""
    # Override sys.argv to add --check flag
    original_argv = sys.argv
    sys.argv = ["update_metadata.py", "--check"]
    
    try:
        update_metadata_main()
    except SystemExit as e:
        sys.exit(e.code if e.code is not None else 0)
    finally:
        sys.argv = original_argv


if __name__ == "__main__":
    main()

