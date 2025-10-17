"""
Setting configuration
"""

import os
from pathlib import Path

__version__ = '0.2.4'

HOME = os.getenv('HOME', os.getenv('USERPROFILE'))
XDG_CACHE_DIR = os.getenv('XDG_CACHE_HOME', os.path.join(HOME, '.cache'))
XDG_CONF_DIR = os.getenv('XDG_CONFIG_HOME', os.path.join(HOME, '.config'))

TEMPLATE_DIR = Path(os.path.join(XDG_CONF_DIR, 'walltheme', 'templates'))
CACHE_DIR = Path(os.path.join(XDG_CACHE_DIR, 'walltheme'))
MODULE_DIR = Path(os.path.dirname(__file__))
