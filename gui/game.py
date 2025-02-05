import tkinter as tk
from collections import deque

from game import Game
from .panels import UpgradeGUI, LeaderboardGUI, AsteroidGraphGUI
from constants import *  # This includes helper functions (e.g. manhattan_distance) and color constants

class GameGUI(tk.Tk):
    def __init__(self, game: Game):
        super().__init__()
        self.title("Space Mining Game")
        self.configure(bg=DARK_BG)
        self.game = game
        self.current_player_index = 0
        self.move_mode = False
        self.remote_plant_mode = False  # For planting a robot (remote planting)
        self.debris_mode = False  # For debris torpedo deployment
        self.allowed_moves = set()
        self.allowed_remote_cells = set()  # Allowed cells for planting a robot
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
        """Return (text, bg_color, fg_color) for the tile at (x,y), showing debris, discovered status, players, asteroids, etc."""
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
        # REMOTE planting is now the only planting action (costs $100)
        self.plant_robot_button = tk.Button(instant_actions_frame, text="Plant Robot ($100)",
                                            command=lambda: [self.cancel_pending_actions(), self.remote_plant_robot()],
                                            bg=BUTTON_BG, fg=BUTTON_FG)
        self.plant_robot_button.pack(side="left", padx=5)
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
        # New Hijack action (turn action)
        self.hijack_robot_button = tk.Button(turn_actions_frame, text="Hijack Robot",
                                             command=lambda: [self.cancel_pending_actions(), self.hijack_robot()],
                                             bg=BUTTON_BG, fg=BUTTON_FG)
        self.hijack_robot_button.pack(side="left", padx=5)
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
        # Movement: update allowed moves if in move_mode.
        if self.move_mode:
            reachable = self.get_reachable_cells((active.x, active.y), active.movement_range)
            self.allowed_moves = set(reachable.keys())
        # Remote planting: update allowed cells for planting a robot.
        if self.remote_plant_mode:
            reachable = self.get_reachable_cells((active.x, active.y), active.robot_range)
            self.allowed_remote_cells = {(a.x, a.y) for a in self.game.asteroids
                                         if (a.x, a.y) in reachable
                                         and (a.x, a.y) in self.game.discovered_tiles
                                         and not a.is_exhausted()
                                         and (a.robot is None)}
        # Update each cell on the grid.
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
        # Update Mine button state.
        mineable = any(a for a in self.game.asteroids if a.x == active.x and a.y == active.y and not a.is_exhausted())
        self.mine_button.config(state="normal" if mineable else "disabled")
        # Update Plant Robot button (instant action) based on valid remote planting options.
        reachable = self.get_reachable_cells((active.x, active.y), active.robot_range)
        plant_candidates = {(a.x, a.y) for a in self.game.asteroids
                             if (a.x, a.y) in reachable
                             and (a.x, a.y) in self.game.discovered_tiles
                             and not a.is_exhausted()
                             and (a.robot is None)}
        if plant_candidates and active.money >= 100:
            self.plant_robot_button.config(state="normal")
        else:
            self.plant_robot_button.config(state="disabled")
        # Update Hijack Robot button (turn action): enable only if on an asteroid with another player's robot.
        hijack_candidate = next((a for a in self.game.asteroids
                                 if a.x == active.x and a.y == active.y
                                 and a.robot is not None
                                 and a.robot.owner != active
                                 and not a.is_exhausted()), None)
        if hijack_candidate:
            self.hijack_robot_button.config(state="normal")
        else:
            self.hijack_robot_button.config(state="disabled")
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
                    message, _ = self.game.remote_plant_robot(active, target)
                    self.log(message)
                    self.remote_plant_mode = False
                    self.allowed_remote_cells = set()
                    self.update_display()
                return
            else:
                self.log("Tile not allowed for planting.")
                return
        # Default: select tile to view its info.
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

    def remote_plant_robot(self):
        """Initiate remote planting (i.e. planting a robot) by highlighting valid asteroid tiles."""
        self.cancel_pending_actions()
        active = self.get_current_player()
        reachable = self.get_reachable_cells((active.x, active.y), active.robot_range)
        self.remote_plant_mode = True
        self.allowed_remote_cells = {(a.x, a.y) for a in self.game.asteroids
                                     if (a.x, a.y) in reachable
                                     and (a.x, a.y) in self.game.discovered_tiles
                                     and not a.is_exhausted()
                                     and (a.robot is None)}
        if self.allowed_remote_cells and active.money >= 100:
            self.log("Select a highlighted asteroid tile to plant a robot ($100).")
        else:
            self.log("No valid asteroid targets available for planting.")
            self.remote_plant_mode = False
        self.update_display()

    def hijack_robot(self):
        """Attempt to hijack the robot on the asteroid at the current player's location."""
        self.cancel_pending_actions()
        active = self.get_current_player()
        result, hijack_flag = self.game.hijack_robot(active)
        self.log(result)
        self.update_display()
        if hijack_flag:
            self.after(500, self.next_turn)

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
