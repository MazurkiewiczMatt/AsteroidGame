import tkinter as tk
from PIL import Image, ImageTk

from gameplay import Game

from constants import *

from .utils import get_module_image_pil
from .action import ActionPanel
from .base import GameGUIBase

# =============================================================================
# SUBCLASS: Implements the display (UI) using Tkinter.
# This class creates the widgets, updates the display, and calls the base class’s
# game-interaction methods when buttons are pressed.
# =============================================================================
class GameGUI(GameGUIBase):
    def __init__(self, game: Game):
        super().__init__(game)
        self.title("Space Mining Game")
        self.configure(bg=DARK_BG)
        self.create_widgets()
        self.update_display()
        self.update_timer()

    # -------------------------
    # Create all UI widgets
    # -------------------------
    def create_widgets(self):
        # Top UI Panel: Buttons and Timer
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

        # Game Board (Grid)
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

        # Right frame for log and player info
        self.right_frame = tk.Frame(self, bg=DARK_BG)
        self.right_frame.grid(row=1, column=1, padx=UI_PADDING_MEDIUM, pady=UI_PADDING_MEDIUM, sticky="n")

        # Log container
        log_container = tk.Frame(self.right_frame, bg=DARK_BG)
        log_container.pack()
        tk.Label(log_container, text="Game Log:", bg=DARK_BG, fg=DARK_FG, font=FONT_HEADER).pack()
        self.log_text = tk.Text(log_container,
                                 width=TEXT_WIDGET_WIDTH,
                                 height=TEXT_WIDGET_HEIGHT,
                                 state="disabled",
                                 bg=DARK_BG,
                                 fg=DARK_FG,
                                 insertbackground=DARK_FG,
                                 font=FONT_NORMAL)
        self.log_text.pack()

        # Player Info Frame
        self.player_info_frame = tk.LabelFrame(self.right_frame, text="Player Info",
                                               bg=DARK_BG, fg=DARK_FG, font=FONT_HEADER)
        self.player_info_frame.pack(fill="x", padx=UI_PADDING_SMALL, pady=UI_PADDING_SMALL)
        self.upgrade_general_button = tk.Button(self.player_info_frame, text="Upgrade",
                                                command=lambda: [self.cancel_pending_actions(), self.open_upgrade_window()],
                                                bg=BUTTON_BG, fg=BUTTON_FG, font=FONT_NORMAL)
        self.upgrade_general_button.pack(side="top", padx=UI_PADDING_SMALL)
        self.player_info_label = tk.Label(self.player_info_frame, compound="bottom", bg=DARK_BG)
        self.player_info_label.pack(padx=UI_PADDING_SMALL, pady=UI_PADDING_SMALL)

        # Bottom Panel: Actions and Info
        self.actions_frame = tk.Frame(self, bg=DARK_BG)
        self.actions_frame.grid(row=2, column=0, columnspan=2, padx=UI_PADDING_MEDIUM, sticky="n")
        instant_actions_data = [
            ("Upgrade Robots", self.upgrade_all_robots, lambda: self.game_has_upgrade_robots_available()),
            (f"Plant Robot ($100)", self.remote_plant_robot, lambda: self.game.get_remote_plant_targets(self.game.get_current_player()) and self.game.get_current_player().money >= 100),
            ("Deploy Debris Torpedo ($200)", self.deploy_debris_torpedo, lambda: self.game_has_debris_available())
        ]
        self.instant_actions_panel = ActionPanel(self.actions_frame, "Instant Actions", instant_actions_data,
                                                  bg=DARK_BG, fg=DARK_FG, font=FONT_HEADER)
        self.instant_actions_panel.pack(fill="x", pady=UI_PADDING_SMALL)
        turn_actions_data = [
            ("Move", self.move_player, lambda: True),
            ("Mine", self.mine_action, lambda: self.game_has_mine_available()),
            ("Pass", self.pass_action, lambda: True),
            ("Hijack Robot", self.hijack_robot, lambda: self.game_has_hijack_available())
        ]
        self.turn_actions_panel = ActionPanel(self.actions_frame, "Turn Actions", turn_actions_data,
                                               bg=DARK_BG, fg=DARK_FG, font=FONT_HEADER)
        self.turn_actions_panel.pack(fill="x", pady=UI_PADDING_SMALL)

        # Bottom Info Panel
        self.bottom_frame = tk.Frame(self, bg=DARK_BG)
        self.bottom_frame.grid(row=3, column=0, columnspan=2, pady=UI_PADDING_MEDIUM, sticky="ew")
        self.money_label = tk.Label(self.bottom_frame, text="",
                                    bg=DARK_BG, fg=DARK_FG, font=FONT_MONEY)
        self.money_label.grid(row=0, column=0, rowspan=2, padx=UI_PADDING_MEDIUM, sticky="n")
        info_container = tk.Frame(self.bottom_frame, bg=DARK_BG)
        info_container.grid(row=0, column=1, padx=UI_PADDING_MEDIUM, sticky="n")
        tk.Label(info_container, text="Tile Information:", bg=DARK_BG, fg=DARK_FG, font=FONT_HEADER).pack()
        self.point_info_label = tk.Label(info_container,
                                         text="Click a grid cell to see details.",
                                         justify="left", anchor="w",
                                         width=INFO_LABEL_WIDTH, height=INFO_LABEL_HEIGHT,
                                         borderwidth=1, relief="solid",
                                         bg=DARK_BG, fg=DARK_FG, font=FONT_NORMAL)
        self.point_info_label.pack()
        self.tile_info_frame = tk.LabelFrame(self.bottom_frame, text="Tile Info",
                                             bg=DARK_BG, fg=DARK_FG, font=FONT_HEADER)
        self.tile_info_frame.grid(row=0, column=2, padx=UI_PADDING_MEDIUM, sticky="n")
        self.current_tile_info_label = tk.Label(self.tile_info_frame, text="",
                                                bg=DARK_BG, fg=DARK_FG, font=FONT_TILE_INFO, justify="left")
        self.current_tile_info_label.pack(padx=UI_PADDING_SMALL, pady=UI_PADDING_SMALL)
        self.bottom_frame.grid_columnconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(1, weight=1)
        self.bottom_frame.grid_columnconfigure(2, weight=1)

    # -------------------------
    # Display update methods
    # -------------------------
    def update_display(self):
        # Update discovered tiles, money, and allowed moves
        self.game.update_discovered()
        active = self.game.get_current_player()
        self.money_label.config(text=f"${active.money:.0f}")

        if self.move_mode:
            allowed, error = self.game.get_allowed_moves(active)
            if error:
                self.allowed_moves = set()
                self.log(error)
            else:
                self.allowed_moves = allowed
        if self.remote_plant_mode:
            self.allowed_remote_cells = self.game.get_remote_plant_targets(active)
        if self.debris_mode:
            self.allowed_debris_cells = self.game.get_debris_targets(active)

        # Update each grid cell (tile)
        for y in range(self.game.grid_height):
            for x in range(self.game.grid_width):
                base_props = self.game.get_base_tile_properties(x, y, active)
                text = base_props["text"]
                bg_color = base_props["bg"]
                fg_color = base_props["fg"]
                if self.move_mode and (x, y) in self.allowed_moves:
                    bg_color = ALLOWED_MOVE_COLOR
                elif self.remote_plant_mode and (x, y) in self.allowed_remote_cells:
                    bg_color = REMOTE_ALLOWED_COLOR
                if self.selected_tile == (x, y):
                    bg_color = SELECTED_TILE_COLOR
                if self.debris_mode and (x, y) in self.allowed_debris_cells:
                    bg_color = DEBRIS_ALLOWED_COLOR
                self.cell_labels[y][x].config(text=text, bg=bg_color, fg=fg_color)

        # Update player ship display (modules)
        self.update_ship_with_modules()
        self.current_tile_info_label.config(text=self.format_current_tile_info(active), fg=DARK_FG)
        self.instant_actions_panel.update_buttons()
        self.turn_actions_panel.update_buttons()
        if self.leaderboard_window is not None:
            self.leaderboard_window.update_content()
        if self.asteroid_stats_window is not None:
            self.asteroid_stats_window.update_content()

    def update_timer_display(self):
        self.timer_label.config(text=f"{self.turn_timer_remaining}")

    def update_ship_with_modules(self):
        # Load the base ship image and paste module images onto it.
        try:
            ship_img = Image.open("gui/modules/ship.png").convert("RGBA")
        except Exception as e:
            print("Error loading ship image:", e)
            return
        start_x, start_y = 170, 130
        offset_x, offset_y = 110, 90
        columns = 2
        active = self.game.get_current_player()
        modules = active.modules
        for index, module in enumerate(modules):
            mod_img, _ = get_module_image_pil(module)
            mod_img = mod_img.resize((64, 64))
            col = index % columns
            row = index // columns
            pos_x = start_x + col * offset_x
            pos_y = start_y + row * offset_y
            ship_img.paste(mod_img, (pos_x, pos_y), mod_img)
        ship_img = ship_img.resize((240, 240))
        self.ship_tk = ImageTk.PhotoImage(ship_img)
        self.player_info_label.configure(image=self.ship_tk,
                                         text=self.format_player_info(active),
                                         fg=active.color)

    def disable_controls(self):
        # Disable all widgets in the bottom frame.
        for child in self.bottom_frame.winfo_children():
            child.config(state="disabled")

    # -------------------------
    # Override handle_tile_info to update the point_info_label
    # -------------------------
    def handle_tile_info(self, info: str):
        self.point_info_label.config(text=info)

