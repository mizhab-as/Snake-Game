import cv2
import mediapipe as mp
import math
from collections import deque

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.8, min_tracking_confidence=0.7)

# Hand position history for motion detection
hand_position_history = deque(maxlen=5)
last_direction = None


def calculate_distance(point1, point2):
    """Calculate Euclidean distance between two landmarks."""
    dx = point1.x - point2.x
    dy = point1.y - point2.y
    return math.sqrt(dx * dx + dy * dy)


def is_finger_extended(tip, pip, dip):
    """
    Check if a finger is extended using distance-based logic.
    A finger is extended if the tip is significantly separated from the PIP joint.
    """
    tip_to_pip = calculate_distance(tip, pip)
    dip_to_pip = calculate_distance(dip, pip)
    return tip_to_pip > dip_to_pip * 0.9


def detect_gesture(hand):
    """
    Detect the current hand gesture.
    Returns: "POINTING", "OPEN", or "FIST"
    """
    # Count extended fingers
    extended_fingers = 0
    
    # Check index finger (8=tip, 7=dip, 6=pip)
    index_extended = is_finger_extended(hand.landmark[8], hand.landmark[7], hand.landmark[6])
    if index_extended:
        extended_fingers += 1
    
    # Check middle finger (12=tip, 11=dip, 10=pip)
    middle_extended = is_finger_extended(hand.landmark[12], hand.landmark[11], hand.landmark[10])
    if middle_extended:
        extended_fingers += 1
    
    # Check ring finger (16=tip, 15=dip, 14=pip)
    ring_extended = is_finger_extended(hand.landmark[16], hand.landmark[15], hand.landmark[14])
    if ring_extended:
        extended_fingers += 1
    
    # Check pinky (20=tip, 19=dip, 18=pip)
    pinky_extended = is_finger_extended(hand.landmark[20], hand.landmark[19], hand.landmark[18])
    if pinky_extended:
        extended_fingers += 1
    
    # Check thumb (4=tip, 3=dip, 2=pip)
    thumb_extended = is_finger_extended(hand.landmark[4], hand.landmark[3], hand.landmark[2])
    if thumb_extended:
        extended_fingers += 1
    
    # Determine gesture based on extended fingers
    if index_extended and extended_fingers == 1:
        return "POINTING"
    elif extended_fingers >= 4:
        return "OPEN"
    else:
        return "FIST"


def get_direction(frame):
    """
    Detect direction based on hand MOVEMENT.
    Track hand position and determine direction of movement.
    
    When you move your hand UP, the snake goes UP.
    When you move your hand DOWN, the snake goes DOWN.
    Etc.
    
    Returns: (direction, confidence)
    - direction: "UP", "DOWN", "LEFT", "RIGHT", or None
    - confidence: hand detection confidence (0-1)
    """
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
        
        # Get hand position (wrist = center of hand)
        wrist = hand.landmark[0]
        
        # Check gesture type for information only (don't skip based on it)
        gesture = detect_gesture(hand)
        
        # Add current position to history REGARDLESS OF GESTURE
        hand_position_history.append((wrist.x, wrist.y))
        
        # Need at least 2 positions to detect motion (reduced from 3)
        if len(hand_position_history) < 2:
            return None, hand_confidence
        
        # Get oldest and newest positions
        positions = list(hand_position_history)
        old_x, old_y = positions[0]
        new_x, new_y = positions[-1]
        
        # Calculate displacement (movement vector)
        dx = new_x - old_x
        dy = new_y - old_y
        
        abs_dx = abs(dx)
        abs_dy = abs(dy)
        
        # Much lower threshold for detecting movement
        min_threshold = 0.02
        
        direction = None
        
        # Determine direction based on which motion is dominant
        if abs_dy > abs_dx and abs_dy > min_threshold:
            # Vertical motion is dominant
            if dy < 0:
                direction = "UP"  # Hand moved upward
            else:
                direction = "DOWN"  # Hand moved downward
        elif abs_dx > abs_dy and abs_dx > min_threshold:
            # Horizontal motion is dominant
            if dx < 0:
                direction = "LEFT"  # Hand moved leftward
            else:
                direction = "RIGHT"  # Hand moved rightward
        
        # Return detected direction
        if direction:
            last_direction = direction
            return direction, hand_confidence
        
        # Return last known direction if no new motion detected
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


