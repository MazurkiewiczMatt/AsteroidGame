# modules.py
"""
This module defines the player capability modules.
Each module is responsible for one aspect of a player's capabilities,
and includes upgrade logic as well as a simple check (can_use)
to indicate whether it is operational.
"""

class Module:
    """
    Base class for all modules.
    """
    def __init__(self, name, upgrade_cost, upgrade_increment, cost_increase, build_cost=1000):
        self.name = name
        self.level = 1
        self.upgrade_cost = upgrade_cost
        self.upgrade_increment = upgrade_increment
        self.cost_increase = cost_increase
        self.build_cost = build_cost

    def next_turn(self):
        pass

    def __str__(self):
        return f"{self.name} (Level {self.level})"


class Drill(Module):
    """
    Drill module responsible for a player's mining capacity.
    """
    def __init__(self, mining_capacity, upgrade_cost, upgrade_increment, cost_increase):
        super().__init__("Drill", upgrade_cost, upgrade_increment, cost_increase)
        self.mining_capacity = mining_capacity

    def upgrade(self, player):
        if self.level < 7:
            if player.money >= self.upgrade_cost:
                player.money -= self.upgrade_cost
                old = self.mining_capacity
                self.mining_capacity += self.upgrade_increment
                self.level += 1
                self.upgrade_cost += self.cost_increase
                return True, f"Drill upgraded: mining capacity increased from {old} to {self.mining_capacity}. Next upgrade will cost ${self.upgrade_cost}."
            else:
                return False, "Insufficient funds for drill upgrade."
        else:
            return False, "Max level of drill reached."


class Reactor(Module):
    """
    Reactor module responsible for a player's movement range.
    """
    def __init__(self, movement_range, upgrade_cost, upgrade_increment, cost_increase):
        super().__init__("Reactor", upgrade_cost, upgrade_increment, cost_increase)
        self.movement_range = movement_range

    def upgrade(self, player):
        if self.level < 7:
            if player.money >= self.upgrade_cost:
                player.money -= self.upgrade_cost
                old = self.movement_range
                self.movement_range += self.upgrade_increment
                self.level += 1
                self.upgrade_cost += self.cost_increase
                return True, f"Reactor upgraded: movement range increased from {old} to {self.movement_range}. Next upgrade will cost ${self.upgrade_cost}."
            else:
                return False, "Insufficient funds for reactor upgrade."
        else:
            return False, "Max level of reactor reached."


class Telescope(Module):
    """
    Telescope module responsible for a player's discovery range.
    """
    def __init__(self, discovery_range, upgrade_cost, upgrade_increment, cost_increase):
        super().__init__("Telescope", upgrade_cost, upgrade_increment, cost_increase)
        self.discovery_range = discovery_range

    def upgrade(self, player):
        if self.level < 7:
            if player.money >= self.upgrade_cost:
                player.money -= self.upgrade_cost
                old = self.discovery_range
                self.discovery_range += self.upgrade_increment
                self.level += 1
                self.upgrade_cost += self.cost_increase
                return True, f"Telescope upgraded: discovery range increased from {old} to {self.discovery_range}. Next upgrade will cost ${self.upgrade_cost}."
            else:
                return False, "Insufficient funds for telescope upgrade."
        else:
            return False, "Max level of telescope reached."


class Factory(Module):
    """
    Factory module responsible for a player's robot capacity.
    """
    def __init__(self, robot_capacity, upgrade_cost, upgrade_increment, cost_increase):
        super().__init__("Factory", upgrade_cost, upgrade_increment, cost_increase)
        self.robot_capacity = robot_capacity
        self.robot_production = 1
        self.robots_produced_this_turn = 0

    def upgrade(self, player):
        if self.level < 7:
            if player.money >= self.upgrade_cost:
                player.money -= self.upgrade_cost
                if self.level in [1, 3]:
                    self.robot_production += 1
                old = self.robot_capacity
                self.robot_capacity += self.upgrade_increment
                self.level += 1
                self.upgrade_cost += self.cost_increase
                return True, f"Factory upgraded: robot capacity increased from {old} to {self.robot_capacity}. Next upgrade will cost ${self.upgrade_cost}."
            else:
                return False, "Insufficient funds for factory upgrade."
        else:
            return False, "Max level of factory reached."

    def next_turn(self):
        self.robots_produced_this_turn = 0


