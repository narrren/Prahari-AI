import math
from app.models import TelemetryData
from app.core.shared_state import BIOMETRIC_HISTORY

HISTORY_LEN = 10

def calculate_variance(data):
    if len(data) < 2: return 0.0
    mean = sum(data) / len(data)
    return sum((x - mean) ** 2 for x in data) / len(data)

def analyze_humanity(data: TelemetryData) -> float:
    """
    Turing Test for GPS:
    Real humans have 'entropy' (jitter).
    Bots move in straight lines or constant speeds.
    """
    history = BIOMETRIC_HISTORY[data.device_id]
    
    # Only append if timestamp is newer (deduplication already done upstream, but safe to check)
    if not history or data.timestamp > history[-1].timestamp:
        history.append(data)
        
    if len(history) > HISTORY_LEN:
        history.pop(0)

    if len(history) < 5:
        return 100.0

    # Extract metrics
    speeds = [p.speed for p in history]
    headings = [p.heading for p in history]
    
    # Variance Analysis
    speed_var = calculate_variance(speeds)
    heading_var = calculate_variance(headings)
    avg_speed = sum(speeds) / len(speeds)
    
    score = 100.0
    
    # Rule 1: Zero Variance = Bot (Perfect Constant Speed)
    # Allow for stationary (speed ~ 0)
    if speed_var < 0.01 and avg_speed > 0.5:
        print(f"BIOMETRICS: {data.device_id} flagged for Robotic Speed (Var: {speed_var:.4f})")
        score -= 40.0
        
    # Rule 2: Straight Line for too long (Zero Heading Variance)
    if heading_var < 0.01 and avg_speed > 0.5:
        print(f"BIOMETRICS: {data.device_id} flagged for Rail-Movement (Heading Var: {heading_var:.4f})")
        score -= 30.0
        
    # Rule 3: Superhuman Speed (e.g., > 30 m/s ~ 100 km/h on foot/trail)
    if max(speeds) > 30.0:
        score -= 90.0
        print(f"BIOMETRICS: {data.device_id} flagged for Impossible Speed")
        
    return max(0.0, score)
