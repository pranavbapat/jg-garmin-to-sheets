from dataclasses import dataclass
from datetime import date
from typing import Optional

# 1. The Dataclass - Focused strictly on Bio-metrics and Running
@dataclass
class GarminMetrics:
    date: date
    sleep_score: Optional[float] = None
    sleep_length: Optional[float] = None
    overnight_hrv: Optional[int] = None
    hrv_status: Optional[str] = None
    resting_heart_rate: Optional[int] = None
    average_stress: Optional[int] = None
    active_calories: Optional[int] = None
    resting_calories: Optional[int] = None
    training_status: Optional[str] = None
    vo2max_running: Optional[float] = None
    intensity_minutes: Optional[int] = None
    all_activity_count: Optional[int] = None
    running_activity_count: Optional[int] = None
    running_distance: Optional[float] = None
    strength_activity_count: Optional[int] = None
    strength_duration: Optional[float] = None
    cardio_activity_count: Optional[int] = None
    cardio_duration: Optional[float] = None
    steps: Optional[int] = None

# 2. Final Headers for your "Garmin_Data" Sheet
HEADERS = [
    "Day/Date", "Sleep Score", "Sleep Length", "HRV (ms)", "HRV Status", 
    "Resting Heart Rate", "Average Stress", "Active Calories", "Resting Calories", 
    "Training Status", "VO2 Max Running", "Intensity Minutes", 
    "All Activity Count", "Running Activity Count", "Running Distance (km)", 
    "Strength Activity Count", "Strength Duration", "Cardio Activity Count", 
    "Cardio Duration", "Steps"
]

# 3. Final Attribute Mapping
HEADER_TO_ATTRIBUTE_MAP = {
    "Day/Date": "date",
    "Sleep Score": "sleep_score",
    "Sleep Length": "sleep_length",
    "HRV (ms)": "overnight_hrv",
    "HRV Status": "hrv_status",
    "Resting Heart Rate": "resting_heart_rate",
    "Average Stress": "average_stress",
    "Active Calories": "active_calories",
    "Resting Calories": "resting_calories",
    "Training Status": "training_status",
    "VO2 Max Running": "vo2max_running",
    "Intensity Minutes": "intensity_minutes",
    "All Activity Count": "all_activity_count",
    "Running Activity Count": "running_activity_count",
    "Running Distance (km)": "running_distance",
    "Strength Activity Count": "strength_activity_count",
    "Strength Duration": "strength_duration",
    "Cardio Activity Count": "cardio_activity_count",
    "Cardio Duration": "cardio_duration",
    "Steps": "steps"
}

# 4. Sheet Settings
SHEET_DATE_FORMAT = "%A %B %-d,%Y" 
TARGET_SHEET_NAME = "Garmin_Data"
