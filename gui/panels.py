import tkinter as tk
from constants import *

class UpgradeGUI(tk.Toplevel):
    def __init__(self, parent, game, player):
        super().__init__(parent)
        self.title("Upgrade Options")
        self.configure(bg=DARK_BG)
        self.game = game
        self.player = player
        self.upgrades = {
            "mining": ("Mining Capacity", self.player.mining_upgrade_cost,
                       f"Increases mining capacity by {self.game.settings.mining_upgrade_amount}. Next upgrade cost increases by {self.game.settings.upgrade_mining_cost_increase}."),
            "discovery": ("Discovery Range", self.player.discovery_upgrade_cost,
                          f"Increases discovery range by {self.game.settings.discovery_upgrade_amount}. Next upgrade cost increases by {self.game.settings.upgrade_discovery_cost_increase}."),
            "movement": ("Movement Range", self.player.movement_upgrade_cost,
                         f"Increases movement range by {self.game.settings.movement_upgrade_amount}. Next upgrade cost increases by {self.game.settings.upgrade_movement_cost_increase}."),
            "robot_range": ("Robot Range", self.player.robot_range_upgrade_cost,
                            f"Increases remote robot planting range by {self.game.settings.robot_range_upgrade_amount}. Next upgrade cost increases by {self.game.settings.upgrade_robot_range_cost_increase}."),
            "robot_capacity": ("Robot Capacity", self.player.robot_capacity_upgrade_cost,
                               f"Increases your robot's capacity by {self.game.settings.robot_capacity_upgrade_amount}. Next upgrade cost increases by {self.game.settings.upgrade_robot_capacity_cost_increase}.")
        }
        self.selected_upgrade = tk.StringVar()
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        tk.Label(self, text="Select an upgrade to view details:", bg=DARK_BG, fg=DARK_FG,
                 font=("Arial", 12, "bold")).pack(padx=10, pady=5)
        self.listbox = tk.Listbox(self, bg=ENTRY_BG, fg=DARK_FG, selectbackground=ACTIVE_PLAYER_TILE_COLOR, width=30,
                                  height=6)
        for key in self.upgrades:
            self.listbox.insert(tk.END, self.upgrades[key][0])
        self.listbox.pack(padx=10, pady=5)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        self.detail_label = tk.Label(self, text="Select an upgrade to see details.", bg=DARK_BG, fg=DARK_FG,
                                     wraplength=300, justify="left")
        self.detail_label.pack(padx=10, pady=5)
        button_frame = tk.Frame(self, bg=DARK_BG)
        button_frame.pack(padx=10, pady=10)
        tk.Button(button_frame, text="Buy", command=self.buy_upgrade, bg=BUTTON_BG, fg=BUTTON_FG).pack(side="left",
                                                                                                       padx=5)
        tk.Button(button_frame, text="Cancel", command=self.on_close, bg=BUTTON_BG, fg=BUTTON_FG).pack(side="left",
                                                                                                       padx=5)

    def on_select(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            key = list(self.upgrades.keys())[index]
            name, cost, detail = self.upgrades[key]
            self.detail_label.config(text=f"{name}\nCost: ${cost}\n{detail}")
            self.selected_upgrade.set(key)

    def buy_upgrade(self):
        key = self.selected_upgrade.get()
        if key:
            self.game.upgrade_player(self.player, key, self.master.log)
            self.master.update_display()
        else:
            self.master.log("No upgrade selected.")
        self.on_close()

    def on_close(self):
        self.destroy()
        self.master.upgrade_window = None


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
        tk.Label(self.content_frame, text="Leaderboard", bg=DARK_BG, fg=DARK_FG, font=("Arial", 14, "bold")).pack(
            pady=5)

        # ---- Horizontal Bar Chart for Players (Leaderboard) ----
        players = self.game.players
        row_height = 35
        header_height = 30
        num_players = len(players)
        chart_width = 600
        chart_height = header_height + row_height * num_players + 10
        canvas = tk.Canvas(self.content_frame, width=chart_width, height=chart_height, bg=DARK_BG, highlightthickness=0)
        canvas.pack(pady=10)
        # Define column positions for header:
        # Columns: Player, Location, Money, Total Mined, Upgrades, and Money Bar.
        col_positions = [10, 70, 140, 240, 340, 440]
        headers = ["Player", "Loc", "Money", "Total Mined", "Upgrades", "Money Bar"]
        for i, header in enumerate(headers):
            canvas.create_text(col_positions[i], 15, anchor="w", text=header, fill=DARK_FG, font=("Arial", 10, "bold"))
        # Compute maximum money for scaling the horizontal money bar.
        max_money = max(p.money for p in players) if players else 1
        for idx, p in enumerate(players):
            y = header_height + idx * row_height
            # Highlight the row if the player's tile is selected.
            if self.master.selected_tile == (p.x, p.y):
                row_bg = SELECTED_TILE_COLOR
            else:
                row_bg = EMPTY_TILE_BG
            canvas.create_rectangle(5, y, chart_width - 5, y + row_height, fill=row_bg, outline="")
            canvas.create_text(col_positions[0], y + row_height / 2, anchor="w", text=p.symbol, fill=p.color,
                               font=("Arial", 10))
            canvas.create_text(col_positions[1], y + row_height / 2, anchor="w", text=f"({p.x},{p.y})", fill=DARK_FG,
                               font=("Arial", 10))
            canvas.create_text(col_positions[2], y + row_height / 2, anchor="w", text=f"${p.money:.0f}", fill=DARK_FG,
                               font=("Arial", 10))
            canvas.create_text(col_positions[3], y + row_height / 2, anchor="w", text=f"{p.total_mined}", fill=DARK_FG,
                               font=("Arial", 10))
            canvas.create_text(col_positions[4], y + row_height / 2, anchor="w", text=f"{p.upgrades_purchased}",
                               fill=DARK_FG, font=("Arial", 10))
            # Draw horizontal money bar starting at col_positions[5]:
            bar_x = col_positions[5]
            bar_y = y + 5
            bar_height = row_height - 10
            max_bar_length = chart_width - bar_x - 20  # leave some margin
            bar_length = (p.money / max_money) * max_bar_length if max_money > 0 else 0
            canvas.create_rectangle(bar_x, bar_y, bar_x + bar_length, bar_y + bar_height, fill=p.color, outline=p.color)

    def on_close(self):
        self.destroy()
        self.master.leaderboard_window = None


class AsteroidGraphGUI(tk.Toplevel):
    def __init__(self, parent, game):
        super().__init__(parent)
        self.title("Asteroid Stats")
        self.configure(bg=DARK_BG)
        self.game = game
        self.canvas_width = 600
        self.row_height = 35
        self.header_height = 30
        self.canvas = tk.Canvas(self, width=self.canvas_width, height=300, bg=DARK_BG, highlightthickness=0)
        self.canvas.pack(padx=10, pady=10, fill="both", expand=True)
        self.update_content()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def update_content(self):
        self.game.update_discovered()
        discovered = [a for a in self.game.asteroids if (a.x, a.y) in self.game.discovered_tiles]
        total_height = self.header_height + self.row_height * len(discovered) + 20
        self.canvas.config(height=total_height)
        self.canvas.delete("all")
        headers = ["Asteroid", "Loc", "Res", "Price", "Players", "Robot (Cap)", "Resource Bar"]
        col_positions = [10, 80, 130, 180, 240, 320, 420]
        for i, header in enumerate(headers):
            self.canvas.create_text(col_positions[i], 15, anchor="w", text=header, fill=DARK_FG,
                                    font=("Arial", 10, "bold"))
        y = self.header_height
        max_resource = self.game.settings.asteroid_max
        for a in discovered:
            # If a robot is present, use its owner's color for the entire row.
            row_color = a.robot.owner.color if a.robot else DARK_FG
            # Use the tile's background color (unchanged) for the row rectangle.
            _, fill_color, _ = self.master.get_tile_properties(a.x, a.y)
            row_id = self.canvas.create_rectangle(5, y, self.canvas_width - 5, y + self.row_height, fill=fill_color,
                                                  outline="")
            self.canvas.tag_bind(row_id, "<Button-1>", lambda e, ax=a.x, ay=a.y: self.on_row_click(ax, ay))
            self.canvas.create_text(col_positions[0], y + self.row_height / 2, anchor="w",
                                    text=f"A{a.id}", fill=row_color, font=("Arial", 10))
            self.canvas.create_text(col_positions[1], y + self.row_height / 2, anchor="w",
                                    text=f"({a.x},{a.y})", fill=row_color, font=("Arial", 10))
            self.canvas.create_text(col_positions[2], y + self.row_height / 2, anchor="w",
                                    text=f"{a.resource:.0f}", fill=row_color, font=("Arial", 10))
            self.canvas.create_text(col_positions[3], y + self.row_height / 2, anchor="w",
                                    text=f"${a.value:.2f}", fill=row_color, font=("Arial", 10))
            players_here = [p for p in self.game.players if p.x == a.x and p.y == a.y]
            players_text = ", ".join(p.symbol for p in players_here)
            self.canvas.create_text(col_positions[4], y + self.row_height / 2, anchor="w",
                                    text=players_text, fill=row_color, font=("Arial", 10))
            robot_text = ""
            if a.robot:
                robot_text = f"{a.robot.owner.symbol} (Cap: {a.robot.capacity})"
            self.canvas.create_text(col_positions[5], y + self.row_height / 2, anchor="w",
                                    text=robot_text, fill=row_color, font=("Arial", 10, "bold"))
            bar_x = col_positions[6]
            bar_y = y + 5
            max_bar_length = 120
            bar_length = (a.resource / max_resource) * max_bar_length
            self.canvas.create_rectangle(bar_x, bar_y, bar_x + bar_length, bar_y + self.row_height - 10,
                                         fill="cyan", outline="cyan")
            y += self.row_height

    def on_row_click(self, x, y):
        self.master.on_asteroid_selected(x, y)

    def on_close(self):
        self.destroy()
        self.master.asteroid_stats_window = None

