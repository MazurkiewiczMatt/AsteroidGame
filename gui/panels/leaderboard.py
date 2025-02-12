import tkinter as tk
from constants import *

class LeaderboardGUI(tk.Toplevel):
    def __init__(self, parent, game):
        super().__init__(parent)
        self.title("Leaderboard")
        self.configure(bg=DARK_BG)
        self.game = game
        self.content_frame = tk.Frame(self, bg=DARK_BG)
        self.content_frame.pack(padx=10, pady=10, fill="both")
        self.update_content()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def update_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        tk.Label(self.content_frame, text="Money Leaderboard", bg=DARK_BG, fg=DARK_FG,
                 font=FONT_HEADER).pack(pady=5)
        self.create_section(self.content_frame, category="money")
        tk.Label(self.content_frame, text="Upgrades Leaderboard", bg=DARK_BG, fg=DARK_FG,
                 font=FONT_HEADER).pack(pady=5)
        self.create_section(self.content_frame, category="upgrades")
        tk.Label(self.content_frame, text="Total Mined Leaderboard", bg=DARK_BG, fg=DARK_FG,
                 font=FONT_HEADER).pack(pady=5)
        self.create_section(self.content_frame, category="mined")
        tk.Label(self.content_frame, text="Robot Turn Earnings Leaderboard", bg=DARK_BG, fg=DARK_FG,
                 font=FONT_HEADER).pack(pady=5)
        self.create_section(self.content_frame, category="robot_money")

    def create_section(self, parent, category):
        canvas_width = 400
        row_height = 35
        header_height = 30
        if category == "money":
            header_text = "Money"
            data_func = lambda p: p.money
            display_func = lambda val: f"${val:.0f}"
        elif category == "upgrades":
            header_text = "Upgrades"
            data_func = lambda p: p.upgrades_purchased
            display_func = lambda val: str(val)
        elif category == "mined":
            header_text = "Total Mined"
            data_func = lambda p: p.total_mined
            display_func = lambda val: str(val)
        elif category == "robot_money":
            header_text = "Turn robot earnings"
            data_func = lambda p: p.money_earned_by_robots
            display_func = lambda val: f"${val:.0f}"
        else:
            return
        players = sorted(self.game.players, key=data_func, reverse=True)
        num_players = len(players)
        canvas_height = header_height + row_height * num_players + 10
        canvas = tk.Canvas(parent, width=canvas_width, height=canvas_height,
                           bg=DARK_BG, highlightthickness=0)
        canvas.pack(pady=5)
        col_positions = [10, 100, 250]
        headers = ["Player", header_text, "Bar Chart"]
        for i, h in enumerate(headers):
            canvas.create_text(col_positions[i], 15, anchor="w", text=h,
                               fill=DARK_FG, font=FONT_SMALL)
        max_value = max(data_func(p) for p in players) if players else 1
        for idx, p in enumerate(players):
            y = header_height + idx * row_height
            row_tag = f"{category}_row_{idx}"
            row_bg = SELECTED_TILE_COLOR if hasattr(self.master, "selected_tile") and self.master.selected_tile == (p.x, p.y) else EMPTY_TILE_BG
            canvas.create_rectangle(5, y, canvas_width - 5, y + row_height,
                                    fill=row_bg, outline="", tags=row_tag)
            canvas.tag_bind(row_tag, "<Button-1>",
                            lambda event, px=p.x, py=p.y: self.on_row_click(px, py))
            canvas.create_text(col_positions[0], y + row_height / 2, anchor="w",
                               text=p.symbol, fill=p.color, font=FONT_SMALL, tags=row_tag)
            value = data_func(p)
            canvas.create_text(col_positions[1], y + row_height / 2, anchor="w",
                               text=display_func(value), fill=p.color, font=FONT_SMALL, tags=row_tag)
            bar_x = col_positions[2]
            bar_y = y + 5
            max_bar_length = canvas_width - bar_x - 20
            bar_length = (value / max_value) * max_bar_length if max_value > 0 else 0
            canvas.create_rectangle(bar_x, bar_y, bar_x + bar_length, bar_y + row_height - 10,
                                    fill=p.color, outline=p.color, tags=row_tag)

    def on_row_click(self, x, y):
        self.master.selected_tile = (x, y)
        if hasattr(self.master, "update_display"):
            self.master.update_display()
        self.update_content()

    def on_close(self):
        self.destroy()
        self.master.leaderboard_window = None
