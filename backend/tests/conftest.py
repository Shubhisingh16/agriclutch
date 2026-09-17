"""
Pytest configuration and global fixtures for AgriClutch.
Ensures repository root and backend directory are present in sys.path.
"""

import os
import sys

# Ensure backend and repository root are on python sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
repo_root = os.path.abspath(os.path.join(backend_dir, ".."))

for p in (backend_dir, repo_root):
    if p not in sys.path:
        sys.path.insert(0, p)
