from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class GarminMetrics:
    date: date
    
    # Readiness & Recovery (NEW)
    training_readiness: Optional[int] = None
    readiness_feedback: Optional[str] = None
    recovery_time: Optional[float] = None
    acute_load: Optional[int] = None
    acwr_status: Optional[str] = None
    
    # Body Battery & Stress
    body_battery_high: Optional[int] = None
    body_battery_low: Optional[int] = None
    avg_stress: Optional[int] = None
    average_stress: Optional[int] = None  # Alias for compatibility
    stress_qualifier: Optional[str] = None
    
    # Sleep & Bio-markers
    sleep_score: Optional[int] = None
    sleep_feedback: Optional[str] = None
    sleep_length: Optional[float] = None
    overnight_hrv: Optional[int] = None
    hrv_status: Optional[str] = None
    resting_hr: Optional[int] = None
    resting_heart_rate: Optional[int] = None  # Alias for compatibility
    respiration_avg: Optional[float] = None
    spo2_avg: Optional[float] = None
    
    # Fueling & Performance
    active_calories: Optional[int] = None
    bmr_calories: Optional[int] = None
    resting_calories: Optional[int] = None  # Alias for compatibility
    steps: Optional[int] = None
    intensity_minutes: Optional[int] = None
    
    # Activities
    all_activity_count: Optional[int] = None
    running_activity_count: Optional[int] = None
    running_distance: Optional[float] = None
    strength_sessions: Optional[int] = 0
    strength_activity_count: Optional[int] = None  # Alias for compatibility
    strength_duration: Optional[float] = None
    cardio_activity_count: Optional[int] = None
    cardio_duration: Optional[float] = None
    
    # Training Metrics
    training_status: Optional[str] = None
    vo2_max: Optional[float] = None
    vo2max_running: Optional[float] = None  # Alias for compatibility
    
    # Body Metrics (from old config - may not be populated)
    weight: Optional[float] = None
    body_fat: Optional[float] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    
    # Cycling & Tennis (from old config - may not be populated)
    vo2max_cycling: Optional[float] = None
    cycling_activity_count: Optional[int] = None
    cycling_distance: Optional[float] = None
    tennis_activity_count: Optional[int] = None
    tennis_activity_duration: Optional[float] = None

HEADERS = [
    "Date", 
    # Readiness & Recovery
    "Readiness", "Feedback", "Recovery (h)", "Acute Load", "Injury Risk",
    # Body Battery & Stress
    "BB High", "BB Low", "Avg Stress", "Stress Type", 
    # Sleep
    "Sleep Score", "Sleep Feedback", "Sleep Length", 
    # Bio-markers
    "HRV", "HRV Status", "RHR", "Respiration", "SpO2",
    # Calories & Activity
    "Active Cals", "BMR Cals", "Steps", "Intensity Mins",
    # Running
    "Run Count", "Run KM", 
    # Strength
    "Strength Count", "Strength Duration",
    # Cardio
    "Cardio Count", "Cardio Duration",
    # Training
    "Training Status", "VO2 Max", 
    # All Activities
    "All Activity Count"
]

HEADER_TO_ATTRIBUTE_MAP = {
    "Date": "date",
    # Readiness & Recovery
    "Readiness": "training_readiness",
    "Feedback": "readiness_feedback",
    "Recovery (h)": "recovery_time",
    "Acute Load": "acute_load",
    "Injury Risk": "acwr_status",
    # Body Battery & Stress
    "BB High": "body_battery_high",
    "BB Low": "body_battery_low",
    "Avg Stress": "avg_stress",
    "Stress Type": "stress_qualifier",
    # Sleep
    "Sleep Score": "sleep_score",
    "Sleep Feedback": "sleep_feedback",
    "Sleep Length": "sleep_length",
    # Bio-markers
    "HRV": "overnight_hrv",
    "HRV Status": "hrv_status",
    "RHR": "resting_hr",
    "Respiration": "respiration_avg",
    "SpO2": "spo2_avg",
    # Calories & Activity
    "Active Cals": "active_calories",
    "BMR Cals": "bmr_calories",
    "Steps": "steps",
    "Intensity Mins": "intensity_minutes",
    # Running
    "Run Count": "running_activity_count",
    "Run KM": "running_distance",
    # Strength
    "Strength Count": "strength_sessions",
    "Strength Duration": "strength_duration",
    # Cardio
    "Cardio Count": "cardio_activity_count",
    "Cardio Duration": "cardio_duration",
    # Training
    "Training Status": "training_status",
    "VO2 Max": "vo2_max",
    # All Activities
    "All Activity Count": "all_activity_count"
}

TARGET_SHEET_NAME = "Garmin Data"
SHEET_DATE_FORMAT = "%A, %b %d"
