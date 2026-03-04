import pygame
import random

WIDTH, HEIGHT = 1200, 800
BLOCK = 20
PLAY_AREA_TOP = 100

class PowerUp:
    TYPE_SPEED_BOOST = "speed_boost"
    TYPE_SHIELD = "shield"
    TYPE_MULTIPLIER = "multiplier"
    
    def __init__(self, x, y, power_type):
        self.x = x
        self.y = y
        self.type = power_type
        self.duration = 300

class SnakeGame:
    
    def __init__(self):
        self.snake = [(WIDTH // 2, (HEIGHT + PLAY_AREA_TOP) // 2)]
        self.direction = "RIGHT"
        self.next_direction = "RIGHT"
        self.food = self.spawn_food()
        self.score = 0
        self.food_eaten = False
        self.game_over = False
        self.combo = 0
        self.difficulty = 1
        self.power_ups = []
        self.active_power_ups = {}
        self.food_streak = 0

    def spawn_food(self):
        """Spawn food in a valid location (not on snake body)."""
        while True:
            x = random.randrange(0, WIDTH, BLOCK)
            y = random.randrange(PLAY_AREA_TOP, HEIGHT, BLOCK)
            if (x, y) not in self.snake:
                return (x, y)
    
    def spawn_power_up(self):
        """Randomly spawn a power-up (20% chance)."""
        if random.random() > 0.8 and len(self.power_ups) < 3:
            x = random.randrange(0, WIDTH, BLOCK)
            y = random.randrange(PLAY_AREA_TOP, HEIGHT, BLOCK)
            if (x, y) not in self.snake and (x, y) != self.food:
                power_type = random.choice([PowerUp.TYPE_SPEED_BOOST, PowerUp.TYPE_MULTIPLIER])
                self.power_ups.append(PowerUp(x, y, power_type))
    
    def update_difficulty(self):
        """Increase difficulty based on score."""
        new_difficulty = 1 + (self.score // 200)
        if new_difficulty != self.difficulty:
            self.difficulty = new_difficulty
    
    def update_power_ups(self):
        """Update power-up durations and remove expired ones."""
        expired = []
        for power_type, frames_left in self.active_power_ups.items():
            self.active_power_ups[power_type] -= 1
            if self.active_power_ups[power_type] <= 0:
                expired.append(power_type)
        
        for power_type in expired:
            del self.active_power_ups[power_type]

    def move(self):
        """Move the snake and handle food collision with growth."""
        if self.game_over:
            return

        if self.next_direction:
            self.direction = self.next_direction
            self.next_direction = None
            
        head_x, head_y = self.snake[0]

        if self.direction == "UP":
            head_y -= BLOCK
        elif self.direction == "DOWN":
            head_y += BLOCK
        elif self.direction == "LEFT":
            head_x -= BLOCK
        elif self.direction == "RIGHT":
            head_x += BLOCK

        if head_x < 0:
            head_x = WIDTH - BLOCK
        elif head_x >= WIDTH:
            head_x = 0
        
        if head_y < PLAY_AREA_TOP:
            head_y = HEIGHT - BLOCK
        elif head_y >= HEIGHT:
            head_y = PLAY_AREA_TOP

        new_head = (head_x, head_y)

        will_eat = new_head == self.food
        body_to_check = self.snake if will_eat else self.snake[:-1]
        if new_head in body_to_check:
            self.game_over = True
            return

        self.snake.insert(0, new_head)

        if new_head == self.food:
            self.food = self.spawn_food()
            self.food_streak += 1
            self.combo += 1
            
            base_score = 10
            multiplier = 1
            if PowerUp.TYPE_MULTIPLIER in self.active_power_ups:
                multiplier = 2
            
            self.score += base_score * multiplier * self.difficulty
            self.food_eaten = True
            self.spawn_power_up()
        else:
            self.food_streak = 0
            self.snake.pop()
        
        for power_up in self.power_ups[:]:
            if new_head == (power_up.x, power_up.y):
                self.active_power_ups[power_up.type] = power_up.duration
                self.score += 50
                self.power_ups.remove(power_up)
        
        self.update_power_ups()
        self.update_difficulty()

    def is_game_over(self):
        """Check if snake collides with itself."""
        return self.game_over