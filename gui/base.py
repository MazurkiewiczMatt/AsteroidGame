
import tkinter as tk

from gameplay import Game

from constants import *  # Must include color constants, FONT_FAMILY, manhattan_distance, TIMER_DELAY_MS, etc.

from .panels import UpgradeGUI, LeaderboardGUI, AsteroidGraphGUI



# =============================================================================
# SUPERCLASS: Defines all points of interaction with the Game.
# (This class contains the “business‐logic” methods that call the Game API.)
# =============================================================================
class GameGUIBase(tk.Tk):
    def __init__(self, game: Game):
        super().__init__()
        self.game = game

        # UI–mode flags (these are not widget references but control the logic)
        self.move_mode = False
        self.remote_plant_mode = False
        self.debris_mode = False
        self.allowed_moves = set()
        self.allowed_remote_cells = set()
        self.allowed_debris_cells = set()
        self.selected_tile = None

        # Windows created by some actions (e.g. leaderboard)
        self.leaderboard_window = None
        self.asteroid_stats_window = None
        self.upgrade_window = None

        # Timer state
        self.timer_paused = False
        self.turn_timer_remaining = self.game.settings.turn_timer_duration

    # -------------------------
    # Abstract / “hook” methods
    # -------------------------
    def handle_tile_info(self, info: str):
        """
        Called to update tile-information display.
        Override this in the subclass to display the tile info in a widget.
        (The default implementation simply prints to console.)
        """
        print(info)

    def update_timer_display(self):
        """
        Update the timer display.
        Override this method to update the timer label in your UI.
        """
        pass

    def update_display(self):
        """
        Update the display based on game state.
        Override this method in the subclass to update all UI widgets.
        """
        raise NotImplementedError

    def create_widgets(self):
        """
        Create and layout all UI widgets.
        Override this method in the subclass.
        """
        raise NotImplementedError

    def update_ship_with_modules(self):
        """
        Update the composite ship image in the player info area.
        Override this method in the subclass.
        """
        raise NotImplementedError

    def disable_controls(self):
        """
        Disable UI controls when the game is over.
        Override in the subclass.
        """
        raise NotImplementedError

    # -------------------------
    # Game interaction methods
    # (These methods call the Game instance and update internal state.)
    # -------------------------
    def log(self, message: str):
        """
        Log a message. In the base class this just prints.
        The subclass can override this to update a log widget.
        """
        print(message)

    def on_grid_click(self, x: int, y: int):
        # If in debris deployment mode:
        if self.debris_mode:
            if (x, y) in self.allowed_debris_cells:
                self.selected_tile = (x, y)
                self.deploy_debris_torpedo()
            else:
                self.log("Tile not allowed for debris deployment.")
            return

        # If in movement mode:
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
                        self.move_mode = False
                        self.allowed_moves = set()
                        self.selected_tile = None
                        self.pause_timer_and_show_event(asteroid, event, active)
                        return
                    self.move_mode = False
                    self.allowed_moves = set()
                    self.selected_tile = None
                    warp = active.get_module("WarpDrive")
                    if warp is None:
                        self.reset_timer()
                        self.next_turn()
                    else:
                        if warp.level > 1 and (x, y) not in [(a.x, a.y) for a in self.game.asteroids] and not warp.used_this_turn:
                            warp.used_this_turn = True
                        else:
                            self.reset_timer()
                            self.next_turn()
            else:
                self.log("Tile not allowed for movement.")
            return

        # If in remote planting mode:
        if self.remote_plant_mode:
            if (x, y) in self.allowed_remote_cells:
                active = self.game.get_current_player()
                target = next((a for a in self.game.asteroids if a.x == x and a.y == y), None)
                if target is None:
                    self.log("No asteroid on this tile.")
                else:
                    message, _ = self.game.remote_plant_robot(active, target)
                    factory = active.get_module("Factory")
                    if factory is not None:
                        factory.robots_produced_this_turn += 1
                    self.log(message)
                    self.remote_plant_mode = False
                    self.allowed_remote_cells = set()
                    self.update_display()
                return
            else:
                self.log("Tile not allowed for planting.")
                return

        # Otherwise, simply update the tile info.
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
        self.handle_tile_info(info)
        self.update_display()

    def move_player(self):
        self.cancel_pending_actions()
        active = self.game.get_current_player()
        allowed, error = self.game.get_allowed_moves(active)
        if error:
            self.log(error)
            return
        self.allowed_moves = allowed
        self.move_mode = True
        self.log("Select a highlighted tile to move to.")
        self.update_display()

    def mine_action(self):
        self.cancel_pending_actions()
        active = self.game.get_current_player()
        asteroid = next((a for a in self.game.asteroids
                         if a.x == active.x and a.y == active.y and not a.is_exhausted()), None)
        if asteroid is None:
            self.log("No asteroid available for mining on this tile.")
        else:
            result = self.game.manual_mine(active, asteroid)
            self.log(result)
        self.update_display()
        self.reset_timer()
        self.next_turn()

    def pass_action(self):
        self.cancel_pending_actions()
        self.log(f"{self.game.get_current_player().symbol} passes.")
        self.update_display()
        self.reset_timer()
        self.next_turn()

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
            self.next_turn()

    def deploy_debris_torpedo(self):
        active = self.game.get_current_player()
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
            success, message = self.game.deploy_debris(active, self.selected_tile)
            if not success:
                self.log(message)
                return
            self.log(message)
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
        self.update_timer_display()

    def update_timer(self):
        if not self.timer_paused:
            self.turn_timer_remaining -= 1
        self.update_timer_display()
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
        self.update_display()
        self.next_turn()

    # -------------------------
    # Utility formatting methods (can be used by the subclass)
    # -------------------------
    def format_player_info(self, player):
        drill = player.get_module("Drill")
        telescope = player.get_module("Telescope")
        reactor = player.get_module("Reactor")
        launch_bay = player.get_module("LaunchBay")
        factory = player.get_module("Factory")
        info = f"{player.symbol}\n"
        info += f"   Drill (Mining Capacity): {drill.mining_capacity if drill else 'None'}\n"
        info += f"   Telescope (Discovery Range): {telescope.discovery_range if telescope else 'None'}\n"
        info += f"   Reactor (Movement Range): {reactor.movement_range if reactor else 'None'}\n\n"
        info += f"   LaunchBay (Robot Range): {launch_bay.robot_range if launch_bay else 'None'}\n"
        info += f"   Factory (Robot Capacity): {factory.robot_capacity if factory else 'None'}\n"
        if factory is not None:
            left = factory.robot_production - factory.robots_produced_this_turn
            total = factory.robot_production
            info += f"   Robots produced this turn: {left}/{total}\n"
        info += f"   Money earned by robots: {int(player.money_earned_by_robots)}\n"
        return info

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


    # -------------------------
    # Helper methods for checking action availability in UI
    # (These mirror the earlier checks in the original GameGUI.)
    # -------------------------
    def game_has_upgrade_robots_available(self):
        active = self.game.get_current_player()
        launch_bay = active.get_module("LaunchBay")
        factory = active.get_module("Factory")
        if launch_bay is None or factory is None:
            return False
        return any(
            a.robot and a.robot.owner == active and
            manhattan_distance(active.x, active.y, a.x, a.y) <= launch_bay.robot_range and
            a.robot.capacity < factory.robot_capacity
            for a in self.game.asteroids
        )

    def game_has_debris_available(self):
        active = self.game.get_current_player()
        return bool(self.game.get_debris_targets(active)) and active.money >= 200

    def game_has_mine_available(self):
        active = self.game.get_current_player()
        drill = active.get_module("Drill")
        if drill is None:
            return False
        return any(a for a in self.game.asteroids
                   if a.x == active.x and a.y == active.y and not a.is_exhausted())

    def game_has_hijack_available(self):
        active = self.game.get_current_player()
        return any(
            a for a in self.game.asteroids
            if a.x == active.x and a.y == active.y and a.robot is not None and
            a.robot.owner != active and not a.is_exhausted()
        )

