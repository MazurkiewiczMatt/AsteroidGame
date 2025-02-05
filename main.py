#!/usr/bin/env python3
import tkinter as tk
from tkinter import messagebox
import random
import math
from collections import deque

# ---------- Dark Theme Colors ----------
DARK_BG = "#2b2b2b"  # Base background for empty/discovered tiles
UNDISCOVERED_BG = "#1a1a1a"  # Background for undiscovered tiles
BUTTON_BG = "#444444"  # Button background
BUTTON_FG = "white"  # Button text
ENTRY_BG = "#333333"  # Entry background
ENTRY_FG = "white"  # Entry text
DARK_FG = "white"  # Default text color

# ---------- Highlight Colors ----------
ALLOWED_MOVE_COLOR = "#666666"  # Allowed move tiles
REMOTE_ALLOWED_COLOR = "#1E90FF"  # Allowed remote planting (blue)
SELECTED_TILE_COLOR = "#800080"  # Selected grid element (purple)
ACTIVE_PLAYER_TILE_COLOR = "#008000"  # Active player's cell
FIELD_OF_VIEW_COLOR = "#3a3a3a"  # Tiles within discovery range
DEBRIS_ALLOWED_COLOR = "#FF4500"  # Allowed debris deployment targets (orange-red)

# ---------- Tile Backgrounds for discovered tiles ----------
EMPTY_TILE_BG = DARK_BG
ASTEROID_BG = "#444444"  # Background for a tile that contains an asteroid
DEBRIS_BG = "#555555"  # Background for debris (impassable)

# ---------- Object Colors ----------
PLAYER_COLORS = ["#FF7F50", "#00FA9A", "#1E90FF", "#FFD700", "#FF69B4", "#ADFF2F"]
DEFAULT_ASTEROID_COLOR = "white"


# =================== Helper Functions ===================

def manhattan_distance(x1, y1, x2, y2):
    return abs(x1 - x2) + abs(y1 - y2)


# =================== Data Classes ===================

class GameSettings:
    def __init__(self,
                 num_players=3,
                 grid_width=16,
                 grid_height=16,asteroid_min=100,
                 asteroid_max=1000,
                 asteroid_value_min=0.8,
                 asteroid_value_max=2.0,
                 initial_money=500,
                 initial_mining_capacity=100,
                 initial_discovery_range=2,
                 initial_movement_range=2,
                 initial_robot_range=0,
                 upgrade_robot_range_cost=200,
                 robot_range_upgrade_amount=1,
                 upgrade_mining_cost=200,
                 mining_upgrade_amount=10,
                 upgrade_discovery_cost=150,
                 discovery_upgrade_amount=1,
                 upgrade_movement_cost=150,
                 movement_upgrade_amount=1,
                 initial_robot_capacity=10,
                 upgrade_robot_capacity_cost=200,
                 robot_capacity_upgrade_amount=5,
                 turn_timer_duration=30,
                 # New parameters for dynamic upgrade costs:
                 upgrade_mining_cost_increase=10,
                 upgrade_discovery_cost_increase=20,
                 upgrade_movement_cost_increase=20,
                 upgrade_robot_range_cost_increase=50,
                 upgrade_robot_capacity_cost_increase=50,
                 # New parameters: minimum and maximum asteroids to spawn.
                 min_asteroids=0,
                 max_asteroids=0):
        self.num_players = num_players
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.asteroid_min = asteroid_min
        self.asteroid_max = asteroid_max
        self.asteroid_value_min = asteroid_value_min
        self.asteroid_value_max = asteroid_value_max
        self.initial_money = initial_money
        self.initial_mining_capacity = initial_mining_capacity
        self.initial_discovery_range = initial_discovery_range
        self.initial_movement_range = initial_movement_range
        self.initial_robot_range = initial_robot_range
        self.upgrade_robot_range_cost = upgrade_robot_range_cost
        self.robot_range_upgrade_amount = robot_range_upgrade_amount
        self.upgrade_mining_cost = upgrade_mining_cost
        self.mining_upgrade_amount = mining_upgrade_amount
        self.upgrade_discovery_cost = upgrade_discovery_cost
        self.discovery_upgrade_amount = discovery_upgrade_amount
        self.upgrade_movement_cost = upgrade_movement_cost
        self.movement_upgrade_amount = movement_upgrade_amount
        self.initial_robot_capacity = initial_robot_capacity
        self.upgrade_robot_capacity_cost = upgrade_robot_capacity_cost
        self.robot_capacity_upgrade_amount = robot_capacity_upgrade_amount
        self.turn_timer_duration = turn_timer_duration
        # New upgrade cost increases:
        self.upgrade_mining_cost_increase = upgrade_mining_cost_increase
        self.upgrade_discovery_cost_increase = upgrade_discovery_cost_increase
        self.upgrade_movement_cost_increase = upgrade_movement_cost_increase
        self.upgrade_robot_range_cost_increase = upgrade_robot_range_cost_increase
        self.upgrade_robot_capacity_cost_increase = upgrade_robot_capacity_cost_increase
        # New asteroid spawn range parameters
        self.min_asteroids = min_asteroids
        self.max_asteroids = max_asteroids


class Robot:
    def __init__(self, owner, capacity):
        self.owner = owner
        self.capacity = capacity  # capacity frozen at deployment


