from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class GarminMetrics:
    date: date
    # Readiness & Recovery
    training_readiness: Optional[int] = None
    readiness_feedback: Optional[str] = None
    recovery_time: Optional[float] = None
    acute_load: Optional[int] = None
    acwr_status: Optional[str] = None
    
    # Body Battery & Stress
    body_battery_high: Optional[int] = None
    body_battery_low: Optional[int] = None
    avg_stress: Optional[int] = None
    stress_qualifier: Optional[str] = None
    
    # Sleep & Bio-markers
    sleep_score: Optional[int] = None
    sleep_feedback: Optional[str] = None
    overnight_hrv: Optional[int] = None
    resting_hr: Optional[int] = None
    respiration_avg: Optional[float] = None
    spo2_avg: Optional[float] = None
    
    # Fueling & Performance
    active_calories: Optional[int] = None
    bmr_calories: Optional[int] = None
    steps: Optional[int] = None
    running_distance: Optional[float] = None
    strength_sessions: Optional[int] = 0
    vo2_max: Optional[float] = None

HEADERS = [
    "Date", "Readiness", "Feedback", "Recovery (h)", "Injury Risk", "Acute Load",
    "BB High", "BB Low", "Avg Stress", "Stress Type", 
    "Sleep Score", "Sleep Feedback", "HRV", "RHR", "Respiration", "SpO2",
    "Active Cals", "BMR Cals", "Steps", "Run KM", "Strength", "VO2 Max"
]

HEADER_TO_ATTRIBUTE_MAP = {
    "Date": "date", "Readiness": "training_readiness", "Feedback": "readiness_feedback",
    "Recovery (h)": "recovery_time", "Injury Risk": "acwr_status", "Acute Load": "acute_load",
    "BB High": "body_battery_high", "BB Low": "body_battery_low", "Avg Stress": "avg_stress",
    "Stress Type": "stress_qualifier", "Sleep Score": "sleep_score", "Sleep Feedback": "sleep_feedback",
    "HRV": "overnight_hrv", "RHR": "resting_hr", "Respiration": "respiration_avg", "SpO2": "spo2_avg",
    "Active Cals": "active_calories", "BMR Cals": "bmr_calories", "Steps": "steps", 
    "Run KM": "running_distance", "Strength": "strength_sessions", "VO2 Max": "vo2_max"
}

TARGET_SHEET_NAME = "Garmin Data"
SHEET_DATE_FORMAT = "%A, %b %d"
