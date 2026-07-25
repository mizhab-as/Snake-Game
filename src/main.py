import pygame
import cv2
import json
import os
import numpy as np
import random
import math
from datetime import datetime
from snake import SnakeGame, PowerUp, GameMode, Particle, WIDTH, HEIGHT, PLAY_AREA_TOP, BLOCK
from hand_tracking import get_direction, get_hand_position, hands

os.environ['SDL_VIDEO_CENTERED'] = '1'
pygame.init()
SCREEN_WIDTH = WIDTH
SCREEN_HEIGHT = HEIGHT
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
RESOLUTIONS = [
    (1280, 720),
    (1366, 768),
    (1440, 900),
    (1600, 900),
    (1920, 1080),
    (2560, 1440)
]
current_res_idx = 0
screen_modes = ["WINDOWED", "FULLSCREEN"]
current_screen_mode_idx = 0
display_screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
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
        "head_shape": "square",

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
        "menu_icon_bg":        (30, 30, 33),
        "menu_icon_bg_sel":    (35, 35, 39),

        "card_bg":     (18, 18, 20),
        "card_border": (44, 44, 48),
        "input_bg":    (14, 14, 16),
        "rank_bg":     (26, 26, 29),
    },
    "retro": {
        "label": "Retro",
        "font_name": "arial",
        "scanlines": False,
        "glow": False,
        "corner_radius": 4,
        "grid_style": "line",
        "head_shape": "circle",

        "app_bg":     (13, 20, 17),
        "panel_bg":   (19, 29, 24),
        "panel_edge": (32, 46, 38),
        "board_bg":   (199, 211, 185),
        "grid_line":  (179, 193, 162),
        "snake_body": (28, 38, 32),
        "snake_head": (20, 28, 24),
        "food":       (194, 59, 50),
        "text_main":  (240, 244, 236),
        "text_sub":   (140, 163, 148),
        "text_sub_sel": (183, 199, 172),
        "accent":     (194, 59, 50),

        "menu_row_bg":         (19, 29, 24),
        "menu_row_bg_sel":     (25, 38, 31),
        "menu_row_border":     (38, 54, 45),
        "menu_row_border_sel": (240, 244, 236),
        "menu_icon_bg":        (28, 42, 35),
        "menu_icon_bg_sel":    (33, 48, 40),

        "card_bg":     (17, 26, 21),
        "card_border": (36, 51, 42),
        "input_bg":    (13, 20, 17),
        "rank_bg":     (24, 36, 29),
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
label_font = None
stats_val_font = None
menu_name_font = None
menu_desc_font = None

def build_fonts():
    global title_font, font, small_font, tiny_font, label_font, stats_val_font, menu_name_font, menu_desc_font
    th = THEMES[current_theme]
    name = th["font_name"]
    title_font = pygame.font.SysFont(name, 60, bold=True)
    font = pygame.font.SysFont(name, 36, bold=True)
    small_font = pygame.font.SysFont(name, 24, bold=True)
    tiny_font = pygame.font.SysFont(name, 18, bold=True)
    label_font = pygame.font.SysFont(name, 16, bold=True)
    stats_val_font = pygame.font.SysFont(name, 22, bold=True)
    menu_name_font = pygame.font.SysFont(name, 32, bold=True)
    menu_desc_font = pygame.font.SysFont(name, 20, bold=False)

def cycle_theme():
    global current_theme_index, current_theme
    current_theme_index = (current_theme_index + 1) % len(THEME_ORDER)
    current_theme = THEME_ORDER[current_theme_index]
    build_fonts()

build_fonts()

def draw_dim_overlay(alpha=150):
    th = THEMES[current_theme]
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(alpha)
    overlay.fill(th["app_bg"])
    screen.blit(overlay, (0, 0))

def draw_card_frame(card_rect):
    th = THEMES[current_theme]
    radius = th["corner_radius"]
    rounded_rect(screen, card_rect, th.get("card_bg", th["panel_bg"]), radius=radius)
    if radius == 0:
        pygame.draw.rect(screen, th.get("card_border", th["panel_edge"]), card_rect, width=1)
    else:
        pygame.draw.rect(screen, th.get("card_border", th["panel_edge"]), card_rect, width=1, border_radius=radius)
    accent_rect = pygame.Rect(card_rect.x, card_rect.y, card_rect.width, 4)
    rounded_rect(screen, accent_rect, th["accent"], radius=radius)

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
cap = None
camera_available = False
camera_index = 0
latest_frame = None
show_camera_preview = False
show_camera_error = False
camera_error_timer = 0.0

def initialize_camera(index=None):
    global cap, camera_available, camera_index
    if hands is None:
        camera_available = False
        return False
    
    indices_to_try = []
    if index is not None:
        indices_to_try.append(index)
    else:
        indices_to_try.append(camera_index)
        for i in range(5):
            if i != camera_index:
                indices_to_try.append(i)
                
    for idx in indices_to_try:
        try:
            if cap is not None:
                cap.release()
            import sys
            if sys.platform == "darwin":
                cap = cv2.VideoCapture(idx, cv2.CAP_AVFOUNDATION)
            else:
                cap = cv2.VideoCapture(idx)
            if cap is not None and cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    camera_index = idx  # Keep track of the working index
                    camera_available = True
                    return True
                cap.release()
        except:
            pass
            
    camera_available = False
    cap = None
    return False

def close_camera():
    global cap, camera_available
    if cap is not None:
        cap.release()
        cap = None
    camera_available = False

initialize_camera()

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

def toggle_fullscreen():
    global display_screen, current_screen_mode_idx
    current_screen_mode_idx = (current_screen_mode_idx + 1) % len(screen_modes)
    mode = screen_modes[current_screen_mode_idx]
    try:
        if mode == "WINDOWED":
            display_screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        else:
            display_screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    except Exception as e:
        print(f"Fullscreen toggle failed: {e}")

def cycle_resolution():
    global current_res_idx, WINDOW_WIDTH, WINDOW_HEIGHT, display_screen
    current_res_idx = (current_res_idx + 1) % len(RESOLUTIONS)
    WINDOW_WIDTH, WINDOW_HEIGHT = RESOLUTIONS[current_res_idx]
    if screen_modes[current_screen_mode_idx] == "WINDOWED":
        try:
            display_screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        except Exception as e:
            print(f"Failed to change resolution: {e}")

def render_to_display(dx=0, dy=0):
    w, h = display_screen.get_size()
    display_screen.fill((0, 0, 0))
    if (w, h) == (SCREEN_WIDTH, SCREEN_HEIGHT):
        display_screen.blit(screen, (dx, dy))
    else:
        scaled = pygame.transform.smoothscale(screen, (w, h))
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
show_settings = False
show_motion_tracker = True
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
    
    # Stats Pill - Nokia style stretched bar with vertical dividers (taller for readability)
    stats_rect = pygame.Rect(18, 64, SCREEN_WIDTH - 36, 44)
    stats_radius = th["corner_radius"]
    rounded_rect(screen, stats_rect, th["board_bg"], radius=stats_radius)
    if stats_radius == 0:
        pygame.draw.rect(screen, th["panel_edge"], stats_rect, width=1)
    else:
        pygame.draw.rect(screen, th["panel_edge"], stats_rect, width=1, border_radius=stats_radius)
        
    val_color = th["snake_body"] if current_theme == "retro" else th["text_main"]
    lbl_color = th["snake_head"] if current_theme == "retro" else th["text_sub"]
    camera_color = (0, 120, 0) if current_theme == "retro" and camera_available else (180, 50, 40) if current_theme == "retro" else (100, 255, 100) if camera_available else (255, 100, 100)
    
    labels = [
        ("SPEED", f"{current_speed:.1f}x", val_color),
        ("LENGTH", str(len(game.snake)), val_color),
        ("MODE", game.mode.upper(), val_color),
        ("CAMERA", "ON" if camera_available else "OFF", camera_color)
    ]
    seg_w = stats_rect.width / len(labels)
    for i, (lbl, val, color) in enumerate(labels):
        cx = stats_rect.x + seg_w * i + seg_w / 2
        if i > 0:
            divider_x = stats_rect.x + seg_w * i
            pygame.draw.line(screen, th["panel_edge"],
                              (divider_x, stats_rect.y + 6), (divider_x, stats_rect.bottom - 6), 1)
        v = stats_val_font.render(val, True, color)
        screen.blit(v, v.get_rect(center=(cx, stats_rect.y + 14)))
        l = label_font.render(lbl, True, lbl_color)
        screen.blit(l, l.get_rect(center=(cx, stats_rect.y + 30)))

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

def draw_camera_preview():
    if not camera_available or latest_frame is None or not show_camera_preview:
        return
    try:
        # Convert BGR frame from OpenCV to RGB
        rgb_frame = cv2.cvtColor(latest_frame, cv2.COLOR_BGR2RGB)
        # Mirror frame for natural self-view
        rgb_frame = cv2.flip(rgb_frame, 1)
        # Resize to 320x240 for preview card
        preview_w, preview_h = 320, 240
        resized = cv2.resize(rgb_frame, (preview_w, preview_h))
        # Convert numpy array to pygame surface
        cam_surf = pygame.surfarray.make_surface(resized.swapaxes(0, 1))
        
        # Position card in the bottom-right corner
        card_w, card_h = 340, 290
        card_rect = pygame.Rect(SCREEN_WIDTH - card_w - 20, SCREEN_HEIGHT - card_h - 20, card_w, card_h)
        draw_card_frame(card_rect)
        
        # Blit camera feed surface
        screen.blit(cam_surf, (card_rect.x + 10, card_rect.y + 10))
        
        # Add visual label for hand detection status
        th = THEMES[current_theme]
        hand_x, hand_y, gesture = get_hand_position(latest_frame)
        status_text = f"HAND ACTIVE ({gesture})" if hand_x is not None else "NO HAND DETECTED"
        status_color = (100, 255, 100) if hand_x is not None else th["text_sub"]
        
        lbl = tiny_font.render(status_text, True, status_color)
        screen.blit(lbl, lbl.get_rect(center=(card_rect.centerx, card_rect.y + 265)))
    except Exception as e:
        print(f"Error drawing camera preview: {e}")

def draw_particles():
    for particle in game.particles:
        particle.draw(screen)

def draw_pills(labels, y):
    th = THEMES[current_theme]
    gap = 24  # gap between pills
    
    parsed_items = []
    for label in labels:
        parts = label.split(" ", 1)
        if len(parts) == 2:
            key, action = parts[0], parts[1]
        else:
            key, action = parts[0], ""
            
        key_surf = tiny_font.render(key, True, th["text_main"])
        action_surf = tiny_font.render(action, True, th["text_sub"]) if action else None
        
        keycap_w = key_surf.get_width() + 16
        keycap_h = 26
        
        pill_w = keycap_w
        if action_surf:
            pill_w += 8 + action_surf.get_width()
            
        parsed_items.append({
            "key_surf": key_surf,
            "action_surf": action_surf,
            "keycap_w": keycap_w,
            "keycap_h": keycap_h,
            "pill_w": pill_w
        })
        
    total_w = sum(item["pill_w"] for item in parsed_items) + gap * (len(parsed_items) - 1)
    x = SCREEN_WIDTH // 2 - total_w // 2
    
    for item in parsed_items:
        # Draw keycap box
        keycap_rect = pygame.Rect(x, y + 1, item["keycap_w"], item["keycap_h"])
        rounded_rect(screen, keycap_rect, th["menu_row_bg_sel"], radius=5)
        pygame.draw.rect(screen, th["menu_row_border"], keycap_rect, 1, border_radius=5)
        
        # Center key text in keycap
        screen.blit(item["key_surf"], item["key_surf"].get_rect(center=keycap_rect.center))
        
        # Draw action label side-by-side
        if item["action_surf"]:
            screen.blit(item["action_surf"], (x + item["keycap_w"] + 8, y + 14 - item["action_surf"].get_height() // 2))
            
        x += item["pill_w"] + gap

def draw_icon(surface, kind, rect, color):
    cx, cy = rect.center
    if kind == "classic":       # filled dot, radio-style
        pygame.draw.circle(surface, color, (cx, cy), int(rect.width * 0.22))
    elif kind == "arcade":      # outlined square
        r = pygame.Rect(0, 0, int(rect.width * 0.5), int(rect.width * 0.5))
        r.center = (cx, cy)
        pygame.draw.rect(surface, color, r, width=2, border_radius=3)
    elif kind == "zen":         # infinity, built from two circles
        r = int(rect.width * 0.14)
        pygame.draw.circle(surface, color, (cx - r, cy), r, width=2)
        pygame.draw.circle(surface, color, (cx + r, cy), r, width=2)
    elif kind == "settings_gear":
        r = int(rect.width * 0.22)
        pygame.draw.circle(surface, color, (cx, cy), r, width=2)
        for i in range(8):
            ang = i * 3.14159 / 4
            x1, y1 = cx + r * 1.1 * math.cos(ang), cy + r * 1.1 * math.sin(ang)
            x2, y2 = cx + r * 1.5 * math.cos(ang), cy + r * 1.5 * math.sin(ang)
            pygame.draw.line(surface, color, (x1, y1), (x2, y2), 2)
    elif kind == "camera":
        r = pygame.Rect(0, 0, int(rect.width * 0.55), int(rect.width * 0.4))
        r.center = (cx, cy)
        pygame.draw.rect(surface, color, r, width=2, border_radius=3)
        pygame.draw.circle(surface, color, (cx, cy), int(rect.width * 0.14), width=2)
    elif kind == "skin":        # simple color dot indicator
        pygame.draw.circle(surface, color, (cx, cy), int(rect.width * 0.22))

def draw_status_strip(card_x, card_y, card_w):
    th = THEMES[current_theme]
    strip_h = 32
    strip_w = 720
    strip_rect = pygame.Rect(SCREEN_WIDTH // 2 - strip_w // 2, card_y + 575, strip_w, strip_h)
    
    rounded_rect(screen, strip_rect, th["menu_row_bg"], radius=8)
    pygame.draw.rect(screen, th["menu_row_border"], strip_rect, 1, border_radius=8)
    
    # Chip 1: Camera
    cam_status = "Camera on" if camera_available else "Camera off"
    cam_color = th["accent"] if camera_available else th["text_sub"]
    cam_txt = tiny_font.render(cam_status, True, cam_color)
    
    cam_icon_rect = pygame.Rect(strip_rect.x + 14, strip_rect.centery - 8, 16, 16)
    draw_icon(screen, "camera", cam_icon_rect, cam_color)
    screen.blit(cam_txt, (strip_rect.x + 36, strip_rect.centery - cam_txt.get_height() // 2))
    
    # Chip 2: Skin
    skin_text_str = active_skin.title()
    skin_txt = tiny_font.render(skin_text_str, True, th["text_sub"])
    total_w = 12 + 6 + skin_txt.get_width()
    start_x = strip_rect.centerx - total_w // 2
    
    skin_icon_rect = pygame.Rect(start_x, strip_rect.centery - 6, 12, 12)
    draw_icon(screen, "skin", skin_icon_rect, th["snake_body"])
    screen.blit(skin_txt, (start_x + 18, strip_rect.centery - skin_txt.get_height() // 2))
    
    # Resolution chip in the corner (tiny & muted)
    res_txt = tiny_font.render(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}", True, th["text_sub"])
    screen.blit(res_txt, res_txt.get_rect(midright=(strip_rect.right - 14, strip_rect.centery)))

def draw_settings():
    th = THEMES[current_theme]
    screen.fill(th["app_bg"])
    
    card_w = 880
    card_h = 660
    card_x = SCREEN_WIDTH // 2 - card_w // 2
    card_y = SCREEN_HEIGHT // 2 - card_h // 2
    card_rect = pygame.Rect(card_x, card_y, card_w, card_h)
    
    rounded_rect(screen, card_rect, th["panel_bg"], radius=th["corner_radius"] * 2)
    pygame.draw.rect(screen, th["panel_edge"], card_rect, 2, border_radius=th["corner_radius"] * 2)
    
    title_text = title_font.render("Settings", True, th["text_main"])
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, card_y + 50))
    screen.blit(title_text, title_rect)
    
    sub_text = small_font.render("Press Esc to go back", True, th["text_sub"])
    sub_rect = sub_text.get_rect(center=(SCREEN_WIDTH // 2, card_y + 105))
    screen.blit(sub_text, sub_rect)
    
    # Quit button in settings
    quit_rect = pygame.Rect(card_x + card_w - 106, card_y + 16, 90, 34)
    rounded_rect(screen, quit_rect, th["menu_row_bg"], radius=6)
    pygame.draw.rect(screen, th["menu_row_border"], quit_rect, 1, border_radius=6)
    quit_txt = tiny_font.render("Quit", True, th["text_sub"])
    screen.blit(quit_txt, quit_txt.get_rect(center=quit_rect.center))
    
    mode_str = screen_modes[current_screen_mode_idx]
    settings_items = [
        ("Theme",         "C", th["label"]),
        ("Skin",          "S", active_skin),
        ("Music",         "M", "ON" if music_active else "OFF"),
        ("Screen",        "F", mode_str),
        ("Resolution",    "P", f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}"),
        ("Camera",        "V", "ON" if camera_available else "OFF"),
        ("Camera source", "O", str(camera_index)),
        ("Tracker",       "T", "ON" if show_motion_tracker else "OFF")
    ]
    
    row_w = 720
    row_h = 46
    start_y = card_y + 165
    spacing = 54
    
    for i, (label, key, val) in enumerate(settings_items):
        y = start_y + (i * spacing)
        row_rect = pygame.Rect(SCREEN_WIDTH // 2 - row_w // 2, y, row_w, row_h)
        
        rounded_rect(screen, row_rect, th["menu_row_bg"], radius=8)
        pygame.draw.rect(screen, th["menu_row_border"], row_rect, 1, border_radius=8)
        
        # Label on left
        label_text = stats_val_font.render(label, True, th["text_main"])
        screen.blit(label_text, (row_rect.x + 14, row_rect.centery - label_text.get_height() // 2))
        
        # Value + hint on right
        val_str = f"{val}   [{key}]"
        val_text = stats_val_font.render(val_str, True, th["text_sub"])
        screen.blit(val_text, val_text.get_rect(midright=(row_rect.right - 14, row_rect.centery)))

def draw_mode_select():
    th = THEMES[current_theme]
    
    # Fill background with app bg
    screen.fill(th["app_bg"])
    
    # Card dimensions
    card_w = 880
    card_h = 660
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
    sub_rect = sub_text.get_rect(center=(SCREEN_WIDTH // 2, card_y + 105))
    screen.blit(sub_text, sub_rect)
    
    # Help button in top-right corner of card
    help_rect = pygame.Rect(card_x + card_w - 50, card_y + 16, 34, 34)
    rounded_rect(screen, help_rect, th["menu_row_bg"], radius=6)
    pygame.draw.rect(screen, th["menu_row_border"], help_rect, 1, border_radius=6)
    help_txt = small_font.render("?", True, th["text_sub"])
    screen.blit(help_txt, help_txt.get_rect(center=help_rect.center))
    
    # Quit button in top-right corner of card
    quit_rect = pygame.Rect(card_x + card_w - 150, card_y + 16, 90, 34)
    rounded_rect(screen, quit_rect, th["menu_row_bg"], radius=6)
    pygame.draw.rect(screen, th["menu_row_border"], quit_rect, 1, border_radius=6)
    quit_txt = tiny_font.render("Quit", True, th["text_sub"])
    screen.blit(quit_txt, quit_txt.get_rect(center=quit_rect.center))
    
    # Game modes list options (using kind strings for vector shapes)
    options = [
        {"name": "Classic", "desc": "Traditional snake gameplay", "icon": "classic"},
        {"name": "Arcade", "desc": "Obstacles, portals, power-ups", "icon": "arcade"},
        {"name": "Zen", "desc": "No death, infinite gameplay", "icon": "zen"}
    ]
    
    row_w = 720
    row_h = 90
    start_y = card_y + 165
    spacing = 110
    
    for i, opt in enumerate(options):
        is_selected = i == selected_mode_index
        y = start_y + (i * spacing)
        box_rect = pygame.Rect(SCREEN_WIDTH // 2 - row_w // 2, y, row_w, row_h)
        
        border_width = 4 if is_selected else 2
        bg = th["menu_row_bg_sel"] if is_selected else th["menu_row_bg"]
        border = th["menu_row_border_sel"] if is_selected else th["menu_row_border"]
        rounded_rect(screen, box_rect, bg, radius=th["corner_radius"] * 2)
        pygame.draw.rect(screen, border, box_rect, border_width, border_radius=th["corner_radius"] * 2)
        
        # Icon box on left (48x48, rounded 10px)
        icon_box = pygame.Rect(box_rect.x + 16, box_rect.y + (row_h - 48) // 2, 48, 48)
        icon_bg = th.get("menu_icon_bg_sel", th["menu_row_bg_sel"]) if is_selected else th.get("menu_icon_bg", th["menu_row_bg"])
        rounded_rect(screen, icon_box, icon_bg, radius=10)
        
        # Draw vector icon inside the icon box
        icon_color = th["text_main"] if is_selected else th["text_sub"]
        draw_icon(screen, opt["icon"], icon_box, icon_color)
        
        # Name (bold, 32px) and description (20px, muted)
        name_text = menu_name_font.render(opt["name"], True, th["text_main"])
        screen.blit(name_text, (box_rect.x + 84, box_rect.y + 18))
        
        desc_color = th["text_sub_sel"] if is_selected else th["text_sub"]
        desc_text = menu_desc_font.render(opt["desc"], True, desc_color)
        screen.blit(desc_text, (box_rect.x + 84, box_rect.y + 52))
        
        # Selected indicator chevron
        if is_selected:
            chevron = font.render("›", True, th["text_main"])
            screen.blit(chevron, chevron.get_rect(midright=(box_rect.right - 24, box_rect.centery)))

    # Separator line
    sep_y = card_y + 490
    pygame.draw.line(screen, th["panel_edge"], (card_x + 30, sep_y), (card_x + card_w - 30, sep_y), 1)
    
    # Action pills
    draw_pills(["↑↓ Navigate", "Enter Select", "Esc Quit", "H Settings"], card_y + 515)
    
    # Compact Status strip below pills
    draw_status_strip(card_x, card_y, card_w)

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
            elif show_mode_select or show_settings:
                if event.key == pygame.K_h:
                    if show_mode_select:
                        show_settings = True
                        show_mode_select = False
                    else:
                        show_mode_select = True
                        show_settings = False
                    play_sound("powerup")
                elif event.key == pygame.K_s:
                    cycle_skin(forward=True)
                elif event.key == pygame.K_m:
                    toggle_music()
                elif event.key == pygame.K_v:
                    if camera_available:
                        close_camera()
                    else:
                        initialize_camera()
                        if not camera_available:
                            show_camera_error = True
                            camera_error_timer = 3.0
                elif event.key == pygame.K_o:
                    camera_index = (camera_index + 1) % 5
                    if camera_available:
                        initialize_camera(camera_index)
                elif event.key == pygame.K_p:
                    cycle_resolution()
                elif event.key == pygame.K_t:
                    show_motion_tracker = not show_motion_tracker
                    play_sound("powerup")

                # Screen-specific navigation / transitions
                elif show_mode_select:
                    if event.key == pygame.K_ESCAPE:
                        running = False  # ESC in menu quits the game
                    elif event.key == pygame.K_q:
                        running = False
                    elif event.key == pygame.K_UP:
                        selected_mode_index = (selected_mode_index - 1) % 3
                    elif event.key == pygame.K_DOWN:
                        selected_mode_index = (selected_mode_index + 1) % 3
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
                elif show_settings:
                    if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                        show_mode_select = True
                        show_settings = False
                    elif event.key == pygame.K_q:
                        running = False
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
                elif event.key == pygame.K_q:
                    running = False
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
                elif event.key == pygame.K_v:
                    if camera_available:
                        show_camera_preview = not show_camera_preview
                    else:
                        initialize_camera()
                        if not camera_available:
                            show_camera_error = True
                            camera_error_timer = 3.0
                        else:
                            show_camera_preview = True
                elif event.key == pygame.K_o:
                    camera_index = (camera_index + 1) % 5
                    if camera_available:
                        initialize_camera(camera_index)
                elif event.key == pygame.K_l:
                    show_leaderboard = True
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left click
                mx, my = event.pos
                w, h = display_screen.get_size()
                logical_mx = int(mx * (SCREEN_WIDTH / w))
                logical_my = int(my * (SCREEN_HEIGHT / h))
                
                card_w = 880
                card_x = SCREEN_WIDTH // 2 - card_w // 2
                card_y = SCREEN_HEIGHT // 2 - 660 // 2
                
                if show_mode_select or show_settings:
                    # Help button "?" click behavior: toggles settings page
                    help_rect = pygame.Rect(card_x + card_w - 50, card_y + 16, 34, 34)
                    if show_mode_select and help_rect.collidepoint(logical_mx, logical_my):
                        show_settings = True
                        show_mode_select = False
                        play_sound("powerup")
                    else:
                        # Quit button click behavior:
                        quit_x = card_x + card_w - 106 if show_settings else card_x + card_w - 150
                        quit_rect = pygame.Rect(quit_x, card_y + 16, 90, 34)
                        if quit_rect.collidepoint(logical_mx, logical_my):
                            running = False
                
                stats_rect = pygame.Rect(18, 64, SCREEN_WIDTH - 36, 44)
                if stats_rect.collidepoint(logical_mx, logical_my):
                    seg_w = stats_rect.width / 4
                    clicked_segment = int((logical_mx - stats_rect.x) / seg_w)
                    if clicked_segment == 3: # CAMERA segment
                        if camera_available:
                            show_camera_preview = not show_camera_preview
                        else:
                            initialize_camera()
                            if not camera_available:
                                show_camera_error = True
                                camera_error_timer = 3.0
                            else:
                                show_camera_preview = True

    if shake_duration > 0:
        shake_duration -= dt

    if camera_available and cap is not None:
        ret, frame = cap.read()
        if ret and frame is not None:
            latest_frame = frame
            if not game_over and not show_mode_select and not paused:
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

    if not game_over and not show_mode_select and not paused:

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
    if show_mode_select or show_settings:
        if show_mode_select:
            draw_mode_select()
        else:
            draw_settings()
            


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
        is_circle = th.get("head_shape") == "circle"
        if active_skin == "CHAMELEON":
            if th["glow"]:
                if i == 0:
                    draw_glow(screen, rect.center, BLOCK * 0.5, th["snake_head"], layers=4, max_alpha=45)
                    if is_circle:
                        pygame.draw.circle(screen, th["snake_head"], rect.center, rect.width // 2)
                    else:
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
                if i == 0 and is_circle:
                    pygame.draw.circle(screen, color, rect.center, rect.width // 2)
                else:
                    rounded_rect(screen, rect, color, radius=th["corner_radius"])
                if i == 0 and not is_circle:
                    dir_map = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}
                    dx, dy = dir_map.get(game.direction, (1, 0))
                    dot_pos = (rect.centerx + dx * 4, rect.centery + dy * 4)
                    pygame.draw.circle(screen, th["board_bg"], dot_pos, 2)
        elif active_skin == "RAINBOW":
            hue = (i * 15 + pygame.time.get_ticks() // 10) % 360
            color = pygame.Color(0)
            color.hsva = (hue, 100, 100, 100)
            if i == 0 and is_circle:
                pygame.draw.circle(screen, color, rect.center, rect.width // 2)
            else:
                rounded_rect(screen, rect, color, radius=th["corner_radius"])
            if i == 0 and not is_circle:
                dir_map = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}
                dx, dy = dir_map.get(game.direction, (1, 0))
                dot_pos = (rect.centerx + dx * 4, rect.centery + dy * 4)
                pygame.draw.circle(screen, th["board_bg"], dot_pos, 2)
        else: # NEON GLOW
            color = (50, 255, 50) if i == 0 else (0, 200, 0)
            if i == 0 and is_circle:
                pygame.draw.circle(screen, color, rect.center, rect.width // 2)
            else:
                rounded_rect(screen, rect, color, radius=th["corner_radius"])
            if i > 0:
                core_color = (180, 255, 180)
                pygame.draw.rect(screen, core_color, (rect.x + 6, rect.y + 6, rect.width - 12, rect.height - 12), border_radius=th["corner_radius"])
            if i == 0 and not is_circle:
                dir_map = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}
                dx, dy = dir_map.get(game.direction, (1, 0))
                dot_pos = (rect.centerx + dx * 4, rect.centery + dy * 4)
                pygame.draw.circle(screen, th["board_bg"], dot_pos, 2)

    food_x, food_y = game.food
    cx = food_x + BLOCK // 2
    cy = food_y + BLOCK // 2
    pulse = (math.sin(pygame.time.get_ticks() / 150.0) + 1.0) / 2.0
    if th["glow"]:
        radius = BLOCK / 2 - 6 + pulse * 2
        draw_glow(screen, (cx, cy), radius, th["food"], layers=5, max_alpha=55)
        pygame.draw.circle(screen, th["food"], (cx, cy), int(radius))
    else:
        # Pulsing size for retro block food
        size_offset = 4 - int(pulse * 2)
        rect_food = pygame.Rect(food_x + size_offset, food_y + size_offset, BLOCK - size_offset * 2, BLOCK - size_offset * 2)
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

    if camera_available and show_motion_tracker:
        if hand_x is not None and hand_y is not None:
            hand_pixel_x = int((1.0 - hand_x) * SCREEN_WIDTH)
            hand_pixel_y = int(hand_y * SCREEN_HEIGHT)
            
            if PLAY_AREA_TOP <= hand_pixel_y < SCREEN_HEIGHT:
                gesture_color = (0, 255, 100) if gesture_type == "POINTING" else (100, 200, 255) if gesture_type == "OPEN" else (200, 100, 200)
                pygame.draw.circle(screen, gesture_color, (hand_pixel_x, hand_pixel_y), 15, 3)
                pygame.draw.circle(screen, gesture_color, (hand_pixel_x, hand_pixel_y), 10, 1)

    if entering_name:
        draw_dim_overlay(180)
        card_w, card_h = 360, 260
        card_rect = pygame.Rect(SCREEN_WIDTH // 2 - card_w // 2, SCREEN_HEIGHT // 2 - card_h // 2 + 20, card_w, card_h)
        draw_card_frame(card_rect)
        
        title_text = font.render("New High Score!", True, th["accent"])
        screen.blit(title_text, title_text.get_rect(center=(card_rect.centerx, card_rect.y + 40)))
        
        score_text = small_font.render(f"Score: {game.score}", True, th["text_main"])
        screen.blit(score_text, score_text.get_rect(center=(card_rect.centerx, card_rect.y + 90)))
        
        input_box = pygame.Rect(card_rect.x + 30, card_rect.y + 130, card_w - 60, 48)
        input_radius = th["corner_radius"]
        rounded_rect(screen, input_box, th.get("input_bg", th["panel_bg"]), radius=input_radius)
        if input_radius == 0:
            pygame.draw.rect(screen, th["accent"], input_box, width=1)
        else:
            pygame.draw.rect(screen, th["accent"], input_box, width=1, border_radius=input_radius)
        name_display = small_font.render(player_name + "|", True, th["text_main"])
        name_rect = name_display.get_rect(center=input_box.center)
        screen.blit(name_display, name_rect)
        
        hint_text = tiny_font.render("Press ENTER to submit", True, th["text_sub"])
        screen.blit(hint_text, hint_text.get_rect(center=(card_rect.centerx, card_rect.y + 210)))
    elif game_over:
        draw_dim_overlay(160)
        card_w, card_h = 400, 340
        card_rect = pygame.Rect(SCREEN_WIDTH // 2 - card_w // 2, SCREEN_HEIGHT // 2 - card_h // 2 + 20, card_w, card_h)
        draw_card_frame(card_rect)
        
        title_text = font.render("Game Over", True, th["accent"])
        screen.blit(title_text, title_text.get_rect(center=(card_rect.centerx, card_rect.y + 35)))
        
        score_str = f"Final Score: {game.score}"
        if game.score >= high_score and game.score > 0:
            score_str += "  (NEW BEST!)"
        score_txt = small_font.render(score_str, True, th["text_main"])
        screen.blit(score_txt, score_txt.get_rect(center=(card_rect.centerx, card_rect.y + 80)))
        
        # Leaderboard sub-list inside card
        modes_leaderboard = load_leaderboard(game.mode)
        start_y = card_rect.y + 115
        if modes_leaderboard:
            scores_title = tiny_font.render("TOP SCORES FOR THIS MODE:", True, th["text_sub"])
            screen.blit(scores_title, (card_rect.x + 35, start_y))
            for idx, entry in enumerate(modes_leaderboard[:3]):
                rank_y = start_y + 25 + idx * 24
                rank_bg_rect = pygame.Rect(card_rect.x + 30, rank_y - 2, card_w - 60, 22)
                rank_radius = th["corner_radius"]
                rounded_rect(screen, rank_bg_rect, th.get("rank_bg", th["board_bg"]), radius=rank_radius)
                if rank_radius == 0:
                    pygame.draw.rect(screen, th["panel_edge"], rank_bg_rect, width=1)
                else:
                    pygame.draw.rect(screen, th["panel_edge"], rank_bg_rect, width=1, border_radius=rank_radius)
                
                num_txt = tiny_font.render(f"#{idx+1}", True, th["accent"])
                screen.blit(num_txt, (card_rect.x + 40, rank_y))
                name_txt = tiny_font.render(entry['name'][:10], True, th["text_main"])
                screen.blit(name_txt, (card_rect.x + 80, rank_y))
                val_txt = tiny_font.render(str(entry['score']), True, th["text_main"])
                screen.blit(val_txt, val_txt.get_rect(topright=(card_rect.right - 40, rank_y)))
                
        menu_text = tiny_font.render("M: Menu   |   R: Restart   |   Q: Quit", True, th["text_sub"])
        screen.blit(menu_text, menu_text.get_rect(center=(card_rect.centerx, card_rect.bottom - 25)))
    elif show_leaderboard:
        draw_leaderboard()
    elif paused:
        draw_dim_overlay(120)
        card_w, card_h = 320, 200
        card_rect = pygame.Rect(SCREEN_WIDTH // 2 - card_w // 2, SCREEN_HEIGHT // 2 - card_h // 2 + 20, card_w, card_h)
        draw_card_frame(card_rect)
        
        pause_title = font.render("Paused", True, th["text_main"])
        screen.blit(pause_title, pause_title.get_rect(center=(card_rect.centerx, card_rect.y + 40)))
        
        pause_desc1 = small_font.render("P / ESC to resume", True, th["text_main"])
        screen.blit(pause_desc1, pause_desc1.get_rect(center=(card_rect.centerx, card_rect.y + 100)))
        
        pause_desc2 = tiny_font.render("M to return to Main Menu", True, th["text_sub"])
        screen.blit(pause_desc2, pause_desc2.get_rect(center=(card_rect.centerx, card_rect.y + 150)))
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

    # Live Webcam Feed and Connection Status Alert
    draw_camera_preview()
    
    if show_camera_error:
        camera_error_timer -= dt
        if camera_error_timer <= 0:
            show_camera_error = False
        alert_w, alert_h = 440, 80
        alert_rect = pygame.Rect(SCREEN_WIDTH // 2 - alert_w // 2, PLAY_AREA_TOP + 20, alert_w, alert_h)
        rounded_rect(screen, alert_rect, th["panel_bg"], radius=th["corner_radius"])
        pygame.draw.rect(screen, (220, 50, 50), alert_rect, width=2, border_radius=th["corner_radius"])
        err_txt = small_font.render("No Webcam Detected!", True, (220, 50, 50))
        sub_txt = tiny_font.render("Connect a camera and press V to try again.", True, th["text_main"])
        screen.blit(err_txt, err_txt.get_rect(center=(alert_rect.centerx, alert_rect.y + 25)))
        screen.blit(sub_txt, sub_txt.get_rect(center=(alert_rect.centerx, alert_rect.y + 55)))

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