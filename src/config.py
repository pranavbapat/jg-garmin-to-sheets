from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class GarminMetrics:
    date: date
    
    # Sleep Metrics
    sleep_score: Optional[int] = None
    sleep_length: Optional[float] = None
    sleep_feedback: Optional[str] = None
    
    # HRV & Heart Rate
    overnight_hrv: Optional[int] = None
    hrv_status: Optional[str] = None
    resting_heart_rate: Optional[int] = None
    
    # Readiness & Recovery
    training_readiness: Optional[int] = None
    readiness_feedback: Optional[str] = None
    recovery_time: Optional[float] = None
    acute_load: Optional[int] = None
    acwr_status: Optional[str] = None
    
    # Body Battery & Stress
    body_battery_high: Optional[int] = None
    body_battery_low: Optional[int] = None
    average_stress: Optional[int] = None
    
    # Respiration & SpO2
    respiration_avg: Optional[float] = None
    spo2_avg: Optional[float] = None
    
    # Calories & Steps
    active_calories: Optional[int] = None
    resting_calories: Optional[int] = None
    steps: Optional[int] = None
    intensity_minutes: Optional[int] = None
    
    # Training & Performance
    training_status: Optional[str] = None
    vo2max_running: Optional[float] = None
    
    # Activities
    all_activity_count: Optional[int] = None
    running_activity_count: Optional[int] = None
    running_distance: Optional[float] = None
    strength_activity_count: Optional[int] = None
    strength_duration: Optional[float] = None
    cardio_activity_count: Optional[int] = None
    cardio_duration: Optional[float] = None
    
    # Aliases for garmin_client compatibility
    avg_stress: Optional[int] = None
    stress_qualifier: Optional[str] = None
    resting_hr: Optional[int] = None
    bmr_calories: Optional[int] = None
    strength_sessions: Optional[int] = 0
    vo2_max: Optional[float] = None
    
    # Extra fields (may not populate but accepted to avoid errors)
    weight: Optional[float] = None
    body_fat: Optional[float] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    vo2max_cycling: Optional[float] = None
    cycling_activity_count: Optional[int] = None
    cycling_distance: Optional[float] = None
    tennis_activity_count: Optional[int] = None
    tennis_activity_duration: Optional[float] = None

# Clean, organized headers for your new sheet
HEADERS = [
    # Date
    "Date",
    # Sleep (3 columns)
    "Sleep Score", "Sleep Hours", "Sleep Feedback",
    # Heart & Recovery (6 columns)
    "HRV", "HRV Status", "Resting HR", "Readiness", "Recovery (h)", "Acute Load",
    # Body Battery & Stress (3 columns)
    "BB High", "BB Low", "Avg Stress",
    # Bio-markers (2 columns)
    "Respiration", "SpO2",
    # Activity & Calories (4 columns)
    "Steps", "Intensity Mins", "Active Cals", "Resting Cals",
    # Training (2 columns)
    "Training Status", "VO2 Max",
    # Activities (7 columns)
    "Total Activities", "Runs", "Run KM", "Strength", "Strength Mins", "Cardio", "Cardio Mins"
]

HEADER_TO_ATTRIBUTE_MAP = {
    # Date
    "Date": "date",
    # Sleep
    "Sleep Score": "sleep_score",
    "Sleep Hours": "sleep_length",
    "Sleep Feedback": "sleep_feedback",
    # Heart & Recovery
    "HRV": "overnight_hrv",
    "HRV Status": "hrv_status",
    "Resting HR": "resting_heart_rate",
    "Readiness": "training_readiness",
    "Recovery (h)": "recovery_time",
    "Acute Load": "acute_load",
    # Body Battery & Stress
    "BB High": "body_battery_high",
    "BB Low": "body_battery_low",
    "Avg Stress": "average_stress",
    # Bio-markers
    "Respiration": "respiration_avg",
    "SpO2": "spo2_avg",
    # Activity & Calories
    "Steps": "steps",
    "Intensity Mins": "intensity_minutes",
    "Active Cals": "active_calories",
    "Resting Cals": "resting_calories",
    # Training
    "Training Status": "training_status",
    "VO2 Max": "vo2max_running",
    # Activities
    "Total Activities": "all_activity_count",
    "Runs": "running_activity_count",
    "Run KM": "running_distance",
    "Strength": "strength_activity_count",
    "Strength Mins": "strength_duration",
    "Cardio": "cardio_activity_count",
    "Cardio Mins": "cardio_duration"
}

TARGET_SHEET_NAME = "Garmin Data"
SHEET_DATE_FORMAT = "%Y-%m-%d"  # Using ISO format for consistency
