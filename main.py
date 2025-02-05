#!/usr/bin/env python3
import tkinter as tk
from tkinter import messagebox
import random
import math

# ---------- Dark Theme Colors ----------
DARK_BG = "#2b2b2b"  # Dark background
DARK_FG = "white"  # White text
BUTTON_BG = "#444444"  # Dark button background
BUTTON_FG = "white"  # White button text
ENTRY_BG = "#333333"  # Dark entry background
ENTRY_FG = "white"  # White entry text

# ---------- Highlight Colors ----------
ALLOWED_MOVE_COLOR = "#666666"  # Allowed move tiles (when in move mode)
SELECTED_TILE_COLOR = "#800080"  # Purple for the selected tile (for tile info)
ACTIVE_PLAYER_TILE_COLOR = "#008000"  # Green for active player's current cell
FIELD_OF_VIEW_COLOR = "#3a3a3a"  # Subtle highlight for tiles in active player's FOV


# =================== Helper Functions ===================

def manhattan_distance(x1, y1, x2, y2):
    return abs(x1 - x2) + abs(y1 - y2)


# =================== Data Classes ===================

class GameSettings:
    def __init__(self,
                 num_players=2,
                 grid_width=10,
                 grid_height=10,
                 num_asteroids=12,
                 asteroid_min=100,
                 asteroid_max=1000,
                 asteroid_value_min=0.8,
                 asteroid_value_max=1.2,
                 robot_capacity=10,
                 initial_money=500,
                 initial_mining_capacity=100,
                 initial_discovery_range=2,
                 initial_movement_range=2,
                 upgrade_mining_cost=200,
                 mining_upgrade_amount=10,
                 upgrade_discovery_cost=150,
                 discovery_upgrade_amount=1,
                 upgrade_movement_cost=150,
                 movement_upgrade_amount=1):
        self.num_players = num_players
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.num_asteroids = num_asteroids
        self.asteroid_min = asteroid_min
        self.asteroid_max = asteroid_max
        self.asteroid_value_min = asteroid_value_min
        self.asteroid_value_max = asteroid_value_max
        self.robot_capacity = robot_capacity
        self.initial_money = initial_money
        self.initial_mining_capacity = initial_mining_capacity
        self.initial_discovery_range = initial_discovery_range
        self.initial_movement_range = initial_movement_range
        self.upgrade_mining_cost = upgrade_mining_cost
        self.mining_upgrade_amount = mining_upgrade_amount
        self.upgrade_discovery_cost = upgrade_discovery_cost
        self.discovery_upgrade_amount = discovery_upgrade_amount
        self.upgrade_movement_cost = upgrade_movement_cost
        self.movement_upgrade_amount = movement_upgrade_amount


class Asteroid:
    def __init__(self, id, x, y, resource, value):
        self.id = id
        self.x = x
        self.y = y
        self.resource = float(resource)
        self.value = float(value)
        self.robot_owner = None  # No robot planted initially

    def is_exhausted(self):
        return self.resource <= 0

    def __str__(self):
        s = f"Asteroid {self.id} at ({self.x},{self.y}): "
        if self.is_exhausted():
            s += "Exhausted"
        else:
            s += f"{self.resource:.1f} resources, Unit Value {self.value:.2f}"
        if self.robot_owner:
            s += f", Robot by {self.robot_owner.symbol}"
        return s


class Player:
    next_id = 1

    def __init__(self, name, x, y, settings: GameSettings):
        self.name = name
        self.symbol = f"P{Player.next_id}"
        Player.next_id += 1
        self.money = settings.initial_money
        self.mining_capacity = settings.initial_mining_capacity
        self.discovery_range = settings.initial_discovery_range
        self.movement_range = settings.initial_movement_range
        self.x = x
        self.y = y

    def __str__(self):
        return f"{self.symbol} ({self.name})"


# =================== Game Logic Class ===================

