import pygame
import random

WIDTH, HEIGHT = 600, 400
BLOCK = 20

class SnakeGame:
    def __init__(self):
        self.snake = [(100, 100)]
        self.direction = "RIGHT"
        self.food = self.spawn_food()

    def spawn_food(self):
        return (random.randrange(0, WIDTH, BLOCK),
                random.randrange(0, HEIGHT, BLOCK))

    def move(self):
        head_x, head_y = self.snake[0]

        if self.direction == "UP":
            head_y -= BLOCK
        elif self.direction == "DOWN":
            head_y += BLOCK
        elif self.direction == "LEFT":
            head_x -= BLOCK
        elif self.direction == "RIGHT":
            head_x += BLOCK

        new_head = (head_x, head_y)
        self.snake.insert(0, new_head)

        if new_head == self.food:
            self.food = self.spawn_food()
        else:
            self.snake.pop()

    def is_game_over(self):
        head = self.snake[0]
        # Check wall collision
        if head[0] < 0 or head[0] >= 600 or head[1] < 0 or head[1] >= 400:
            return True
        # Check self collision
        if head in self.snake[1:]:
            return True
        return False