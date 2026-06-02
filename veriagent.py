#!/usr/bin/env python3
"""
VeriAgent Command Line Interface - Direct Python Script Version

This file provides a direct Python script interface for users who prefer running:
    python veriagent.py [args...]

It imports and calls the main CLI function from veriagent.cli, providing
the same functionality as the `veriagent` command installed via pip.
"""

import os
import sys

# Add the current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Import and use the main CLI function
from veriagent.cli import main

if __name__ == "__main__":
    main()
