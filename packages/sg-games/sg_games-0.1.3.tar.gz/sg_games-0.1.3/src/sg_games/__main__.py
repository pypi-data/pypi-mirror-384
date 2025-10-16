import argparse
import sys
# Main file


def main():
    parser = argparse.ArgumentParser(description='SG Games Collection')
    parser.add_argument('--brick_breaker', action='store_true',
                        help='Launch Brick Breaker game')
    parser.add_argument('--flappy_bird', action='store_true',
                        help='Launch Flappy Bird game')
    parser.add_argument('--ping_pong',action='store_true',
                        help='Launch Ping Pong game')
    parser.add_argument('--snake',action='store_true',
                        help='Launch Snake game')
    parser.add_argument('--xox',action='store_true',
                        help='Launch TicTacToe')

    args = parser.parse_args()

    # Check which game to launch
    if args.brick_breaker:
        from .brickbreaker_game import brick_breaker
        brick_breaker()

    elif args.flappy_bird:
        from .flappy_bird import flappy_bird
        flappy_bird()

    elif args.ping_pong:
        from .pingpong_game import ping_pong
        ping_pong()

    elif args.snake:
        from .snake_game import snake_game
        snake_game()

    elif args.xox:
        from .XOX_game import xox
        xox()

    else:
        print("SG Games Collection")
        print("\nAvailable games:")
        print("  --brick_breaker    Launch Brick Breaker game")
        print("  --flappy_bird      Launch Flappy Bird game")
        print("  --ping_pong        Launch Ping Pong Game")
        print("  --snake            Launch Snake Game")
        print("  --xox              Launch TicTacToe")
        print("\n Example Usage:")
        print("  python -m sg_games --flappy_bird")
        sys.exit(0)