import pygame
import cv2
import json
import os
import numpy as np
import random
from datetime import datetime
from snake import SnakeGame, PowerUp, GameMode, Particle, WIDTH, HEIGHT, PLAY_AREA_TOP, BLOCK
from hand_tracking import get_direction, get_hand_position, hands

pygame.init()
SCREEN_WIDTH = WIDTH
SCREEN_HEIGHT = HEIGHT
screen_modes = ["WINDOWED", "FULLSCREEN"]
current_screen_mode_idx = 0
display_screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Snake Game - Hand Gesture Control")
clock = pygame.time.Clock()

THEMES = {
    "modern": {
        "label": "Modern",
        "font_name": "arial",
        "scanlines": False,
        "glow": True,
        "corner_radius": 8,
        "grid_style": "line",

        "app_bg":     (10, 10, 11),
        "panel_bg":   (20, 20, 22),
        "panel_edge": (34, 34, 37),
        "board_bg":   (16, 16, 18),
        "grid_line":  (26, 26, 29),
        "snake_body": (150, 150, 156),
        "snake_head": (255, 255, 255),
        "food":       (255, 255, 255),
        "text_main":  (240, 240, 242),
        "text_sub":   (118, 118, 124),
        "text_sub_sel": (168, 168, 174),
        "accent":     (255, 255, 255),

        "menu_row_bg":         (20, 20, 22),
        "menu_row_bg_sel":     (26, 26, 29),
        "menu_row_border":     (42, 42, 45),
        "menu_row_border_sel": (240, 240, 242),
    },
    "retro": {
        "label": "Retro",
        "font_name": "couriernew",
        "scanlines": True,
        "glow": False,
        "corner_radius": 0,
        "grid_style": "dots",

        "app_bg":     (2, 4, 2),
        "panel_bg":   (5, 10, 5),
        "panel_edge": (18, 40, 18),
        "board_bg":   (4, 9, 4),
        "grid_line":  (14, 32, 14),
        "snake_body": (40, 160, 60),
        "snake_head": (140, 255, 160),
        "food":       (140, 255, 160),
        "text_main":  (140, 255, 160),
        "text_sub":   (55, 130, 70),
        "text_sub_sel": (90, 190, 105),
        "accent":     (140, 255, 160),

        "menu_row_bg":         (6, 12, 6),
        "menu_row_bg_sel":     (10, 20, 10),
        "menu_row_border":     (20, 45, 20),
        "menu_row_border_sel": (140, 255, 160),
    },
}

THEME_ORDER = ["modern", "retro"]
current_theme_index = 0
current_theme = "modern"

def rounded_rect(surface, rect, color, radius=6):
    if radius <= 0:
        pygame.draw.rect(surface, color, rect)
    else:
        pygame.draw.rect(surface, color, rect, border_radius=radius)

def draw_glow(surface, center, radius, color, layers=5, max_alpha=70):
    cx, cy = center
    span = int(radius * 3)
    glow_surf = pygame.Surface((span * 2, span * 2), pygame.SRCALPHA)
    for i in range(layers, 0, -1):
        r = radius + (radius * 1.6) * (i / layers)
        alpha = int(max_alpha * (1 - i / layers) * 0.5) + 4
        pygame.draw.circle(glow_surf, (*color, alpha), (span, span), int(r))
    surface.blit(glow_surf, (cx - span, cy - span))

def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

title_font = None
font = None
small_font = None
tiny_font = None

def build_fonts():
    global title_font, font, small_font, tiny_font
    th = THEMES[current_theme]
    name = th["font_name"]
    title_font = pygame.font.SysFont(name, 60, bold=True)
    font = pygame.font.SysFont(name, 36, bold=True)
    small_font = pygame.font.SysFont(name, 24, bold=True)
    tiny_font = pygame.font.SysFont(name, 18, bold=True)

def cycle_theme():
    global current_theme_index, current_theme
    current_theme_index = (current_theme_index + 1) % len(THEME_ORDER)
    current_theme = THEME_ORDER[current_theme_index]
    build_fonts()

build_fonts()

# --- Audio Synthesis ---
mixer_initialized = False
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    mixer_initialized = True
except Exception as e:
    print(f"Warning: Could not initialize pygame.mixer: {e}")

sounds = {}

def generate_sound(freq_start, freq_end, duration, volume=0.1, wave_type='sine'):
    if not mixer_initialized:
        return None
    try:
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)
        
        frequencies = np.linspace(freq_start, freq_end, n_samples)
        phases = 2 * np.pi * frequencies * t
        
        if wave_type == 'sine':
            data = np.sin(phases)
        elif wave_type == 'square':
            data = np.sign(np.sin(phases))
        elif wave_type == 'noise':
            data = np.random.uniform(-1, 1, n_samples)
        else:
            data = np.sin(phases)
            
        envelope = np.exp(-4 * t / duration)
        data = data * envelope
        
        audio = (data * volume * 32767).astype(np.int16)
        stereo_audio = np.ascontiguousarray(np.vstack((audio, audio)).T)
        return pygame.sndarray.make_sound(stereo_audio)
    except Exception as e:
        print(f"Warning: Failed to generate sound: {e}")
        return None

