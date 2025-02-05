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
        # Clear any existing content.
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # --- Section 1: Money Leaderboard ---
        tk.Label(self.content_frame, text="Money Leaderboard", bg=DARK_BG, fg=DARK_FG,
                 font=("Arial", 14, "bold")).pack(pady=5)
        self.create_section(self.content_frame, category="money")

        # --- Section 2: Upgrades Leaderboard ---
        tk.Label(self.content_frame, text="Upgrades Leaderboard", bg=DARK_BG, fg=DARK_FG,
                 font=("Arial", 14, "bold")).pack(pady=5)
        self.create_section(self.content_frame, category="upgrades")

        # --- Section 3: Total Mined Leaderboard ---
        tk.Label(self.content_frame, text="Total Mined Leaderboard", bg=DARK_BG, fg=DARK_FG,
                 font=("Arial", 14, "bold")).pack(pady=5)
        self.create_section(self.content_frame, category="mined")

    def create_section(self, parent, category):
        """
        Draw a section for a particular leaderboard category.
        'category' should be one of:
          - "money"   -> Shows player's money with a currency symbol.
          - "upgrades" -> Shows the number of upgrades purchased.
          - "mined"   -> Shows the total mined amount.
        The players are sorted in descending order by the chosen value.
        """
        canvas_width = 400
        row_height = 35
        header_height = 30

        # Define which value to show, header text, and how to display the value.
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
        else:
            return  # Unknown category

        # Sort players descending by the chosen metric.
        players = sorted(self.game.players, key=data_func, reverse=True)
        num_players = len(players)
        canvas_height = header_height + row_height * num_players + 10

        canvas = tk.Canvas(parent, width=canvas_width, height=canvas_height,
                           bg=DARK_BG, highlightthickness=0)
        canvas.pack(pady=5)

        # Create header columns: Player symbol, numeric value, and a bar chart.
        col_positions = [10, 100, 250]  # Adjust these as needed.
        headers = ["Player", header_text, "Bar Chart"]
        for i, h in enumerate(headers):
            canvas.create_text(col_positions[i], 15, anchor="w", text=h,
                               fill=DARK_FG, font=("Arial", 10, "bold"))

        # Compute the maximum value among players for scaling the bar chart.
        max_value = max(data_func(p) for p in players) if players else 1

        for idx, p in enumerate(players):
            y = header_height + idx * row_height
            row_tag = f"{category}_row_{idx}"

            # If the player's tile is selected, highlight the row.
            if hasattr(self.master, "selected_tile") and self.master.selected_tile == (p.x, p.y):
                row_bg = SELECTED_TILE_COLOR
            else:
                row_bg = EMPTY_TILE_BG

            # Draw the row background rectangle.
            canvas.create_rectangle(5, y, canvas_width - 5, y + row_height,
                                    fill=row_bg, outline="", tags=row_tag)
            # Bind the row click event.
            canvas.tag_bind(row_tag, "<Button-1>",
                            lambda event, px=p.x, py=p.y: self.on_row_click(px, py))

            # Column 1: Player symbol, colored by player.
            canvas.create_text(col_positions[0], y + row_height / 2, anchor="w",
                               text=p.symbol, fill=p.color, font=("Arial", 10), tags=row_tag)
            # Column 2: The numeric value, colored by player.
            value = data_func(p)
            canvas.create_text(col_positions[1], y + row_height / 2, anchor="w",
                               text=display_func(value), fill=p.color, font=("Arial", 10), tags=row_tag)
            # Column 3: Bar chart representing the value.
            bar_x = col_positions[2]
            bar_y = y + 5
            max_bar_length = canvas_width - bar_x - 20
            bar_length = (value / max_value) * max_bar_length if max_value > 0 else 0
            canvas.create_rectangle(bar_x, bar_y, bar_x + bar_length, bar_y + row_height - 10,
                                    fill=p.color, outline=p.color, tags=row_tag)

    def on_row_click(self, x, y):
        # Set the selected tile to the player's coordinates.
        self.master.selected_tile = (x, y)
        if hasattr(self.master, "update_display"):
            self.master.update_display()
        self.update_content()

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

        # Toggle mode: True = show Resource bar; False = show Total Value bar.
        self.show_resource_bar = True

        # Button to toggle bar chart mode.
        button_frame = tk.Frame(self, bg=DARK_BG)
        button_frame.pack(pady=5)
        self.toggle_button = tk.Button(button_frame, text="Show Total Value Bar", command=self.toggle_bar_chart,
                                       bg=BUTTON_BG, fg=BUTTON_FG)
        self.toggle_button.pack()

        self.canvas = tk.Canvas(self, width=self.canvas_width, height=300, bg=DARK_BG, highlightthickness=0)
        self.canvas.pack(padx=10, pady=10, fill="both", expand=True)
        self.update_content()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def toggle_bar_chart(self):
        self.show_resource_bar = not self.show_resource_bar
        if self.show_resource_bar:
            self.toggle_button.config(text="Show Total Value")
        else:
            self.toggle_button.config(text="Show Resource")
        self.update_content()

    def update_content(self):
        self.game.update_discovered()
        discovered = [a for a in self.game.asteroids if (a.x, a.y) in self.game.discovered_tiles]
        total_height = self.header_height + self.row_height * len(discovered) + 20
        self.canvas.config(height=total_height)
        self.canvas.delete("all")

        # Define new headers including a Total Value column.
        # Headers: Asteroid, Loc, Res, Price, Tot. Val, Players, Robot (Cap), and Bar chart.
        headers = ["Asteroid", "Loc", "Res", "Price", "Tot. Val", "Players", "Robot (Cap)",
                   "Resource" if self.show_resource_bar else "Value"]
        # Choose column positions (adjust as needed).
        col_positions = [10, 70, 120, 170, 230, 290, 380, 480]

        for i, header in enumerate(headers):
            self.canvas.create_text(col_positions[i], 15, anchor="w", text=header, fill=DARK_FG,
                                    font=("Arial", 10, "bold"))
        y = self.header_height

        # Determine the maximum for scaling the bar chart.
        if self.show_resource_bar:
            max_bar_value = max(a.resource for a in discovered) if discovered else 1
        else:
            # Total value: resource * value
            max_bar_value = max(a.resource * a.value for a in discovered) if discovered else 1

        for a in discovered:
            # Use the tile's background color (e.g. as defined by your get_tile_properties) for the row.
            _, fill_color, _ = self.master.get_tile_properties(a.x, a.y)
            row_tag = f"asteroid_{a.id}"
            row_id = self.canvas.create_rectangle(5, y, self.canvas_width - 5, y + self.row_height, fill=fill_color,
                                                  outline="", tags=row_tag)
            # Bind clicking on the row.
            self.canvas.tag_bind(row_tag, "<Button-1>", lambda e, ax=a.x, ay=a.y: self.on_row_click(ax, ay))

            # Determine the color to use for text: if a robot is present, use its owner's color.
            row_color = a.robot.owner.color if a.robot else DARK_FG

            self.canvas.create_text(col_positions[0], y + self.row_height / 2, anchor="w",
                                    text=f"A{a.id}", fill=row_color, font=("Arial", 10), tags=row_tag)
            self.canvas.create_text(col_positions[1], y + self.row_height / 2, anchor="w",
                                    text=f"({a.x},{a.y})", fill=row_color, font=("Arial", 10), tags=row_tag)
            self.canvas.create_text(col_positions[2], y + self.row_height / 2, anchor="w",
                                    text=f"{a.resource:.0f}", fill=row_color, font=("Arial", 10), tags=row_tag)
            self.canvas.create_text(col_positions[3], y + self.row_height / 2, anchor="w",
                                    text=f"${a.value:.2f}", fill=row_color, font=("Arial", 10), tags=row_tag)
            total_val = a.resource * a.value
            self.canvas.create_text(col_positions[4], y + self.row_height / 2, anchor="w",
                                    text=f"${total_val:.2f}", fill=row_color, font=("Arial", 10), tags=row_tag)
            players_here = [p for p in self.game.players if p.x == a.x and p.y == a.y]
            players_text = ", ".join(p.symbol for p in players_here)
            self.canvas.create_text(col_positions[5], y + self.row_height / 2, anchor="w",
                                    text=players_text, fill=row_color, font=("Arial", 10), tags=row_tag)
            robot_text = ""
            if a.robot:
                robot_text = f"{a.robot.owner.symbol} (Cap: {a.robot.capacity})"
            self.canvas.create_text(col_positions[6], y + self.row_height / 2, anchor="w",
                                    text=robot_text, fill=row_color, font=("Arial", 10, "bold"), tags=row_tag)
            # Draw the bar chart rectangle.
            bar_x = col_positions[7]
            bar_y = y + 5
            max_bar_length = self.canvas_width - bar_x - 20
            if self.show_resource_bar:
                bar_val = a.resource
            else:
                bar_val = total_val
            bar_length = (bar_val / max_bar_value) * max_bar_length if max_bar_value > 0 else 0
            self.canvas.create_rectangle(bar_x, bar_y, bar_x + bar_length, bar_y + self.row_height - 10,
                                         fill="cyan", outline="cyan", tags=row_tag)
            y += self.row_height

    def on_row_click(self, x, y):
        self.master.on_asteroid_selected(x, y)

    def on_close(self):
        self.destroy()
        self.master.asteroid_stats_window = None
