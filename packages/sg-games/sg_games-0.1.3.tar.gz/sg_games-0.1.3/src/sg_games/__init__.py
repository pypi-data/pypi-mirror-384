from .XOX_game import xox
from .pingpong_game import ping_pong
from .snake_game import snake_game
from .flappy_bird import flappy_bird
from .brickbreaker_game import brick_breaker

try:
    import tkinter
except ImportError:
    raise ImportError(
        "Tkinter is required but not found. "
        "On Linux, install it with: sudo apt-get install python3-tk"
    )