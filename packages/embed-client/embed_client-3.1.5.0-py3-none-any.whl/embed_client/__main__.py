#!/usr/bin/env python3
"""
Main entry point for embed-client CLI.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
