#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entry point for python -m cammy
"""

import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())