class Game:
    def __init__(self, settings: GameSettings):
        self.settings = settings
        self.grid_width = settings.grid_width
        self.grid_height = settings.grid_height
        self.num_asteroids = settings.num_asteroids
        self.players = []
        self.asteroids = []
        self.discovered_tiles = set()
        self.turn = 1
        self.initialize_players(settings.num_players)
        self.initialize_asteroids()

    def initialize_players(self, num_players):
        for i in range(num_players):
            x = random.randint(0, self.grid_width - 1)
            y = random.randint(0, self.grid_height - 1)
            self.players.append(Player(f"Player {i + 1}", x, y, self.settings))

    def initialize_asteroids(self):
        positions_used = set()
        asteroid_id = 1
        while len(self.asteroids) < self.num_asteroids:
            x = random.randint(0, self.grid_width - 1)
            y = random.randint(0, self.grid_height - 1)
            if (x, y) in positions_used:
                continue
            positions_used.add((x, y))
            resource = random.randint(self.settings.asteroid_min, self.settings.asteroid_max)
            value = random.uniform(self.settings.asteroid_value_min, self.settings.asteroid_value_max)
            self.asteroids.append(Asteroid(asteroid_id, x, y, resource, value))
            asteroid_id += 1

    def update_discovered(self):
        """For each player, add all tiles within his Manhattan discovery range."""
        for p in self.players:
            for x in range(self.grid_width):
                for y in range(self.grid_height):
                    if manhattan_distance(p.x, p.y, x, y) <= p.discovery_range:
                        self.discovered_tiles.add((x, y))

    def manual_mine(self, player, asteroid):
        if asteroid.is_exhausted():
            return f"Asteroid {asteroid.id} is exhausted."
        capacity = player.mining_capacity
        if asteroid.resource >= capacity:
            extraction = capacity
            asteroid.resource -= extraction
            gain = extraction * asteroid.value
            player.money += gain
            return (f"{player.symbol} manually mines {extraction} units from Asteroid {asteroid.id} "
                    f"and earns ${gain:.1f}.")
        else:
            extraction = asteroid.resource
            gain = extraction * asteroid.value
            player.money += gain
            asteroid.resource = 0
            return (f"{player.symbol} manually mines {extraction} units from Asteroid {asteroid.id} "
                    f"(all remaining) and earns ${gain:.1f}.")

    def robot_mining(self, log_func):
        for a in self.asteroids:
            if a.robot_owner and not a.is_exhausted():
                extraction = min(self.settings.robot_capacity, a.resource)
                gain = extraction * a.value
                a.resource -= extraction
                a.robot_owner.money += gain
                log_func(f"Robot on Asteroid {a.id} (owned by {a.robot_owner.symbol}) extracts "
                         f"{extraction} units and earns ${gain:.1f}.")

    def plant_robot(self, player):
        # Find an asteroid on the player's tile that is not exhausted and has no robot.
        asteroid = next((a for a in self.asteroids
                         if a.x == player.x and a.y == player.y and not a.is_exhausted() and a.robot_owner is None),
                        None)
        if asteroid:
            asteroid.robot_owner = player
            return f"{player.symbol} plants a mining robot on Asteroid {asteroid.id}."
        else:
            return "No suitable asteroid for planting a robot on this tile."

    def upgrade_player(self, player, upgrade_type, log_func):
        if upgrade_type == "mining":
            if player.money >= self.settings.upgrade_mining_cost:
                player.money -= self.settings.upgrade_mining_cost
                player.mining_capacity += self.settings.mining_upgrade_amount
                log_func(f"{player.symbol} upgraded mining capacity to {player.mining_capacity}.")
            else:
                log_func(f"{player.symbol} does not have enough money for mining upgrade.")
        elif upgrade_type == "discovery":
            if player.money >= self.settings.upgrade_discovery_cost:
                player.money -= self.settings.upgrade_discovery_cost
                player.discovery_range += self.settings.discovery_upgrade_amount
                log_func(f"{player.symbol} upgraded discovery range to {player.discovery_range}.")
            else:
                log_func(f"{player.symbol} does not have enough money for discovery upgrade.")
        elif upgrade_type == "movement":
            if player.money >= self.settings.upgrade_movement_cost:
                player.money -= self.settings.upgrade_movement_cost
                player.movement_range += self.settings.movement_upgrade_amount
                log_func(f"{player.symbol} upgraded movement range to {player.movement_range}.")
            else:
                log_func(f"{player.symbol} does not have enough money for movement upgrade.")

    def is_game_over(self):
        return all(a.is_exhausted() for a in self.asteroids)


# =================== Tkinter GUI Classes ===================

class SettingsGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Space Mining Game - Settings")
        self.configure(bg=DARK_BG)
        self.resizable(False, False)
        self.fields = {}
        entries = [
            ("Number of Players", "num_players", 2),
            ("Grid Width", "grid_width", 10),
            ("Grid Height", "grid_height", 10),
            ("Number of Asteroids", "num_asteroids", 12),
            ("Asteroid Resource Min", "asteroid_min", 100),
            ("Asteroid Resource Max", "asteroid_max", 1000),
            ("Asteroid Unit Value Min", "asteroid_value_min", 0.8),
            ("Asteroid Unit Value Max", "asteroid_value_max", 1.2),
            ("Robot Capacity", "robot_capacity", 10),
            ("Initial Money", "initial_money", 500),
            ("Initial Mining Capacity", "initial_mining_capacity", 100),
            ("Initial Discovery Range", "initial_discovery_range", 2),
            ("Initial Movement Range", "initial_movement_range", 2),
            ("Upgrade Mining Cost", "upgrade_mining_cost", 200),
            ("Mining Upgrade Amount", "mining_upgrade_amount", 10),
            ("Upgrade Discovery Cost", "upgrade_discovery_cost", 150),
            ("Discovery Upgrade Amount", "discovery_upgrade_amount", 1),
            ("Upgrade Movement Cost", "upgrade_movement_cost", 150),
            ("Movement Upgrade Amount", "movement_upgrade_amount", 1)
        ]
        row = 0
        for label_text, key, default in entries:
            tk.Label(self, text=label_text, bg=DARK_BG, fg=DARK_FG).grid(row=row, column=0, padx=5, pady=2, sticky="w")
            ent = tk.Entry(self, bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=DARK_FG)
            ent.insert(0, str(default))
            ent.grid(row=row, column=1, padx=5, pady=2)
            self.fields[key] = ent
            row += 1

        tk.Button(self, text="Start Game", command=self.start_game,
                  bg=BUTTON_BG, fg=BUTTON_FG).grid(row=row, column=0, columnspan=2, pady=10)

    def start_game(self):
        try:
            settings = GameSettings(
                num_players=int(self.fields["num_players"].get()),
                grid_width=int(self.fields["grid_width"].get()),
                grid_height=int(self.fields["grid_height"].get()),
                num_asteroids=int(self.fields["num_asteroids"].get()),
                asteroid_min=int(self.fields["asteroid_min"].get()),
                asteroid_max=int(self.fields["asteroid_max"].get()),
                asteroid_value_min=float(self.fields["asteroid_value_min"].get()),
                asteroid_value_max=float(self.fields["asteroid_value_max"].get()),
                robot_capacity=int(self.fields["robot_capacity"].get()),
                initial_money=int(self.fields["initial_money"].get()),
                initial_mining_capacity=int(self.fields["initial_mining_capacity"].get()),
                initial_discovery_range=int(self.fields["initial_discovery_range"].get()),
                initial_movement_range=int(self.fields["initial_movement_range"].get()),
                upgrade_mining_cost=int(self.fields["upgrade_mining_cost"].get()),
                mining_upgrade_amount=int(self.fields["mining_upgrade_amount"].get()),
                upgrade_discovery_cost=int(self.fields["upgrade_discovery_cost"].get()),
                discovery_upgrade_amount=int(self.fields["discovery_upgrade_amount"].get()),
                upgrade_movement_cost=int(self.fields["upgrade_movement_cost"].get()),
                movement_upgrade_amount=int(self.fields["movement_upgrade_amount"].get())
            )
        except Exception as e:
            messagebox.showerror("Error", f"Invalid settings: {e}")
            return

        game = Game(settings)
        self.destroy()  # close settings window
        game_gui = GameGUI(game)
        game_gui.mainloop()