class Asteroid:
    def __init__(self, id, x, y, resource, value):
        self.id = id
        self.x = x
        self.y = y
        self.resource = float(resource)
        self.value = float(value)
        self.robot = None  # Holds a Robot instance if planted

    def is_exhausted(self):
        return self.resource <= 0

    def __str__(self):
        s = f"Asteroid {self.id} at ({self.x},{self.y}): "
        if self.is_exhausted():
            s += "Exhausted"
        else:
            s += f"{self.resource:.1f} res, V:{self.value:.2f}"
        if self.robot:
            s += f", Robot by {self.robot.owner.symbol} (Cap: {self.robot.capacity})"
        return s


class Player:
    next_id = 1

    def __init__(self, name, x, y, settings: GameSettings):
        self.name = name
        self.symbol = f"P{Player.next_id}"
        self.color = PLAYER_COLORS[(Player.next_id - 1) % len(PLAYER_COLORS)]
        Player.next_id += 1
        self.money = settings.initial_money
        self.mining_capacity = settings.initial_mining_capacity
        self.discovery_range = settings.initial_discovery_range
        self.movement_range = settings.initial_movement_range
        self.robot_range = settings.initial_robot_range
        self.robot_capacity = settings.initial_robot_capacity
        self.upgrades_purchased = 0  # count of upgrades purchased
        self.total_mined = 0  # total mined resources
        self.x = x
        self.y = y
        # Initialize each player’s current upgrade costs:
        self.mining_upgrade_cost = settings.upgrade_mining_cost
        self.discovery_upgrade_cost = settings.upgrade_discovery_cost
        self.movement_upgrade_cost = settings.upgrade_movement_cost
        self.robot_range_upgrade_cost = settings.upgrade_robot_range_cost
        self.robot_capacity_upgrade_cost = settings.upgrade_robot_capacity_cost

    def __str__(self):
        return f"{self.symbol}"


class Game:
    def __init__(self, settings: GameSettings):
        self.settings = settings
        self.grid_width = settings.grid_width
        self.grid_height = settings.grid_height
        self.players = []
        self.asteroids = []
        self.discovered_tiles = set()
        self.debris = set()  # Cells where debris has been deployed (impassable)
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
        num_to_spawn = random.randint(self.settings.min_asteroids, self.settings.max_asteroids)
        while len(self.asteroids) < num_to_spawn:
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
        # For each player, add all tiles within their discovery range (based on current position).
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
            player.total_mined += extraction
            return (
                f"{player.symbol} manually mines {extraction} from A{asteroid.id} and immediately receives ${gain:.1f}.")
        else:
            extraction = asteroid.resource
            gain = extraction * asteroid.value
            player.money += gain
            player.total_mined += extraction
            asteroid.resource = 0
            return (
                f"{player.symbol} manually mines {extraction} from A{asteroid.id} (all) and immediately receives ${gain:.1f}.")

    def robot_mining(self, log_func):
        for a in self.asteroids:
            if a.robot and not a.is_exhausted():
                extraction = min(a.robot.capacity, a.resource)
                gain = extraction * a.value
                a.resource -= extraction
                a.robot.owner.money += gain
                a.robot.owner.total_mined += extraction
                log_func(
                    f"Robot on A{a.id} (owned by {a.robot.owner.symbol}, Cap: {a.robot.owner.robot_capacity}) extracts {extraction} and earns ${gain:.1f} at end of turn.")

    def plant_robot(self, player):
        # Local planting is only possible on the player's tile which is discovered.
        asteroid = next((a for a in self.asteroids if a.x == player.x and a.y == player.y and not a.is_exhausted()),
                        None)
        if asteroid is None:
            return ("No asteroid here for robot planting.", False)
        if player.money < 100:
            return ("Not enough money to plant robot.", False)
        player.money -= 100
        if asteroid.robot is None:
            asteroid.robot = Robot(player, player.robot_capacity)
            return (f"{player.symbol} plants a robot on A{asteroid.id} with capacity {player.robot_capacity}.", False)
        elif asteroid.robot.owner != player:
            asteroid.robot = Robot(player, player.robot_capacity)
            return (f"{player.symbol} hijacks the robot on A{asteroid.id} with capacity {player.robot_capacity}.", True)
        else:
            return ("You already own the robot here.", False)

    def remote_plant_robot(self, player, target):
        # Remote planting is allowed only if the asteroid's tile has been discovered.
        if target is None:
            return ("No valid asteroid at that location.", False)
        if (target.x, target.y) not in self.discovered_tiles:
            return ("Asteroid is undiscovered.", False)
        if target.is_exhausted():
            return ("Asteroid is exhausted.", False)
        if player.money < 100:
            return ("Not enough money to plant robot remotely.", False)
        # Disallow hijacking remotely.
        if target.robot is not None and target.robot.owner != player:
            return ("Cannot hijack robot remotely.", False)
        player.money -= 100
        if target.robot is None:
            target.robot = Robot(player, player.robot_capacity)
            return (
            f"{player.symbol} remotely plants a robot on A{target.id} with capacity {player.robot_capacity}.", False)
        else:
            return ("You already own the robot here.", False)

    def upgrade_robot_on_tile(self, player):
        # Look for an asteroid within the player's robot range that contains the player's robot.
        candidate = None
        for a in self.asteroids:
            if a.robot and a.robot.owner == player and manhattan_distance(player.x, player.y, a.x,
                                                                          a.y) <= player.robot_range:
                candidate = a
                break
        if candidate:
            if candidate.robot.capacity < player.robot_capacity:
                candidate.robot.capacity = player.robot_capacity
                return f"{player.symbol} upgrades robot on A{candidate.id} to capacity {player.robot_capacity}."
            else:
                return f"Robot on A{candidate.id} is already at current capacity."
        else:
            return "No robot within range to upgrade."

    def upgrade_player(self, player, upgrade_type, log_func):
        if upgrade_type == "mining":
            if player.money >= player.mining_upgrade_cost:
                cost = player.mining_upgrade_cost
                player.money -= cost
                player.mining_capacity += self.settings.mining_upgrade_amount
                player.upgrades_purchased += 1
                player.mining_upgrade_cost += self.settings.upgrade_mining_cost_increase
                log_func(
                    f"{player.symbol} mining capacity upgraded to {player.mining_capacity}. Next upgrade will cost ${player.mining_upgrade_cost}.")
            else:
                log_func(f"{player.symbol} lacks money for mining upgrade.")
        elif upgrade_type == "discovery":
            if player.money >= player.discovery_upgrade_cost:
                cost = player.discovery_upgrade_cost
                player.money -= cost
                player.discovery_range += self.settings.discovery_upgrade_amount
                player.upgrades_purchased += 1
                player.discovery_upgrade_cost += self.settings.upgrade_discovery_cost_increase
                log_func(
                    f"{player.symbol} discovery range upgraded to {player.discovery_range}. Next upgrade will cost ${player.discovery_upgrade_cost}.")
            else:
                log_func(f"{player.symbol} lacks money for discovery upgrade.")
        elif upgrade_type == "movement":
            if player.money >= player.movement_upgrade_cost:
                cost = player.movement_upgrade_cost
                player.money -= cost
                player.movement_range += self.settings.movement_upgrade_amount
                player.upgrades_purchased += 1
                player.movement_upgrade_cost += self.settings.upgrade_movement_cost_increase
                log_func(
                    f"{player.symbol} movement range upgraded to {player.movement_range}. Next upgrade will cost ${player.movement_upgrade_cost}.")
            else:
                log_func(f"{player.symbol} lacks money for movement upgrade.")
        elif upgrade_type == "robot_range":
            if player.money >= player.robot_range_upgrade_cost:
                cost = player.robot_range_upgrade_cost
                player.money -= cost
                player.robot_range += self.settings.robot_range_upgrade_amount
                player.upgrades_purchased += 1
                player.robot_range_upgrade_cost += self.settings.upgrade_robot_range_cost_increase
                log_func(
                    f"{player.symbol} robot range upgraded to {player.robot_range}. Next upgrade will cost ${player.robot_range_upgrade_cost}.")
            else:
                log_func(f"{player.symbol} lacks money for robot range upgrade.")
        elif upgrade_type == "robot_capacity":
            if player.money >= player.robot_capacity_upgrade_cost:
                cost = player.robot_capacity_upgrade_cost
                player.money -= cost
                player.robot_capacity += self.settings.robot_capacity_upgrade_amount
                player.upgrades_purchased += 1
                player.robot_capacity_upgrade_cost += self.settings.upgrade_robot_capacity_cost_increase
                log_func(
                    f"{player.symbol} robot capacity upgraded to {player.robot_capacity}. Next upgrade will cost ${player.robot_capacity_upgrade_cost}.")
            else:
                log_func(f"{player.symbol} lacks money for robot capacity upgrade.")

    def is_game_over(self):
        return all(a.is_exhausted() for a in self.asteroids)


