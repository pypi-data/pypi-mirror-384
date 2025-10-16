"""
Setting configuration
"""

import os
from pathlib import Path

__version__ = '0.2.2'

TEMPLATE_DIR = Path(os.path.expanduser('~/.config/walltheme/templates'))
CACHE_DIR = Path(os.path.expanduser('~/.cache/walltheme'))
MODULE_DIR = Path(os.path.dirname(__file__))
