import pygame
import random

WIDTH, HEIGHT = 1200, 800
BLOCK = 20
PLAY_AREA_TOP = 100  # Space for stats at the top

class SnakeGame:
    def __init__(self):
        self.snake = [(WIDTH // 2, (HEIGHT + PLAY_AREA_TOP) // 2)]
        self.direction = "RIGHT"
        self.next_direction = "RIGHT"
        self.food = self.spawn_food()
        self.score = 0
        self.food_eaten = False
        self.game_over = False

    def spawn_food(self):
        """Spawn food in a valid location (not on snake body)."""
        while True:
            x = random.randrange(0, WIDTH, BLOCK)
            y = random.randrange(PLAY_AREA_TOP, HEIGHT, BLOCK)
            # Make sure food doesn't spawn on snake
            if (x, y) not in self.snake:
                return (x, y)

    def move(self):
        """Move the snake and handle food collision with growth."""
        if self.game_over:
            return

        # Use next_direction for smoother controls
        if self.next_direction:
            self.direction = self.next_direction
            self.next_direction = None
            
        head_x, head_y = self.snake[0]

        # Move in current direction
        if self.direction == "UP":
            head_y -= BLOCK
        elif self.direction == "DOWN":
            head_y += BLOCK
        elif self.direction == "LEFT":
            head_x -= BLOCK
        elif self.direction == "RIGHT":
            head_x += BLOCK

        # WRAP AROUND BORDERS (toroidal world)
        # Horizontal wrapping
        if head_x < 0:
            head_x = WIDTH - BLOCK
        elif head_x >= WIDTH:
            head_x = 0
        
        # Vertical wrapping (respecting play area boundaries)
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

        # Check if food is eaten
        if new_head == self.food:
            self.food = self.spawn_food()
            self.score += 10
            self.food_eaten = True
            # DON'T pop tail - snake grows!
        else:
            self.snake.pop()  # Remove tail if not eating food

    def is_game_over(self):
        """Check if snake collides with itself."""
        return self.game_over