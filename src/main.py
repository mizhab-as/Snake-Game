import pygame
import cv2
import numpy as np
import json
import os
from snake import SnakeGame, WIDTH, HEIGHT, PLAY_AREA_TOP, BLOCK
from hand_tracking import get_direction, get_hand_position

pygame.init()
SCREEN_WIDTH = WIDTH
SCREEN_HEIGHT = HEIGHT
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("🐍 Snake Game - Hand Gesture Control")
clock = pygame.time.Clock()

# Professional fonts
title_font = pygame.font.Font(None, 64)
font = pygame.font.Font(None, 48)
small_font = pygame.font.Font(None, 32)
tiny_font = pygame.font.Font(None, 24)

# High score file
HIGH_SCORE_FILE = "/tmp/snake_highscore.json"

def load_high_score():
    """Load high score from file."""
    try:
        if os.path.exists(HIGH_SCORE_FILE):
            with open(HIGH_SCORE_FILE, 'r') as f:
                data = json.load(f)
                return data.get('high_score', 0)
    except:
        pass
    return 0

def save_high_score(score):
    """Save high score to file."""
    try:
        with open(HIGH_SCORE_FILE, 'w') as f:
            json.dump({'high_score': score}, f)
    except:
        pass

high_score = load_high_score()

game = SnakeGame()
cap = cv2.VideoCapture(0)
camera_available = cap.isOpened() and cap.get(cv2.CAP_PROP_FRAME_WIDTH) > 0

running = True
game_over = False
show_gesture_help = False
gesture_type = None
hand_x, hand_y = None, None
hand_confidence = 0

def draw_gradient_background():
    """Draw a nice gradient background."""
    for y in range(SCREEN_HEIGHT):
        # Dark blue to darker blue gradient
        color = (10 + int(20 * (y / SCREEN_HEIGHT)), 15 + int(40 * (y / SCREEN_HEIGHT)), 40)
        pygame.draw.line(screen, color, (0, y), (SCREEN_WIDTH, y))

def draw_game_area():
    """Draw the game play area with border."""
    # Draw border around play area
    border_color = (100, 200, 100)
    pygame.draw.rect(screen, border_color, (0, PLAY_AREA_TOP, SCREEN_WIDTH, HEIGHT - PLAY_AREA_TOP), 3)
    
    # Draw grid pattern (subtle)
    grid_color = (30, 50, 30)
    for x in range(0, SCREEN_WIDTH, BLOCK * 5):
        pygame.draw.line(screen, grid_color, (x, PLAY_AREA_TOP), (x, SCREEN_HEIGHT), 1)
    for y in range(PLAY_AREA_TOP, SCREEN_HEIGHT, BLOCK * 5):
        pygame.draw.line(screen, grid_color, (0, y), (SCREEN_WIDTH, y), 1)

