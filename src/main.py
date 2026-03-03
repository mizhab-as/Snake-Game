import pygame
import cv2
import numpy as np
from snake import SnakeGame
from hand_tracking import get_direction, get_hand_position

pygame.init()
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Snake Game - Arrow Keys or Hand Gestures")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)
tiny_font = pygame.font.Font(None, 18)

game = SnakeGame()
cap = cv2.VideoCapture(0)
camera_available = cap.isOpened() and cap.get(cv2.CAP_PROP_FRAME_WIDTH) > 0

running = True
game_over = False
show_gesture_help = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            # Keyboard controls (arrow keys or WASD)
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                if game.direction != "DOWN":
                    game.direction = "UP"
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                if game.direction != "UP":
                    game.direction = "DOWN"
            elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                if game.direction != "RIGHT":
                    game.direction = "LEFT"
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                if game.direction != "LEFT":
                    game.direction = "RIGHT"
            # Restart on R key
            elif event.key == pygame.K_r:
                game = SnakeGame()
                game_over = False
            # Toggle help on H key
            elif event.key == pygame.K_h:
                show_gesture_help = not show_gesture_help

    if not game_over:
        hand_x, hand_y = None, None
        hand_confidence = 0
        
        if camera_available:
            ret, frame = cap.read()
            if ret and frame is not None:
                direction, confidence = get_direction(frame)
                if direction:
                    game.direction = direction
                
                hand_x, hand_y = get_hand_position(frame)
                if confidence:
                    hand_confidence = confidence

        game.move()

        if game.is_game_over():
            game_over = True

    screen.fill((0, 0, 0))

    # Draw snake
    for segment in game.snake:
        pygame.draw.rect(screen, (0, 255, 0), (*segment, 20, 20))

    # Draw food
    pygame.draw.rect(screen, (255, 0, 0), (*game.food, 20, 20))

    # Draw score
    score_text = font.render(f"Score: {len(game.snake) - 1}", True, (255, 255, 255))
    screen.blit(score_text, (10, 10))

    # Draw camera status
    if camera_available:
        camera_status = f"Camera: ON | Confidence: {int(hand_confidence * 100)}%"
        status_color = (100, 255, 100)
    else:
        camera_status = "Camera: OFF (Use Keyboard)"
        status_color = (255, 100, 100)
    
    status_text = small_font.render(camera_status, True, status_color)
    screen.blit(status_text, (10, 50))

    # Draw gesture zones and guides
    if show_gesture_help and camera_available:
        # Draw gesture direction guides
        zone_color = (100, 255, 100)
        
        # Draw arrows/directions for gestures
        arrow_length = 30
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        
        # UP arrow
        pygame.draw.line(screen, zone_color, (center_x, center_y - 50), (center_x, center_y - 80), 3)
        pygame.draw.line(screen, zone_color, (center_x - 10, center_y - 70), (center_x, center_y - 80), 3)
        pygame.draw.line(screen, zone_color, (center_x + 10, center_y - 70), (center_x, center_y - 80), 3)
        
        # DOWN arrow
        pygame.draw.line(screen, zone_color, (center_x, center_y + 50), (center_x, center_y + 80), 3)
        pygame.draw.line(screen, zone_color, (center_x - 10, center_y + 70), (center_x, center_y + 80), 3)
        pygame.draw.line(screen, zone_color, (center_x + 10, center_y + 70), (center_x, center_y + 80), 3)
        
        # LEFT arrow
        pygame.draw.line(screen, zone_color, (center_x - 50, center_y), (center_x - 80, center_y), 3)
        pygame.draw.line(screen, zone_color, (center_x - 70, center_y - 10), (center_x - 80, center_y), 3)
        pygame.draw.line(screen, zone_color, (center_x - 70, center_y + 10), (center_x - 80, center_y), 3)
        
        # RIGHT arrow
        pygame.draw.line(screen, zone_color, (center_x + 50, center_y), (center_x + 80, center_y), 3)
        pygame.draw.line(screen, zone_color, (center_x + 70, center_y - 10), (center_x + 80, center_y), 3)
        pygame.draw.line(screen, zone_color, (center_x + 70, center_y + 10), (center_x + 80, center_y), 3)
        
        # Center text
        center_text = tiny_font.render("POINT FINGER IN DIRECTION", True, (255, 255, 100))
        screen.blit(center_text, (center_x - 120, center_y - 12))
        
        # Draw current hand position if detected
        if hand_x is not None and hand_y is not None:
            hand_pixel_x = int(hand_x * SCREEN_WIDTH)
            hand_pixel_y = int(hand_y * SCREEN_HEIGHT)
            pygame.draw.circle(screen, (0, 255, 255), (hand_pixel_x, hand_pixel_y), 10, 2)
            wrist_label = tiny_font.render("Wrist", True, (0, 255, 255))
            screen.blit(wrist_label, (hand_pixel_x + 15, hand_pixel_y))
    
    # Draw help text
    if show_gesture_help:
        help_lines = [
            "HAND GESTURES: Point your finger in the direction you want to move",
            "KEYBOARD: Arrow Keys or WASD",
            "PRESS H to hide guides | R to restart"
        ]
        for i, line in enumerate(help_lines):
            help_text = tiny_font.render(line, True, (200, 200, 200))
            screen.blit(help_text, (10, SCREEN_HEIGHT - 70 + i * 22))

    # Draw game over message
    if game_over:
        game_over_text = font.render("GAME OVER!", True, (255, 0, 0))
        text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, 150))
        screen.blit(game_over_text, text_rect)
        
        final_score = small_font.render(f"Final Score: {len(game.snake) - 1}", True, (255, 255, 255))
        score_rect = final_score.get_rect(center=(SCREEN_WIDTH // 2, 200))
        screen.blit(final_score, score_rect)
        
        restart_text = small_font.render("Press R to Restart or Close Window", True, (255, 255, 255))
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, 250))
        screen.blit(restart_text, restart_rect)

    pygame.display.update()
    clock.tick(10)

pygame.quit()
cap.release()