# =================== UI Classes ===================

class SettingsGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Space Mining Game - Settings")
        self.configure(bg=DARK_BG)
        self.resizable(False, False)
        self.fields = {}
        entries = [
            ("Number of Players", "num_players", 3),
            ("Grid Width", "grid_width", 16),
            ("Grid Height", "grid_height", 16),
            ("Asteroid Resource Min", "asteroid_min", 100),
            ("Asteroid Resource Max", "asteroid_max", 1000),
            ("Asteroid Unit Value Min", "asteroid_value_min", 0.8),
            ("Asteroid Unit Value Max", "asteroid_value_max", 2.0),
            ("Initial Money", "initial_money", 500),
            ("Initial Mining Capacity", "initial_mining_capacity", 100),
            ("Initial Discovery Range", "initial_discovery_range", 2),
            ("Initial Movement Range", "initial_movement_range", 2),
            ("Initial Robot Range", "initial_robot_range", 0),
            ("Initial Robot Capacity", "initial_robot_capacity", 10),
            ("Upgrade Robot Range Cost", "upgrade_robot_range_cost", 200),
            ("Robot Range Upgrade Amount", "robot_range_upgrade_amount", 1),
            ("Upgrade Mining Cost", "upgrade_mining_cost", 200),
            ("Mining Upgrade Amount", "mining_upgrade_amount", 10),
            ("Upgrade Discovery Cost", "upgrade_discovery_cost", 150),
            ("Discovery Upgrade Amount", "discovery_upgrade_amount", 1),
            ("Upgrade Movement Cost", "upgrade_movement_cost", 150),
            ("Movement Upgrade Amount", "movement_upgrade_amount", 1),
            ("Upgrade Robot Capacity Cost", "upgrade_robot_capacity_cost", 200),
            ("Robot Capacity Upgrade Amount", "robot_capacity_upgrade_amount", 5),
            ("Turn Timer Duration (sec)", "turn_timer_duration", 50),
            # New upgrade cost increases:
            ("Upgrade Mining Cost Increase", "upgrade_mining_cost_increase", 10),
            ("Upgrade Discovery Cost Increase", "upgrade_discovery_cost_increase", 20),
            ("Upgrade Movement Cost Increase", "upgrade_movement_cost_increase", 20),
            ("Upgrade Robot Range Cost Increase", "upgrade_robot_range_cost_increase", 50),
            ("Upgrade Robot Capacity Cost Increase", "upgrade_robot_capacity_cost_increase", 50),
            ("Minimum Asteroids", "min_asteroids", 15),
            ("Maximum Asteroids", "max_asteroids", 25)
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
                asteroid_min=int(self.fields["asteroid_min"].get()),
                asteroid_max=int(self.fields["asteroid_max"].get()),
                asteroid_value_min=float(self.fields["asteroid_value_min"].get()),
                asteroid_value_max=float(self.fields["asteroid_value_max"].get()),
                initial_money=int(self.fields["initial_money"].get()),
                initial_mining_capacity=int(self.fields["initial_mining_capacity"].get()),
                initial_discovery_range=int(self.fields["initial_discovery_range"].get()),
                initial_movement_range=int(self.fields["initial_movement_range"].get()),
                initial_robot_range=int(self.fields["initial_robot_range"].get()),
                initial_robot_capacity=int(self.fields["initial_robot_capacity"].get()),
                upgrade_robot_range_cost=int(self.fields["upgrade_robot_range_cost"].get()),
                robot_range_upgrade_amount=int(self.fields["robot_range_upgrade_amount"].get()),
                upgrade_mining_cost=int(self.fields["upgrade_mining_cost"].get()),
                mining_upgrade_amount=int(self.fields["mining_upgrade_amount"].get()),
                upgrade_discovery_cost=int(self.fields["upgrade_discovery_cost"].get()),
                discovery_upgrade_amount=int(self.fields["discovery_upgrade_amount"].get()),
                upgrade_movement_cost=int(self.fields["upgrade_movement_cost"].get()),
                movement_upgrade_amount=int(self.fields["movement_upgrade_amount"].get()),
                upgrade_robot_capacity_cost=int(self.fields["upgrade_robot_capacity_cost"].get()),
                robot_capacity_upgrade_amount=int(self.fields["robot_capacity_upgrade_amount"].get()),
                turn_timer_duration=int(self.fields["turn_timer_duration"].get()),
                upgrade_mining_cost_increase=int(self.fields["upgrade_mining_cost_increase"].get()),
                upgrade_discovery_cost_increase=int(self.fields["upgrade_discovery_cost_increase"].get()),
                upgrade_movement_cost_increase=int(self.fields["upgrade_movement_cost_increase"].get()),
                upgrade_robot_range_cost_increase=int(self.fields["upgrade_robot_range_cost_increase"].get()),
                upgrade_robot_capacity_cost_increase=int(self.fields["upgrade_robot_capacity_cost_increase"].get()),
                min_asteroids=int(self.fields["min_asteroids"].get()),
                max_asteroids=int(self.fields["max_asteroids"].get())
            )
        except Exception as e:
            messagebox.showerror("Error", f"Invalid settings: {e}")
            return
        game = Game(settings)
        self.destroy()
        game_gui = GameGUI(game)
        game_gui.mainloop()


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


