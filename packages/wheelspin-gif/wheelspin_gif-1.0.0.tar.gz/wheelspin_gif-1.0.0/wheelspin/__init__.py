"""
WheelSpin - A library for creating animated spinning wheel GIFs

Main functions:
- create_spinning_wheel(): Simple wheel creation
- create_spinning_wheel_advanced(): Advanced options
- quick_spin(): Quick spin with defaults
- decision_wheel(): Decision-making wheel
"""

from .wheelspin_lib import (
    create_spinning_wheel,
    create_spinning_wheel_advanced,
    quick_spin,
    decision_wheel,
    __version__,
    __author__
)

__all__ = [
    'create_spinning_wheel',
    'create_spinning_wheel_advanced', 
    'quick_spin',
    'decision_wheel',
    '__version__',
    '__author__'
]