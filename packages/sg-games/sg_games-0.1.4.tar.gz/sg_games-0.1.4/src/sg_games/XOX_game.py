import tkinter as tk
from tkinter import messagebox


class TicTacToe:
    def __init__(self, root):
        # Window setup
        self.root = root
        self.root.title("Tic Tac Toe")
        self.root.config(bg="#0A0F0D")  # Dark background
        self.root.geometry("400x500")
        self.root.resizable(False, False)

        # Game state
        self.player = "X"
        self.buttons = [[None for _ in range(3)] for _ in range(3)]

        # Colors
        self.BG_COLOR = "#0A0F0D"
        self.BTN_COLOR = "#2ECC71"
        self.BTN_HOVER = "#27AE60"
        self.TEXT_COLOR = "#ECF0F1"
        self.WIN_HIGHLIGHT = "#1E8449"

        # UI setup
        self.create_widgets()

    # ---------------------- UI Creation ---------------------- #
    def create_widgets(self):
        """Create all UI elements like title, grid, and restart button."""
        title_label = tk.Label(
            self.root,
            text="TicTacToe",
            font=("Arial", 24, "bold"),
            bg=self.BG_COLOR,
            fg=self.BTN_COLOR,
        )
        title_label.pack(pady=20)

        self.frame = tk.Frame(self.root, bg=self.BG_COLOR)
        self.frame.pack(pady=20)

        # Create 3x3 grid buttons
        for i in range(3):
            for j in range(3):
                btn = tk.Button(
                    self.frame,
                    text="",
                    font=("Arial", 20, "bold"),
                    width=5,
                    height=2,
                    bg=self.BTN_COLOR,
                    fg=self.TEXT_COLOR,
                    activebackground=self.BTN_HOVER,
                    command=lambda r=i, c=j: self.on_click(r, c),
                )
                btn.grid(row=i, column=j, padx=5, pady=5)
                self.buttons[i][j] = btn

        # Restart Button
        restart_btn = tk.Button(
            self.root,
            text="🔄 Restart Game",
            font=("Arial", 14, "bold"),
            bg="#145A32",
            fg="white",
            activebackground="#1E8449",
            width=20,
            height=2,
            command=self.restart_game,
        )
        restart_btn.pack(pady=20)

    # ---------------------- Game Logic ---------------------- #
    def on_click(self, row, col):
        """Handle player's move when button is clicked."""
        button = self.buttons[row][col]
        if button["text"] == "" and not self.check_winner():
            button.config(text=self.player)
            if self.check_winner():
                messagebox.showinfo("Game Over", f"Player {self.player} wins!")
                self.highlight_winner()
                self.disable_buttons()
            elif self.is_draw():
                messagebox.showinfo("Game Over", "It's a draw!")
            else:
                self.switch_player()

    def check_winner(self):
        """Check if current player has won."""
        b = self.buttons
        for i in range(3):
            if b[i][0]["text"] == b[i][1]["text"] == b[i][2]["text"] != "":
                self.winning_cells = [(i, 0), (i, 1), (i, 2)]
                return True
            if b[0][i]["text"] == b[1][i]["text"] == b[2][i]["text"] != "":
                self.winning_cells = [(0, i), (1, i), (2, i)]
                return True
        if b[0][0]["text"] == b[1][1]["text"] == b[2][2]["text"] != "":
            self.winning_cells = [(0, 0), (1, 1), (2, 2)]
            return True
        if b[0][2]["text"] == b[1][1]["text"] == b[2][0]["text"] != "":
            self.winning_cells = [(0, 2), (1, 1), (2, 0)]
            return True
        return False

    def highlight_winner(self):
        """Highlight the winning cells."""
        for (r, c) in self.winning_cells:
            self.buttons[r][c].config(bg=self.WIN_HIGHLIGHT)

    def disable_buttons(self):
        """Disable all buttons after a win."""
        for row in self.buttons:
            for button in row:
                button.config(state="disabled")

    def is_draw(self):
        """Check if all cells are filled and no winner."""
        return all(self.buttons[r][c]["text"] != "" for r in range(3) for c in range(3))

    def switch_player(self):
        """Switch between players X and O."""
        self.player = "O" if self.player == "X" else "X"

    def restart_game(self):
        """Reset the board for a new round."""
        self.player = "X"
        for r in range(3):
            for c in range(3):
                self.buttons[r][c].config(text="", state="normal", bg=self.BTN_COLOR)


# ---------------------- Run the Game ---------------------- #
def xox():
    root = tk.Tk()
    game = TicTacToe(root)
    root.mainloop()