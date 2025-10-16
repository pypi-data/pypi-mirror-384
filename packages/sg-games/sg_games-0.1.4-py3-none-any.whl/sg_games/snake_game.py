import tkinter as tk
import random

class SnakeGame:
    def __init__(self, root):
        self.root = root
        self.root.title("🐍 Snake Game")
        self.root.resizable(False, False)

        self.WIDTH = 600
        self.HEIGHT = 400
        self.CELL_SIZE = 20

        self.canvas = tk.Canvas(root, width=self.WIDTH, height=self.HEIGHT, bg="black")
        self.canvas.pack()

        self.reset_game()

        # Key bindings
        self.root.bind("<Up>", lambda e: self.change_direction("Up"))
        self.root.bind("<Down>", lambda e: self.change_direction("Down"))
        self.root.bind("<Left>", lambda e: self.change_direction("Left"))
        self.root.bind("<Right>", lambda e: self.change_direction("Right"))

        self.update_game()

    def reset_game(self):
        self.direction = "Right"
        self.snake = [(100, 100), (80, 100), (60, 100)]  # Starting 3-block snake
        self.food = self.create_food()
        self.game_over = False
        self.score = 0
        self.speed = 100  # milliseconds delay
        self.draw_board()

    def create_food(self):
        x = random.randrange(0, self.WIDTH - self.CELL_SIZE, self.CELL_SIZE)
        y = random.randrange(0, self.HEIGHT - self.CELL_SIZE, self.CELL_SIZE)
        return (x, y)

    def draw_board(self):
        self.canvas.delete("all")

        # Draw food
        fx, fy = self.food
        self.canvas.create_rectangle(fx, fy, fx + self.CELL_SIZE, fy + self.CELL_SIZE, fill="red")

        # Draw snake
        for i, (x, y) in enumerate(self.snake):
            color = "lime" if i == 0 else "green"
            self.canvas.create_rectangle(x, y, x + self.CELL_SIZE, y + self.CELL_SIZE, fill=color)

        # Draw score
        self.canvas.create_text(70, 10, fill="white", font=("Arial", 12), text=f"Score: {self.score}")

    def change_direction(self, new_dir):
        opposite = {"Up": "Down", "Down": "Up", "Left": "Right", "Right": "Left"}
        if new_dir != opposite.get(self.direction):
            self.direction = new_dir

    def move_snake(self):
        if self.game_over:
            return

        head_x, head_y = self.snake[0]

        if self.direction == "Up":
            head_y -= self.CELL_SIZE
        elif self.direction == "Down":
            head_y += self.CELL_SIZE
        elif self.direction == "Left":
            head_x -= self.CELL_SIZE
        elif self.direction == "Right":
            head_x += self.CELL_SIZE

        new_head = (head_x, head_y)

        # Check collision with walls
        if (
            head_x < 0
            or head_x >= self.WIDTH
            or head_y < 0
            or head_y >= self.HEIGHT
            or new_head in self.snake
        ):
            self.end_game()
            return

        self.snake.insert(0, new_head)

        # Check if food eaten
        if new_head == self.food:
            self.score += 10
            self.food = self.create_food()
        else:
            self.snake.pop()

    def end_game(self):
        self.game_over = True
        self.canvas.create_text(
            self.WIDTH / 2,
            self.HEIGHT / 2,
            fill="white",
            font=("Helvetica", 20, "bold"),
            text=f"GAME OVER\nScore: {self.score}",
        )
        self.canvas.create_text(
            self.WIDTH / 2,
            self.HEIGHT / 2 + 50,
            fill="yellow",
            font=("Helvetica", 12),
            text="Press SPACE to Restart",
        )
        self.root.bind("<space>", lambda e: self.reset_game())

    def update_game(self):
        if not self.game_over:
            self.move_snake()
            self.draw_board()
        self.root.after(self.speed, self.update_game)

# Run the game
def snake_game():
    root = tk.Tk()
    game = SnakeGame(root)
    root.mainloop()
