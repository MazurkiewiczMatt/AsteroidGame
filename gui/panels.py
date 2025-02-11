import tkinter as tk
from constants import *
# Make sure to import your module classes:
from modules import Drill, Reactor, Telescope, Factory, LaunchBay, IcePenetrator, FusionReactor, ExplosivesLab, WarpDrive

# Standardized fonts:
FONT_SMALL = (FONT_FAMILY, 10)
FONT_MEDIUM = (FONT_FAMILY, 12, "bold")
FONT_HEADER = (FONT_FAMILY, 14, "bold")

class UpgradeGUI(tk.Toplevel):
    def __init__(self, parent, game, player):
        """
        This upgrade window now works with player.modules (a list of module objects).
        Each module is expected to have attributes:
          - name (e.g. "Drill", "Telescope", etc.)
          - level
          - upgrade_cost
          - upgrade_increment
          - cost_increase
        The window lets the user upgrade a module, remove it, or buy new modules.
        """
        super().__init__(parent)
        self.title("Upgrade Options")
        self.configure(bg=DARK_BG)
        self.game = game
        self.player = player  # Player now has a list: self.modules
        # To keep image references (to avoid garbage collection)
        self.image_cache = {}
        # Dictionary mapping module names to a lambda that returns a new instance.
        # (These default values can be adjusted as needed.)
        self.available_modules = {
            "Drill": lambda: Drill(mining_capacity=10, upgrade_cost=500, upgrade_increment=5, cost_increase=200),
            "Reactor": lambda: Reactor(movement_range=5, upgrade_cost=500, upgrade_increment=1, cost_increase=200),
            "Telescope": lambda: Telescope(discovery_range=3, upgrade_cost=500, upgrade_increment=1, cost_increase=200),
            "Factory": lambda: Factory(robot_capacity=2, upgrade_cost=500, upgrade_increment=1, cost_increase=200),
            "LaunchBay": lambda: LaunchBay(robot_range=2, upgrade_cost=500, upgrade_increment=1, cost_increase=200),
            "IcePenetrator": lambda: IcePenetrator(),
            "NERVA": lambda: FusionReactor(),
            "ExplosivesLab": lambda: ExplosivesLab(),
            "WarpDrive": lambda: WarpDrive(),
        }
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        header = tk.Label(self, text="Upgrade/Remove Modules", bg=DARK_BG, fg=DARK_FG, font=FONT_HEADER)
        header.pack(padx=10, pady=5)

        # Frame for the currently owned modules:
        self.table_frame = tk.Frame(self, bg=DARK_BG)
        self.table_frame.pack(padx=10, pady=5)
        self.build_table()

        # --- Purchase Section ---
        purchase_header = tk.Label(self, text="Purchase New Modules", bg=DARK_BG, fg=DARK_FG, font=FONT_HEADER)
        purchase_header.pack(padx=10, pady=5)
        self.purchase_frame = tk.Frame(self, bg=DARK_BG)
        self.purchase_frame.pack(padx=10, pady=5)
        self.build_purchase_table()

        # Close button:
        button_frame = tk.Frame(self, bg=DARK_BG)
        button_frame.pack(padx=10, pady=10)
        tk.Button(
            button_frame, text="Close", command=self.on_close,
            bg=BUTTON_BG, fg=BUTTON_FG, font=FONT_SMALL
        ).pack(side="left", padx=5)

    def build_table(self):
        # Clear any existing widgets from the modules table.
        for child in self.table_frame.winfo_children():
            child.destroy()

        # Table header row.
        headers = ["Component", "Level", "Upgrade Cost", "Description", "Actions"]
        for col, text in enumerate(headers):
            lbl = tk.Label(
                self.table_frame, text=text, bg=DARK_BG, fg=DARK_FG,
                font=FONT_MEDIUM, borderwidth=1, relief="solid", padx=5, pady=3
            )
            lbl.grid(row=0, column=col, sticky="nsew", padx=1, pady=1)

        # One row per owned module.
        for row_index, module in enumerate(self.player.modules, start=1):
            # Column 0: Module name (with image).
            img = self.get_module_image(module)
            lbl_name = tk.Label(
                self.table_frame, image=img, compound="left",
                bg=EMPTY_TILE_BG, fg=DARK_FG, font=FONT_SMALL,
                borderwidth=1, relief="solid", padx=5, pady=3
            )
            lbl_name.image = img  # keep a reference
            lbl_name.grid(row=row_index, column=0, sticky="nsew", padx=1, pady=1)

            # Column 1: Level.
            lbl_level = tk.Label(
                self.table_frame, text=f"{module.name} (grade {module.level})",
                bg=EMPTY_TILE_BG, fg=DARK_FG, font=FONT_SMALL,
                borderwidth=1, relief="solid", padx=5, pady=3
            )
            lbl_level.grid(row=row_index, column=1, sticky="nsew", padx=1, pady=1)

            # Column 2: Upgrade cost.
            lbl_cost = tk.Label(
                self.table_frame, text=f"${module.upgrade_cost}",
                bg=EMPTY_TILE_BG, fg=DARK_FG, font=FONT_SMALL,
                borderwidth=1, relief="solid", padx=5, pady=3
            )
            lbl_cost.grid(row=row_index, column=2, sticky="nsew", padx=1, pady=1)

            # Column 3: Description.
            description = self.get_description(module)
            lbl_desc = tk.Label(
                self.table_frame, text=description,
                bg=EMPTY_TILE_BG, fg=DARK_FG, font=FONT_SMALL,
                borderwidth=1, relief="solid", padx=5, pady=3,
                wraplength=300, justify="left"
            )
            lbl_desc.grid(row=row_index, column=3, sticky="nsew", padx=1, pady=1)

            # Column 4: Actions – Upgrade and Remove buttons.
            action_frame = tk.Frame(self.table_frame, bg=EMPTY_TILE_BG)
            action_frame.grid(row=row_index, column=4, sticky="nsew", padx=1, pady=1)
            btn_upgrade = tk.Button(
                action_frame, text="Upgrade", bg=BUTTON_BG, fg=BUTTON_FG, font=FONT_SMALL,
                command=lambda m=module: self.upgrade_module(m)
            )
            btn_upgrade.pack(side="left", padx=2)
            btn_remove = tk.Button(
                action_frame, text="Remove", bg=BUTTON_BG, fg=BUTTON_FG, font=FONT_SMALL,
                command=lambda m=module: self.remove_module(m)
            )
            btn_remove.pack(side="left", padx=2)

    def build_purchase_table(self):
        # Clear any existing widgets from the purchase frame.
        for child in self.purchase_frame.winfo_children():
            child.destroy()

        # Header row for the purchase table.
        headers = ["Component", "Cost", "Actions"]
        for col, text in enumerate(headers):
            lbl = tk.Label(
                self.purchase_frame, text=text, bg=DARK_BG, fg=DARK_FG,
                font=FONT_MEDIUM, borderwidth=1, relief="solid", padx=5, pady=3
            )
            lbl.grid(row=0, column=col, sticky="nsew", padx=1, pady=1)

        # Only list modules that the player does not yet own.
        owned_module_names = {module.name for module in self.player.modules}
        row_index = 1
        for module_name, constructor in self.available_modules.items():
            if module_name not in owned_module_names:
                # Create a temporary module instance (for display purposes).
                temp_module = constructor()
                img = self.get_module_image(temp_module)
                # Column 0: Module name (with image).
                lbl_name = tk.Label(
                    self.purchase_frame, image=img, compound="left", text=module_name,
                    bg=EMPTY_TILE_BG, fg=DARK_FG, font=FONT_SMALL,
                    borderwidth=1, relief="solid", padx=5, pady=3
                )
                lbl_name.image = img
                lbl_name.grid(row=row_index, column=0, sticky="nsew", padx=1, pady=1)
                # Column 1: Cost (always $1000 for purchase).
                lbl_cost = tk.Label(
                    self.purchase_frame, text=f"${self.get_cost_of_module(module_name)}", bg=EMPTY_TILE_BG, fg=DARK_FG,
                    font=FONT_SMALL, borderwidth=1, relief="solid", padx=5, pady=3
                )
                lbl_cost.grid(row=row_index, column=1, sticky="nsew", padx=1, pady=1)
                # Column 2: Action – Buy button.
                action_frame = tk.Frame(self.purchase_frame, bg=EMPTY_TILE_BG)
                action_frame.grid(row=row_index, column=2, sticky="nsew", padx=1, pady=1)
                btn_buy = tk.Button(
                    action_frame, text="Buy", bg=BUTTON_BG, fg=BUTTON_FG, font=FONT_SMALL,
                    command=lambda mn=module_name: self.buy_module(mn)
                )
                btn_buy.pack(side="left", padx=2)
                row_index += 1

    def get_cost_of_module(self, module_name):
        temp_module = self.available_modules[module_name]()
        return temp_module.build_cost

    def buy_module(self, module_name):
        """
        Buys a new module of the given type if the player has at least $1000.
        """
        cost = self.get_cost_of_module(module_name)
        if len(self.player.modules) < 8:
            if self.player.money >= cost:
                self.player.money -= cost
                new_module = self.available_modules[module_name]()
                self.player.modules.append(new_module)
                self.master.log(f"Purchased {module_name} for ${cost}.")
                self.master.update_display()
                self.build_purchase_table()
                self.build_table()
            else:
                self.master.log("Insufficient funds to purchase module.")
        else:
            self.master.log("No available slot for the module.")

    def get_module_image(self, module):
        """
        Determines and loads the image for the module based on its type and level.
        For new modules (IcePenetrator, FusionReactor, ExplosivesLab, WarpDrive) we use
        the specific filenames (e.g. "Ice_penetrator.png"). For the others, we follow the
        existing naming convention.
        """
        mod_name = module.name
        # Special handling for new modules:
        if mod_name.lower() in ["icepenetrator", "nerva", "explosiveslab", "warpdrive"]:
            mapping = {
                "icepenetrator": "Ice_penetrator",
                "nerva": "NERVA",
                "explosiveslab": "Explosives_lab",
                "warpdrive": "Warp_drive",
            }
            if module.level == 1:
                filename = mapping[mod_name.lower()] + ".png"
            else:
                filename = mapping[mod_name.lower()] + "_upgrade.png"
        else:
            if mod_name.lower() == "launchbay":
                filename = f"Launch_Bay{module.level}.png"
            else:
                filename = f"{mod_name}{module.level}.png"
        # Try to load the image; fall back to "Blank.png" if needed.
        try:
            img = tk.PhotoImage(file=f"gui/modules/{filename}")
        except Exception:
            img = tk.PhotoImage(file="gui/modules/Blank.png")
        self.image_cache[filename] = img
        return img

    def get_description(self, module):
        """
        Returns a description string for the module.
        For the basic modules we show their upgrade details;
        for the new modules we provide a brief summary.
        """
        name = module.name.lower()
        if name == "drill":
            return f"Increases mining capacity by {module.upgrade_increment}. Next upgrade cost increases by {module.cost_increase}."
        elif name == "telescope":
            return f"Increases discovery range by {module.upgrade_increment}. Next upgrade cost increases by {module.cost_increase}."
        elif name == "reactor":
            return f"Increases movement range by {module.upgrade_increment}. Next upgrade cost increases by {module.cost_increase}."
        elif name == "launchbay":
            return f"Increases robot range by {module.upgrade_increment}. Next upgrade cost increases by {module.cost_increase}."
        elif name == "factory":
            return f"Increases robot capacity by {module.upgrade_increment}. Next upgrade cost increases by {module.cost_increase}."
        elif name == "icepenetrator":
            return "Doubles mining capacity for ice asteroids at level 1 and triples it at level 2."
        elif name == "nerva":
            return "Multiplies movement range: 1.5x at level 1 and 2x at level 2."
        elif name == "explosiveslab":
            return "At level 1: sets debris radius to 2; at level 2 adds bonus Factory production."
        elif name == "warpdrive":
            return "Allows movement anywhere on the map; at level 2, movement is instant."
        else:
            return ""

    def upgrade_module(self, module):
        """
        Upgrades the selected module by calling its own upgrade method.
        If successful, logs the message, increments the player's upgrades_purchased,
        and refreshes the table.
        """
        success, message = module.upgrade(self.player)
        if success:
            self.player.upgrades_purchased += 1
        self.master.log(message)
        self.master.update_display()
        self.build_table()

    def remove_module(self, module):
        """
        Removes the given module from the player's modules list.
        (Be aware that removal of a module means the player loses that capability.)
        """
        self.player.modules.remove(module)
        self.master.log(f"{module.name} has been removed from your modules.")
        self.master.update_display()
        self.build_table()

    def on_close(self):
        self.destroy()
        self.master.upgrade_window = None




