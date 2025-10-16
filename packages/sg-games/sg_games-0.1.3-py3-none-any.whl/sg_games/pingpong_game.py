import tkinter as tk
import random

class PongGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Ping Pong Game")
        self.root.resizable(False, False)

        # Canvas setup
        self.canvas = tk.Canvas(root, width=800, height=400, bg="black")
        self.canvas.pack()

        # Draw paddles and ball
        self.paddle1 = self.canvas.create_rectangle(20, 150, 40, 250, fill="cyan")
        self.paddle2 = self.canvas.create_rectangle(760, 150, 780, 250, fill="orange")
        self.ball = self.canvas.create_oval(390, 190, 410, 210, fill="white")

        # Scoreboard
        self.score1 = 0
        self.score2 = 0
        self.score_text = self.canvas.create_text(
            400, 20, text="Player 1: 0    Player 2: 0", fill="white", font=("Helvetica", 14)
        )

        # Ball direction
        self.ball_dx = random.choice([-4, 4])
        self.ball_dy = random.choice([-3, 3])

        # Movement speed
        self.paddle_speed = 30

        # Key bindings
        self.root.bind("w", lambda e: self.move_paddle(self.paddle1, -self.paddle_speed))
        self.root.bind("s", lambda e: self.move_paddle(self.paddle1, self.paddle_speed))
        self.root.bind("<Up>", lambda e: self.move_paddle(self.paddle2, -self.paddle_speed))
        self.root.bind("<Down>", lambda e: self.move_paddle(self.paddle2, self.paddle_speed))

        # Start game loop
        self.update_game()

    def move_paddle(self, paddle, dy):
        x1, y1, x2, y2 = self.canvas.coords(paddle)
        if 0 < y1 + dy and y2 + dy < 400:  # Prevent going out of bounds
            self.canvas.move(paddle, 0, dy)

    def update_game(self):
        # Move ball
        self.canvas.move(self.ball, self.ball_dx, self.ball_dy)
        bx1, by1, bx2, by2 = self.canvas.coords(self.ball)

        # Bounce from top/bottom walls
        if by1 <= 0 or by2 >= 400:
            self.ball_dy *= -1

        # Paddle collision (Player 1)
        if self.check_collision(self.paddle1, bx1, by1, bx2, by2):
            self.ball_dx = abs(self.ball_dx)

        # Paddle collision (Player 2)
        if self.check_collision(self.paddle2, bx1, by1, bx2, by2):
            self.ball_dx = -abs(self.ball_dx)

        # Left and right wall scoring
        if bx1 <= 0:
            self.score2 += 1
            self.reset_ball(direction=1)
        elif bx2 >= 800:
            self.score1 += 1
            self.reset_ball(direction=-1)

        # Update score text
        self.canvas.itemconfig(
            self.score_text, text=f"Player 1: {self.score1}    Player 2: {self.score2}"
        )

        self.root.after(20, self.update_game)  # 50 FPS

    def check_collision(self, paddle, bx1, by1, bx2, by2):
        px1, py1, px2, py2 = self.canvas.coords(paddle)
        return px1 < bx2 and px2 > bx1 and py1 < by2 and py2 > by1

    def reset_ball(self, direction):
        # Reset to center
        self.canvas.coords(self.ball, 390, 190, 410, 210)
        self.ball_dx = 4 * direction
        self.ball_dy = random.choice([-3, 3])

# Run the game
def ping_pong():
    root = tk.Tk()
    game = PongGame(root)
    root.mainloop()
