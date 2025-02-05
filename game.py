import random

from settings import GameSettings
from constants import *  # Includes PLAYER_COLORS and helper functions such as manhattan_distance

class Robot:
    def __init__(self, owner, capacity):
        self.owner = owner
        self.capacity = capacity  # Capacity frozen at deployment

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
        self.upgrades_purchased = 0  # Count of upgrades purchased
        self.total_mined = 0  # Total mined resources
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
            return (f"{player.symbol} manually mines {extraction} from A{asteroid.id} and immediately receives ${gain:.1f}.")
        else:
            extraction = asteroid.resource
            gain = extraction * asteroid.value
            player.money += gain
            player.total_mined += extraction
            asteroid.resource = 0
            return (f"{player.symbol} manually mines {extraction} from A{asteroid.id} (all) and immediately receives ${gain:.1f}.")

    def robot_mining(self, log_func):
        for a in self.asteroids:
            if a.robot and not a.is_exhausted():
                extraction = min(a.robot.capacity, a.resource)
                gain = extraction * a.value
                a.resource -= extraction
                a.robot.owner.money += gain
                a.robot.owner.total_mined += extraction
                log_func(f"Robot on A{a.id} (owned by {a.robot.owner.symbol}, Cap: {a.robot.owner.robot_capacity}) extracts {extraction} and earns ${gain:.1f} at end of turn.")

    def remote_plant_robot(self, player, target):
        """
        Plant a robot remotely.
        Valid only if the target asteroid is discovered, not exhausted, and does not already have a robot.
        Costs $100.
        """
        if target is None:
            return ("No valid asteroid at that location.", False)
        if (target.x, target.y) not in self.discovered_tiles:
            return ("Asteroid is undiscovered.", False)
        if target.is_exhausted():
            return ("Asteroid is exhausted.", False)
        if player.money < 100:
            return ("Not enough money to plant robot remotely.", False)
        if target.robot is not None:
            return ("A robot already exists on this asteroid.", False)
        player.money -= 100
        target.robot = Robot(player, player.robot_capacity)
        return (f"{player.symbol} plants a robot on A{target.id} with capacity {player.robot_capacity}.", False)

    def hijack_robot(self, player):
        """
        Hijack is allowed only if the player is standing on an asteroid that has a robot owned by another player.
        Hijacking costs nothing and transfers ownership of the robot.
        """
        asteroid = next((a for a in self.asteroids if a.x == player.x and a.y == player.y and not a.is_exhausted()), None)
        if asteroid is None:
            return ("No asteroid here for hijacking.", False)
        if asteroid.robot is None:
            return ("No robot on this asteroid to hijack.", False)
        if asteroid.robot.owner == player:
            return ("You already own the robot here.", False)
        # Transfer robot ownership without cost.
        asteroid.robot.owner = player
        # Optionally, update robot capacity to match the hijacking player's capacity.
        asteroid.robot.capacity = player.robot_capacity
        return (f"{player.symbol} hijacks the robot on A{asteroid.id} and now controls it.", True)

    def upgrade_robot_on_tile(self, player):
        """
        Look for an asteroid within the player's robot range that contains the player's robot.
        Upgrade the robot’s capacity if it is less than the player's current robot_capacity.
        """
        candidate = None
        for a in self.asteroids:
            if a.robot and a.robot.owner == player and manhattan_distance(player.x, player.y, a.x, a.y) <= player.robot_range:
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
                log_func(f"{player.symbol} mining capacity upgraded to {player.mining_capacity}. Next upgrade will cost ${player.mining_upgrade_cost}.")
            else:
                log_func(f"{player.symbol} lacks money for mining upgrade.")
        elif upgrade_type == "discovery":
            if player.money >= player.discovery_upgrade_cost:
                cost = player.discovery_upgrade_cost
                player.money -= cost
                player.discovery_range += self.settings.discovery_upgrade_amount
                player.upgrades_purchased += 1
                player.discovery_upgrade_cost += self.settings.upgrade_discovery_cost_increase
                log_func(f"{player.symbol} discovery range upgraded to {player.discovery_range}. Next upgrade will cost ${player.discovery_upgrade_cost}.")
            else:
                log_func(f"{player.symbol} lacks money for discovery upgrade.")
        elif upgrade_type == "movement":
            if player.money >= player.movement_upgrade_cost:
                cost = player.movement_upgrade_cost
                player.money -= cost
                player.movement_range += self.settings.movement_upgrade_amount
                player.upgrades_purchased += 1
                player.movement_upgrade_cost += self.settings.upgrade_movement_cost_increase
                log_func(f"{player.symbol} movement range upgraded to {player.movement_range}. Next upgrade will cost ${player.movement_upgrade_cost}.")
            else:
                log_func(f"{player.symbol} lacks money for movement upgrade.")
        elif upgrade_type == "robot_range":
            if player.money >= player.robot_range_upgrade_cost:
                cost = player.robot_range_upgrade_cost
                player.money -= cost
                player.robot_range += self.settings.robot_range_upgrade_amount
                player.upgrades_purchased += 1
                player.robot_range_upgrade_cost += self.settings.upgrade_robot_range_cost_increase
                log_func(f"{player.symbol} robot range upgraded to {player.robot_range}. Next upgrade will cost ${player.robot_range_upgrade_cost}.")
            else:
                log_func(f"{player.symbol} lacks money for robot range upgrade.")
        elif upgrade_type == "robot_capacity":
            if player.money >= player.robot_capacity_upgrade_cost:
                cost = player.robot_capacity_upgrade_cost
                player.money -= cost
                player.robot_capacity += self.settings.robot_capacity_upgrade_amount
                player.upgrades_purchased += 1
                player.robot_capacity_upgrade_cost += self.settings.upgrade_robot_capacity_cost_increase
                log_func(f"{player.symbol} robot capacity upgraded to {player.robot_capacity}. Next upgrade will cost ${player.robot_capacity_upgrade_cost}.")
            else:
                log_func(f"{player.symbol} lacks money for robot capacity upgrade.")

    def is_game_over(self):
        return all(a.is_exhausted() for a in self.asteroids)
