from settings import GameSettings
from constants import *

from .modules import Drill, Reactor, Telescope, Factory, LaunchBay

class Player:
    next_id = 1

    def __init__(self, name, x, y, settings: GameSettings):
        self.name = name
        self.symbol = f"P{Player.next_id}"
        self.color = PLAYER_COLORS[(Player.next_id - 1) % len(PLAYER_COLORS)]
        Player.next_id += 1
        self.money = settings.initial_money
        # Instead of separate attributes, store all modules in a list.
        self.modules = []
        self.modules.append(Drill(settings.initial_mining_capacity,
                                  settings.upgrade_mining_cost,
                                  settings.mining_upgrade_amount,
                                  settings.upgrade_mining_cost_increase))
        self.modules.append(Telescope(settings.initial_discovery_range,
                                      settings.upgrade_discovery_cost,
                                      settings.discovery_upgrade_amount,
                                      settings.upgrade_discovery_cost_increase))
        self.modules.append(Reactor(settings.initial_movement_range,
                                    settings.upgrade_movement_cost,
                                    settings.movement_upgrade_amount,
                                    settings.upgrade_movement_cost_increase))
        self.modules.append(LaunchBay(settings.initial_robot_range,
                                      settings.upgrade_robot_range_cost,
                                      settings.robot_range_upgrade_amount,
                                      settings.upgrade_robot_range_cost_increase))
        self.modules.append(Factory(settings.initial_robot_capacity,
                                    settings.upgrade_robot_capacity_cost,
                                    settings.robot_capacity_upgrade_amount,
                                    settings.upgrade_robot_capacity_cost_increase))
        self.upgrades_purchased = 0
        self.total_mined = 0
        self.x = x
        self.y = y

        self.money_earned_by_robots = 0

    def get_module(self, module_name):
        """Returns the first module in self.modules whose name matches module_name (case-insensitive)."""
        for mod in self.modules:
            if module_name == "FusionReactor":
                if mod.name.lower() == "nerva":
                    return mod
            if mod.name.lower() == module_name.lower():
                return mod
        return None

    def __str__(self):
        return f"{self.symbol}"

    def next_turn(self):
        for module in self.modules:
            module.next_turn()