class LaunchBay(Module):
    """
    LaunchBay module responsible for a player's robot range.
    """
    def __init__(self, robot_range, upgrade_cost, upgrade_increment, cost_increase):
        super().__init__("LaunchBay", upgrade_cost, upgrade_increment, cost_increase)
        self.robot_range = robot_range

    def upgrade(self, player):
        if self.level < 7:
            if player.money >= self.upgrade_cost:
                player.money -= self.upgrade_cost
                old = self.robot_range
                self.robot_range += self.upgrade_increment
                self.level += 1
                self.upgrade_cost += self.cost_increase
                return True, f"LaunchBay upgraded: robot range increased from {old} to {self.robot_range}. Next upgrade will cost ${self.upgrade_cost}."
            else:
                return False, "Insufficient funds for launch bay upgrade."
        else:
            return False, "Max level of launch bay reached."


class IcePenetrator(Module):
    """
    IcePenetrator doubles mining capacity for ice asteroids at level 1 and triples it at level 2.
    Only one upgrade is allowed (two total levels).
    """
    def __init__(self, build_cost=1000, upgrade_cost=500):
        # upgrade_increment and cost_increase are not used numerically here.
        super().__init__("IcePenetrator", upgrade_cost, 0, 0, build_cost)
        self.multiplier = 2  # At level 1, multiplier = 2

    def upgrade(self, player):
        if self.level < 2:
            if player.money >= self.upgrade_cost:
                player.money -= self.upgrade_cost
                self.level = 2
                self.multiplier = 3  # At level 2, multiplier = 3
                return True, f"IcePenetrator upgraded: multiplier increased to {self.multiplier}."
            else:
                return False, "Insufficient funds for IcePenetrator upgrade."
        else:
            return False, "Max level of IcePenetrator reached."


class FusionReactor(Module):
    """
    FusionReactor multiplies your movement range.
    At level 1: multiplier = 1.5; at level 2: multiplier = 2.
    Only one upgrade is allowed.
    """
    def __init__(self, build_cost=800, upgrade_cost=600):
        super().__init__("NERVA", upgrade_cost, 0, 0, build_cost)
        self.movement_multiplier = 1.5  # Level 1 multiplier

    def upgrade(self, player):
        if self.level < 2:
            if player.money >= self.upgrade_cost:
                player.money -= self.upgrade_cost
                self.level = 2
                self.movement_multiplier = 2  # Level 2 multiplier
                return True, f"NERVA upgraded: movement multiplier increased to {self.movement_multiplier}."
            else:
                return False, "Insufficient funds for NERVA upgrade."
        else:
            return False, "Max level of NERVA reached."


class ExplosivesLab(Module):
    """
    ExplosivesLab increases the debris deployment radius.
    At level 1, debris radius becomes 2 (instead of the normal 1).
    At level 2, it adds an additional bonus of 3 to the Factory's production capacity.
    Only one upgrade is allowed.
    """
    def __init__(self, build_cost=1000, upgrade_cost=500):
        super().__init__("ExplosivesLab", upgrade_cost, 0, 0, build_cost)
        self.debris_radius = 0
        self.extra_range = 2

    def upgrade(self, player):
        if self.level < 2:
            if player.money >= self.upgrade_cost:
                player.money -= self.upgrade_cost
                self.level = 2
                self.debris_radius += 1
                self.extra_range += 1
                return True, "ExplosivesLab upgraded: bigger debris radius"
            else:
                return False, "Insufficient funds for ExplosivesLab upgrade."
        else:
            return False, "Max level of ExplosivesLab reached."


class WarpDrive(Module):
    """
    WarpDrive allows you to move anywhere on the map (except onto debris, asteroids, or undiscovered tiles).
    At level 2, movement is instant and does not use up the turn.
    Only one upgrade is allowed.
    """
    def __init__(self, build_cost=2000, upgrade_cost=4000):
        super().__init__("WarpDrive", upgrade_cost, 0, 0, build_cost)
        self.instant = False  # At level 1, movement consumes the turn.
        self.used_this_turn = False

    def upgrade(self, player):
        if self.level < 2:
            if player.money >= self.upgrade_cost:
                player.money -= self.upgrade_cost
                self.level = 2
                self.instant = True
                return True, "WarpDrive upgraded: movement becomes instant once per turn."
            else:
                return False, "Insufficient funds for WarpDrive upgrade."
        else:
            return False, "Max level of WarpDrive reached."

    def next_turn(self):
        self.used_this_turn = False