def build_sounds():
    global sounds
    if not mixer_initialized:
        return
    sounds["eat"] = generate_sound(400, 800, 0.08, volume=0.1, wave_type='sine')
    sounds["powerup"] = generate_sound(600, 1200, 0.15, volume=0.08, wave_type='sine')
    sounds["shield_break"] = generate_sound(300, 100, 0.25, volume=0.15, wave_type='noise')
    sounds["gameover"] = generate_sound(500, 200, 0.4, volume=0.12, wave_type='square')

def play_sound(name):
    if mixer_initialized and name in sounds and sounds[name] is not None:
        sounds[name].play()

build_sounds()

# --- Background Music (BGM) Sequence ---
def generate_bgm():
    if not mixer_initialized:
        return None
    try:
        sample_rate = 22050
        duration = 8.0
        n_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)
        data = np.zeros(n_samples)
        
        notes = [
            130.81, 155.56, 196.00, 155.56, 130.81, 155.56, 196.00, 155.56,
            174.61, 207.65, 261.63, 207.65, 174.61, 207.65, 261.63, 207.65,
            116.54, 146.83, 174.61, 146.83, 116.54, 146.83, 174.61, 146.83,
            196.00, 246.94, 293.66, 246.94, 196.00, 246.94, 293.66, 246.94
        ]
        
        note_duration = duration / len(notes)
        samples_per_note = int(sample_rate * note_duration)
        
        for i, freq in enumerate(notes):
            start_idx = i * samples_per_note
            end_idx = min(start_idx + samples_per_note, n_samples)
            note_samples = end_idx - start_idx
            
            t_note = np.linspace(0, note_duration, note_samples, False)
            note_data = np.sign(np.sin(2 * np.pi * freq * t_note))
            envelope = np.exp(-6 * t_note / note_duration)
            data[start_idx:end_idx] = note_data * envelope * 0.04
            
        audio = (data * 32767).astype(np.int16)
        stereo_audio = np.ascontiguousarray(np.vstack((audio, audio)).T)
        return pygame.sndarray.make_sound(stereo_audio)
    except Exception as e:
        print(f"Warning: Failed to generate BGM: {e}")
        return None

bgm_sound = generate_bgm()
channel_bgm = pygame.mixer.Channel(0) if mixer_initialized else None
music_active = True

def update_music():
    if not mixer_initialized or channel_bgm is None or bgm_sound is None:
        return
    if music_active and not paused and not game_over and not show_mode_select:
        if not channel_bgm.get_busy():
            channel_bgm.play(bgm_sound, loops=-1)
    else:
        channel_bgm.stop()

# --- Screen Shake ---
shake_intensity = 0
shake_duration = 0.0

def trigger_shake(intensity, duration):
    global shake_intensity, shake_duration
    shake_intensity = intensity
    shake_duration = duration

HIGH_SCORE_FILE = "leaderboard.json"

leaderboard_view_mode = GameMode.CLASSIC

def load_leaderboard(mode=None):
    if mode is None:
        mode = leaderboard_view_mode
    try:
        if os.path.exists(HIGH_SCORE_FILE):
            with open(HIGH_SCORE_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data.get(mode, [])
                else:
                    return data if mode == GameMode.CLASSIC else []
    except:
        pass
    return []

def save_leaderboard(leaderboard_list, mode=None):
    if mode is None:
        mode = leaderboard_view_mode
    try:
        data = {}
        if os.path.exists(HIGH_SCORE_FILE):
            with open(HIGH_SCORE_FILE, 'r') as f:
                old_data = json.load(f)
                if isinstance(old_data, dict):
                    data = old_data
                else:
                    data = {GameMode.CLASSIC: old_data}
        data[mode] = leaderboard_list
        with open(HIGH_SCORE_FILE, 'w') as f:
            json.dump(data, f)
    except:
        pass

def add_to_leaderboard(score, name="Player", mode=None):
    if mode is None:
        mode = game_mode
    l_list = load_leaderboard(mode)
    entry = {
        'name': name,
        'score': score,
        'date': datetime.now().strftime("%m/%d/%Y")
    }
    l_list.append(entry)
    l_list.sort(key=lambda x: x['score'], reverse=True)
    l_list = l_list[:10]
    save_leaderboard(l_list, mode)
    return l_list

# Load initial high score for classic mode
initial_leaderboard = load_leaderboard(GameMode.CLASSIC)
high_score = initial_leaderboard[0]['score'] if initial_leaderboard else 0

game_mode = GameMode.CLASSIC
selected_mode_index = 0
game = SnakeGame(mode=game_mode)
cap = cv2.VideoCapture(0) if hands is not None else None
camera_available = cap is not None and cap.isOpened() and cap.get(cv2.CAP_PROP_FRAME_WIDTH) > 0

direction_queue = []
move_timer = 0.0

def queue_direction(new_dir):
    ref_dir = direction_queue[-1] if direction_queue else game.direction
    opposites = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}
    if new_dir != opposites.get(ref_dir) and new_dir != ref_dir:
        if len(direction_queue) < 2:
            direction_queue.append(new_dir)

# --- Fullscreen & Pause States ---
fullscreen = False
paused = False

desktop_w = SCREEN_WIDTH
desktop_h = SCREEN_HEIGHT

try:
    info = pygame.display.Info()
    if info.current_w > 0:
        desktop_w = info.current_w
        desktop_h = info.current_h
except:
    pass

