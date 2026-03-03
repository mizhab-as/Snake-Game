import cv2
import mediapipe as mp
import math

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5)

# History for smoothing gestures
direction_history = []
MAX_HISTORY = 3

def get_direction(frame):
    """
    Detect hand gesture direction based on finger pointing.
    
    Gestures:
    - Point UP: middle finger above wrist
    - Point DOWN: middle finger below wrist
    - Point LEFT: middle finger left of wrist
    - Point RIGHT: middle finger right of wrist
    """
    global direction_history
    
    if frame is None:
        return None, None

    try:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(frame_rgb)

        if result.multi_hand_landmarks and result.multi_handedness:
            hand = result.multi_hand_landmarks[0]
            handedness = result.multi_handedness[0]
            
            # Get confidence of hand detection
            hand_confidence = handedness.classification[0].score
            
            # Get key landmarks
            wrist = hand.landmark[0]  # Wrist
            middle_finger_tip = hand.landmark[12]  # Middle finger tip
            index_finger_tip = hand.landmark[8]    # Index finger tip
            
            # Calculate direction vector from wrist to middle finger
            dx = middle_finger_tip.x - wrist.x
            dy = middle_finger_tip.y - wrist.y
            
            # Calculate absolute distances
            abs_dx = abs(dx)
            abs_dy = abs(dy)
            
            # Determine direction based on which component is larger
            direction = None
            
            # Require significant finger pointing (high threshold - only point counts)
            min_threshold = 0.12  # Finger must move at least 12% of frame away from wrist
            
            if abs_dy > abs_dx and abs_dy > min_threshold:
                # Vertical gesture - strong pointing required
                if dy < 0:
                    direction = "UP"      # Finger points up (negative y)
                else:
                    direction = "DOWN"    # Finger points down (positive y)
            elif abs_dx > abs_dy and abs_dx > min_threshold:
                # Horizontal gesture - strong pointing required
                if dx < 0:
                    direction = "LEFT"    # Finger points left (negative x)
                else:
                    direction = "RIGHT"   # Finger points right (positive x)
            
            # Add to history for smoothing
            if direction:
                direction_history.append(direction)
                if len(direction_history) > MAX_HISTORY:
                    direction_history.pop(0)
                
                # Return most common direction in recent history
                if len(direction_history) >= 2:
                    most_common = max(set(direction_history), key=direction_history.count)
                    return most_common, hand_confidence
            
            return None, hand_confidence

    except Exception as e:
        print(f"Hand tracking error: {e}")
        return None, None

    return None, None


def get_hand_position(frame):
    """Get normalized hand position for display (0-1 range)."""
    if frame is None:
        return None, None
    
    try:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(frame_rgb)
        
        if result.multi_hand_landmarks:
            hand = result.multi_hand_landmarks[0]
            wrist = hand.landmark[0]
            return wrist.x, wrist.y
    except:
        pass
    
    return None, None

