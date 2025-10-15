#!/usr/bin/env python3
"""
Enable running mahoraga-mcp as a module: python -m mahoraga_mcp
This allows the package to work in any Python environment where it's installed.
"""

from .server import main

if __name__ == "__main__":
    main()