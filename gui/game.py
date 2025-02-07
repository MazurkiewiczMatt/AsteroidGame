# game_gui.py

import tkinter as tk
from collections import deque
import random

from game import Game
from .panels import UpgradeGUI, LeaderboardGUI, AsteroidGraphGUI
from constants import *  # This must include color constants, FONT_FAMILY, manhattan_distance, etc.

# ----------------------------------------------------------------------
# UI Constants and Standardized Fonts
# ----------------------------------------------------------------------
UI_PADDING_SMALL = 5
UI_PADDING_MEDIUM = 10
UI_PADDING_GRID_CELL = 1

FONT_FAMILY = "Arial"
FONT_TIMER = (FONT_FAMILY, 30, "bold")
FONT_MONEY = (FONT_FAMILY, 24, "bold")
FONT_PLAYER_INFO = (FONT_FAMILY, 10, "bold")
FONT_TILE_INFO = (FONT_FAMILY, 10)
FONT_HEADER = (FONT_FAMILY, 14, "bold")
FONT_NORMAL = (FONT_FAMILY, 10)

GRID_CELL_WIDTH = 4
GRID_CELL_HEIGHT = 2
TEXT_WIDGET_WIDTH = 40
TEXT_WIDGET_HEIGHT = 15
INFO_LABEL_WIDTH = 40
INFO_LABEL_HEIGHT = 6

TIMER_DELAY_MS = 1000

# ----------------------------------------------------------------------
# Reusable Action Button class
# ----------------------------------------------------------------------
class GameActionButton(tk.Button):
    """
    A button that automatically shows or hides itself based on a condition.
    The condition is a callable (with no arguments) that returns True if the action is allowed.
    """
    def __init__(self, parent, label, command, condition, pack_opts=None, **kwargs):
        super().__init__(parent, text=label, command=command, **kwargs)
        self.condition = condition
        self.pack_opts = pack_opts if pack_opts is not None else {}

    def update_visibility(self):
        if self.condition():
            if not self.winfo_ismapped():
                self.pack(**self.pack_opts)
        else:
            if self.winfo_ismapped():
                self.pack_forget()

# ----------------------------------------------------------------------
# Action Panel class
# ----------------------------------------------------------------------
class ActionPanel(tk.LabelFrame):
    """
    A panel that contains a collection of GameActionButtons.
    The actions parameter is a list of tuples: (label, callback, condition).
    """
    def __init__(self, parent, title, actions, **kwargs):
        super().__init__(parent, text=title, **kwargs)
        self.action_buttons = []
        # For each action, create a GameActionButton and pack it.
        for (label, callback, condition) in actions:
            btn = GameActionButton(
                self, label, callback, condition,
                pack_opts={"side": "left", "padx": UI_PADDING_SMALL},
                bg=BUTTON_BG, fg=BUTTON_FG, font=FONT_NORMAL
            )
            self.action_buttons.append(btn)
            btn.pack(**btn.pack_opts)

    def update_buttons(self):
        for btn in self.action_buttons:
            btn.update_visibility()