def draw_stats(current_score):
    """Draw score and high score at the top."""
    # Background for stats
    pygame.draw.rect(screen, (20, 30, 50), (0, 0, SCREEN_WIDTH, PLAY_AREA_TOP))
    pygame.draw.line(screen, (100, 200, 100), (0, PLAY_AREA_TOP), (SCREEN_WIDTH, PLAY_AREA_TOP), 2)
    
    # Score
    score_text = font.render(f"Score: {current_score}", True, (100, 255, 100))
    screen.blit(score_text, (30, 20))
    
    # High score
    high_score_text = font.render(f"High Score: {high_score}", True, (255, 200, 100))
    high_score_rect = high_score_text.get_rect()
    high_score_rect.topright = (SCREEN_WIDTH - 30, 20)
    screen.blit(high_score_text, high_score_rect)
    
    # Camera status
    if camera_available:
        status_text = tiny_font.render("🎥 Camera: ON", True, (100, 255, 100))
    else:
        status_text = tiny_font.render("⌨️  Keyboard Mode", True, (255, 100, 100))
    screen.blit(status_text, (SCREEN_WIDTH // 2 - 70, 48))

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if game_over and event.key == pygame.K_q:
                running = False
            # Keyboard controls (arrow keys or WASD)
            elif event.key == pygame.K_UP or event.key == pygame.K_w:
                if not game_over and game.direction != "DOWN":
                    game.next_direction = "UP"
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                if not game_over and game.direction != "UP":
                    game.next_direction = "DOWN"
            elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                if not game_over and game.direction != "RIGHT":
                    game.next_direction = "LEFT"
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                if not game_over and game.direction != "LEFT":
                    game.next_direction = "RIGHT"
            # Restart on R key
            elif event.key == pygame.K_r:
                game = SnakeGame()
                game_over = False
            # Toggle help on H key
            elif event.key == pygame.K_h:
                show_gesture_help = not show_gesture_help

    if not game_over:
        if camera_available:
            ret, frame = cap.read()
            if ret and frame is not None:
                direction, confidence = get_direction(frame)
                if direction and game.direction != direction:
                    # Fix camera mirroring (left/right are reversed in camera view)
                    if direction == "LEFT":
                        direction = "RIGHT"
                    elif direction == "RIGHT":
                        direction = "LEFT"
                    
                    # Prevent opposite direction
                    opposite = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}
                    if direction != opposite.get(game.direction):
                        game.next_direction = direction
                
                hand_x, hand_y, gesture_type = get_hand_position(frame)
                if confidence:
                    hand_confidence = confidence

        game.move()

        if game.is_game_over():
            game_over = True
            if game.score > high_score:
                high_score = game.score
                save_high_score(high_score)

    # Draw everything
    draw_gradient_background()
    draw_game_area()
    draw_stats(game.score)

    # Draw snake with gradient effect
    for i, segment in enumerate(game.snake):
        # Snake gets darker towards the tail
        intensity = int(255 * (1 - (i / len(game.snake)) * 0.5))
        color = (0, intensity, 0)
        pygame.draw.rect(screen, color, (*segment, BLOCK, BLOCK))
        pygame.draw.rect(screen, (100, 255, 100), (*segment, BLOCK, BLOCK), 1)  # Border

    # Draw food with glow effect
    food_x, food_y = game.food
    pygame.draw.rect(screen, (255, 100, 100), (food_x - 3, food_y - 3, BLOCK + 6, BLOCK + 6))  # Glow
    pygame.draw.rect(screen, (255, 0, 0), (food_x, food_y, BLOCK, BLOCK))
    pygame.draw.rect(screen, (255, 150, 150), (food_x, food_y, BLOCK, BLOCK), 1)

    # Draw gesture indicator if camera available
    if camera_available and camera_available:
        if hand_x is not None and hand_y is not None:
            hand_pixel_x = int(hand_x * SCREEN_WIDTH)
            hand_pixel_y = int(hand_y * SCREEN_HEIGHT)
            
            # Only draw if in game area
            if PLAY_AREA_TOP <= hand_pixel_y < SCREEN_HEIGHT:
                gesture_color = (0, 255, 100) if gesture_type == "POINTING" else (100, 200, 255) if gesture_type == "OPEN" else (200, 100, 200)
                pygame.draw.circle(screen, gesture_color, (hand_pixel_x, hand_pixel_y), 15, 3)
                pygame.draw.circle(screen, gesture_color, (hand_pixel_x, hand_pixel_y), 10, 1)

    # Draw game over screen
    if game_over:
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # Game over text
        game_over_text = title_font.render("GAME OVER!", True, (255, 100, 100))
        text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 150))
        screen.blit(game_over_text, text_rect)
        
        # Final score
        final_score = font.render(f"Final Score: {game.score}", True, (100, 255, 100))
        score_rect = final_score.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        screen.blit(final_score, score_rect)
        
        # High score indicator
        if game.score >= high_score:
            new_high = small_font.render("🏆 NEW HIGH SCORE! 🏆", True, (255, 200, 100))
            new_high_rect = new_high.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
            screen.blit(new_high, new_high_rect)
        
        # Restart instruction
        restart_text = small_font.render("Press R to Restart or Q to Quit", True, (200, 200, 200))
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
        screen.blit(restart_text, restart_rect)

    # Draw help overlay
    if show_gesture_help and not game_over:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        help_title = title_font.render("CONTROLS", True, (100, 200, 255))
        help_title_rect = help_title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        screen.blit(help_title, help_title_rect)
        
        help_lines = [
            "🤚 Hand Gesture: Move your hand to control the snake",
            "⌨️  Keyboard: Arrow Keys or WASD",
            "🎮 Touch Input: Swipe to change direction",
            "",
            "R: Restart Game",
            "H: Toggle Help",
            "Q: Quit Game"
        ]
        for i, line in enumerate(help_lines):
            help_text = small_font.render(line, True, (200, 200, 200))
            screen.blit(help_text, (SCREEN_WIDTH // 2 - 250, 250 + i * 50))

    pygame.display.update()
    clock.tick(10)

pygame.quit()
cap.release()