import cv2
import mediapipe as mp
import math
from collections import deque

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.8, min_tracking_confidence=0.7)

hand_position_history = deque(maxlen=5)
last_direction = None


def calculate_distance(point1, point2):
    """Calculate Euclidean distance between two landmarks."""
    dx = point1.x - point2.x
    dy = point1.y - point2.y
    return math.sqrt(dx * dx + dy * dy)


def is_finger_extended(tip, pip, dip):
    """Check if a finger is extended based on distance from PIP joint."""
    tip_to_pip = calculate_distance(tip, pip)
    dip_to_pip = calculate_distance(dip, pip)
    return tip_to_pip > dip_to_pip * 0.9


def detect_gesture(hand):
    """Detect hand gesture: POINTING, OPEN, or FIST."""
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
    """Detect direction from hand movement."""
    global last_direction
    
    if frame is None:
        return None, 0
    
    try:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(frame_rgb)
        
        if not result.multi_hand_landmarks or not result.multi_handedness:
            return None, 0
        
        hand = result.multi_hand_landmarks[0]
        handedness = result.multi_handedness[0]
        hand_confidence = handedness.classification[0].score
        
        if hand_confidence < 0.7:
            return None, hand_confidence
        
        wrist = hand.landmark[0]
        gesture = detect_gesture(hand)
        
        hand_position_history.append((wrist.x, wrist.y))
        
        if len(hand_position_history) < 2:
            return None, hand_confidence
        
        positions = list(hand_position_history)
        old_x, old_y = positions[0]
        new_x, new_y = positions[-1]
        
        dx = new_x - old_x
        dy = new_y - old_y
        
        abs_dx = abs(dx)
        abs_dy = abs(dy)
        
        min_threshold = 0.02
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
            return direction, hand_confidence
        
        return last_direction, hand_confidence
    
    except Exception as e:
        return None, 0


def get_hand_position(frame):
    """Get hand position for display (0-1 range) and gesture type."""
    if frame is None:
        return None, None, None
    
    try:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(frame_rgb)
        
        if result.multi_hand_landmarks:
            hand = result.multi_hand_landmarks[0]
            wrist = hand.landmark[0]
            gesture_type = detect_gesture(hand)
            return wrist.x, wrist.y, gesture_type
    except:
        pass
    
    return None, None, None


