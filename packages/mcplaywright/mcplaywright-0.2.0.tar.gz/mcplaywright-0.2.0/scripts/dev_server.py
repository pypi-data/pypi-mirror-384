#!/usr/bin/env python3
"""
Development server runner for MCPlaywright

Starts the FastMCP server with hot-reload and development-friendly settings.
"""

import os
import sys
from pathlib import Path

# Add src to path for development
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from mcplaywright.cli import main

if __name__ == "__main__":
    # Set development environment
    os.environ.setdefault("DEVELOPMENT_MODE", "true")
    os.environ.setdefault("LOG_LEVEL", "DEBUG")
    
    # Run the CLI with serve command and dev flag
    sys.argv = [
        "mcplaywright",
        "serve", 
        "--dev",
        "--log-level", "DEBUG",
        "--host", "0.0.0.0",
        "--port", "8000"
    ]
    
    main()