class UpgradeGUI(tk.Toplevel):
    def __init__(self, parent, game, player):
        super().__init__(parent)
        self.title("Upgrade Options")
        self.configure(bg=DARK_BG)
        self.game = game
        self.player = player
        tk.Label(self, text="Select an attribute to upgrade:", bg=DARK_BG, fg=DARK_FG).pack(padx=10, pady=5)
        tk.Button(self, text=f"Upgrade Mining (Cost: {game.settings.upgrade_mining_cost})",
                  command=self.upgrade_mining, bg=BUTTON_BG, fg=BUTTON_FG).pack(padx=10, pady=5)
        tk.Button(self, text=f"Upgrade Discovery (Cost: {game.settings.upgrade_discovery_cost})",
                  command=self.upgrade_discovery, bg=BUTTON_BG, fg=BUTTON_FG).pack(padx=10, pady=5)
        tk.Button(self, text=f"Upgrade Movement (Cost: {game.settings.upgrade_movement_cost})",
                  command=self.upgrade_movement, bg=BUTTON_BG, fg=BUTTON_FG).pack(padx=10, pady=5)
        tk.Button(self, text="Close", command=self.destroy, bg=BUTTON_BG, fg=BUTTON_FG).pack(padx=10, pady=10)

    def upgrade_mining(self):
        self.game.upgrade_player(self.player, "mining", self.master.log)
        self.master.update_display()

    def upgrade_discovery(self):
        self.game.upgrade_player(self.player, "discovery", self.master.log)
        self.master.update_display()

    def upgrade_movement(self):
        self.game.upgrade_player(self.player, "movement", self.master.log)
        self.master.update_display()


class LeaderboardGUI(tk.Toplevel):
    def __init__(self, parent, game):
        super().__init__(parent)
        self.title("Leaderboard")
        self.configure(bg=DARK_BG)
        self.game = game
        tk.Label(self, text="Leaderboard", bg=DARK_BG, fg=DARK_FG, font=("Arial", 14, "bold")).pack(padx=10, pady=5)

        # Compute rankings.
        players = self.game.players
        # Top Money ranking.
        sorted_money = sorted(players, key=lambda p: p.money, reverse=True)
        # Compute total upgrades for each player.
        s = self.game.settings

        def total_upgrades(p):
            return ((p.mining_capacity - s.initial_mining_capacity) +
                    (p.discovery_range - s.initial_discovery_range) +
                    (p.movement_range - s.initial_movement_range))

        sorted_upgrades = sorted(players, key=total_upgrades, reverse=True)

        money_frame = tk.Frame(self, bg=DARK_BG)
        money_frame.pack(padx=10, pady=5, fill="both")
        tk.Label(money_frame, text="Top Money Owners:", bg=DARK_BG, fg=DARK_FG, font=("Arial", 12, "underline")).pack(
            anchor="w")
        for p in sorted_money:
            tk.Label(money_frame, text=f"{p.symbol} ({p.name}): ${p.money:.2f}", bg=DARK_BG, fg=DARK_FG).pack(
                anchor="w")

        upgrades_frame = tk.Frame(self, bg=DARK_BG)
        upgrades_frame.pack(padx=10, pady=5, fill="both")
        tk.Label(upgrades_frame, text="Top Ship Upgrades Owners:", bg=DARK_BG, fg=DARK_FG,
                 font=("Arial", 12, "underline")).pack(anchor="w")
        for p in sorted_upgrades:
            upg = total_upgrades(p)
            tk.Label(upgrades_frame, text=f"{p.symbol} ({p.name}): +{upg}", bg=DARK_BG, fg=DARK_FG).pack(anchor="w")

        tk.Button(self, text="Close", command=self.destroy, bg=BUTTON_BG, fg=BUTTON_FG).pack(pady=10)


