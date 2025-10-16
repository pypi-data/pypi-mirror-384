# SG Games Collection

SG Games Collection is a Python package that provides a set of classic games implemented with **Tkinter**. Play games like Brick Breaker, Flappy Bird, Ping-Pong, Snake, and TicTacToe from a simple command-line interface.

## Features

- Brick Breaker
- Flappy Bird
- Ping Pong
- Snake
- TicTacToe

Run each game from the terminal using convenient command-line flags.

---

## Installation

You can install `sg-games` from [PyPI](https://pypi.org) using `pip`.  

### Step 1: Install Python 3 (if not already installed)

Check your Python version:

```bash
    python3 --version
```
### Step 2: Ensure Tkinter is Installed

#### - Ubuntu / Debian
```bash
    sudo apt update
    sudo apt install python3-tk
```

#### - Fedora
```bash
    sudo dnf install python3-tkinter
```

#### - Arch Linux / Manjaro
```bash
    sudo pacman -S tk
```

Verify Tkinter Installation
```bash
    python3 -m tkinter
```

### Step 3: Install SG games
```bash
    pip install sg-games
```

### Usage
Run the games from your terminal using the following flags:
```bash
    sg-games --help
```

Output:

```less
usage: sg-games [-h] [--brick_breaker] [--flappy_bird] [--ping_pong] [--snake] [--xox]

SG Games Collection

options:
  -h, --help       show this help message and exit
  --brick_breaker  Launch Brick Breaker game
  --flappy_bird    Launch Flappy Bird game
  --ping_pong      Launch Ping Pong game
  --snake          Launch Snake game
  --xox            Launch TicTacToe
```

### Examples

- Launch Brick Breaker
```bash
    sg-games --brick_breaker
```

- Launch Snake
```bash
    from sg_games import snake
    snake_game()
```

### Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your improvements.