import pygame
import cv2
import numpy as np
import json
import os
from datetime import datetime
from snake import SnakeGame, PowerUp, GameMode, Particle, WIDTH, HEIGHT, PLAY_AREA_TOP, BLOCK
from hand_tracking import get_direction, get_hand_position

pygame.init()
SCREEN_WIDTH = WIDTH
SCREEN_HEIGHT = HEIGHT
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Snake Game - Hand Gesture Control")
clock = pygame.time.Clock()

title_font = pygame.font.Font(None, 64)
font = pygame.font.Font(None, 48)
small_font = pygame.font.Font(None, 32)
tiny_font = pygame.font.Font(None, 24)

HIGH_SCORE_FILE = "/tmp/snake_leaderboard.json"

def load_leaderboard():
    """Load leaderboard from file."""
    try:
        if os.path.exists(HIGH_SCORE_FILE):
            with open(HIGH_SCORE_FILE, 'r') as f:
                data = json.load(f)
                return data.get('leaderboard', [])
    except:
        pass
    return []

def save_leaderboard(leaderboard):
    """Save leaderboard to file."""
    try:
        with open(HIGH_SCORE_FILE, 'w') as f:
            json.dump({'leaderboard': leaderboard}, f)
    except:
        pass

def add_to_leaderboard(score, name="Player"):
    """Add a score to the leaderboard if it qualifies."""
    leaderboard = load_leaderboard()
    entry = {
        'name': name,
        'score': score,
        'date': datetime.now().strftime("%m/%d/%Y")
    }
    
    leaderboard.append(entry)
    leaderboard.sort(key=lambda x: x['score'], reverse=True)
    leaderboard = leaderboard[:10]
    
    save_leaderboard(leaderboard)
    return leaderboard

leaderboard = load_leaderboard()
high_score = leaderboard[0]['score'] if leaderboard else 0

game_mode = GameMode.CLASSIC
selected_mode_index = 0
game = SnakeGame(mode=game_mode)
cap = cv2.VideoCapture(0)
camera_available = cap.isOpened() and cap.get(cv2.CAP_PROP_FRAME_WIDTH) > 0

running = True
game_over = False
show_gesture_help = False
show_leaderboard = False
show_mode_select = True
player_name = ""
entering_name = False
gesture_type = None
hand_x, hand_y = None, None
hand_confidence = 0

def draw_gradient_background():
    for y in range(SCREEN_HEIGHT):
        color = (10 + int(20 * (y / SCREEN_HEIGHT)), 15 + int(40 * (y / SCREEN_HEIGHT)), 40)
        pygame.draw.line(screen, color, (0, y), (SCREEN_WIDTH, y))

def draw_game_area():
    border_color = (100, 200, 100)
    pygame.draw.rect(screen, border_color, (0, PLAY_AREA_TOP, SCREEN_WIDTH, HEIGHT - PLAY_AREA_TOP), 3)
    
    grid_color = (30, 50, 30)
    for x in range(0, SCREEN_WIDTH, BLOCK * 5):
        pygame.draw.line(screen, grid_color, (x, PLAY_AREA_TOP), (x, SCREEN_HEIGHT), 1)
    for y in range(PLAY_AREA_TOP, SCREEN_HEIGHT, BLOCK * 5):
        pygame.draw.line(screen, grid_color, (0, y), (SCREEN_WIDTH, y), 1)