class GameGUI(tk.Tk):
    def __init__(self, game: Game):
        super().__init__()
        self.title("Space Mining Game")
        self.configure(bg=DARK_BG)
        self.game = game
        self.current_player_index = 0
        # Flags for move mode and the selected tile.
        self.move_mode = False
        self.allowed_moves = set()
        self.selected_tile = None  # (x,y) for tile info selection
        self.create_widgets()
        self.update_display()

    def create_widgets(self):
        # --- Grid display (selectable) ---
        self.grid_frame = tk.Frame(self, bg=DARK_BG)
        self.grid_frame.grid(row=0, column=0, padx=10, pady=10)
        self.cell_labels = []
        for y in range(self.game.grid_height):
            row_labels = []
            for x in range(self.game.grid_width):
                lbl = tk.Label(self.grid_frame, text="??", width=4, height=2,
                               borderwidth=1, relief="solid",
                               bg=DARK_BG, fg=DARK_FG)
                lbl.grid(row=y, column=x, padx=1, pady=1)
                lbl.bind("<Button-1>", lambda e, x=x, y=y: self.on_grid_click(x, y))
                row_labels.append(lbl)
            self.cell_labels.append(row_labels)

        # --- Right frame containing game log and tile info ---
        self.right_frame = tk.Frame(self, bg=DARK_BG)
        self.right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="n")
        # Game Log
        log_container = tk.Frame(self.right_frame, bg=DARK_BG)
        log_container.pack()
        tk.Label(log_container, text="Game Log:", bg=DARK_BG, fg=DARK_FG).pack()
        self.log_text = tk.Text(log_container, width=40, height=15, state="disabled",
                                bg=DARK_BG, fg=DARK_FG, insertbackground=DARK_FG)
        self.log_text.pack()
        # Tile Information display
        info_container = tk.Frame(self.right_frame, bg=DARK_BG)
        info_container.pack(pady=5)
        tk.Label(info_container, text="Tile Information:", bg=DARK_BG, fg=DARK_FG).pack()
        self.point_info_label = tk.Label(info_container, text="Click a grid cell to see details.",
                                         justify="left", anchor="w", width=40, height=6,
                                         borderwidth=1, relief="solid",
                                         bg=DARK_BG, fg=DARK_FG)
        self.point_info_label.pack()

        # --- Controls ---
        self.control_frame = tk.Frame(self, bg=DARK_BG)
        self.control_frame.grid(row=1, column=0, columnspan=2, pady=10)
        self.player_info_label = tk.Label(self.control_frame, text="", bg=DARK_BG, fg=DARK_FG, justify="left")
        self.player_info_label.pack(pady=5)

        # Free action buttons
        free_actions_frame = tk.Frame(self.control_frame, bg=DARK_BG)
        free_actions_frame.pack(pady=5)
        tk.Button(free_actions_frame, text="Upgrade", command=self.open_upgrade_window,
                  bg=BUTTON_BG, fg=BUTTON_FG).pack(side="left", padx=5)
        tk.Button(free_actions_frame, text="Plant Robot", command=self.plant_robot,
                  bg=BUTTON_BG, fg=BUTTON_FG).pack(side="left", padx=5)
        tk.Button(free_actions_frame, text="Leaderboard", command=self.open_leaderboard_window,
                  bg=BUTTON_BG, fg=BUTTON_FG).pack(side="left", padx=5)

        # Main action buttons
        main_actions_frame = tk.Frame(self.control_frame, bg=DARK_BG)
        main_actions_frame.pack(pady=5)
        tk.Button(main_actions_frame, text="Move", command=self.move_player,
                  bg=BUTTON_BG, fg=BUTTON_FG).pack(side="left", padx=5)
        tk.Button(main_actions_frame, text="Mine", command=self.mine_action,
                  bg=BUTTON_BG, fg=BUTTON_FG).pack(side="left", padx=5)
        tk.Button(main_actions_frame, text="Pass", command=self.pass_action,
                  bg=BUTTON_BG, fg=BUTTON_FG).pack(side="left", padx=5)

    def format_player_info(self, player):
        s = (f"Active Player:\n"
             f"Name: {player.name} ({player.symbol})\n"
             f"Money: ${player.money:.2f}\n"
             f"Mining Capacity: {player.mining_capacity}\n"
             f"Discovery Range: {player.discovery_range}\n"
             f"Movement Range: {player.movement_range}\n"
             f"Position: ({player.x}, {player.y})")
        return s

    def log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def update_display(self):
        # Update discovered tiles
        self.game.update_discovered()
        active = self.get_current_player()
        for y in range(self.game.grid_height):
            for x in range(self.game.grid_width):
                # Default text if not discovered.
                if (x, y) not in self.game.discovered_tiles:
                    text = "??"
                else:
                    # Show players if present; else show asteroid if present; else dot.
                    cell_players = [p for p in self.game.players if p.x == x and p.y == y]
                    if cell_players:
                        text = "/".join([p.symbol for p in cell_players])
                    else:
                        asteroid_here = next((a for a in self.game.asteroids if a.x == x and a.y == y), None)
                        text = f"A{asteroid_here.id}" if asteroid_here else "."

                # Determine background color with priority:
                # 1. Active player's cell (green)
                # 2. Selected tile (purple)
                # 3. Allowed move cell (when in move mode)
                # 4. Field-of-view cell (subtle highlight)
                # 5. Otherwise default.
                if (x, y) == (active.x, active.y):
                    bg_color = ACTIVE_PLAYER_TILE_COLOR
                elif self.selected_tile == (x, y):
                    bg_color = SELECTED_TILE_COLOR
                elif self.move_mode and (x, y) in self.allowed_moves:
                    bg_color = ALLOWED_MOVE_COLOR
                elif (x, y) in self.game.discovered_tiles and manhattan_distance(active.x, active.y, x,
                                                                                 y) <= active.discovery_range:
                    bg_color = FIELD_OF_VIEW_COLOR
                else:
                    bg_color = DARK_BG
                self.cell_labels[y][x].config(text=text, bg=bg_color)
        # Update current player info
        self.player_info_label.config(text=self.format_player_info(active))

    def on_grid_click(self, x, y):
        # If in move mode, clicking an allowed tile executes the move.
        if self.move_mode:
            if (x, y) in self.allowed_moves:
                active = self.get_current_player()
                old = (active.x, active.y)
                active.x, active.y = x, y
                self.log(f"{active.symbol} moves from {old} to ({x},{y}).")
                self.move_mode = False
                self.allowed_moves = set()
                self.selected_tile = None
                self.update_display()
                self.after(500, self.next_turn)
            else:
                self.log("Tile not allowed for movement.")
            return
        # Otherwise, set the clicked tile as the selected tile for tile information.
        self.selected_tile = (x, y)
        info = f"Tile ({x},{y}):\n"
        if (x, y) not in self.game.discovered_tiles:
            info += "Not discovered yet."
        else:
            players_here = [p for p in self.game.players if p.x == x and p.y == y]
            asteroids_here = [a for a in self.game.asteroids if a.x == x and a.y == y]
            if players_here:
                info += "Players:\n" + "\n".join(str(p) for p in players_here) + "\n"
            if asteroids_here:
                for a in asteroids_here:
                    info += f"Asteroid {a.id}: Resource {a.resource:.1f}, Value {a.value:.2f}"
                    if a.robot_owner:
                        info += f" (Robot by {a.robot_owner.symbol})"
                    info += "\n"
            if not players_here and not asteroids_here:
                info += "Empty tile."
        self.point_info_label.config(text=info)
        self.update_display()

    def get_current_player(self):
        return self.game.players[self.current_player_index]

    def move_player(self):
        active = self.get_current_player()
        self.move_mode = True
        self.allowed_moves = set()
        # Allowed moves: any tile (except current) within movement range.
        for x in range(self.game.grid_width):
            for y in range(self.game.grid_height):
                if (x, y) != (active.x, active.y) and manhattan_distance(active.x, active.y, x,
                                                                         y) <= active.movement_range:
                    self.allowed_moves.add((x, y))
        self.log("Select a highlighted tile to move to.")
        self.update_display()

    def mine_action(self):
        active = self.get_current_player()
        asteroid = next((a for a in self.game.asteroids
                         if a.x == active.x and a.y == active.y and not a.is_exhausted()), None)
        if asteroid is None:
            self.log("No asteroid available for mining on this tile.")
        else:
            result = self.game.manual_mine(active, asteroid)
            self.log(result)
        self.update_display()
        self.after(500, self.next_turn)

    def pass_action(self):
        self.log(f"{self.get_current_player().symbol} passes.")
        self.update_display()
        self.after(500, self.next_turn)

    def next_turn(self):
        # Process automatic robot mining at turn's end.
        self.game.robot_mining(self.log)
        self.log(f"--- End of Turn {self.game.turn} ---")
        if self.game.is_game_over():
            self.log("All asteroids have been exhausted. Game over!")
            self.disable_controls()
            return
        # Advance to next player.
        self.current_player_index = (self.current_player_index + 1) % len(self.game.players)
        if self.current_player_index == 0:
            self.game.turn += 1
        self.selected_tile = None  # Clear any selected tile.
        self.update_display()

    def disable_controls(self):
        for child in self.control_frame.winfo_children():
            child.config(state="disabled")

    # --- Command methods for free actions ---
    def open_upgrade_window(self):
        active = self.get_current_player()
        UpgradeGUI(self, self.game, active)

    def plant_robot(self):
        active = self.get_current_player()
        result = self.game.plant_robot(active)
        self.log(result)
        self.update_display()

    def open_leaderboard_window(self):
        LeaderboardGUI(self, self.game)


# =================== Main ===================

if __name__ == "__main__":
    app = SettingsGUI()
    app.mainloop()