def update_screen_mode():
    global display_screen, current_screen_mode_idx
    mode = screen_modes[current_screen_mode_idx]
    if mode == "WINDOWED":
        display_screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    elif mode == "FULLSCREEN":
        try:
            display_screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        except pygame.error:
            current_screen_mode_idx = 0
            display_screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

def toggle_fullscreen():
    global current_screen_mode_idx
    current_screen_mode_idx = (current_screen_mode_idx + 1) % len(screen_modes)
    try:
        success = pygame.display.toggle_fullscreen()
        if not success:
            update_screen_mode()
    except:
        update_screen_mode()

def render_to_display(dx=0, dy=0):
    w, h = display_screen.get_size()
    display_screen.fill((0, 0, 0))
    if (w, h) == (SCREEN_WIDTH, SCREEN_HEIGHT):
        display_screen.blit(screen, (dx, dy))
    else:
        scaled = pygame.transform.scale(screen, (w, h))
        sdx = int(dx * (w / SCREEN_WIDTH))
        sdy = int(dy * (h / SCREEN_HEIGHT))
        display_screen.blit(scaled, (sdx, sdy))
    pygame.display.update()

def cycle_speed(forward=True):
    global starting_speed, starting_speed_label
    speeds = [
        ("zen", 6.0),
        ("normal", 10.0),
        ("fast", 15.0),
        ("hyper", 20.0)
    ]
    curr_idx = 1
    for idx, (lbl, val) in enumerate(speeds):
        if lbl == starting_speed_label:
            curr_idx = idx
            break
    step = 1 if forward else -1
    next_idx = (curr_idx + step) % len(speeds)
    starting_speed_label, starting_speed = speeds[next_idx]

def cycle_skin(forward=True):
    global active_skin
    skins = ["NEON GLOW", "RAINBOW", "CHAMELEON"]
    curr_idx = skins.index(active_skin) if active_skin in skins else 0
    step = 1 if forward else -1
    active_skin = skins[(curr_idx + step) % len(skins)]

def toggle_music():
    global music_active
    music_active = not music_active
    update_music()

starting_speed = 10.0
starting_speed_label = "normal"
active_skin = "CHAMELEON"

running = True
speed = 6.0
display_speed = 1.0
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
    th = THEMES[current_theme]
    screen.fill(th["app_bg"])
    board_rect = pygame.Rect(0, PLAY_AREA_TOP, SCREEN_WIDTH, SCREEN_HEIGHT - PLAY_AREA_TOP)
    screen.fill(th["board_bg"], board_rect)

