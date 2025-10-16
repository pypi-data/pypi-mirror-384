import tkinter as tk
import random


class FlappyBird:
    def __init__(self, root):
        self.root = root
        self.root.title("Flappy Bird")
        self.root.resizable(False, False)

        # Canvas setup
        self.WIDTH = 600
        self.HEIGHT = 500
        self.canvas = tk.Canvas(root, width=self.WIDTH, height=self.HEIGHT, bg="#0A0F0D", highlightthickness=0)
        self.canvas.pack()

        # Bind keys (only once)
        self.root.bind("<space>", self.flap)
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
        self.frame_count = 0

        # Bird setup
        self.bird_size = 25
        self.bird_x = 100
        self.bird_y = self.HEIGHT // 2
        self.bird = self.canvas.create_oval(
            self.bird_x - self.bird_size / 2, self.bird_y - self.bird_size / 2,
            self.bird_x + self.bird_size / 2, self.bird_y + self.bird_size / 2,
            fill="#27AE60", outline="#2ECC71", width=2
        )
        self.bird_velocity = 0
        self.gravity = 0.5
        self.flap_strength = -8

        # Pipe setup
        self.pipes = []
        self.pipe_width = 60
        self.pipe_gap = 150
        self.pipe_speed = 3
        self.pipe_spacing = 200

        # Score display
        self.score_text = self.canvas.create_text(
            self.WIDTH // 2, 30,
            text="Score: 0", fill="Red", font=("Arial", 20, "bold")
        )

        # Instructions
        self.instruction_text = self.canvas.create_text(
            self.WIDTH // 2, self.HEIGHT // 2 + 50,
            text="Press SPACE to Flap", fill="#2ECC71", font=("Arial", 14)
        )

        self.update_game()

    # ---------------- Core Game Loop ---------------- #
    def update_game(self):
        if self.running:
            self.frame_count += 1
            self.move_bird()
            self.move_pipes()
            self.check_collision()

            # Spawn new pipes
            if self.frame_count % 70 == 0:
                self.create_pipe()

            self.root.after(20, self.update_game)
        else:
            self.canvas.create_text(
                self.WIDTH / 2, self.HEIGHT / 2,
                text="Game Over! Press 'R' to Restart",
                fill="#2ECC71", font=("Arial", 18, "bold")
            )

    # ---------------- Bird Control ---------------- #
    def flap(self, event):
        if self.running:
            # Remove instruction text on first flap
            if self.instruction_text:
                self.canvas.delete(self.instruction_text)
                self.instruction_text = None
            self.bird_velocity = self.flap_strength

    def move_bird(self):
        # Apply gravity
        self.bird_velocity += self.gravity
        self.bird_y += self.bird_velocity

        # Update bird position
        self.canvas.coords(
            self.bird,
            self.bird_x - self.bird_size / 2, self.bird_y - self.bird_size / 2,
            self.bird_x + self.bird_size / 2, self.bird_y + self.bird_size / 2
        )

        # Check boundaries
        if self.bird_y - self.bird_size / 2 <= 0 or self.bird_y + self.bird_size / 2 >= self.HEIGHT:
            self.running = False

    # ---------------- Pipe Management ---------------- #
    def create_pipe(self):
        # Random gap position
        gap_y = random.randint(100, self.HEIGHT - 150)

        # Top pipe
        top_pipe = self.canvas.create_rectangle(
            self.WIDTH, 0,
            self.WIDTH + self.pipe_width, gap_y - self.pipe_gap / 2,
            fill="#145A32", outline="#1E8449", width=2
        )

        # Bottom pipe
        bottom_pipe = self.canvas.create_rectangle(
            self.WIDTH, gap_y + self.pipe_gap / 2,
                        self.WIDTH + self.pipe_width, self.HEIGHT,
            fill="#145A32", outline="#1E8449", width=2
        )

        self.pipes.append({
            'top': top_pipe,
            'bottom': bottom_pipe,
            'x': self.WIDTH,
            'scored': False
        })

    def move_pipes(self):
        for pipe in self.pipes[:]:
            pipe['x'] -= self.pipe_speed

            # Move pipe rectangles
            self.canvas.move(pipe['top'], -self.pipe_speed, 0)
            self.canvas.move(pipe['bottom'], -self.pipe_speed, 0)

            # Score when bird passes pipe
            if not pipe['scored'] and pipe['x'] + self.pipe_width < self.bird_x:
                pipe['scored'] = True
                self.score += 1
                self.canvas.itemconfig(self.score_text, text=f"Score: {self.score}")

            # Remove off-screen pipes
            if pipe['x'] + self.pipe_width < 0:
                self.canvas.delete(pipe['top'])
                self.canvas.delete(pipe['bottom'])
                self.pipes.remove(pipe)

    # ---------------- Collision Detection ---------------- #
    def check_collision(self):
        bird_coords = self.canvas.coords(self.bird)

        for pipe in self.pipes:
            top_coords = self.canvas.coords(pipe['top'])
            bottom_coords = self.canvas.coords(pipe['bottom'])

            # Check collision with pipes
            if self.intersect(bird_coords, top_coords) or self.intersect(bird_coords, bottom_coords):
                self.running = False
                break

    def intersect(self, a, b):
        """Check if two rectangles intersect"""
        return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])

    def reset_game(self):
        """Restart the game"""
        self.init_game()


# ---------------- Run the Game ---------------- #
def flappy_bird():
    root = tk.Tk()
    game = FlappyBird(root)
    root.mainloop()