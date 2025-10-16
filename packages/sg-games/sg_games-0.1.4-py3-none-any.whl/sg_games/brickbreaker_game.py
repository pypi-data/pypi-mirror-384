import tkinter as tk
import random


class BrickBreaker:
    def __init__(self, root):
        self.root = root
        self.root.title("Brick Breaker")
        self.root.resizable(False, False)

        # Canvas setup
        self.WIDTH = 600
        self.HEIGHT = 500
        self.canvas = tk.Canvas(root, width=self.WIDTH, height=self.HEIGHT, bg="#0A0F0D", highlightthickness=0)
        self.canvas.pack()

        # Bind keys (only once)
        self.root.bind("<Left>", self.move_left)
        self.root.bind("<Right>", self.move_right)
        self.root.bind("r", lambda e: self.reset_game())

        # Initialize game
        self.init_game()

    def init_game(self):
        """Initialize or reset game state"""
        # Clear canvas
        self.canvas.delete("all")

        # Game state
        self.running = True
        self.score = 0

        # Paddle setup
        self.paddle_width = 100
        self.paddle_height = 15
        self.paddle = self.canvas.create_rectangle(
            (self.WIDTH / 2 - self.paddle_width / 2, self.HEIGHT - 40,
             self.WIDTH / 2 + self.paddle_width / 2, self.HEIGHT - 25),
            fill="#2ECC71", outline=""
        )

        # Ball setup (reduced speed from 3 to 2)
        self.ball_size = 15
        self.ball = self.canvas.create_oval(
            (self.WIDTH / 2 - self.ball_size / 2, self.HEIGHT / 2 - self.ball_size / 2,
             self.WIDTH / 2 + self.ball_size / 2, self.HEIGHT / 2 + self.ball_size / 2),
            fill="#27AE60", outline=""
        )
        self.ball_dx = random.choice([-2, 2])
        self.ball_dy = -2

        # Brick setup
        self.bricks = []
        self.create_bricks(rows=5, cols=8)

        # Score display
        self.score_text = self.canvas.create_text(
            10, 10, anchor="nw",
            text="Score: 0", fill="#2ECC71", font=("Arial", 14, "bold")
        )

        self.update_game()

    # ---------------- Core Game Loop ---------------- #
    def update_game(self):
        if self.running:
            self.move_ball()
            self.check_collision()
            self.root.after(10, self.update_game)
        else:
            self.canvas.create_text(
                self.WIDTH / 2, self.HEIGHT / 2,
                text="Game Over! Press 'R' to Restart",
                fill="#2ECC71", font=("Arial", 16, "bold")
            )

    # ---------------- Paddle Control ---------------- #
    def move_left(self, event):
        x1, y1, x2, y2 = self.canvas.coords(self.paddle)
        if x1 > 0:
            self.canvas.move(self.paddle, -20, 0)

    def move_right(self, event):
        x1, y1, x2, y2 = self.canvas.coords(self.paddle)
        if x2 < self.WIDTH:
            self.canvas.move(self.paddle, 20, 0)

    # ---------------- Ball Movement ---------------- #
    def move_ball(self):
        self.canvas.move(self.ball, self.ball_dx, self.ball_dy)
        x1, y1, x2, y2 = self.canvas.coords(self.ball)

        # Wall collisions
        if x1 <= 0 or x2 >= self.WIDTH:
            self.ball_dx *= -1
        if y1 <= 0:
            self.ball_dy *= -1
        if y2 >= self.HEIGHT:
            self.running = False  # Game over if ball falls down

    # ---------------- Collision Logic ---------------- #
    def check_collision(self):
        ball_coords = self.canvas.coords(self.ball)
        paddle_coords = self.canvas.coords(self.paddle)

        # Paddle collision
        if self.intersect(ball_coords, paddle_coords):
            self.ball_dy *= -1

        # Brick collision
        for brick in self.bricks[:]:
            if self.intersect(ball_coords, self.canvas.coords(brick)):
                self.canvas.delete(brick)
                self.bricks.remove(brick)
                self.ball_dy *= -1
                self.score += 10
                self.canvas.itemconfig(self.score_text, text=f"Score: {self.score}")
                break

        # Win condition
        if not self.bricks:
            self.running = False
            self.canvas.create_text(
                self.WIDTH / 2, self.HEIGHT / 2,
                text="You Win! Press 'R' to Restart",
                fill="#2ECC71", font=("Arial", 18, "bold")
            )

    # ---------------- Helper Methods ---------------- #
    def intersect(self, a, b):
        return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])

    def create_bricks(self, rows, cols):
        brick_width = (self.WIDTH - 80) / cols
        brick_height = 20
        for r in range(rows):
            for c in range(cols):
                x1 = 40 + c * brick_width
                y1 = 40 + r * (brick_height + 5)
                x2 = x1 + brick_width - 5
                y2 = y1 + brick_height
                brick = self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=random.choice(["#145A32", "#1E8449", "#27AE60"]),
                    outline=""
                )
                self.bricks.append(brick)

    def reset_game(self):
        """Restart the game."""
        self.init_game()


# ---------------- Run the Game ---------------- #
def brick_breaker():
    root = tk.Tk()
    game = BrickBreaker(root)
    root.mainloop()