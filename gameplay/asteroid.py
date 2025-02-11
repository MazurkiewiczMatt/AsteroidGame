import random
import math

from .robot import Robot

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
            drill = player.get_module("Drill")
            if drill is None:
                return "No Drill available. Cannot increase mining capacity."
            old = drill.mining_capacity
            drill.mining_capacity += 10
            return f"Your mining capacity increased by 10! {old} -> {drill.mining_capacity}"
        elif event_type == "discovery":
            telescope = player.get_module("Telescope")
            if telescope is None:
                return "No Telescope available. Cannot increase discovery range."
            old = telescope.discovery_range
            telescope.discovery_range += 1
            return f"Your discovery range increased by 1! {old} -> {telescope.discovery_range}"
        elif event_type == "movement":
            reactor = player.get_module("Reactor")
            if reactor is None:
                return "No Reactor available. Cannot increase movement range."
            old = reactor.movement_range
            reactor.movement_range += 1
            return f"Your movement range increased by 1! {old} -> {reactor.movement_range}"
        elif event_type == "robot_range":
            launch_bay = player.get_module("LaunchBay")
            if launch_bay is None:
                return "No LaunchBay available. Cannot increase robot range."
            old = launch_bay.robot_range
            launch_bay.robot_range += 1
            return f"Your robot range increased by 1! {old} -> {launch_bay.robot_range}"
        elif event_type == "robot_capacity":
            factory = player.get_module("Factory")
            if factory is None:
                return "No Factory available. Cannot increase robot capacity."
            old = factory.robot_capacity
            factory.robot_capacity += 5
            return f"Your robot capacity increased by 10! {old} -> {factory.robot_capacity}"
        elif event_type == "money":
            bonus = random.randint(100, 500)
            player.money += bonus
            return f"You received a bonus of ${bonus}!"
        elif event_type == "free_robot":
            if self.robot is None:
                factory = player.get_module("Factory")
                if factory is None:
                    return "No Factory available. Cannot plant a free robot."
                self.robot = Robot(player, factory.robot_capacity)
                return "A robot has been planted for you for free on this asteroid!"
            else:
                return "A free robot event was triggered—but a robot is already present. No effect."
        elif event_type == "double_upgrade":
            upgrades = ["mining", "discovery", "movement", "robot_range", "robot_capacity"]
            chosen = random.sample(upgrades, 2)
            messages = []
            for upgrade in chosen:
                if upgrade == "mining":
                    drill = player.get_module("Drill")
                    if drill is not None:
                        old = drill.mining_capacity
                        drill.mining_capacity += 10
                        messages.append(f"mining capacity: {old} -> {drill.mining_capacity}")
                elif upgrade == "discovery":
                    telescope = player.get_module("Telescope")
                    if telescope is not None:
                        old = telescope.discovery_range
                        telescope.discovery_range += 1
                        messages.append(f"discovery range: {old} -> {telescope.discovery_range}")
                elif upgrade == "movement":
                    reactor = player.get_module("Reactor")
                    if reactor is not None:
                        old = reactor.movement_range
                        reactor.movement_range += 1
                        messages.append(f"movement range: {old} -> {reactor.movement_range}")
                elif upgrade == "robot_range":
                    launch_bay = player.get_module("LaunchBay")
                    if launch_bay is not None:
                        old = launch_bay.robot_range
                        launch_bay.robot_range += 1
                        messages.append(f"robot range: {old} -> {launch_bay.robot_range}")
                elif upgrade == "robot_capacity":
                    factory = player.get_module("Factory")
                    if factory is not None:
                        old = factory.robot_capacity
                        factory.robot_capacity += 10
                        messages.append(f"robot capacity: {old} -> {factory.robot_capacity}")
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