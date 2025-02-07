# settings.py

class GameSettings:
    def __init__(self,
                 num_players=3,
                 grid_width=16,
                 grid_height=16,
                 initial_money=500,
                 initial_mining_capacity=100,
                 initial_discovery_range=2,
                 initial_movement_range=2,
                 initial_robot_range=0,
                 upgrade_robot_range_cost=200,
                 robot_range_upgrade_amount=1,
                 upgrade_mining_cost=200,
                 mining_upgrade_amount=10,
                 upgrade_discovery_cost=150,
                 discovery_upgrade_amount=1,
                 upgrade_movement_cost=150,
                 movement_upgrade_amount=1,
                 initial_robot_capacity=10,
                 upgrade_robot_capacity_cost=200,
                 robot_capacity_upgrade_amount=5,
                 turn_timer_duration=30,
                 # Dynamic upgrade cost increases:
                 upgrade_mining_cost_increase=10,
                 upgrade_discovery_cost_increase=20,
                 upgrade_movement_cost_increase=20,
                 upgrade_robot_range_cost_increase=50,
                 upgrade_robot_capacity_cost_increase=50,
                 # Asteroid spawn count (unused “asteroid_min/max” removed):
                 min_asteroids=5,
                 max_asteroids=10, **kwargs):
        self.num_players = num_players
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.initial_money = initial_money
        self.initial_mining_capacity = initial_mining_capacity
        self.initial_discovery_range = initial_discovery_range
        self.initial_movement_range = initial_movement_range
        self.initial_robot_range = initial_robot_range
        self.upgrade_robot_range_cost = upgrade_robot_range_cost
        self.robot_range_upgrade_amount = robot_range_upgrade_amount
        self.upgrade_mining_cost = upgrade_mining_cost
        self.mining_upgrade_amount = mining_upgrade_amount
        self.upgrade_discovery_cost = upgrade_discovery_cost
        self.discovery_upgrade_amount = discovery_upgrade_amount
        self.upgrade_movement_cost = upgrade_movement_cost
        self.movement_upgrade_amount = movement_upgrade_amount
        self.initial_robot_capacity = initial_robot_capacity
        self.upgrade_robot_capacity_cost = upgrade_robot_capacity_cost
        self.robot_capacity_upgrade_amount = robot_capacity_upgrade_amount
        self.turn_timer_duration = turn_timer_duration
        self.upgrade_mining_cost_increase = upgrade_mining_cost_increase
        self.upgrade_discovery_cost_increase = upgrade_discovery_cost_increase
        self.upgrade_movement_cost_increase = upgrade_movement_cost_increase
        self.upgrade_robot_range_cost_increase = upgrade_robot_range_cost_increase
        self.upgrade_robot_capacity_cost_increase = upgrade_robot_capacity_cost_increase
        self.min_asteroids = min_asteroids
        self.max_asteroids = max_asteroids
