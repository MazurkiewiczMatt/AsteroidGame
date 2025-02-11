import tkinter as tk
from tkinter import messagebox

from gui import GameGUI
from gameplay import Game
from settings import GameSettings
from constants import *


class SettingsGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Space Mining Game - Settings")
        self.configure(bg=DARK_BG)
        self.resizable(False, False)
        self.fields = {}

        # Main container is divided into two columns: left and right.
        # Left column: Gameplay and Map sections.
        # Right column: Upgrades (arranged by upgrade type).
        #
        # Create the left and right frames.
        left_frame = tk.Frame(self, bg=DARK_BG)
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="n")
        right_frame = tk.Frame(self, bg=DARK_BG)
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="n")

        # --- Left Column: Gameplay and Map Sections ---

        # Gameplay Section
        gameplay_frame = tk.Frame(left_frame, bg=DARK_BG, bd=2, relief="groove")
        gameplay_frame.pack(side="top", fill="both", expand=True, pady=(0, 10))
        tk.Label(gameplay_frame, text="Gameplay", bg=DARK_BG, fg=DARK_FG,
                 font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=(5, 5))
        gameplay_entries = [
            ("Number of Players", "num_players", 3),
            ("Initial Money", "initial_money", 500),
            ("Turn Timer Duration (sec)", "turn_timer_duration", 50),
            ("Initial Mining Capacity", "initial_mining_capacity", 150),
            ("Initial Discovery Range", "initial_discovery_range", 2),
            ("Initial Movement Range", "initial_movement_range", 2),
            ("Initial Robot Range", "initial_robot_range", 0),
            ("Initial Robot Capacity", "initial_robot_capacity", 10)
        ]
        row_index = 1
        for label_text, key, default in gameplay_entries:
            tk.Label(gameplay_frame, text=label_text, bg=DARK_BG, fg=DARK_FG) \
                .grid(row=row_index, column=0, padx=5, pady=2, sticky="w")
            ent = tk.Entry(gameplay_frame, bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=DARK_FG)
            ent.insert(0, str(default))
            ent.grid(row=row_index, column=1, padx=5, pady=2)
            self.fields[key] = ent
            row_index += 1

        # Map Section
        map_frame = tk.Frame(left_frame, bg=DARK_BG, bd=2, relief="groove")
        map_frame.pack(side="top", fill="both", expand=True)
        tk.Label(map_frame, text="Map", bg=DARK_BG, fg=DARK_FG,
                 font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=(5, 5))
        map_entries = [
            ("Grid Width", "grid_width", 16),
            ("Grid Height", "grid_height", 16),
            ("Minimum Asteroids", "min_asteroids", 15),
            ("Maximum Asteroids", "max_asteroids", 25)
        ]
        row_index = 1
        for label_text, key, default in map_entries:
            tk.Label(map_frame, text=label_text, bg=DARK_BG, fg=DARK_FG) \
                .grid(row=row_index, column=0, padx=5, pady=2, sticky="w")
            ent = tk.Entry(map_frame, bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=DARK_FG)
            ent.insert(0, str(default))
            ent.grid(row=row_index, column=1, padx=5, pady=2)
            self.fields[key] = ent
            row_index += 1

        # --- Right Column: Upgrades Section (grouped by upgrade type) ---

        upgrades_frame = tk.Frame(right_frame, bg=DARK_BG, bd=2, relief="groove")
        upgrades_frame.pack(fill="both", expand=True)
        tk.Label(upgrades_frame, text="Upgrades", bg=DARK_BG, fg=DARK_FG,
                 font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=(5, 5))

        # Define upgrade categories grouped by type.
        upgrade_categories = {
            "Robot Range": [
                ("Upgrade Robot Range Cost", "upgrade_robot_range_cost", 200),
                ("Robot Range Upgrade Amount", "robot_range_upgrade_amount", 1),
                ("Upgrade Robot Range Cost Increase", "upgrade_robot_range_cost_increase", 50)
            ],
            "Mining": [
                ("Upgrade Mining Cost", "upgrade_mining_cost", 200),
                ("Mining Upgrade Amount", "mining_upgrade_amount", 20),
                ("Upgrade Mining Cost Increase", "upgrade_mining_cost_increase", 10)
            ],
            "Discovery": [
                ("Upgrade Discovery Cost", "upgrade_discovery_cost", 150),
                ("Discovery Upgrade Amount", "discovery_upgrade_amount", 1),
                ("Upgrade Discovery Cost Increase", "upgrade_discovery_cost_increase", 20)
            ],
            "Movement": [
                ("Upgrade Movement Cost", "upgrade_movement_cost", 150),
                ("Movement Upgrade Amount", "movement_upgrade_amount", 1),
                ("Upgrade Movement Cost Increase", "upgrade_movement_cost_increase", 20)
            ],
            "Robot Capacity": [
                ("Upgrade Robot Capacity Cost", "upgrade_robot_capacity_cost", 200),
                ("Robot Capacity Upgrade Amount", "robot_capacity_upgrade_amount", 5),
                ("Upgrade Robot Capacity Cost Increase", "upgrade_robot_capacity_cost_increase", 50)
            ]
        }

        # Start from row 1 in the upgrades_frame.
        row_index = 1
        for group_name, settings_list in upgrade_categories.items():
            # Insert a subheader for the upgrade group.
            tk.Label(upgrades_frame, text=f"--- {group_name} Upgrades ---", bg=DARK_BG, fg=DARK_FG,
                     font=('Arial', 10, 'italic')).grid(row=row_index, column=0, columnspan=2, pady=(5, 2))
            row_index += 1
            for label_text, key, default in settings_list:
                tk.Label(upgrades_frame, text=label_text, bg=DARK_BG, fg=DARK_FG) \
                    .grid(row=row_index, column=0, padx=5, pady=2, sticky="w")
                ent = tk.Entry(upgrades_frame, bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=DARK_FG)
                ent.insert(0, str(default))
                ent.grid(row=row_index, column=1, padx=5, pady=2)
                self.fields[key] = ent
                row_index += 1

        # --- Start Game Button ---
        # Place the Start Game button below both columns, spanning across them.
        tk.Button(self, text="Start Game", command=self.start_game,
                  bg=BUTTON_BG, fg=BUTTON_FG) \
            .grid(row=1, column=0, columnspan=2, pady=10)

    def start_game(self):
        try:
            settings = GameSettings(
                num_players=int(self.fields["num_players"].get()),
                grid_width=int(self.fields["grid_width"].get()),
                grid_height=int(self.fields["grid_height"].get()),
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