def draw_stats(current_score):
    pygame.draw.rect(screen, (20, 30, 50), (0, 0, SCREEN_WIDTH, PLAY_AREA_TOP))
    pygame.draw.line(screen, (100, 200, 100), (0, PLAY_AREA_TOP), (SCREEN_WIDTH, PLAY_AREA_TOP), 2)
    
    score_text = font.render(f"Score: {current_score}", True, (100, 255, 100))
    screen.blit(score_text, (30, 20))
    
    difficulty_text = small_font.render(f"Lvl {game.difficulty}", True, (255, 180, 100))
    screen.blit(difficulty_text, (30, 50))
    
    high_score_text = font.render(f"High Score: {high_score}", True, (255, 200, 100))
    high_score_rect = high_score_text.get_rect()
    high_score_rect.topright = (SCREEN_WIDTH - 30, 20)
    screen.blit(high_score_text, high_score_rect)
    
    combo_text = small_font.render(f"Combo: {game.combo}x", True, (255, 100, 200))
    combo_rect = combo_text.get_rect()
    combo_rect.topright = (SCREEN_WIDTH - 30, 50)
    screen.blit(combo_text, combo_rect)
    
    if camera_available:
        status_text = tiny_font.render("Camera: ON", True, (100, 255, 100))
    else:
        status_text = tiny_font.render("Keyboard Mode", True, (255, 100, 100))
    screen.blit(status_text, (SCREEN_WIDTH // 2 - 60, 50))

def draw_leaderboard():
    """Draw the leaderboard overlay."""
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(200)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))
    
    title = title_font.render("LEADERBOARD", True, (100, 255, 200))
    title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 50))
    screen.blit(title, title_rect)
    
    start_y = 150
    for i, entry in enumerate(leaderboard[:10]):
        rank_color = (255, 215, 0) if i == 0 else (200, 200, 200)
        rank_text = font.render(f"#{i+1}", True, rank_color)
        screen.blit(rank_text, (50, start_y + i * 50))
        
        name_text = font.render(entry['name'][:15], True, rank_color)
        screen.blit(name_text, (150, start_y + i * 50))
        
        score_text = font.render(str(entry['score']), True, (100, 255, 100))
        score_rect = score_text.get_rect()
        score_rect.topright = (SCREEN_WIDTH - 50, start_y + i * 50)
        screen.blit(score_text, score_rect)
    
    close_text = small_font.render("Press L to close", True, (150, 150, 150))
    close_rect = close_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
    screen.blit(close_text, close_rect)

def draw_power_ups():
    """Draw active power-ups on screen."""
    for i, (power_type, frames_left) in enumerate(game.active_power_ups.items()):
        if power_type == PowerUp.TYPE_SPEED_BOOST:
            color = (255, 255, 100)
            label = "SPEED"
        elif power_type == PowerUp.TYPE_MULTIPLIER:
            color = (255, 150, 100)
            label = "2X SCORE"
        elif power_type == PowerUp.TYPE_SHIELD:
            color = (100, 200, 255)
            label = "SHIELD"
        else:
            continue
        
        x_pos = SCREEN_WIDTH - 200 - (i * 150)
        pygame.draw.rect(screen, color, (x_pos, 10, 130, 30))
        pygame.draw.rect(screen, (255, 255, 255), (x_pos, 10, 130, 30), 2)
        
        power_text = tiny_font.render(label, True, (0, 0, 0))
        screen.blit(power_text, (x_pos + 10, 12))
        
        duration_ratio = frames_left / 300
        bar_width = int(110 * duration_ratio)
        pygame.draw.rect(screen, (0, 200, 0), (x_pos + 10, 27, bar_width, 8))

def draw_obstacles():
    """Draw obstacles on the map."""
    for obs_x, obs_y in game.obstacles:
        pygame.draw.rect(screen, (150, 100, 100), (obs_x, obs_y, BLOCK, BLOCK))
        pygame.draw.rect(screen, (200, 150, 150), (obs_x, obs_y, BLOCK, BLOCK), 2)

def draw_particles():
    """Draw particle effects."""
    for particle in game.particles:
        particle.draw(screen)

