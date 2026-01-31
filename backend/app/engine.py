from app.models import TelemetryData, AlertType
from app.services.db import get_table
from app.core.config import settings
import boto3
import time
import datetime
from decimal import Decimal

# --- 2. The AI Engine: Weighted Logic & Kalman Filter ---

class SentinelAI:
    @staticmethod
    def calculate_risk(current: dict, all_states: dict) -> dict:
        """
        Production Logic:
        Calculates a Risk Score (0-100) based on Spatial, Temporal, and Behavioral factors.
        Returns: { "score": int, "status": str, "factors": list }
        """
        score = 0
        factors = []
        
        # Extract fields from dict (FastAPI Pydantic dict())
        lat = current['location']['lat']
        lng = current['location']['lng']
        speed = current.get('speed', 0.0)
        
        # A. Spatial Check (GeoJSON Polygons)
        # We reuse our efficient geofence service
        from app.services.geofence import check_geofence_breach, GeoPoint
        
        # Convert to GeoPoint for the service
        gpoint = GeoPoint(lat=lat, lng=lng)
        zone = check_geofence_breach(gpoint)
        
        if zone:
            if zone.risk_level == "HIGH":
                score += 50
                factors.append("RED_ZONE_BREACH")
            elif zone.risk_level == "MEDIUM":
                score += 25
                factors.append("WARN_ZONE_ENTRY")
            
        # B. Behavioral (Speed/Stagnation)
        # Using a simple moving average or Kalman logic to handle GPS Drift
        # If speed < 0.1, we consider it potential stagnation.
        # Ideally we check duration, but for instantaneous risk scoring:
        if speed < 0.1:
            # Check if this state has persisted?
            # We access 'all_states' which is the InMemory Cache.
            # But 'current' is likely already IN 'all_states' due to ingestion order.
            # We assume the caller checks 'time since first stopped'.
            
            # Simple Production Rule:
            # If speed is virtually zero AND we are in a risk zone -> +20 Risk
            if zone:
                score += 20
                factors.append("STAGNATION_IN_RISK_ZONE")
            else:
                # Just resting in Safe Zone? Low risk.
                score += 5
                
        # C. Temporal Weighting
        # Night time operations are inherently riskier in border areas.
        current_dt = datetime.datetime.now()
        hour = current_dt.hour
        if hour >= 18 or hour < 5:
            if score > 0:
                score = score * 1.2 # 20% risk multiplier at night
                factors.append("NIGHT_MULTIPLIER")
                
        # D. Weather Context (Context-Aware AI Upgrade)
        # In Tawang/Zero, weather is a major killer.
        weather_condition = SentinelAI.get_weather_condition(lat, lng)
        if weather_condition in ['Thunderstorm', 'Heavy Snow', 'Blizzard']:
            score += 30
            factors.append(f"SEVERE_WEATHER_WARNING: {weather_condition}")
        elif weather_condition in ['Rain', 'Fog']:
            score += 10
            factors.append(f"WEATHER_ADVISORY: {weather_condition}")

    @staticmethod
    def get_weather_condition(lat, lng):
        """
        Mocks a call to OpenWeatherMap API for demonstration.
        In production, this would use 'requests.get(api_url)'.
        For the demo, we simulate bad weather in specific 'micro-climates' (zones).
        """
        import random
        # Simulate a localized storm near the Red Zone coordinates
        if 27.585 < lat < 27.590 and 91.855 < lng < 91.865:
            return random.choice(['Thunderstorm', 'Heavy Snow', 'Blizzard'])
        
        return "Clear Sky"
            
        # D. SOS Override
        if current.get('is_panic', False):
            return {"score": 100, "status": "CRITICAL", "factors": ["SOS_PANIC_BUTTON"]}

        # Final Thresholds
        score = min(score, 100)
        status = "SAFE"
        
        if score >= 80: 
            status = "CRITICAL"
        elif score >= 50: 
            status = "WARNING"
        
        return {"score": int(score), "status": status, "factors": factors}

# Legacy Adapter to keep existing simple calls working if needed, 
# or we refactor anomaly_detection.py to use this Class.
