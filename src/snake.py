import pygame
import random

WIDTH, HEIGHT = 1200, 800
BLOCK = 20
PLAY_AREA_TOP = 100

class GameMode:
    CLASSIC = "classic"
    ARCADE = "arcade"
    ZEN = "zen"

class Particle:
    def __init__(self, x, y, color, lifetime=20):
        self.x = x
        self.y = y
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-3, 0)
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.1
        self.lifetime -= 1
    
    def draw(self, screen):
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        size = int(4 * (self.lifetime / self.max_lifetime))
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), max(1, size))

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
    
    def __init__(self, mode=GameMode.CLASSIC):
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
        self.mode = mode
        self.obstacles = []
        self.shield_active = False
        self.particles = []
        self.generate_obstacles()

    def spawn_food(self):
        while True:
            x = random.randrange(0, WIDTH, BLOCK)
            y = random.randrange(PLAY_AREA_TOP, HEIGHT, BLOCK)
            if (x, y) not in self.snake:
                return (x, y)
    
    def spawn_power_up(self):
        if random.random() > 0.8 and len(self.power_ups) < 3:
            x = random.randrange(0, WIDTH, BLOCK)
            y = random.randrange(PLAY_AREA_TOP, HEIGHT, BLOCK)
            if (x, y) not in self.snake and (x, y) != self.food and (x, y) not in self.obstacles:
                power_type = random.choice([PowerUp.TYPE_SPEED_BOOST, PowerUp.TYPE_MULTIPLIER, PowerUp.TYPE_SHIELD])
                self.power_ups.append(PowerUp(x, y, power_type))
    
    def update_difficulty(self):
        new_difficulty = 1 + (self.score // 200)
        if new_difficulty != self.difficulty:
            self.difficulty = new_difficulty
    
    def update_power_ups(self):
        expired = []
        for power_type, frames_left in self.active_power_ups.items():
            self.active_power_ups[power_type] -= 1
            if self.active_power_ups[power_type] <= 0:
                expired.append(power_type)
        
        for power_type in expired:
            del self.active_power_ups[power_type]
            if power_type == PowerUp.TYPE_SHIELD:
                self.shield_active = False
    
    def generate_obstacles(self):
        self.obstacles = []
        if self.mode == GameMode.ARCADE:
            num_obstacles = random.randint(8, 12)
            for _ in range(num_obstacles):
                while True:
                    x = random.randrange(0, WIDTH, BLOCK)
                    y = random.randrange(PLAY_AREA_TOP, HEIGHT, BLOCK)
                    if (x, y) not in self.snake and (x, y) != self.food:
                        self.obstacles.append((x, y))
                        break
    
    def spawn_particles(self, x, y, color, count=10):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def move(self):
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

        if new_head in self.obstacles:
            if self.shield_active:
                self.shield_active = False
                self.active_power_ups.pop(PowerUp.TYPE_SHIELD, None)
                self.spawn_particles(head_x, head_y, (0, 150, 255), 15)
                return
            else:
                self.game_over = True
                return

        self.snake.insert(0, new_head)

        if new_head == self.food:
            self.spawn_particles(head_x, head_y, (255, 100, 100), 12)
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
                if power_up.type == PowerUp.TYPE_SHIELD:
                    self.shield_active = True
                    self.spawn_particles(power_up.x, power_up.y, (100, 255, 100), 20)
                self.score += 50
                self.power_ups.remove(power_up)
        
        self.update_particles()
        self.update_power_ups()
        self.update_difficulty()
    
    def update_particles(self):
        for particle in self.particles[:]:
            particle.update()
            if particle.lifetime <= 0:
                self.particles.remove(particle)

    def is_game_over(self):
        return self.game_over