# ----------------------------------------------------------------------
# Main Game GUI class
# ----------------------------------------------------------------------
class GameGUI(tk.Tk):
    def __init__(self, game: Game):
        super().__init__()
        self.title("Space Mining Game")
        self.configure(bg=DARK_BG)
        self.game = game
        # Modes for pending actions:
        self.move_mode = False
        self.remote_plant_mode = False
        self.debris_mode = False
        self.allowed_moves = set()
        self.allowed_remote_cells = set()
        self.allowed_debris_cells = set()
        self.selected_tile = None

        self.leaderboard_window = None
        self.asteroid_stats_window = None
        self.upgrade_window = None

        self.timer_paused = False
        self.turn_timer_remaining = self.game.settings.turn_timer_duration

        # Create all widgets
        self.create_widgets()
        self.update_display()
        self.update_timer()

    # ------------------------------------------------------------------
    # Helper methods for action availability
    # ------------------------------------------------------------------
    def game_has_upgrade_robots_available(self):
        active = self.game.get_current_player()
        return any(
            a.robot and a.robot.owner == active and
            manhattan_distance(active.x, active.y, a.x, a.y) <= active.robot_range and
            a.robot.capacity < active.robot_capacity
            for a in self.game.asteroids
        )

    def game_has_plant_robot_available(self):
        active = self.game.get_current_player()
        return bool(self.game.get_remote_plant_targets(active)) and active.money >= 100

    def game_has_debris_available(self):
        active = self.game.get_current_player()
        return bool(self.game.get_debris_targets(active)) and active.money >= 200

    def game_has_mine_available(self):
        active = self.game.get_current_player()
        return any(a for a in self.game.asteroids
                   if a.x == active.x and a.y == active.y and not a.is_exhausted())

    def game_has_hijack_available(self):
        active = self.game.get_current_player()
        return any(
            a for a in self.game.asteroids
            if a.x == active.x and a.y == active.y and a.robot is not None and
            a.robot.owner != active and not a.is_exhausted()
        )

    # ------------------------------------------------------------------
    # Widget creation
    # ------------------------------------------------------------------
    def create_widgets(self):
        # --- Top UI Panel: Buttons and Timer ---
        self.top_ui_frame = tk.Frame(self, bg=DARK_BG)
        self.top_ui_frame.grid(row=0, column=0, columnspan=2,
                                padx=UI_PADDING_MEDIUM, pady=UI_PADDING_SMALL, sticky="ew")

        ui_and_timer_frame = tk.Frame(self.top_ui_frame, bg=DARK_BG)
        ui_and_timer_frame.pack(fill="x")

        ui_panel_frame = tk.LabelFrame(ui_and_timer_frame, text="UI Panels",
                                       bg=DARK_BG, fg=DARK_FG, font=FONT_HEADER)
        ui_panel_frame.pack(side="left", fill="x", expand=True)
        tk.Button(ui_panel_frame, text="Leaderboard",
                  command=lambda: [self.cancel_pending_actions(), self.open_leaderboard_window()],
                  bg=BUTTON_BG, fg=BUTTON_FG, font=FONT_NORMAL).pack(side="left", padx=UI_PADDING_SMALL)
        tk.Button(ui_panel_frame, text="Asteroid Stats",
                  command=lambda: [self.cancel_pending_actions(), self.open_asteroid_graph_window()],
                  bg=BUTTON_BG, fg=BUTTON_FG, font=FONT_NORMAL).pack(side="left", padx=UI_PADDING_SMALL)
        self.pause_timer_button = tk.Button(ui_panel_frame, text="Pause Timer",
                                            command=self.toggle_timer,
                                            bg=BUTTON_BG, fg=BUTTON_FG, font=FONT_NORMAL)
        self.pause_timer_button.pack(side="left", padx=UI_PADDING_SMALL)

        self.timer_label = tk.Label(ui_and_timer_frame,
                                    text=f"{self.turn_timer_remaining}",
                                    bg=DARK_BG, fg=DARK_FG,
                                    font=FONT_TIMER)
        self.timer_label.pack(side="right", padx=UI_PADDING_MEDIUM)

        # --- Game Board (Grid) ---
        self.grid_frame = tk.Frame(self, bg=DARK_BG)
        self.grid_frame.grid(row=1, column=0, padx=UI_PADDING_MEDIUM, pady=UI_PADDING_MEDIUM)
        self.cell_labels = []
        for y in range(self.game.grid_height):
            row_labels = []
            for x in range(self.game.grid_width):
                lbl = tk.Label(self.grid_frame, text="??",
                               width=GRID_CELL_WIDTH, height=GRID_CELL_HEIGHT,
                               borderwidth=1, relief="solid",
                               bg=UNDISCOVERED_BG, fg=DARK_FG, font=FONT_NORMAL)
                lbl.grid(row=y, column=x, padx=UI_PADDING_GRID_CELL, pady=UI_PADDING_GRID_CELL)
                lbl.bind("<Button-1>", lambda e, x=x, y=y: self.on_grid_click(x, y))
                row_labels.append(lbl)
            self.cell_labels.append(row_labels)

        # --- Right Panel: Log and Tile Info ---
        self.right_frame = tk.Frame(self, bg=DARK_BG)
        self.right_frame.grid(row=1, column=1, padx=UI_PADDING_MEDIUM, pady=UI_PADDING_MEDIUM, sticky="n")
        log_container = tk.Frame(self.right_frame, bg=DARK_BG)
        log_container.pack()
        tk.Label(log_container, text="Game Log:", bg=DARK_BG, fg=DARK_FG, font=FONT_HEADER).pack()
        self.log_text = tk.Text(log_container,
                                width=TEXT_WIDGET_WIDTH, height=TEXT_WIDGET_HEIGHT,
                                state="disabled", bg=DARK_BG, fg=DARK_FG,
                                insertbackground=DARK_FG, font=FONT_NORMAL)
        self.log_text.pack()
        info_container = tk.Frame(self.right_frame, bg=DARK_BG)
        info_container.pack(pady=UI_PADDING_SMALL)
        tk.Label(info_container, text="Tile Information:", bg=DARK_BG, fg=DARK_FG, font=FONT_HEADER).pack()
        self.point_info_label = tk.Label(info_container,
                                         text="Click a grid cell to see details.",
                                         justify="left", anchor="w",
                                         width=INFO_LABEL_WIDTH, height=INFO_LABEL_HEIGHT,
                                         borderwidth=1, relief="solid",
                                         bg=DARK_BG, fg=DARK_FG, font=FONT_NORMAL)
        self.point_info_label.pack()

        # --- Bottom Panel: Actions and Info ---
        self.actions_frame = tk.Frame(self, bg=DARK_BG)
        self.actions_frame.grid(row=2, column=0, columnspan=2, padx=UI_PADDING_MEDIUM, sticky="n")

        # Define instant actions as a list of tuples: (label, callback, condition)
        instant_actions_data = [
            ("Upgrade Robots", self.upgrade_all_robots, lambda: self.game_has_upgrade_robots_available()),
            ("Plant Robot ($100)", self.remote_plant_robot, lambda: self.game_has_plant_robot_available()),
            ("Deploy Debris Torpedo ($200)", self.deploy_debris_torpedo, lambda: self.game_has_debris_available())
        ]
        self.instant_actions_panel = ActionPanel(
            self.actions_frame, "Instant Actions", instant_actions_data,
            bg=DARK_BG, fg=DARK_FG, font=FONT_HEADER
        )
        self.instant_actions_panel.pack(fill="x", pady=UI_PADDING_SMALL)

        # Define turn actions as a list of tuples.
        turn_actions_data = [
            ("Move", self.move_player, lambda: True),
            ("Mine", self.mine_action, lambda: self.game_has_mine_available()),
            ("Pass", self.pass_action, lambda: True),
            ("Hijack Robot", self.hijack_robot, lambda: self.game_has_hijack_available())
        ]
        self.turn_actions_panel = ActionPanel(
            self.actions_frame, "Turn Actions", turn_actions_data,
            bg=DARK_BG, fg=DARK_FG, font=FONT_HEADER
        )
        self.turn_actions_panel.pack(fill="x", pady=UI_PADDING_SMALL)

        # --- Bottom Info Panel ---
        self.bottom_frame = tk.Frame(self, bg=DARK_BG)
        self.bottom_frame.grid(row=3, column=0, columnspan=2, pady=UI_PADDING_MEDIUM, sticky="ew")
        self.money_label = tk.Label(self.bottom_frame, text="",
                                    bg=DARK_BG, fg=DARK_FG, font=FONT_MONEY)
        self.money_label.grid(row=0, column=0, rowspan=2, padx=UI_PADDING_MEDIUM, sticky="n")

        self.player_info_frame = tk.LabelFrame(self.bottom_frame, text="Player Info",
                                               bg=DARK_BG, fg=DARK_FG, font=FONT_HEADER)
        self.player_info_frame.grid(row=0, column=1, padx=UI_PADDING_MEDIUM, sticky="n")
        self.upgrade_general_button = tk.Button(self.player_info_frame, text="Upgrade",
                                                command=lambda: [self.cancel_pending_actions(), self.open_upgrade_window()],
                                                bg=BUTTON_BG, fg=BUTTON_FG, font=FONT_NORMAL)
        self.upgrade_general_button.pack(side="top", padx=UI_PADDING_SMALL)
        self.player_info_label = tk.Label(self.player_info_frame, text="",
                                          bg=DARK_BG, font=FONT_PLAYER_INFO, justify="left")
        self.player_info_label.pack(padx=UI_PADDING_SMALL, pady=UI_PADDING_SMALL)

        self.tile_info_frame = tk.LabelFrame(self.bottom_frame, text="Tile Info",
                                             bg=DARK_BG, fg=DARK_FG, font=FONT_HEADER)
        self.tile_info_frame.grid(row=0, column=2, padx=UI_PADDING_MEDIUM, sticky="n")
        self.current_tile_info_label = tk.Label(self.tile_info_frame, text="",
                                                bg=DARK_BG, fg=DARK_FG, font=FONT_TILE_INFO, justify="left")
        self.current_tile_info_label.pack(padx=UI_PADDING_SMALL, pady=UI_PADDING_SMALL)

        self.bottom_frame.grid_columnconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(1, weight=1)
        self.bottom_frame.grid_columnconfigure(2, weight=1)

    # ------------------------------------------------------------------
    # Display and Update methods
    # ------------------------------------------------------------------
    def update_display(self):
        self.game.update_discovered()
        active = self.game.get_current_player()
        self.money_label.config(text=f"${active.money:.0f}")

        if self.move_mode:
            reachable = self.game.get_reachable_cells((active.x, active.y), active.movement_range)
            self.allowed_moves = set(reachable.keys())
        if self.remote_plant_mode:
            self.allowed_remote_cells = self.game.get_remote_plant_targets(active)

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

        # Update our action panels (they each check their condition)
        self.instant_actions_panel.update_buttons()
        self.turn_actions_panel.update_buttons()

        
        if self.leaderboard_window is not None:
            self.leaderboard_window.update_content()
        if self.asteroid_stats_window is not None:
            self.asteroid_stats_window.update_content()

    def get_tile_properties(self, x, y):
        if (x, y) in self.game.debris:
            return ("D", DEBRIS_BG, "white")
        if (x, y) not in self.game.discovered_tiles:
            return ("??", UNDISCOVERED_BG, DARK_FG)
        active = self.game.get_current_player()
        cell_players = [p for p in self.game.players if p.x == x and p.y == y]
        asteroid_here = next((a for a in self.game.asteroids if a.x == x and a.y == y), None)
        if cell_players:
            if len(cell_players) == 1:
                text = cell_players[0].symbol
                fg_color = cell_players[0].color
            else:
                text = "/".join(p.symbol for p in cell_players)
                fg_color = "white"
            if (x, y) == (active.x, active.y):
                bg_color = ACTIVE_PLAYER_TILE_COLOR
            elif asteroid_here:
                bg_color = asteroid_here.color
                if asteroid_here.is_exhausted():
                    bg_color = ASTEROID_BG
            else:
                bg_color = EMPTY_TILE_BG
        else:
            if asteroid_here:
                text = f"A{asteroid_here.id}"
                fg_color = asteroid_here.robot.owner.color if asteroid_here.robot else "white"
                bg_color = asteroid_here.color
                if asteroid_here.is_exhausted():
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

    def format_player_info(self, player):
        return (f"{player.symbol}\n"
                f"   Mining Capacity: {player.mining_capacity}\n"
                f"   Discovery Range: {player.discovery_range}\n"
                f"   Movement Range: {player.movement_range}\n"
                f"   Robot Range: {player.robot_range}\n"
                f"   Robot Capacity: {player.robot_capacity}\n")

    def format_current_tile_info(self, player):
        x, y = player.x, player.y
        info = f"Tile ({x},{y}):\n"
        others = [p for p in self.game.players if p.x == x and p.y == y and p != player]
        if others:
            info += "Other Players: " + ", ".join(str(p) for p in others) + "\n"
        asteroid = next((a for a in self.game.asteroids if a.x == x and a.y == y), None)
        if asteroid:
            info += f"Asteroid A{asteroid.id} ({asteroid.asteroid_type}): {asteroid.resource:.0f} resources, value:{asteroid.value:.2f}"
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

    # ------------------------------------------------------------------
    # Event Handlers and Action Callbacks
    # ------------------------------------------------------------------
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
                active = self.game.get_current_player()
                success, result = self.game.move_player(active, (x, y))
                if not success:
                    self.log(result)
                else:
                    message, event, path, asteroid = result
                    self.log(message)
                    if event:
                        self.pause_timer_and_show_event(asteroid, event, active)
                        return
                self.move_mode = False
                self.allowed_moves = set()
                self.selected_tile = None
                self.reset_timer()
                self.update_display()
                self.after(50, self.next_turn)
            else:
                self.log("Tile not allowed for movement.")
            return
        elif self.remote_plant_mode:
            if (x, y) in self.allowed_remote_cells:
                active = self.game.get_current_player()
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
                    info += f"A{a.id}: {a.resource:.0f} resource, value:{a.value:.2f} ({'visited' if a.visited else 'undiscovered'})"
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

    def move_player(self):
        self.cancel_pending_actions()
        active = self.game.get_current_player()
        reachable = self.game.get_reachable_cells((active.x, active.y), active.movement_range)
        self.allowed_moves = set(reachable.keys())
        self.move_mode = True
        self.log("Select a highlighted tile to move to.")
        self.update_display()

    def mine_action(self):
        self.cancel_pending_actions()
        active = self.game.get_current_player()
        asteroid = next((a for a in self.game.asteroids if a.x == active.x and a.y == active.y and not a.is_exhausted()), None)
        if asteroid is None:
            self.log("No asteroid available for mining on this tile.")
        else:
            result = self.game.manual_mine(active, asteroid)
            self.log(result)
        self.update_display()
        self.reset_timer()
        self.after(50, self.next_turn)

    def pass_action(self):
        self.cancel_pending_actions()
        self.log(f"{self.game.get_current_player().symbol} passes.")
        self.update_display()
        self.reset_timer()
        self.after(50, self.next_turn)

    def remote_plant_robot(self):
        self.cancel_pending_actions()
        active = self.game.get_current_player()
        self.remote_plant_mode = True
        self.allowed_remote_cells = self.game.get_remote_plant_targets(active)
        if self.allowed_remote_cells and active.money >= 100:
            self.log("Select a highlighted asteroid tile to plant a robot ($100).")
        else:
            self.log("No valid asteroid targets available for planting.")
            self.remote_plant_mode = False
        self.update_display()

    def hijack_robot(self):
        self.cancel_pending_actions()
        active = self.game.get_current_player()
        result, flag = self.game.hijack_robot(active)
        self.log(result)
        self.update_display()
        if flag:
            self.after(50, self.next_turn)

    def deploy_debris_torpedo(self):
        active = self.game.get_current_player()
        if active.money < 200:
            self.log("Not enough money for debris torpedo.")
            return
        if not self.debris_mode:
            allowed = self.game.get_debris_targets(active)
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
            valid, region = self.game.can_deploy_debris(self.selected_tile)
            if not valid:
                self.log("Selected tile fails debris deployment validation.")
                return
            active.money -= 200
            for tile in region:
                if any(a for a in self.game.asteroids if a.x == tile[0] and a.y == tile[1]):
                    continue
                self.game.debris.add(tile)
            self.log(f"{active.symbol} deploys debris torpedo at {self.selected_tile}. Debris covers {region} (asteroid tiles skipped).")
            self.debris_mode = False
            self.allowed_debris_cells = set()
            self.update_display()

    def upgrade_all_robots(self):
        active = self.game.get_current_player()
        messages = self.game.upgrade_all_robots(active)
        for msg in messages:
            self.log(msg)
        self.update_display()

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
        active = self.game.get_current_player()
        if self.upgrade_window is not None:
            self.upgrade_window.destroy()
            self.upgrade_window = None
        self.upgrade_window = UpgradeGUI(self, self.game, active)

    def next_turn(self):
        if self.upgrade_window is not None:
            self.upgrade_window.destroy()
            self.upgrade_window = None
        self.game.robot_mining(self.log)
        self.log(f"--- End of Turn {self.game.turn} ---")
        if self.game.is_game_over():
            self.log("All asteroids exhausted. Game over!")
            self.disable_controls()
            return
        self.game.next_turn()
        self.selected_tile = None
        self.reset_timer()
        self.update_display()

    def disable_controls(self):
        for child in self.bottom_frame.winfo_children():
            child.config(state="disabled")

    def cancel_pending_actions(self):
        self.move_mode = False
        self.remote_plant_mode = False
        self.debris_mode = False
        self.allowed_moves = set()
        self.allowed_remote_cells = set()
        self.allowed_debris_cells = set()
        self.selected_tile = None
        self.update_display()

    def reset_timer(self):
        self.turn_timer_remaining = self.game.settings.turn_timer_duration
        self.timer_label.config(text=f"{self.turn_timer_remaining}")

    def update_timer(self):
        if not self.timer_paused:
            self.turn_timer_remaining -= 1
        self.timer_label.config(text=f"{self.turn_timer_remaining}")
        if self.turn_timer_remaining <= 0:
            self.pass_action()
            self.reset_timer()
            self.update_timer()
        else:
            self.after(TIMER_DELAY_MS, self.update_timer)

    def toggle_timer(self):
        self.timer_paused = not self.timer_paused
        state = "paused" if self.timer_paused else "running"
        self.log(f"Timer {state}.")

    def pause_timer_and_show_event(self, asteroid, event, player):
        self.timer_paused = True
        event_text = event if event is not None else f"You have encountered a mysterious event on Asteroid A{asteroid.id}."
        self.event_window = tk.Toplevel(self)
        self.event_window.title(f"Asteroid Event A{asteroid.id}")
        self.event_window.configure(bg=DARK_BG)
        label = tk.Label(self.event_window,
                         text=f"{event_text}\nPress 'Confirm' to continue.",
                         padx=10, pady=10,
                         bg=DARK_BG, fg=DARK_FG, font=FONT_NORMAL)
        label.pack()
        confirm_button = tk.Button(self.event_window,
                                   text="Confirm",
                                   command=self.on_event_confirm,
                                   bg=BUTTON_BG, fg=BUTTON_FG, font=FONT_NORMAL)
        confirm_button.pack(padx=10, pady=10)
        self.event_window.protocol("WM_DELETE_WINDOW", self.on_event_confirm)

    def on_event_confirm(self):
        if hasattr(self, 'event_window') and self.event_window:
            self.event_window.destroy()
            self.event_window = None
        self.timer_paused = False
        self.next_turn()