class GameGUI(tk.Tk):
    def __init__(self, game: Game):
        super().__init__()
        self.title("Space Mining Game")
        self.configure(bg=DARK_BG)
        self.game = game
        self.current_player_index = 0
        self.move_mode = False
        self.remote_plant_mode = False
        self.debris_mode = False  # New mode for debris deployment
        self.allowed_moves = set()
        self.allowed_remote_cells = set()
        self.allowed_debris_cells = set()  # Allowed cells for debris torpedo deployment
        self.selected_tile = None
        self.leaderboard_window = None
        self.asteroid_stats_window = None
        self.upgrade_window = None
        self.timer_paused = False
        self.turn_timer_remaining = self.game.settings.turn_timer_duration
        self.create_widgets()
        self.update_display()
        self.update_timer()

    def get_tile_properties(self, x, y):
        """Return (text, bg_color, fg_color) for tile at (x,y) using obstructed metric and debris."""
        if (x, y) in self.game.debris:
            return ("D", DEBRIS_BG, "white")
        if (x, y) not in self.game.discovered_tiles:
            return ("??", UNDISCOVERED_BG, DARK_FG)
        active = self.get_current_player()
        cell_players = [p for p in self.game.players if p.x == x and p.y == y]
        asteroid_here = next((a for a in self.game.asteroids if a.x == x and a.y == y), None)
        if cell_players:
            if len(cell_players) == 1:
                text = cell_players[0].symbol
                fg_color = cell_players[0].color
            else:
                text = "/".join(p.symbol for p in cell_players)
                fg_color = "white"
            bg_color = FIELD_OF_VIEW_COLOR
            if (x, y) == (active.x, active.y):
                bg_color = ACTIVE_PLAYER_TILE_COLOR
        else:
            if asteroid_here:
                text = f"A{asteroid_here.id}"
                if asteroid_here.is_exhausted():
                    fg_color = "black"
                elif asteroid_here.robot:
                    fg_color = asteroid_here.robot.owner.color
                else:
                    fg_color = "white"
                bg_color = ASTEROID_BG
            else:
                text = "."
                fg_color = DARK_FG
                bg_color = EMPTY_TILE_BG
        if self.selected_tile == (x, y):
            bg_color = SELECTED_TILE_COLOR
        if self.debris_mode and (x, y) in self.allowed_debris_cells:
            bg_color = DEBRIS_ALLOWED_COLOR
        return text, bg_color, fg_color

    def can_deploy_debris(self, cell):
        """Return (True, debris_region) if debris torpedo can be deployed at cell;
           otherwise (False, error message). Debris region is the center and its 4 orthogonal neighbors."""
        cx, cy = cell
        debris_region = {(cx, cy), (cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)}
        forbidden = set()
        for d in debris_region:
            x, y = d
            forbidden.update({(x, y), (x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)})
        for (x, y) in forbidden:
            if not (0 <= x < self.game.grid_width and 0 <= y < self.game.grid_height):
                continue
            for p in self.game.players:
                if (p.x, p.y) == (x, y):
                    return (False, "Debris region too close to a player.")
        return (True, debris_region)

    def cancel_pending_actions(self):
        self.move_mode = False
        self.remote_plant_mode = False
        self.debris_mode = False
        self.allowed_moves = set()
        self.allowed_remote_cells = set()
        self.allowed_debris_cells = set()
        self.selected_tile = None
        self.update_display()

    def create_widgets(self):
        # Game Board (Grid)
        self.grid_frame = tk.Frame(self, bg=DARK_BG)
        self.grid_frame.grid(row=0, column=0, padx=10, pady=10)
        self.cell_labels = []
        for y in range(self.game.grid_height):
            row_labels = []
            for x in range(self.game.grid_width):
                lbl = tk.Label(self.grid_frame, text="??", width=4, height=2,
                               borderwidth=1, relief="solid",
                               bg=UNDISCOVERED_BG, fg=DARK_FG)
                lbl.grid(row=y, column=x, padx=1, pady=1)
                lbl.bind("<Button-1>", lambda e, x=x, y=y: self.on_grid_click(x, y))
                row_labels.append(lbl)
            self.cell_labels.append(row_labels)
        # Right Panel for Log and Tile Info
        self.right_frame = tk.Frame(self, bg=DARK_BG)
        self.right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="n")
        log_container = tk.Frame(self.right_frame, bg=DARK_BG)
        log_container.pack()
        tk.Label(log_container, text="Game Log:", bg=DARK_BG, fg=DARK_FG).pack()
        self.log_text = tk.Text(log_container, width=40, height=15, state="disabled",
                                bg=DARK_BG, fg=DARK_FG, insertbackground=DARK_FG)
        self.log_text.pack()
        info_container = tk.Frame(self.right_frame, bg=DARK_BG)
        info_container.pack(pady=5)
        tk.Label(info_container, text="Tile Information:", bg=DARK_BG, fg=DARK_FG).pack()
        self.point_info_label = tk.Label(info_container, text="Click a grid cell to see details.",
                                         justify="left", anchor="w", width=40, height=6,
                                         borderwidth=1, relief="solid",
                                         bg=DARK_BG, fg=DARK_FG)
        self.point_info_label.pack()
        # Control Panels: Three Rows
        self.control_frame = tk.Frame(self, bg=DARK_BG)
        self.control_frame.grid(row=1, column=0, columnspan=2, pady=10)
        # --- UI Panels Row ---
        ui_panel_frame = tk.LabelFrame(self.control_frame, text="UI Panels", bg=DARK_BG, fg=DARK_FG)
        ui_panel_frame.pack(fill="x", pady=5)
        tk.Button(ui_panel_frame, text="Leaderboard",
                  command=lambda: [self.cancel_pending_actions(), self.open_leaderboard_window()],
                  bg=BUTTON_BG, fg=BUTTON_FG).pack(side="left", padx=5)
        tk.Button(ui_panel_frame, text="Asteroid Stats",
                  command=lambda: [self.cancel_pending_actions(), self.open_asteroid_graph_window()],
                  bg=BUTTON_BG, fg=BUTTON_FG).pack(side="left", padx=5)
        # --- Instant Actions Row ---
        instant_actions_frame = tk.LabelFrame(self.control_frame, text="Instant Actions", bg=DARK_BG, fg=DARK_FG)
        instant_actions_frame.pack(fill="x", pady=5)
        self.upgrade_general_button = tk.Button(instant_actions_frame, text="Upgrade (General)",
                                                command=lambda: [self.cancel_pending_actions(),
                                                                 self.open_upgrade_window()],
                                                bg=BUTTON_BG, fg=BUTTON_FG)
        self.upgrade_general_button.pack(side="left", padx=5)
        self.plant_robot_button = tk.Button(instant_actions_frame, text="Plant Robot ($100)",
                                            command=lambda: [self.cancel_pending_actions(), self.plant_robot()],
                                            bg=BUTTON_BG, fg=BUTTON_FG)
        self.plant_robot_button.pack(side="left", padx=5)
        self.remote_plant_robot_button = tk.Button(instant_actions_frame, text="Remote Plant Robot ($100)",
                                                   command=lambda: [self.cancel_pending_actions(),
                                                                    self.remote_plant_robot()],
                                                   bg=BUTTON_BG, fg=BUTTON_FG)
        self.remote_plant_robot_button.pack(side="left", padx=5)
        self.upgrade_robot_button = tk.Button(instant_actions_frame, text="Upgrade Robot",
                                              command=lambda: [self.cancel_pending_actions(), self.upgrade_robot()],
                                              bg=BUTTON_BG, fg=BUTTON_FG)
        self.upgrade_robot_button.pack(side="left", padx=5)
        self.pause_timer_button = tk.Button(instant_actions_frame, text="Pause Timer", command=self.toggle_timer,
                                            bg=BUTTON_BG, fg=BUTTON_FG)
        self.pause_timer_button.pack(side="left", padx=5)
        # --- Turn Actions Row ---
        turn_actions_frame = tk.LabelFrame(self.control_frame, text="Turn Actions", bg=DARK_BG, fg=DARK_FG)
        turn_actions_frame.pack(fill="x", pady=5)
        tk.Button(turn_actions_frame, text="Move", command=self.move_player,
                  bg=BUTTON_BG, fg=BUTTON_FG).pack(side="left", padx=5)
        self.mine_button = tk.Button(turn_actions_frame, text="Mine",
                                     command=lambda: [self.cancel_pending_actions(), self.mine_action()],
                                     bg=BUTTON_BG, fg=BUTTON_FG)
        self.mine_button.pack(side="left", padx=5)
        tk.Button(turn_actions_frame, text="Pass", command=lambda: [self.cancel_pending_actions(), self.pass_action()],
                  bg=BUTTON_BG, fg=BUTTON_FG).pack(side="left", padx=5)
        self.debris_button = tk.Button(turn_actions_frame, text="Deploy Debris Torpedo ($200)",
                                       command=lambda: [self.cancel_pending_actions(), self.deploy_debris_torpedo()],
                                       bg=BUTTON_BG, fg=BUTTON_FG)
        self.debris_button.pack(side="left", padx=5)
        self.timer_label = tk.Label(turn_actions_frame, text=f"Time remaining: {self.turn_timer_remaining}", bg=DARK_BG,
                                    fg=DARK_FG)
        self.timer_label.pack(side="left", padx=10)
        # Player and Tile Info
        info_columns = tk.Frame(self.control_frame, bg=DARK_BG)
        info_columns.pack()
        self.player_info_label = tk.Label(info_columns, text="", bg=DARK_BG, font=("Arial", 10, "bold"), justify="left")
        self.player_info_label.grid(row=0, column=0, padx=10)
        self.current_tile_info_label = tk.Label(info_columns, text="", bg=DARK_BG, fg=DARK_FG, font=("Arial", 10),
                                                justify="left")
        self.current_tile_info_label.grid(row=0, column=1, padx=10)

    def format_player_info(self, player):
        return (f"{player.symbol}\n"
                f"Economy:\n"
                f"   Money: ${player.money:.0f}\n"
                f"   Total Mined: {player.total_mined}\n"
                f"Capabilities:\n"
                f"   Mining Capacity: {player.mining_capacity}\n"
                f"   Discovery Range: {player.discovery_range}\n"
                f"   Movement Range: {player.movement_range}\n"
                f"Robot:\n"
                f"   Robot Range: {player.robot_range}\n"
                f"   Robot Capacity: {player.robot_capacity}\n"
                f"Upgrades:\n"
                f"   Upgrades Purchased: {player.upgrades_purchased}")

    def format_current_tile_info(self, player):
        x, y = player.x, player.y
        info = f"Tile ({x},{y}):\n"
        others = [p for p in self.game.players if p.x == x and p.y == y and p != player]
        if others:
            info += "Other Players: " + ", ".join(str(p) for p in others) + "\n"
        asteroid = next((a for a in self.game.asteroids if a.x == x and a.y == y), None)
        if asteroid:
            info += f"Asteroid A{asteroid.id}: {asteroid.resource:.0f} res, V:{asteroid.value:.2f}"
            if asteroid.robot:
                info += f" (Robot: {asteroid.robot.owner.symbol}, Cap: {asteroid.robot.capacity})"
        else:
            info += "No asteroid."
        return info

    def log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def update_display(self):
        self.game.update_discovered()
        active = self.get_current_player()
        if self.move_mode:
            reachable = self.get_reachable_cells((active.x, active.y), active.movement_range)
            self.allowed_moves = set(reachable.keys())
        if self.remote_plant_mode:
            reachable = self.get_reachable_cells((active.x, active.y), active.robot_range)
            self.allowed_remote_cells = {(a.x, a.y) for a in self.game.asteroids
                                         if (a.x, a.y) in reachable
                                         and (a.x, a.y) in self.game.discovered_tiles
                                         and not a.is_exhausted()
                                         and (a.robot is None or a.robot.owner != active)}
        for y in range(self.game.grid_height):
            for x in range(self.game.grid_width):
                text, bg_color, fg_color = self.get_tile_properties(x, y)
                if self.move_mode and (x, y) in self.allowed_moves:
                    bg_color = ALLOWED_MOVE_COLOR
                elif self.remote_plant_mode and (x, y) in self.allowed_remote_cells:
                    bg_color = REMOTE_ALLOWED_COLOR
                self.cell_labels[y][x].config(text=text, bg=bg_color, fg=fg_color)
        self.player_info_label.config(text=self.format_player_info(active), fg=active.color)
        self.current_tile_info_label.config(text=self.format_current_tile_info(active), fg=DARK_FG)
        mineable = any(a for a in self.game.asteroids if a.x == active.x and a.y == active.y and not a.is_exhausted())
        self.mine_button.config(state="normal" if mineable else "disabled")
        local_asteroid = next(
            (a for a in self.game.asteroids if a.x == active.x and a.y == active.y and not a.is_exhausted()), None)
        if local_asteroid and (
                local_asteroid.robot is None or local_asteroid.robot.owner != active) and active.money >= 100:
            self.plant_robot_button.config(state="normal")
        else:
            self.plant_robot_button.config(state="disabled")
        reachable = self.get_reachable_cells((active.x, active.y), active.robot_range)
        remote_candidates = {(a.x, a.y) for a in self.game.asteroids
                             if (a.x, a.y) != (active.x, active.y)
                             and (a.x, a.y) in reachable
                             and (a.x, a.y) in self.game.discovered_tiles
                             and not a.is_exhausted()
                             and (a.robot is None or a.robot.owner != active)}
        if active.robot_range > 0 and remote_candidates:
            self.remote_plant_robot_button.config(state="normal")
        else:
            self.remote_plant_robot_button.config(state="disabled")
        candidate = next((a for a in self.game.asteroids if
                          a.robot and a.robot.owner == active and manhattan_distance(active.x, active.y, a.x,
                                                                                     a.y) <= active.robot_range), None)
        if candidate and candidate.robot.capacity < active.robot_capacity:
            self.upgrade_robot_button.config(state="normal")
        else:
            self.upgrade_robot_button.config(state="disabled")
        self.debris_button.config(state="normal" if active.money >= 200 else "disabled")
        if self.leaderboard_window is not None:
            self.leaderboard_window.update_content()
        if self.asteroid_stats_window is not None:
            self.asteroid_stats_window.update_content()

    def on_grid_click(self, x, y):
        if self.debris_mode:
            if (x, y) in self.allowed_debris_cells:
                self.selected_tile = (x, y)
                self.deploy_debris_torpedo()  # Deploy immediately.
            else:
                self.log("Tile not allowed for debris deployment.")
            return
        if self.move_mode:
            if (x, y) in self.allowed_moves:
                active = self.get_current_player()
                old = (active.x, active.y)
                path = self.find_path(old, (x, y))
                if path:
                    for (px, py) in path:
                        for i in range(max(0, px - active.discovery_range),
                                       min(self.game.grid_width, px + active.discovery_range + 1)):
                            for j in range(max(0, py - active.discovery_range),
                                           min(self.game.grid_height, py + active.discovery_range + 1)):
                                if manhattan_distance(px, py, i, j) <= active.discovery_range:
                                    self.game.discovered_tiles.add((i, j))
                active.x, active.y = x, y
                self.log(f"{active.symbol} moves from {old} to ({x},{y}) via path {path}.")
                self.move_mode = False
                self.allowed_moves = set()
                self.selected_tile = None
                self.reset_timer()
                self.update_display()
                self.after(500, self.next_turn)
            else:
                self.log("Tile not allowed for movement.")
            return
        elif self.remote_plant_mode:
            if (x, y) in self.allowed_remote_cells:
                active = self.get_current_player()
                target = next((a for a in self.game.asteroids if a.x == x and a.y == y), None)
                if target is None:
                    self.log("No asteroid on this tile.")
                else:
                    message, hijack = self.game.remote_plant_robot(active, target)
                    self.log(message)
                    self.remote_plant_mode = False
                    self.allowed_remote_cells = set()
                    self.update_display()
                    if hijack:
                        self.after(500, self.next_turn)
                return
            else:
                self.log("Tile not allowed for remote planting.")
                return
        self.selected_tile = (x, y)
        info = f"Tile ({x},{y}):\n"
        if (x, y) not in self.game.discovered_tiles:
            info += "Not discovered yet."
        else:
            players_here = [p for p in self.game.players if p.x == x and p.y == y]
            asteroids_here = [a for a in self.game.asteroids if a.x == x and a.y == y]
            if players_here:
                info += "Players: " + ", ".join(str(p) for p in players_here) + "\n"
            if asteroids_here:
                for a in asteroids_here:
                    info += f"A{a.id}: {a.resource:.0f} res, V:{a.value:.2f}"
                    if a.robot:
                        info += f" (Robot: {a.robot.owner.symbol}, Cap: {a.robot.capacity})"
                    info += "\n"
            if not players_here and not asteroids_here:
                info += "Empty tile."
        self.point_info_label.config(text=info)
        self.update_display()

    def on_asteroid_selected(self, x, y):
        self.selected_tile = (x, y)
        self.update_display()

    def get_current_player(self):
        return self.game.players[self.current_player_index]

    def get_reachable_cells(self, start, max_distance):
        reachable = {}
        queue = deque()
        queue.append((start, 0))
        reachable[start] = 0
        while queue:
            (x, y), dist = queue.popleft()
            if dist >= max_distance:
                continue
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.game.grid_width and 0 <= ny < self.game.grid_height:
                    if (nx, ny) not in self.game.discovered_tiles:
                        continue
                    if (nx, ny) in self.game.debris:
                        continue
                    if (nx, ny) not in reachable or reachable[(nx, ny)] > dist + 1:
                        reachable[(nx, ny)] = dist + 1
                        queue.append(((nx, ny), dist + 1))
        return reachable

    def find_path(self, start, end):
        queue = deque()
        queue.append(start)
        prev = {start: None}
        while queue:
            current = queue.popleft()
            if current == end:
                break
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nxt = (current[0] + dx, current[1] + dy)
                if nxt in self.allowed_moves and nxt not in prev:
                    prev[nxt] = current
                    queue.append(nxt)
        if end not in prev:
            return []
        path = []
        cur = end
        while cur is not None:
            path.append(cur)
            cur = prev[cur]
        path.reverse()
        return path

    def move_player(self):
        self.cancel_pending_actions()
        active = self.get_current_player()
        reachable = self.get_reachable_cells((active.x, active.y), active.movement_range)
        self.allowed_moves = set(reachable.keys())
        self.move_mode = True
        self.log("Select a highlighted tile to move to.")
        self.update_display()

    def mine_action(self):
        self.cancel_pending_actions()
        active = self.get_current_player()
        asteroid = next(
            (a for a in self.game.asteroids if a.x == active.x and a.y == active.y and not a.is_exhausted()), None)
        if asteroid is None:
            self.log("No asteroid available for mining on this tile.")
        else:
            result = self.game.manual_mine(active, asteroid)
            self.log(result)
        self.update_display()
        self.reset_timer()
        self.after(500, self.next_turn)

    def pass_action(self):
        self.cancel_pending_actions()
        self.log(f"{self.get_current_player().symbol} passes.")
        self.update_display()
        self.reset_timer()
        self.after(500, self.next_turn)

    def plant_robot(self):
        self.cancel_pending_actions()
        active = self.get_current_player()
        message, hijack = self.game.plant_robot(active)
        self.log(message)
        self.update_display()
        if hijack:
            self.after(500, self.next_turn)

    def remote_plant_robot(self):
        self.cancel_pending_actions()
        active = self.get_current_player()
        reachable = self.get_reachable_cells((active.x, active.y), active.robot_range)
        self.allowed_remote_cells = {(a.x, a.y) for a in self.game.asteroids
                                     if (a.x, a.y) in reachable
                                     and (a.x, a.y) in self.game.discovered_tiles
                                     and not a.is_exhausted()
                                     and (a.robot is None or a.robot.owner != active)}
        if active.robot_range > 0 and self.allowed_remote_cells:
            self.remote_plant_mode = True
            self.log("Select a highlighted asteroid tile to remotely plant a robot (hijacking not allowed).")
        else:
            self.log("No valid remote asteroid targets available.")
        self.update_display()

    def upgrade_robot(self):
        self.cancel_pending_actions()
        active = self.get_current_player()
        result = self.game.upgrade_robot_on_tile(active)
        self.log(result)
        self.update_display()

    def deploy_debris_torpedo(self):
        active = self.get_current_player()
        if active.money < 200:
            self.log("Not enough money for debris torpedo.")
            return
        if not self.debris_mode:
            reachable = self.get_reachable_cells((active.x, active.y), active.robot_range)
            allowed = set()
            for cell in reachable:
                if any(a for a in self.game.asteroids if a.x == cell[0] and a.y == cell[1]):
                    continue
                valid, region = self.can_deploy_debris(cell)
                if valid:
                    allowed.add(cell)
            if not allowed:
                self.log("No valid debris deployment targets available.")
                return
            self.debris_mode = True
            self.allowed_debris_cells = allowed
            self.log("Select a highlighted tile to deploy debris torpedo.")
            self.update_display()
            return
        else:
            if self.selected_tile not in self.allowed_debris_cells:
                self.log("Selected tile is not a valid debris deployment target.")
                return
            valid, region = self.can_deploy_debris(self.selected_tile)
            if not valid:
                self.log("Selected tile fails debris deployment validation.")
                return
            active.money -= 200
            for tile in region:
                if any(a for a in self.game.asteroids if a.x == tile[0] and a.y == tile[1]):
                    continue
                self.game.debris.add(tile)
            self.log(
                f"{active.symbol} deploys debris torpedo at {self.selected_tile}. Debris covers {region} (asteroid tiles skipped).")
            self.debris_mode = False
            self.allowed_debris_cells = set()
            self.reset_timer()
            self.update_display()
            self.after(500, self.next_turn)

    def open_asteroid_graph_window(self):
        self.cancel_pending_actions()
        if self.asteroid_stats_window is None:
            self.asteroid_stats_window = AsteroidGraphGUI(self, self.game)
        else:
            self.asteroid_stats_window.lift()
            self.asteroid_stats_window.update_content()

    def open_leaderboard_window(self):
        self.cancel_pending_actions()
        if self.leaderboard_window is None:
            self.leaderboard_window = LeaderboardGUI(self, self.game)
        else:
            self.leaderboard_window.lift()
            self.leaderboard_window.update_content()

    def open_upgrade_window(self):
        self.cancel_pending_actions()
        active = self.get_current_player()
        if self.upgrade_window is not None:
            self.upgrade_window.destroy()
            self.upgrade_window = None
        self.upgrade_window = UpgradeGUI(self, self.game, active)

    def next_turn(self):
        if self.upgrade_window is not None:
            self.upgrade_window.destroy()
            self.upgrade_window = None
        self.game.robot_mining(self.log)
        self.log("Processing end-of-turn robot mining: resources are credited now.")
        self.log(f"--- End of Turn {self.game.turn} ---")
        if self.game.is_game_over():
            self.log("All asteroids exhausted. Game over!")
            self.disable_controls()
            return
        self.current_player_index = (self.current_player_index + 1) % len(self.game.players)
        if self.current_player_index == 0:
            self.game.turn += 1
        self.selected_tile = None
        self.reset_timer()
        self.update_display()

    def disable_controls(self):
        for child in self.control_frame.winfo_children():
            child.config(state="disabled")

    def reset_timer(self):
        self.turn_timer_remaining = self.game.settings.turn_timer_duration
        self.timer_label.config(text=f"Time remaining: {self.turn_timer_remaining}")

    def update_timer(self):
        if not self.timer_paused:
            self.turn_timer_remaining -= 1
        self.timer_label.config(text=f"Time remaining: {self.turn_timer_remaining}")
        if self.turn_timer_remaining <= 0:
            self.pass_action()
            self.reset_timer()
            self.update_timer()
        else:
            self.after(1000, self.update_timer)

    def toggle_timer(self):
        self.timer_paused = not self.timer_paused
        state = "paused" if self.timer_paused else "running"
        self.log(f"Timer {state}.")


# =================== Main ===================

if __name__ == "__main__":
    app = SettingsGUI()
    app.mainloop()
