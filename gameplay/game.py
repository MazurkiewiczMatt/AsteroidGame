# game.py

import random
from collections import deque
from settings import GameSettings
from constants import *

from .player import Player
from .asteroid import Asteroid, ASTEROID_TYPES
from .robot import Robot




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
            telescope = p.get_module("Telescope")
            if telescope is None:
                continue
            for x in range(self.grid_width):
                for y in range(self.grid_height):
                    if manhattan_distance(p.x, p.y, x, y) <= telescope.discovery_range:
                        self.discovered_tiles.add((x, y))

    def get_reachable_cells(self, start, player):

        if not(type(player) == int):

            warp = player.get_module("WarpDrive")
            allowed_warp = set()
            if warp is not None and not(warp.used_this_turn):
                # Allowed moves: any cell that is discovered, not debris, and without an asteroid.
                allowed_warp = {(x, y) for x in range(self.grid_width) for y in range(self.grid_height)
                        if (x, y) in self.discovered_tiles
                        and (x, y) not in self.debris
                        and not any(a for a in self.asteroids if a.x == x and a.y == y)}
            reactor = player.get_module("Reactor")

            if reactor is None and warp is None:
                return False, "No Reactor available nor warp. Cannot move."
                # Check if player has a FusionReactor to modify movement range.
            fusion = player.get_module("FusionReactor")
            if reactor is not None:
                base_range = reactor.movement_range
            else: 
                base_range = 0
            if fusion is not None:
                base_range = int(base_range * fusion.movement_multiplier)
        else:
            base_range = player
        
        
        reachable = {}
        queue = deque()
        queue.append((start, 0))
        reachable[start] = 0
        while queue:
            (x, y), dist = queue.popleft()
            if dist >= base_range:
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

        if not(type(player) == int): 
            reachable = set(reachable.keys()) | set(allowed_warp)

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
        # Check if the player has a WarpDrive.
        warp = player.get_module("WarpDrive")
        allowed_warp = {}
        if warp is not None and not(warp.used_this_turn):
            # Allowed moves: any cell that is discovered, not debris, and without an asteroid.
            allowed_warp = {(x, y) for x in range(self.grid_width) for y in range(self.grid_height)
                       if (x, y) in self.discovered_tiles
                       and (x, y) not in self.debris
                       and not any(a for a in self.asteroids if a.x == x and a.y == y)}
        reactor = player.get_module("Reactor")
        if reactor is None and warp is None:
            return False, "No Reactor available. Cannot move."
            # Check if player has a FusionReactor to modify movement range.
        fusion = player.get_module("FusionReactor")
        base_range = reactor.movement_range
        if fusion is not None:
            base_range = int(base_range * fusion.movement_multiplier)
        allowed = self.get_reachable_cells((player.x, player.y), player)
        if dest not in allowed:
            return False, "Destination not reachable."
        path = self.find_path((player.x, player.y), dest, allowed)
        if not path and warp is None:
            return False, "No valid path found."
        # If not using warp drive, update discovered tiles based on Telescope.
        telescope = player.get_module("Telescope")
        if telescope is not None:
            for (px, py) in path:
                for i in range(max(0, px - telescope.discovery_range), min(self.grid_width, px + telescope.discovery_range + 1)):
                    for j in range(max(0, py - telescope.discovery_range), min(self.grid_height, py + telescope.discovery_range + 1)):
                        if manhattan_distance(px, py, i, j) <= telescope.discovery_range:
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
        # If using WarpDrive level 2, movement is instant (do not end turn).
        if warp is not None and warp.level == 2:
            message += " (Instant Warp: turn not consumed)"
        return True, (message, event, path, asteroid)

    def get_remote_plant_targets(self, player):
        launch_bay = player.get_module("LaunchBay")
        factory = player.get_module("Factory")
        if launch_bay is None or factory is None or factory.robots_produced_this_turn >= factory.robot_production:
            return set()
        reachable = self.get_reachable_cells((player.x, player.y), launch_bay.robot_range)
        targets = {(a.x, a.y) for a in self.asteroids
                   if (a.x, a.y) in reachable and (a.x, a.y) in self.discovered_tiles
                   and not a.is_exhausted() and a.robot is None}
        return targets

    def can_deploy_debris(self, cell):
        cx, cy = cell
        # Check if player has an ExplosivesLab to modify debris radius.
        # For simplicity, we assume that the current player’s ExplosivesLab (if any) affects debris.
        current = self.players[self.current_player_index]
        explosives = current.get_module("ExplosivesLab")
        radius = 1  # default
        if explosives is not None:
            radius += explosives.debris_radius
        debris_region = {(cx + dx, cy + dy) for dx in range(-radius, radius + 1) for dy in range(-radius, radius + 1)
                         if abs(dx) + abs(dy) <= radius}
        forbidden = set()
        for (x, y) in debris_region:
            forbidden.update({(x, y), (x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)})
        for (x, y) in forbidden:
            if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
                for p in self.players:
                    if (p.x, p.y) == (x, y):
                        return False, "Debris region too close to a player."
        return True, debris_region

    def get_debris_targets(self, player):
        launch_bay = player.get_module("LaunchBay")
        if launch_bay is None:
            return set()
        explosives = player.get_module("ExplosivesLab")
        if explosives is not None:
            reachable = self.get_reachable_cells((player.x, player.y), launch_bay.robot_range + explosives.extra_range)
        else:
            reachable = self.get_reachable_cells((player.x, player.y), launch_bay.robot_range + 3)
        targets = set()
        for cell in reachable:
            if any(a for a in self.asteroids if (a.x, a.y) == cell):
                continue
            valid, region = self.can_deploy_debris(cell)
            if valid:
                targets.add(cell)
        return targets

    def manual_mine(self, player, asteroid):
        drill = player.get_module("Drill")
        if drill is None:
            return "No Drill available. Cannot mine."
        if asteroid.is_exhausted():
            return f"Asteroid {asteroid.id} is exhausted."
        capacity = drill.mining_capacity
        # Check for IcePenetrator effect if mining an ice asteroid.
        if asteroid.asteroid_type.lower() == "ice":
            ip = player.get_module("IcePenetrator")
            if ip is not None:
                capacity *= ip.multiplier
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
        launch_bay = player.get_module("LaunchBay")
        if launch_bay is None:
            return ("No LaunchBay available. Cannot plant robot remotely.", False)
        player.money -= 100
        factory = player.get_module("Factory")
        if factory is None:
            return ("No Factory available. Cannot determine robot capacity.", False)
        target.robot = Robot(player, factory.robot_capacity)
        return (f"{player.symbol} plants a robot on A{target.id} with capacity {factory.robot_capacity}.", False)

    def hijack_robot(self, player):
        asteroid = next((a for a in self.asteroids if a.x == player.x and a.y == player.y and not a.is_exhausted()), None)
        if asteroid is None:
            return ("No asteroid here for hijacking.", False)
        if asteroid.robot is None:
            return ("No robot on this asteroid to hijack.", False)
        if asteroid.robot.owner == player:
            return ("You already own the robot here.", False)
        factory = player.get_module("Factory")
        if factory is None:
            return ("No Factory available. Cannot hijack robot.", False)
        asteroid.robot.owner = player
        asteroid.robot.capacity = factory.robot_capacity
        return (f"{player.symbol} hijacks the robot on A{asteroid.id} and now controls it.", True)

    def upgrade_all_robots(self, player):
        launch_bay = player.get_module("LaunchBay")
        factory = player.get_module("Factory")
        if launch_bay is None or factory is None:
            return ["Required modules missing to upgrade robots."]
        upgraded_any = False
        messages = []
        for a in self.asteroids:
            if a.robot and a.robot.owner == player:
                if manhattan_distance(player.x, player.y, a.x, a.y) <= launch_bay.robot_range:
                    if a.robot.capacity < factory.robot_capacity:
                        old_cap = a.robot.capacity
                        a.robot.capacity = factory.robot_capacity
                        messages.append(f"{player.symbol} upgrades robot on A{a.id} from capacity {old_cap} to {factory.robot_capacity}.")
                        upgraded_any = True
        if upgraded_any:
            messages.append("All eligible robots have been upgraded.")
        else:
            messages.append("No eligible robots found to upgrade.")
        return messages

    def upgrade_player(self, player, upgrade_type, log_func):
        if upgrade_type == "mining":
            drill = player.get_module("Drill")
            if drill is None:
                log_func("No Drill available to upgrade.")
                return
            success, message = drill.upgrade(player)
            if success:
                player.upgrades_purchased += 1
            log_func(message)
        elif upgrade_type == "discovery":
            telescope = player.get_module("Telescope")
            if telescope is None:
                log_func("No Telescope available to upgrade.")
                return
            success, message = telescope.upgrade(player)
            if success:
                player.upgrades_purchased += 1
            log_func(message)
        elif upgrade_type == "movement":
            reactor = player.get_module("Reactor")
            if reactor is None:
                log_func("No Reactor available to upgrade.")
                return
            success, message = reactor.upgrade(player)
            if success:
                player.upgrades_purchased += 1
            log_func(message)
        elif upgrade_type == "robot_range":
            launch_bay = player.get_module("LaunchBay")
            if launch_bay is None:
                log_func("No LaunchBay available to upgrade.")
                return
            success, message = launch_bay.upgrade(player)
            if success:
                player.upgrades_purchased += 1
            log_func(message)
        elif upgrade_type == "robot_capacity":
            factory = player.get_module("Factory")
            if factory is None:
                log_func("No Factory available to upgrade.")
                return
            success, message = factory.upgrade(player)
            if success:
                player.upgrades_purchased += 1
            log_func(message)

    def is_game_over(self):
        return all(a.is_exhausted() for a in self.asteroids)

    def get_current_player(self):
        return self.players[self.current_player_index]

    def next_turn(self):
        # resetting modules
        for player in self.players:
            for module in player.modules:
                module.next_turn()
        # updating active player index
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        if self.current_player_index == 0:
            self.turn += 1
