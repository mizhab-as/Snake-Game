import cv2
import mediapipe as mp
import math
from collections import deque

mp_hands = None
hands = None
try:
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
except (AttributeError, ModuleNotFoundError):
    pass

hand_position_history = deque(maxlen=10)  # Increased to 10 for better noise filtering
last_direction = None

# Frame caching variables to prevent multiple MediaPipe runs on the same frame in a single loop
_cached_frame_id = None
_cached_result = None

def _process_frame_cached(frame):
    global _cached_frame_id, _cached_result
    if frame is None or hands is None:
        return None
    
    frame_id = id(frame)
    if frame_id == _cached_frame_id:
        return _cached_result
        
    try:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        _cached_result = hands.process(frame_rgb)
        _cached_frame_id = frame_id
        return _cached_result
    except Exception as e:
        return None

def calculate_distance(point1, point2):
    dx = point1.x - point2.x
    dy = point1.y - point2.y
    return math.sqrt(dx * dx + dy * dy)


def is_finger_extended(tip, pip, dip):
    tip_to_pip = calculate_distance(tip, pip)
    dip_to_pip = calculate_distance(dip, pip)
    return tip_to_pip > dip_to_pip * 0.9


def detect_gesture(hand):
    extended_fingers = 0
    
    if is_finger_extended(hand.landmark[8], hand.landmark[7], hand.landmark[6]):
        extended_fingers += 1
    
    if is_finger_extended(hand.landmark[12], hand.landmark[11], hand.landmark[10]):
        extended_fingers += 1
    
    if is_finger_extended(hand.landmark[16], hand.landmark[15], hand.landmark[14]):
        extended_fingers += 1
    
    if is_finger_extended(hand.landmark[20], hand.landmark[19], hand.landmark[18]):
        extended_fingers += 1
    
    index_extended = is_finger_extended(hand.landmark[8], hand.landmark[7], hand.landmark[6])
    thumb_extended = is_finger_extended(hand.landmark[4], hand.landmark[3], hand.landmark[2])
    
    if index_extended and extended_fingers == 1:
        return "POINTING"
    elif extended_fingers >= 4:
        return "OPEN"
    else:
        return "FIST"


def get_direction(frame):
    global last_direction
    
    if frame is None or hands is None:
        return None, 0
    
    try:
        result = _process_frame_cached(frame)
        if not result or not result.multi_hand_landmarks or not result.multi_handedness:
            # Clear history if no hand is visible to prevent old swipes from registering
            hand_position_history.clear()
            return None, 0
        
        hand = result.multi_hand_landmarks[0]
        handedness = result.multi_handedness[0]
        hand_confidence = handedness.classification[0].score
        
        if hand_confidence < 0.65:
            return None, hand_confidence
        
        # Use Middle Finger MCP (landmark 9) as the palm center reference because it is highly stable
        ref_point = hand.landmark[9]
        
        hand_position_history.append((ref_point.x, ref_point.y))
        
        if len(hand_position_history) < 3:
            return None, hand_confidence
        
        positions = list(hand_position_history)
        old_x, old_y = positions[0]
        new_x, new_y = positions[-1]
        
        dx = new_x - old_x
        dy = new_y - old_y
        
        abs_dx = abs(dx)
        abs_dy = abs(dy)
        
        # 0.025 threshold over 10 frames provides clear, deliberate swipe registration without jitter
        min_threshold = 0.025
        direction = None
        
        if abs_dy > abs_dx and abs_dy > min_threshold:
            if dy < 0:
                direction = "UP"
            else:
                direction = "DOWN"
        elif abs_dx > abs_dy and abs_dx > min_threshold:
            if dx < 0:
                direction = "LEFT"
            else:
                direction = "RIGHT"
        
        if direction:
            last_direction = direction
            # Clear history after successful swipe registration so it does not trigger repeatedly
            hand_position_history.clear()
            return direction, hand_confidence
        
        # Return None for discrete swipe behavior (does not spam or override keyboard when hand is still)
        return None, hand_confidence
    
    except Exception as e:
        return None, 0


def get_hand_position(frame):
    if frame is None or hands is None:
        return None, None, None
    
    try:
        result = _process_frame_cached(frame)
        if result and result.multi_hand_landmarks:
            hand = result.multi_hand_landmarks[0]
            ref_point = hand.landmark[9]
            gesture_type = detect_gesture(hand)
            return ref_point.x, ref_point.y, gesture_type
    except:
        pass
    
    return None, None, None
