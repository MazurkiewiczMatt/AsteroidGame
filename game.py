# game.py

import random
import math
from collections import deque
from settings import GameSettings
from constants import manhattan_distance, PLAYER_COLORS  # assumes you have these defined

# Define asteroid types and their properties.
ASTEROID_TYPES = {
    "ice": {
        "resource_range": (1000, 3000),
        "value_range": (0.6, 1.0),
        "color": "#1447FF",
        "event_probability_override": None
    },
    "hematite": {
        "resource_range": (800, 1800),
        "value_range": (0.8, 2.0),
        "color": "#B50407",
        "event_probability_override": None
    },
    "malachite": {
        "resource_range": (600, 1200),
        "value_range": (1.2, 3.0),
        "color": "#D45E22",
        "event_probability_override": None
    },
    "sperrylite": {
        "resource_range": (100, 400),
        "value_range": (5.0, 10.0),
        "color": "#595A32",
        "event_probability_override": 0.0
    }
}

class Robot:
    def __init__(self, owner, capacity):
        self.owner = owner
        self.capacity = capacity

class Asteroid:
    def __init__(self, id, x, y, resource, value, asteroid_type, color, event_probability_override=None):
        self.id = id
        self.x = x
        self.y = y
        self.resource = float(resource)
        self.initial_resource = float(resource)
        self.value = float(value)
        self.asteroid_type = asteroid_type
        self.color = color
        self.robot = None
        self.visited = False
        if event_probability_override is not None:
            self.event_probability = event_probability_override
        else:
            self.event_probability = math.exp(-0.001 * self.initial_resource)

    def is_exhausted(self):
        return self.resource <= 0

    def discovery(self, player):
        events = [
            ("mining", 20),
            ("discovery", 10),
            ("movement", 5),
            ("robot_range", 5),
            ("robot_capacity", 5),
            ("money", 15),
            ("free_robot", 35),
            ("double_upgrade", 5)
        ]
        event_type = random.choices([etype for etype, weight in events],
                                    weights=[weight for etype, weight in events],
                                    k=1)[0]
        if event_type == "mining":
            old = player.mining_capacity
            player.mining_capacity += 10
            return f"Your mining capacity increased by 10! {old} -> {player.mining_capacity}"
        elif event_type == "discovery":
            old = player.discovery_range
            player.discovery_range += 1
            return f"Your discovery range increased by 1! {old} -> {player.discovery_range}"
        elif event_type == "movement":
            old = player.movement_range
            player.movement_range += 1
            return f"Your movement range increased by 1! {old} -> {player.movement_range}"
        elif event_type == "robot_range":
            old = player.robot_range
            player.robot_range += 1
            return f"Your robot range increased by 1! {old} -> {player.robot_range}"
        elif event_type == "robot_capacity":
            old = player.robot_capacity
            player.robot_capacity += 5
            return f"Your robot capacity increased by 10! {old} -> {player.robot_capacity}"
        elif event_type == "money":
            bonus = random.randint(100, 500)
            player.money += bonus
            return f"You received a bonus of ${bonus}!"
        elif event_type == "free_robot":
            if self.robot is None:
                self.robot = Robot(player, player.robot_capacity)
                return "A robot has been planted for you for free on this asteroid!"
            else:
                return "A free robot event was triggered—but a robot is already present. No effect."
        elif event_type == "double_upgrade":
            upgrades = ["mining", "discovery", "movement", "robot_range", "robot_capacity"]
            chosen = random.sample(upgrades, 2)
            messages = []
            for upgrade in chosen:
                if upgrade == "mining":
                    old = player.mining_capacity
                    player.mining_capacity += 10
                    messages.append(f"mining capacity: {old} -> {player.mining_capacity}")
                elif upgrade == "discovery":
                    old = player.discovery_range
                    player.discovery_range += 1
                    messages.append(f"discovery range: {old} -> {player.discovery_range}")
                elif upgrade == "movement":
                    old = player.movement_range
                    player.movement_range += 1
                    messages.append(f"movement range: {old} -> {player.movement_range}")
                elif upgrade == "robot_range":
                    old = player.robot_range
                    player.robot_range += 1
                    messages.append(f"robot range: {old} -> {player.robot_range}")
                elif upgrade == "robot_capacity":
                    old = player.robot_capacity
                    player.robot_capacity += 10
                    messages.append(f"robot capacity: {old} -> {player.robot_capacity}")
            return "Double Upgrade! " + ", ".join(messages)
        else:
            return f"You have encountered a mysterious event on Asteroid A{self.id}."

    def __str__(self):
        s = f"Asteroid {self.id} ({self.asteroid_type}) at ({self.x},{self.y}): "
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
        self.upgrades_purchased = 0
        self.total_mined = 0
        self.x = x
        self.y = y
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
        self.debris = set()  # cells where debris is deployed (impassable)
        self.turn = 1
        self.current_player_index = 0
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
            asteroid_type = random.choice(list(ASTEROID_TYPES.keys()))
            type_props = ASTEROID_TYPES[asteroid_type]
            resource = random.randint(*type_props["resource_range"])
            value = random.uniform(*type_props["value_range"])
            color = type_props["color"]
            event_override = type_props["event_probability_override"]
            self.asteroids.append(
                Asteroid(asteroid_id, x, y, resource, value, asteroid_type, color, event_override)
            )
            asteroid_id += 1

    def update_discovered(self):
        for p in self.players:
            for x in range(self.grid_width):
                for y in range(self.grid_height):
                    if manhattan_distance(p.x, p.y, x, y) <= p.discovery_range:
                        self.discovered_tiles.add((x, y))

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
                if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                    if (nx, ny) not in self.discovered_tiles:
                        continue
                    if (nx, ny) in self.debris:
                        continue
                    if (nx, ny) not in reachable or reachable[(nx, ny)] > dist + 1:
                        reachable[(nx, ny)] = dist + 1
                        queue.append(((nx, ny), dist + 1))
        return reachable

    def find_path(self, start, end, allowed_moves):
        queue = deque()
        queue.append(start)
        prev = {start: None}
        while queue:
            current = queue.popleft()
            if current == end:
                break
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nxt = (current[0] + dx, current[1] + dy)
                if nxt in allowed_moves and nxt not in prev:
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

    def move_player(self, player, dest):
        allowed = self.get_reachable_cells((player.x, player.y), player.movement_range)
        if dest not in allowed:
            return False, "Destination not reachable."
        path = self.find_path((player.x, player.y), dest, allowed)
        if not path:
            return False, "No valid path found."
        for (px, py) in path:
            for i in range(max(0, px - player.discovery_range), min(self.grid_width, px + player.discovery_range + 1)):
                for j in range(max(0, py - player.discovery_range), min(self.grid_height, py + player.discovery_range + 1)):
                    if manhattan_distance(px, py, i, j) <= player.discovery_range:
                        self.discovered_tiles.add((i, j))
        old_pos = (player.x, player.y)
        player.x, player.y = dest
        message = f"{player.symbol} moves from {old_pos} to {dest} via path {path}."
        asteroid = next((a for a in self.asteroids if (a.x, a.y) == dest), None)
        event = None
        if asteroid and not asteroid.visited:
            asteroid.visited = True
            chance = asteroid.event_probability
            if chance > 1:
                chance = 1
            if random.random() < chance:
                event = asteroid.discovery(player)
        return True, (message, event, path, asteroid)

    def get_remote_plant_targets(self, player):
        reachable = self.get_reachable_cells((player.x, player.y), player.robot_range)
        targets = {(a.x, a.y) for a in self.asteroids
                   if (a.x, a.y) in reachable and (a.x, a.y) in self.discovered_tiles
                   and not a.is_exhausted() and a.robot is None}
        return targets

    def can_deploy_debris(self, cell):
        cx, cy = cell
        debris_region = {(cx, cy), (cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)}
        forbidden = set()
        for d in debris_region:
            x, y = d
            forbidden.update({(x, y), (x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)})
        for (x, y) in forbidden:
            if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
                for p in self.players:
                    if (p.x, p.y) == (x, y):
                        return False, "Debris region too close to a player."
        return True, debris_region

    def get_debris_targets(self, player):
        reachable = self.get_reachable_cells((player.x, player.y), player.robot_range + 3)
        targets = set()
        for cell in reachable:
            if any(a for a in self.asteroids if (a.x, a.y) == cell):
                continue
            valid, region = self.can_deploy_debris(cell)
            if valid:
                targets.add(cell)
        return targets

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
            return f"{player.symbol} manually mines {extraction} from A{asteroid.id} and receives ${gain:.1f}."
        else:
            extraction = asteroid.resource
            gain = extraction * asteroid.value
            player.money += gain
            player.total_mined += extraction
            asteroid.resource = 0
            return f"{player.symbol} manually mines {extraction} from A{asteroid.id} (all) and receives ${gain:.1f}."

    def robot_mining(self, log_func):
        for a in self.asteroids:
            if a.robot and not a.is_exhausted():
                extraction = min(a.robot.capacity, a.resource)
                gain = extraction * a.value
                a.resource -= extraction
                a.robot.owner.money += gain
                a.robot.owner.total_mined += extraction
                log_func(f"Robot on A{a.id} (owned by {a.robot.owner.symbol}, Cap: {a.robot.capacity}) extracts {extraction} and earns ${gain:.1f}.")

    def remote_plant_robot(self, player, target):
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
        asteroid = next((a for a in self.asteroids if a.x == player.x and a.y == player.y and not a.is_exhausted()), None)
        if asteroid is None:
            return ("No asteroid here for hijacking.", False)
        if asteroid.robot is None:
            return ("No robot on this asteroid to hijack.", False)
        if asteroid.robot.owner == player:
            return ("You already own the robot here.", False)
        asteroid.robot.owner = player
        asteroid.robot.capacity = player.robot_capacity
        return (f"{player.symbol} hijacks the robot on A{asteroid.id} and now controls it.", True)

    def upgrade_all_robots(self, player):
        upgraded_any = False
        messages = []
        for a in self.asteroids:
            if a.robot and a.robot.owner == player:
                if manhattan_distance(player.x, player.y, a.x, a.y) <= player.robot_range:
                    if a.robot.capacity < player.robot_capacity:
                        old_cap = a.robot.capacity
                        a.robot.capacity = player.robot_capacity
                        messages.append(f"{player.symbol} upgrades robot on A{a.id} from capacity {old_cap} to {player.robot_capacity}.")
                        upgraded_any = True
        if upgraded_any:
            messages.append("All eligible robots have been upgraded.")
        else:
            messages.append("No eligible robots found to upgrade.")
        return messages

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

    def get_current_player(self):
        return self.players[self.current_player_index]

    def next_turn(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        if self.current_player_index == 0:
            self.turn += 1