class AsteroidGraphGUI(tk.Toplevel):
    def __init__(self, parent, game):
        super().__init__(parent)
        self.title("Asteroid Stats")
        self.configure(bg=DARK_BG)
        self.game = game
        self.canvas_width = 600
        self.row_height = 35
        self.header_height = 30
        self.show_resource_bar = True
        button_frame = tk.Frame(self, bg=DARK_BG)
        button_frame.pack(pady=5)
        self.toggle_button = tk.Button(button_frame, text="Show Total Value Bar", command=self.toggle_bar_chart,
                                       bg=BUTTON_BG, fg=BUTTON_FG, font=FONT_SMALL)
        self.toggle_button.pack()
        self.canvas = tk.Canvas(self, width=self.canvas_width, height=300, bg=DARK_BG, highlightthickness=0)
        self.canvas.pack(padx=10, pady=10, fill="both", expand=True)
        self.update_content()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def toggle_bar_chart(self):
        self.show_resource_bar = not self.show_resource_bar
        self.toggle_button.config(text="Show Total Value" if self.show_resource_bar else "Show Resource")
        self.update_content()

    def update_content(self):
        discovered = [a for a in self.game.asteroids if (a.x, a.y) in self.game.discovered_tiles]
        total_height = self.header_height + self.row_height * len(discovered) + 20
        self.canvas.config(height=total_height)
        self.canvas.delete("all")
        headers = ["Asteroid", "Loc", "Res", "Price", "Tot. Val", "Players", "Robot (Cap)",
                   "Resource" if self.show_resource_bar else "Value"]
        col_positions = [10, 70, 120, 170, 230, 290, 380, 480]
        for i, header in enumerate(headers):
            self.canvas.create_text(col_positions[i], 15, anchor="w", text=header, fill=DARK_FG,
                                    font=FONT_SMALL)
        y = self.header_height
        if self.show_resource_bar:
            max_bar_value = max(a.resource for a in discovered) if discovered else 1
        else:
            max_bar_value = max(a.resource * a.value for a in discovered) if discovered else 1
        for a in discovered:
            if not a.is_exhausted():
                _, fill_color, _ = self.master.get_tile_properties(a.x, a.y)
                if fill_color not in [SELECTED_TILE_COLOR, ACTIVE_PLAYER_TILE_COLOR]:
                    fill_color = ASTEROID_BG
                row_tag = f"asteroid_{a.id}"
                self.canvas.create_rectangle(5, y, self.canvas_width - 5, y + self.row_height, fill=fill_color,
                                             outline="", tags=row_tag)
                self.canvas.tag_bind(row_tag, "<Button-1>", lambda e, ax=a.x, ay=a.y: self.on_row_click(ax, ay))
                row_color = a.robot.owner.color if a.robot else DARK_FG
                self.canvas.create_text(col_positions[0], y + self.row_height / 2, anchor="w",
                                        text=f"{'(??) ' if not a.visited else ''}A{a.id}", fill=row_color, font=FONT_SMALL, tags=row_tag)
                self.canvas.create_text(col_positions[1], y + self.row_height / 2, anchor="w",
                                        text=f"({a.x},{a.y})", fill=row_color, font=FONT_SMALL, tags=row_tag)
                self.canvas.create_text(col_positions[2], y + self.row_height / 2, anchor="w",
                                        text=f"{a.resource:.0f}", fill=row_color, font=FONT_SMALL, tags=row_tag)
                self.canvas.create_text(col_positions[3], y + self.row_height / 2, anchor="w",
                                        text=f"${a.value:.2f}", fill=row_color, font=FONT_SMALL, tags=row_tag)
                total_val = a.resource * a.value
                self.canvas.create_text(col_positions[4], y + self.row_height / 2, anchor="w",
                                        text=f"${total_val:.2f}", fill=row_color, font=FONT_SMALL, tags=row_tag)
                players_here = [p for p in self.game.players if p.x == a.x and p.y == a.y]
                players_text = ", ".join(p.symbol for p in players_here)
                self.canvas.create_text(col_positions[5], y + self.row_height / 2, anchor="w",
                                        text=players_text, fill=row_color, font=FONT_SMALL, tags=row_tag)
                robot_text = f"{a.robot.owner.symbol} (Cap: {a.robot.capacity})" if a.robot else ""
                self.canvas.create_text(col_positions[6], y + self.row_height / 2, anchor="w",
                                        text=robot_text, fill=row_color, font=FONT_SMALL, tags=row_tag)
                bar_x = col_positions[7]
                bar_y = y + 5
                max_bar_length = self.canvas_width - bar_x - 20
                bar_val = a.resource if self.show_resource_bar else total_val
                bar_length = (bar_val / max_bar_value) * max_bar_length if max_bar_value > 0 else 0
                self.canvas.create_rectangle(bar_x, bar_y, bar_x + bar_length, bar_y + self.row_height - 10,
                                             fill=a.color, outline="white", tags=row_tag)
                y += self.row_height

    def on_row_click(self, x, y):
        self.master.on_asteroid_selected(x, y)

    def on_close(self):
        self.destroy()
        self.master.asteroid_stats_window = None



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