def draw_mode_select():
    """Draw game mode selection screen with arrow key navigation."""
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(220)
    overlay.fill((10, 15, 40))
    screen.blit(overlay, (0, 0))
    
    title_text = title_font.render("SELECT GAME MODE", True, (100, 200, 255))
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 80))
    screen.blit(title_text, title_rect)
    
    modes = [
        {"name": "CLASSIC", "desc": "Traditional snake gameplay", "mode": GameMode.CLASSIC},
        {"name": "ARCADE", "desc": "Obstacles + Challenges", "mode": GameMode.ARCADE},
        {"name": "ZEN", "desc": "No death, infinite gameplay", "mode": GameMode.ZEN},
    ]
    
    box_width = 500
    box_height = 120
    start_y = 200
    spacing = 180
    
    for i, mode_opt in enumerate(modes):
        is_selected = i == selected_mode_index
        color = (100, 255, 100) if is_selected else (100, 200, 255)
        
        y = start_y + (i * spacing)
        box_rect = pygame.Rect(SCREEN_WIDTH // 2 - box_width // 2, y, box_width, box_height)
        
        border_width = 4 if is_selected else 2
        pygame.draw.rect(screen, color, box_rect, border_width)
        
        if is_selected:
            pygame.draw.rect(screen, color, (box_rect.x - 10, box_rect.y - 10, box_width + 20, box_height + 20), 1)
        
        name_text = font.render(mode_opt["name"], True, color)
        screen.blit(name_text, (box_rect.x + 20, box_rect.y + 10))
        
        desc_text = small_font.render(mode_opt["desc"], True, (200, 200, 200))
        screen.blit(desc_text, (box_rect.x + 20, box_rect.y + 60))
    
    hint_text = small_font.render("UP/DOWN to Navigate  |  ENTER to Start", True, (200, 255, 200))
    hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
    screen.blit(hint_text, hint_rect)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if show_mode_select:
                if event.key == pygame.K_UP:
                    selected_mode_index = (selected_mode_index - 1) % 3
                elif event.key == pygame.K_DOWN:
                    selected_mode_index = (selected_mode_index + 1) % 3
                elif event.key == pygame.K_RETURN:
                    modes_list = [GameMode.CLASSIC, GameMode.ARCADE, GameMode.ZEN]
                    game_mode = modes_list[selected_mode_index]
                    show_mode_select = False
                    game = SnakeGame(mode=game_mode)
                    game_over = False
            elif entering_name:
                if event.key == pygame.K_RETURN:
                    leaderboard = add_to_leaderboard(game.score, player_name or "Player")
                    high_score = leaderboard[0]['score'] if leaderboard else 0
                    entering_name = False
                    player_name = ""
                elif event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                elif event.unicode.isalnum() or event.unicode == " ":
                    if len(player_name) < 15:
                        player_name += event.unicode
            elif show_leaderboard:
                if event.key == pygame.K_l:
                    show_leaderboard = False
            elif game_over:
                if event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_r:
                    show_mode_select = True
                    selected_mode_index = 0
                    game_mode = GameMode.CLASSIC
                elif event.key == pygame.K_m:
                    show_mode_select = True
                    selected_mode_index = 0
                    game_mode = GameMode.CLASSIC
            else:
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    if game.direction != "DOWN":
                        game.next_direction = "UP"
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    if game.direction != "UP":
                        game.next_direction = "DOWN"
                elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    if game.direction != "RIGHT":
                        game.next_direction = "LEFT"
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    if game.direction != "LEFT":
                        game.next_direction = "RIGHT"
                elif event.key == pygame.K_h:
                    show_gesture_help = not show_gesture_help
                elif event.key == pygame.K_l:
                    show_leaderboard = True

    if not game_over and not show_mode_select:
        if camera_available:
            ret, frame = cap.read()
            if ret and frame is not None:
                direction, confidence = get_direction(frame)
                if direction and game.direction != direction:
                    if direction == "LEFT":
                        direction = "RIGHT"
                    elif direction == "RIGHT":
                        direction = "LEFT"
                    
                    opposite = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}
                    if direction != opposite.get(game.direction):
                        game.next_direction = direction
                
                hand_x, hand_y, gesture_type = get_hand_position(frame)
                if confidence:
                    hand_confidence = confidence

        game.move()

        if game.is_game_over():
            if game.mode != GameMode.ZEN:
                game_over = True
                entering_name = True
            else:
                game.game_over = False

    draw_gradient_background()
    draw_game_area()
    draw_stats(game.score)
    draw_power_ups()
    draw_obstacles()

    for i, segment in enumerate(game.snake):
        intensity = int(255 * (1 - (i / len(game.snake)) * 0.5))
        color = (50 + intensity // 3, intensity, 50 + intensity // 3)
        pygame.draw.rect(screen, color, (*segment, BLOCK, BLOCK))
        
        border_color = (150, 255, 150) if i == 0 else (100, 200, 100)
        pygame.draw.rect(screen, border_color, (*segment, BLOCK, BLOCK), 2)
        
        if i == 0:
            pygame.draw.circle(screen, (255, 255, 100), (segment[0] + BLOCK // 2, segment[1] + BLOCK // 2 - 3), 3)

    food_x, food_y = game.food
    pygame.draw.circle(screen, (255, 100, 100), (food_x + BLOCK // 2, food_y + BLOCK // 2), BLOCK // 2 + 3)
    pygame.draw.circle(screen, (255, 50, 50), (food_x + BLOCK // 2, food_y + BLOCK // 2), BLOCK // 2)
    pygame.draw.circle(screen, (255, 150, 150), (food_x + BLOCK // 2, food_y + BLOCK // 2), 3)

    for power_up in game.power_ups:
        if power_up.type == PowerUp.TYPE_SPEED_BOOST:
            color = (255, 255, 0)
        elif power_up.type == PowerUp.TYPE_MULTIPLIER:
            color = (255, 150, 0)
        else:
            color = (100, 255, 100)
        pygame.draw.rect(screen, color, (power_up.x - 5, power_up.y - 5, BLOCK + 10, BLOCK + 10), 2)
        pygame.draw.polygon(screen, color, [(power_up.x + BLOCK//2, power_up.y - 8), (power_up.x + BLOCK + 8, power_up.y + BLOCK//2), (power_up.x + BLOCK//2, power_up.y + BLOCK + 8), (power_up.x - 8, power_up.y + BLOCK//2)])

    draw_particles()

    if camera_available and camera_available:
        if hand_x is not None and hand_y is not None:
            hand_pixel_x = int(hand_x * SCREEN_WIDTH)
            hand_pixel_y = int(hand_y * SCREEN_HEIGHT)
            
            if PLAY_AREA_TOP <= hand_pixel_y < SCREEN_HEIGHT:
                gesture_color = (0, 255, 100) if gesture_type == "POINTING" else (100, 200, 255) if gesture_type == "OPEN" else (200, 100, 200)
                pygame.draw.circle(screen, gesture_color, (hand_pixel_x, hand_pixel_y), 15, 3)
                pygame.draw.circle(screen, gesture_color, (hand_pixel_x, hand_pixel_y), 10, 1)

    if show_mode_select:
        draw_mode_select()
    elif entering_name:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(220)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        title_text = title_font.render("ENTER YOUR NAME", True, (100, 200, 255))
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        screen.blit(title_text, title_rect)
        
        score_text = font.render(f"Score: {game.score}", True, (100, 255, 100))
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        screen.blit(score_text, score_rect)
        
        input_box = pygame.Rect(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 30, 300, 50)
        pygame.draw.rect(screen, (255, 255, 255), input_box, 2)
        name_display = font.render(player_name + "|", True, (255, 255, 255))
        screen.blit(name_display, (input_box.x + 10, input_box.y + 5))
        
        hint_text = small_font.render("Press ENTER to submit", True, (200, 200, 200))
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120))
        screen.blit(hint_text, hint_rect)
    elif game_over:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        game_over_text = title_font.render("GAME OVER!", True, (255, 100, 100))
        text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 150))
        screen.blit(game_over_text, text_rect)
        
        final_score = font.render(f"Final Score: {game.score}", True, (100, 255, 100))
        score_rect = final_score.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        screen.blit(final_score, score_rect)
        
        if game.score >= high_score:
            new_high = small_font.render("*** NEW HIGH SCORE! ***", True, (255, 200, 100))
            new_high_rect = new_high.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
            screen.blit(new_high, new_high_rect)
        
        menu_text = small_font.render("M: Main Menu  |  R: Restart  |  Q: Quit", True, (200, 200, 200))
        menu_rect = menu_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
        screen.blit(menu_text, menu_rect)

    if show_leaderboard:
        draw_leaderboard()
    elif show_gesture_help and not game_over:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        help_title = title_font.render("CONTROLS", True, (100, 200, 255))
        help_title_rect = help_title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        screen.blit(help_title, help_title_rect)
        
        help_lines = [
            "Hand Gesture: Move your hand to control the snake",
            "Keyboard: Arrow Keys or WASD",
            "Touch Input: Swipe to change direction",
            "",
            "R: Restart Game",
            "H: Toggle Help",
            "L: Leaderboard",
            "Q: Quit Game"
        ]
        for i, line in enumerate(help_lines):
            help_text = small_font.render(line, True, (200, 200, 200))
            screen.blit(help_text, (SCREEN_WIDTH // 2 - 250, 250 + i * 50))

    pygame.display.update()
    clock.tick(10)

pygame.quit()
cap.release()