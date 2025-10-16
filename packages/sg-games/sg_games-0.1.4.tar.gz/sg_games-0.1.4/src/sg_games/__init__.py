"""
SG Games Package

This package contains multiple retro-style games
that can be launched via CLI or imported individually.
"""

__version__ = "0.1.4"
__author__ = "Marri Bhuvaneshwar"

# Optional: import submodules for easier access
from . import brickbreaker_game
from . import flappy_bird
from . import pingpong_game
from . import snake_game
from . import XOX_game

__all__ = ["brickbreaker_game","flappy_bird","pingpong_game","snake_game","XOX_game"]


try:
    import tkinter
except ImportError:
    raise ImportError(
        "Tkinter is required but not found. "
        "On Linux, install it with: sudo apt-get install python3-tk"
    )