def draw_game_area():
    th = THEMES[current_theme]
    if th["grid_style"] == "line":
        for x in range(SCREEN_WIDTH // BLOCK + 1):
            xpos = x * BLOCK
            pygame.draw.line(screen, th["grid_line"], (xpos, PLAY_AREA_TOP), (xpos, SCREEN_HEIGHT), 1)
        for y in range((SCREEN_HEIGHT - PLAY_AREA_TOP) // BLOCK + 1):
            ypos = y * BLOCK + PLAY_AREA_TOP
            pygame.draw.line(screen, th["grid_line"], (0, ypos), (SCREEN_WIDTH, ypos), 1)
    elif th["grid_style"] == "dots":
        for x in range(SCREEN_WIDTH // BLOCK):
            for y in range((SCREEN_HEIGHT - PLAY_AREA_TOP) // BLOCK):
                cx = x * BLOCK + BLOCK // 2
                cy = y * BLOCK + PLAY_AREA_TOP + BLOCK // 2
                pygame.draw.circle(screen, th["grid_line"], (cx, cy), 1)

def draw_stats(current_score, current_speed=10.0):
    th = THEMES[current_theme]
    
    # Fill top panel background
    panel_rect = pygame.Rect(0, 0, SCREEN_WIDTH, PLAY_AREA_TOP)
    rounded_rect(screen, panel_rect, th["panel_bg"], radius=0)
    
    # Bottom border of top panel
    border_color = th["panel_edge"]
    pygame.draw.line(screen, border_color, (0, PLAY_AREA_TOP), (SCREEN_WIDTH, PLAY_AREA_TOP), 2)
    
    # Score Card
    score_txt = font.render(str(current_score), True, th["text_main"])
    screen.blit(score_txt, (30, 12))
    score_lbl = tiny_font.render("SCORE", True, th["text_sub"])
    screen.blit(score_lbl, (30, 48))
    
    if game.combo > 0:
        combo_txt = tiny_font.render(f"COMBO {game.combo}x", True, th["accent"])
        screen.blit(combo_txt, (30, 72))

    # High Score Card
    best_txt = font.render(str(high_score), True, th["text_main"])
    best_rect = best_txt.get_rect(topright=(SCREEN_WIDTH - 30, 12))
    screen.blit(best_txt, best_rect)
    best_lbl = tiny_font.render("BEST", True, th["text_sub"])
    best_lbl_rect = best_lbl.get_rect(topright=(SCREEN_WIDTH - 30, 48))
    screen.blit(best_lbl, best_lbl_rect)
    
    # Stats Pill
    stats_rect = pygame.Rect(SCREEN_WIDTH // 2 - 250, 56, 500, 32)
    pill_bg = th["board_bg"]
    rounded_rect(screen, stats_rect, pill_bg, radius=th["corner_radius"] * 2)
    
    labels = [
        ("SPEED", f"{current_speed:.1f}x"),
        ("LENGTH", str(len(game.snake))),
        ("MODE", game.mode.upper()),
        ("CAMERA", "ON" if camera_available else "OFF")
    ]
    seg_w = stats_rect.width / 4
    for i, (lbl, val) in enumerate(labels):
        cx = stats_rect.x + seg_w * i + seg_w / 2
        text_str = f"{lbl}: {val}"
        text_color = th["text_main"]
        if lbl == "CAMERA":
            text_color = (100, 255, 100) if camera_available else (255, 100, 100)
            
        v = tiny_font.render(text_str, True, text_color)
        screen.blit(v, v.get_rect(center=(cx, stats_rect.y + 16)))

def draw_leaderboard():
    th = THEMES[current_theme]
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(220)
    overlay.fill(th["app_bg"])
    screen.blit(overlay, (0, 0))
    
    # Load dynamic leaderboard for active view mode
    l_list = load_leaderboard(leaderboard_view_mode)
    
    title = title_font.render(f"LEADERBOARD - {leaderboard_view_mode.upper()}", True, th["accent"])
    title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 50))
    screen.blit(title, title_rect)
    
    start_y = 130
    left_x = SCREEN_WIDTH // 2 - 300
    name_x = SCREEN_WIDTH // 2 - 120
    right_x = SCREEN_WIDTH // 2 + 300

    # Draw headings
    rank_lbl = small_font.render("RANK", True, th["text_sub"])
    screen.blit(rank_lbl, (left_x, start_y))
    name_lbl = small_font.render("NAME", True, th["text_sub"])
    screen.blit(name_lbl, (name_x, start_y))
    score_lbl = small_font.render("SCORE", True, th["text_sub"])
    score_lbl_rect = score_lbl.get_rect(topright=(right_x, start_y))
    screen.blit(score_lbl, score_lbl_rect)
    
    start_y = 170
    for i, entry in enumerate(l_list[:10]):
        rank_color = (255, 215, 0) if i == 0 else th["text_main"]
        rank_text = font.render(f"#{i+1}", True, rank_color)
        screen.blit(rank_text, (left_x, start_y + i * 45))
        
        name_text = font.render(entry['name'][:15], True, th["text_main"])
        screen.blit(name_text, (name_x, start_y + i * 45))
        
        score_text = font.render(str(entry['score']), True, (100, 255, 100) if current_theme == "retro" else th["text_main"])
        score_rect = score_text.get_rect()
        score_rect.topright = (right_x, start_y + i * 45)
        screen.blit(score_text, score_rect)
    
    hint_text = small_font.render("Press LEFT / RIGHT to cycle game modes", True, th["accent"])
    hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
    screen.blit(hint_text, hint_rect)
    
    close_text = small_font.render("Press L to close", True, th["text_sub"])
    close_rect = close_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
    screen.blit(close_text, close_rect)

def draw_power_ups():
    th = THEMES[current_theme]
    for i, (power_type, frames_left) in enumerate(game.active_power_ups.items()):
        if power_type == PowerUp.TYPE_SPEED_BOOST:
            color = (255, 220, 100)
            label = "SPEED"
        elif power_type == PowerUp.TYPE_MULTIPLIER:
            color = (255, 150, 100)
            label = "2X SCORE"
        elif power_type == PowerUp.TYPE_SHIELD:
            color = (100, 200, 255)
            label = "SHIELD"
        elif power_type == PowerUp.TYPE_GHOST:
            color = (200, 100, 255)
            label = "GHOST"
        elif power_type == PowerUp.TYPE_FREEZE:
            color = (100, 255, 255)
            label = "FREEZE"
        else:
            continue
        
        # Position them at the center top
        x_pos = SCREEN_WIDTH // 2 - 160 + (i * 110)
        rect = pygame.Rect(x_pos, 12, 100, 32)
        rounded_rect(screen, rect, color, radius=th["corner_radius"])
        
        power_text = tiny_font.render(label, True, (0, 0, 0))
        screen.blit(power_text, power_text.get_rect(center=(rect.centerx, rect.centery - 6)))
        
        duration_ratio = frames_left / 150
        bar_width = int(80 * duration_ratio)
        pygame.draw.rect(screen, (0, 150, 0), (rect.x + 10, rect.y + 22, bar_width, 4))

def draw_portals():
    if game.mode == GameMode.ARCADE and game.portal_a and game.portal_b:
        radius_offset = int(random.uniform(-2, 2))
        
        # Portal A: Neon Blue
        pygame.draw.circle(screen, (50, 150, 255), (game.portal_a[0] + BLOCK // 2, game.portal_a[1] + BLOCK // 2), BLOCK // 2 + radius_offset, 2)
        pygame.draw.circle(screen, (200, 230, 255), (game.portal_a[0] + BLOCK // 2, game.portal_a[1] + BLOCK // 2), 4)
        
        # Portal B: Neon Orange
        pygame.draw.circle(screen, (255, 120, 50), (game.portal_b[0] + BLOCK // 2, game.portal_b[1] + BLOCK // 2), BLOCK // 2 + radius_offset, 2)
        pygame.draw.circle(screen, (255, 220, 200), (game.portal_b[0] + BLOCK // 2, game.portal_b[1] + BLOCK // 2), 4)

def draw_obstacles():
    th = THEMES[current_theme]
    obs_color = (130, 90, 80) if th["glow"] else (14, 32, 14)
    border_color = (180, 140, 130) if th["glow"] else th["accent"]
    for obs_x, obs_y in game.obstacles:
        rect = pygame.Rect(obs_x + 2, obs_y + 2, BLOCK - 4, BLOCK - 4)
        rounded_rect(screen, rect, obs_color, radius=th["corner_radius"])
        pygame.draw.rect(screen, border_color, (obs_x, obs_y, BLOCK, BLOCK), 1)

def draw_particles():
    for particle in game.particles:
        particle.draw(screen)

def draw_pills(labels, y):
    th = THEMES[current_theme]
    pad_x = 12
    gap = 10
    surfs = [tiny_font.render(l, True, th["text_sub"]) for l in labels]
    widths = [s.get_width() + pad_x * 2 for s in surfs]
    total_w = sum(widths) + gap * (len(widths) - 1)
    x = SCREEN_WIDTH // 2 - total_w // 2
    for s, w in zip(surfs, widths):
        pill_rect = pygame.Rect(x, y, w, 28)
        rounded_rect(screen, pill_rect, th["menu_row_bg"], radius=max(2, th["corner_radius"] - 2))
        screen.blit(s, s.get_rect(center=pill_rect.center))
        x += w + gap

def draw_mode_select():
    th = THEMES[current_theme]
    
    # Fill background with app bg
    screen.fill(th["app_bg"])
    
    # Card dimensions
    card_w = 700
    card_h = 580
    card_x = SCREEN_WIDTH // 2 - card_w // 2
    card_y = SCREEN_HEIGHT // 2 - card_h // 2
    card_rect = pygame.Rect(card_x, card_y, card_w, card_h)
    
    # Draw card background and border
    rounded_rect(screen, card_rect, th["panel_bg"], radius=th["corner_radius"] * 2)
    pygame.draw.rect(screen, th["panel_edge"], card_rect, 2, border_radius=th["corner_radius"] * 2)
    
    # Title & Subtitle centered inside card
    title_text = title_font.render("Select mode", True, th["text_main"])
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, card_y + 50))
    screen.blit(title_text, title_rect)
    
    sub_text = small_font.render("Choose how you want to play", True, th["text_sub"])
    sub_rect = sub_text.get_rect(center=(SCREEN_WIDTH // 2, card_y + 85))
    screen.blit(sub_text, sub_rect)
    
    # Game modes list options
    options = [
        {"name": "Classic", "desc": "Traditional snake gameplay", "icon": "●"},
        {"name": "Arcade", "desc": "Obstacles, portals, power-ups", "icon": "◆"},
        {"name": "Zen", "desc": "No death, infinite gameplay", "icon": "∞"}
    ]
    
    row_w = 600
    row_h = 75
    start_y = card_y + 130
    spacing = 90
    
    for i, opt in enumerate(options):
        is_selected = i == selected_mode_index
        y = start_y + (i * spacing)
        box_rect = pygame.Rect(SCREEN_WIDTH // 2 - row_w // 2, y, row_w, row_h)
        
        border_width = 4 if is_selected else 2
        bg = th["menu_row_bg_sel"] if is_selected else th["menu_row_bg"]
        border = th["menu_row_border_sel"] if is_selected else th["menu_row_border"]
        rounded_rect(screen, box_rect, bg, radius=th["corner_radius"] * 2)
        pygame.draw.rect(screen, border, box_rect, border_width, border_radius=th["corner_radius"] * 2)
        
        # Icon box on left
        icon_box = pygame.Rect(box_rect.x + 16, box_rect.y + 13, 48, 48)
        icon_bg = th["menu_row_bg"] if is_selected else th["menu_row_bg_sel"]
        rounded_rect(screen, icon_box, icon_bg, radius=th["corner_radius"])
        
        icon_color = th["text_main"] if is_selected else th["text_sub"]
        icon_txt = font.render(opt["icon"], True, icon_color)
        screen.blit(icon_txt, icon_txt.get_rect(center=icon_box.center))
        
        # Name and description
        name_text = font.render(opt["name"], True, th["text_main"])
        screen.blit(name_text, (box_rect.x + 80, box_rect.y + 12))
        
        desc_color = th["text_sub_sel"] if is_selected else th["text_sub"]
        desc_text = small_font.render(opt["desc"], True, desc_color)
        screen.blit(desc_text, (box_rect.x + 80, box_rect.y + 42))
        
        # Selected indicator chevron
        if is_selected:
            chevron = font.render("›", True, th["text_main"])
            screen.blit(chevron, chevron.get_rect(midright=(box_rect.right - 20, box_rect.centery)))

    # Separator line
    sep_y = card_y + 420
    pygame.draw.line(screen, th["panel_edge"], (card_x + 30, sep_y), (card_x + card_w - 30, sep_y), 1)
    
    # Action pills
    draw_pills(["↑↓ Navigate", "Enter Select"], card_y + 440)
    
    # Settings pills
    mode_str = screen_modes[current_screen_mode_idx]
    settings_labels = [
        f"[C] Theme: {th['label']}",
        f"[S] Skin: {active_skin}",
        f"[M] Music: {'ON' if music_active else 'OFF'}",
        f"[F] Screen: {mode_str}"
    ]
    draw_pills(settings_labels, card_y + 490)

while running:
    dt = clock.tick(60) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                toggle_fullscreen()
            elif event.key == pygame.K_c:
                cycle_theme()
            elif show_mode_select:
                if event.key == pygame.K_UP:
                    selected_mode_index = (selected_mode_index - 1) % 3
                elif event.key == pygame.K_DOWN:
                    selected_mode_index = (selected_mode_index + 1) % 3
                elif event.key == pygame.K_s:
                    cycle_skin(forward=True)
                elif event.key == pygame.K_m:
                    toggle_music()
                elif event.key == pygame.K_f:
                    toggle_fullscreen()
                elif event.key == pygame.K_RETURN:
                    modes_list = [GameMode.CLASSIC, GameMode.ARCADE, GameMode.ZEN]
                    game_mode = modes_list[selected_mode_index]
                    show_mode_select = False
                    game = SnakeGame(mode=game_mode)
                    direction_queue.clear()
                    move_timer = 0.0
                    game_over = False
                    paused = False
                    update_music()
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
                elif event.key == pygame.K_LEFT:
                    modes_list = [GameMode.CLASSIC, GameMode.ARCADE, GameMode.ZEN]
                    curr_idx = modes_list.index(leaderboard_view_mode)
                    leaderboard_view_mode = modes_list[(curr_idx - 1) % 3]
                elif event.key == pygame.K_RIGHT:
                    modes_list = [GameMode.CLASSIC, GameMode.ARCADE, GameMode.ZEN]
                    curr_idx = modes_list.index(leaderboard_view_mode)
                    leaderboard_view_mode = modes_list[(curr_idx + 1) % 3]
            elif paused:
                if event.key in (pygame.K_p, pygame.K_ESCAPE):
                    paused = False
                    update_music()
                elif event.key == pygame.K_m:
                    show_mode_select = True
                    selected_mode_index = 0
                    game_mode = GameMode.CLASSIC
                    paused = False
                    direction_queue.clear()
                    move_timer = 0.0
                    update_music()
            elif game_over:
                if event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_r:
                    show_mode_select = True
                    selected_mode_index = 0
                    game_mode = GameMode.CLASSIC
                    direction_queue.clear()
                    move_timer = 0.0
                    update_music()
                elif event.key == pygame.K_m:
                    show_mode_select = True
                    selected_mode_index = 0
                    game_mode = GameMode.CLASSIC
                    direction_queue.clear()
                    move_timer = 0.0
                    update_music()
            else:
                if event.key in (pygame.K_UP, pygame.K_w):
                    queue_direction("UP")
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    queue_direction("DOWN")
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    queue_direction("LEFT")
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    queue_direction("RIGHT")
                elif event.key in (pygame.K_p, pygame.K_ESCAPE):
                    paused = True
                    update_music()
                elif event.key == pygame.K_h:
                    show_gesture_help = not show_gesture_help
                elif event.key == pygame.K_l:
                    show_leaderboard = True

    if shake_duration > 0:
        shake_duration -= dt

    if not game_over and not show_mode_select and not paused:
        if camera_available:
            ret, frame = cap.read()
            if ret and frame is not None:
                direction, confidence = get_direction(frame)
                if direction:
                    if direction == "LEFT":
                        direction = "RIGHT"
                    elif direction == "RIGHT":
                        direction = "LEFT"
                    queue_direction(direction)
                
                hand_x, hand_y, gesture_type = get_hand_position(frame)
                if confidence:
                    hand_confidence = confidence

        move_timer += dt
        
        # Track active gameplay time on the game state
        if not hasattr(game, 'play_time'):
            game.play_time = 0.0
        game.play_time += dt
        
        # Base speed increases gradually in Classic/Arcade, stays relaxed in Zen
        if game.mode != GameMode.ZEN:
            starting_speed = 6.0
            base_speed = 6.0 + (game.play_time * 0.04)
            base_speed = min(base_speed, 18.0)
        else:
            starting_speed = 4.0
            base_speed = 4.0 + (game.play_time * 0.015)
            base_speed = min(base_speed, 12.0)
            
        speed = base_speed
        if PowerUp.TYPE_SPEED_BOOST in game.active_power_ups:
            speed = base_speed * 1.5
            
        if PowerUp.TYPE_FREEZE in game.active_power_ups:
            speed = speed * 0.5
            
        display_speed = speed / starting_speed

        step = 1.0 / speed
        if move_timer >= step:
            move_timer -= step
            if direction_queue:
                game.next_direction = direction_queue.pop(0)
                
            was_shield_active = game.shield_active
            active_powerups_before = list(game.active_power_ups.keys())
            
            game.move()

            # Play portal teleport sound/shake
            if getattr(game, 'teleported', False):
                play_sound("powerup")
                trigger_shake(8, 0.2)
                game.teleported = False

            if game.food_eaten:
                play_sound("eat")
                trigger_shake(5, 0.15)
                game.food_eaten = False
                
            new_powerups = [p for p in game.active_power_ups.keys() if p not in active_powerups_before]
            if new_powerups:
                play_sound("powerup")
                trigger_shake(8, 0.2)
                
            if was_shield_active and not game.shield_active and not game.is_game_over():
                play_sound("shield_break")
                trigger_shake(15, 0.3)

            if game.is_game_over():
                play_sound("gameover")
                trigger_shake(20, 0.5)
                update_music()
                if game.mode != GameMode.ZEN:
                    game_over = True
                    entering_name = True
                else:
                    game.game_over = False

    th = THEMES[current_theme]
    if show_mode_select:
        draw_mode_select()

        if th["scanlines"]:
            overlay_lines = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            for y in range(0, SCREEN_HEIGHT, 3):
                pygame.draw.line(overlay_lines, (0, 0, 0, 40), (0, y), (SCREEN_WIDTH, y))
            screen.blit(overlay_lines, (0, 0))

        # Camera Shake & Blit to physical display
        dx, dy = 0, 0
        if shake_duration > 0:
            dx = random.randint(-shake_intensity, shake_intensity)
            dy = random.randint(-shake_intensity, shake_intensity)
            
        render_to_display(dx, dy)
        continue

    draw_gradient_background()
    draw_game_area()
    draw_stats(game.score, display_speed)
    draw_power_ups()
    draw_portals()
    draw_obstacles()

    th = THEMES[current_theme]
    for i, segment in enumerate(game.snake):
        rect = pygame.Rect(segment[0] + 2, segment[1] + 2, BLOCK - 4, BLOCK - 4)
        
        # Skip rendering alternating body segments if Ghost mode is active
        if PowerUp.TYPE_GHOST in game.active_power_ups:
            if (pygame.time.get_ticks() // 80 + i) % 2 == 0:
                continue
                
        # Skin Color & Shape selection
        if active_skin == "CHAMELEON":
            if th["glow"]:
                if i == 0:
                    draw_glow(screen, rect.center, BLOCK * 0.5, th["snake_head"], layers=4, max_alpha=45)
                    rounded_rect(screen, rect, th["snake_head"], radius=th["corner_radius"])
                    dir_map = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}
                    dx, dy = dir_map.get(game.direction, (1, 0))
                    dot_pos = (rect.centerx + dx * 4, rect.centery + dy * 4)
                    pygame.draw.circle(screen, th["board_bg"], dot_pos, 2)
                else:
                    n = len(game.snake)
                    t_val = i / max(1, n - 1)
                    fade = tuple(int(th["snake_body"][k] * (1 - t_val * 0.55)) for k in range(3))
                    rounded_rect(screen, rect, fade, radius=th["corner_radius"])
            else:
                color = th["accent"] if i == 0 else th["snake_body"]
                rounded_rect(screen, rect, color, radius=th["corner_radius"])
                if i == 0:
                    dir_map = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}
                    dx, dy = dir_map.get(game.direction, (1, 0))
                    dot_pos = (rect.centerx + dx * 4, rect.centery + dy * 4)
                    pygame.draw.circle(screen, th["board_bg"], dot_pos, 2)
        elif active_skin == "RAINBOW":
            hue = (i * 15 + pygame.time.get_ticks() // 10) % 360
            color = pygame.Color(0)
            color.hsva = (hue, 100, 100, 100)
            rounded_rect(screen, rect, color, radius=th["corner_radius"])
            if i == 0:
                dir_map = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}
                dx, dy = dir_map.get(game.direction, (1, 0))
                dot_pos = (rect.centerx + dx * 4, rect.centery + dy * 4)
                pygame.draw.circle(screen, th["board_bg"], dot_pos, 2)
        else: # NEON GLOW
            color = (50, 255, 50) if i == 0 else (0, 200, 0)
            rounded_rect(screen, rect, color, radius=th["corner_radius"])
            if i > 0:
                core_color = (180, 255, 180)
                pygame.draw.rect(screen, core_color, (rect.x + 6, rect.y + 6, rect.width - 12, rect.height - 12), border_radius=th["corner_radius"])
            if i == 0:
                dir_map = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}
                dx, dy = dir_map.get(game.direction, (1, 0))
                dot_pos = (rect.centerx + dx * 4, rect.centery + dy * 4)
                pygame.draw.circle(screen, th["board_bg"], dot_pos, 2)

    food_x, food_y = game.food
    if th["glow"]:
        import math
        cx = food_x + BLOCK // 2
        cy = food_y + BLOCK // 2
        pulse = (math.sin(pygame.time.get_ticks() / 150.0) + 1.0) / 2.0
        radius = BLOCK / 2 - 6 + pulse * 2
        draw_glow(screen, (cx, cy), radius, th["food"], layers=5, max_alpha=55)
        pygame.draw.circle(screen, th["food"], (cx, cy), int(radius))
    else:
        rect_food = pygame.Rect(food_x + 4, food_y + 4, BLOCK - 8, BLOCK - 8)
        rounded_rect(screen, rect_food, th["food"], radius=th["corner_radius"])

    for power_up in game.power_ups:
        # Blink warning if lifetime is low (< 50)
        if getattr(power_up, 'lifetime', 200) < 50:
            if (pygame.time.get_ticks() // 150) % 2 == 0:
                continue

        if power_up.type == PowerUp.TYPE_SPEED_BOOST:
            color = (255, 220, 100)
        elif power_up.type == PowerUp.TYPE_MULTIPLIER:
            color = (255, 150, 100)
        elif power_up.type == PowerUp.TYPE_SHIELD:
            color = (100, 200, 255)
        elif power_up.type == PowerUp.TYPE_GHOST:
            color = (200, 100, 255)
        elif power_up.type == PowerUp.TYPE_FREEZE:
            color = (100, 255, 255)
        else:
            color = (255, 255, 255)
            
        rect_pu = pygame.Rect(power_up.x + 2, power_up.y + 2, BLOCK - 4, BLOCK - 4)
        rounded_rect(screen, rect_pu, color, radius=th["corner_radius"])
        pygame.draw.rect(screen, th["text_main"], (power_up.x, power_up.y, BLOCK, BLOCK), 1)

    draw_particles()

    if camera_available and camera_available:
        if hand_x is not None and hand_y is not None:
            hand_pixel_x = int(hand_x * SCREEN_WIDTH)
            hand_pixel_y = int(hand_y * SCREEN_HEIGHT)
            
            if PLAY_AREA_TOP <= hand_pixel_y < SCREEN_HEIGHT:
                gesture_color = (0, 255, 100) if gesture_type == "POINTING" else (100, 200, 255) if gesture_type == "OPEN" else (200, 100, 200)
                pygame.draw.circle(screen, gesture_color, (hand_pixel_x, hand_pixel_y), 15, 3)
                pygame.draw.circle(screen, gesture_color, (hand_pixel_x, hand_pixel_y), 10, 1)

    if entering_name:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(220)
        overlay.fill(th["app_bg"])
        screen.blit(overlay, (0, 0))
        
        title_text = title_font.render("ENTER YOUR NAME", True, th["accent"])
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        screen.blit(title_text, title_rect)
        
        score_text = font.render(f"Score: {game.score}", True, th["text_main"])
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        screen.blit(score_text, score_rect)
        
        input_box = pygame.Rect(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 30, 300, 50)
        rounded_rect(screen, input_box, th["panel_bg"], radius=th["corner_radius"])
        pygame.draw.rect(screen, th["accent"], input_box, 2, border_radius=th["corner_radius"])
        name_display = font.render(player_name + "|", True, th["text_main"])
        screen.blit(name_display, (input_box.x + 10, input_box.y + 10))
        
        hint_text = small_font.render("Press ENTER to submit", True, th["text_sub"])
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120))
        screen.blit(hint_text, hint_rect)
    elif game_over:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(th["app_bg"])
        screen.blit(overlay, (0, 0))
        
        game_over_text = title_font.render("GAME OVER!", True, th["accent"])
        text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 180))
        screen.blit(game_over_text, text_rect)
        
        final_score = font.render(f"Final Score: {game.score}", True, th["text_main"])
        score_rect = final_score.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 90))
        screen.blit(final_score, score_rect)
        
        if game.score >= high_score:
            new_high = small_font.render("*** NEW HIGH SCORE! ***", True, th["accent"])
            new_high_rect = new_high.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
            screen.blit(new_high, new_high_rect)
            
        # Draw top 3 high scores for the current game mode
        modes_leaderboard = load_leaderboard(game.mode)
        if modes_leaderboard:
            scores_title = small_font.render("TOP SCORES FOR THIS MODE:", True, th["accent"])
            screen.blit(scores_title, scores_title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10)))
            for idx, entry in enumerate(modes_leaderboard[:3]):
                score_str = f"#{idx+1}  {entry['name'][:10]}  -  {entry['score']}"
                score_line = small_font.render(score_str, True, th["text_main"])
                screen.blit(score_line, score_line.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40 + idx * 25)))
        
        menu_text = small_font.render("M: Main Menu  |  R: Restart  |  Q: Quit", True, th["text_sub"])
        menu_rect = menu_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150))
        screen.blit(menu_text, menu_rect)
 
    if show_leaderboard:
        draw_leaderboard()
    elif paused:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(th["app_bg"])
        screen.blit(overlay, (0, 0))
        
        pause_title = title_font.render("GAME PAUSED", True, th["accent"])
        pause_title_rect = pause_title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        screen.blit(pause_title, pause_title_rect)
        
        pause_desc1 = font.render("P / ESC to Resume", True, th["text_main"])
        screen.blit(pause_desc1, pause_desc1.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20)))
        
        pause_desc2 = small_font.render("M to return to Main Menu", True, th["text_sub"])
        screen.blit(pause_desc2, pause_desc2.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80)))
    elif show_gesture_help and not game_over:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(th["app_bg"])
        screen.blit(overlay, (0, 0))
        
        help_title = title_font.render("CONTROLS", True, th["accent"])
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
            help_text = small_font.render(line, True, th["text_main"] if line else th["text_sub"])
            screen.blit(help_text, (SCREEN_WIDTH // 2 - 250, 220 + i * 40))

    # Theme Hint at bottom left
    theme_hint = tiny_font.render(f"[C] Theme: {th['label']}", True, th["text_sub"])
    screen.blit(theme_hint, (20, SCREEN_HEIGHT - 30))

    if th["scanlines"]:
        overlay_lines = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for y in range(0, SCREEN_HEIGHT, 3):
            pygame.draw.line(overlay_lines, (0, 0, 0, 40), (0, y), (SCREEN_WIDTH, y))
        screen.blit(overlay_lines, (0, 0))

    # Camera Shake & Blit to physical display
    dx, dy = 0, 0
    if shake_duration > 0:
        dx = random.randint(-shake_intensity, shake_intensity)
        dy = random.randint(-shake_intensity, shake_intensity)
        
    render_to_display(dx, dy)

pygame.quit()
if cap is not None:
    cap.release()