class AsteroidGraphGUI(tk.Toplevel):
    def __init__(self, parent, game):
        super().__init__(parent)
        self.title("Asteroid Stats")
        self.configure(bg=DARK_BG)
        self.game = game
        self.canvas_width = 600
        self.row_height = 35
        self.header_height = 30
        self.show_resource_bar = True
        button_frame = tk.Frame(self, bg=DARK_BG)
        button_frame.pack(pady=5)
        self.toggle_button = tk.Button(button_frame, text="Show Total Value Bar", command=self.toggle_bar_chart,
                                       bg=BUTTON_BG, fg=BUTTON_FG, font=FONT_SMALL)
        self.toggle_button.pack()
        self.canvas = tk.Canvas(self, width=self.canvas_width, height=300, bg=DARK_BG, highlightthickness=0)
        self.canvas.pack(padx=10, pady=10, fill="both", expand=True)
        self.update_content()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def toggle_bar_chart(self):
        self.show_resource_bar = not self.show_resource_bar
        self.toggle_button.config(text="Show Total Value" if self.show_resource_bar else "Show Resource")
        self.update_content()

    def update_content(self):
        discovered = [a for a in self.game.asteroids if (a.x, a.y) in self.game.discovered_tiles]
        total_height = self.header_height + self.row_height * len(discovered) + 20
        self.canvas.config(height=total_height)
        self.canvas.delete("all")
        headers = ["Asteroid", "Loc", "Res", "Price", "Tot. Val", "Players", "Robot (Cap)",
                   "Resource" if self.show_resource_bar else "Value"]
        col_positions = [10, 70, 120, 170, 230, 290, 380, 480]
        for i, header in enumerate(headers):
            self.canvas.create_text(col_positions[i], 15, anchor="w", text=header, fill=DARK_FG,
                                    font=FONT_SMALL)
        y = self.header_height
        if self.show_resource_bar:
            max_bar_value = max(a.resource for a in discovered) if discovered else 1
        else:
            max_bar_value = max(a.resource * a.value for a in discovered) if discovered else 1
        for a in discovered:
            if not a.is_exhausted():
                _, fill_color, _ = self.master.get_tile_properties(a.x, a.y)
                if fill_color not in [SELECTED_TILE_COLOR, ACTIVE_PLAYER_TILE_COLOR]:
                    fill_color = ASTEROID_BG
                row_tag = f"asteroid_{a.id}"
                self.canvas.create_rectangle(5, y, self.canvas_width - 5, y + self.row_height, fill=fill_color,
                                             outline="", tags=row_tag)
                self.canvas.tag_bind(row_tag, "<Button-1>", lambda e, ax=a.x, ay=a.y: self.on_row_click(ax, ay))
                row_color = a.robot.owner.color if a.robot else DARK_FG
                self.canvas.create_text(col_positions[0], y + self.row_height / 2, anchor="w",
                                        text=f"{'(??) ' if not a.visited else ''}A{a.id}", fill=row_color, font=FONT_SMALL, tags=row_tag)
                self.canvas.create_text(col_positions[1], y + self.row_height / 2, anchor="w",
                                        text=f"({a.x},{a.y})", fill=row_color, font=FONT_SMALL, tags=row_tag)
                self.canvas.create_text(col_positions[2], y + self.row_height / 2, anchor="w",
                                        text=f"{a.resource:.0f}", fill=row_color, font=FONT_SMALL, tags=row_tag)
                self.canvas.create_text(col_positions[3], y + self.row_height / 2, anchor="w",
                                        text=f"${a.value:.2f}", fill=row_color, font=FONT_SMALL, tags=row_tag)
                total_val = a.resource * a.value
                self.canvas.create_text(col_positions[4], y + self.row_height / 2, anchor="w",
                                        text=f"${total_val:.2f}", fill=row_color, font=FONT_SMALL, tags=row_tag)
                players_here = [p for p in self.game.players if p.x == a.x and p.y == a.y]
                players_text = ", ".join(p.symbol for p in players_here)
                self.canvas.create_text(col_positions[5], y + self.row_height / 2, anchor="w",
                                        text=players_text, fill=row_color, font=FONT_SMALL, tags=row_tag)
                robot_text = f"{a.robot.owner.symbol} (Cap: {a.robot.capacity})" if a.robot else ""
                self.canvas.create_text(col_positions[6], y + self.row_height / 2, anchor="w",
                                        text=robot_text, fill=row_color, font=FONT_SMALL, tags=row_tag)
                bar_x = col_positions[7]
                bar_y = y + 5
                max_bar_length = self.canvas_width - bar_x - 20
                bar_val = a.resource if self.show_resource_bar else total_val
                bar_length = (bar_val / max_bar_value) * max_bar_length if max_bar_value > 0 else 0
                self.canvas.create_rectangle(bar_x, bar_y, bar_x + bar_length, bar_y + self.row_height - 10,
                                             fill=a.color, outline="white", tags=row_tag)
                y += self.row_height

    def on_row_click(self, x, y):
        self.master.on_asteroid_selected(x, y)

    def on_close(self):
        self.destroy()
        self.master.asteroid_stats_window = None
