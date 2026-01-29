from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class GarminMetrics:
    date: date
    sleep_score: Optional[float] = None
    sleep_length: Optional[float] = None
    overnight_hrv: Optional[int] = None
    hrv_status: Optional[str] = None
    resting_heart_rate: Optional[int] = None
    average_stress: Optional[int] = None
    # --- New Recovery Metrics ---
    body_battery_high: Optional[int] = None
    body_battery_low: Optional[int] = None
    recovery_time: Optional[int] = None
    training_readiness: Optional[int] = None
    # ----------------------------
    active_calories: Optional[int] = None
    resting_calories: Optional[int] = None
    training_status: Optional[str] = None
    vo2max_running: Optional[float] = None
    intensity_minutes: Optional[int] = None
    all_activity_count: Optional[int] = None
    running_activity_count: Optional[int] = None
    running_distance: Optional[float] = None
    steps: Optional[int] = None
    # Accepted but hidden fields
    weight: Optional[float] = None
    body_fat: Optional[float] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    vo2max_cycling: Optional[float] = None
    cycling_activity_count: Optional[int] = None
    cycling_distance: Optional[float] = None
    strength_activity_count: Optional[int] = None
    strength_duration: Optional[float] = None
    cardio_activity_count: Optional[int] = None
    cardio_duration: Optional[float] = None
    tennis_activity_count: Optional[int] = None
    tennis_activity_duration: Optional[float] = None

HEADERS = [
    "Day/Date", "Sleep Score", "Sleep Length", "HRV (ms)", "HRV Status", 
    "Body Battery High", "Body Battery Low", "Recovery Time (h)", "Readiness",
    "Resting Heart Rate", "Average Stress", "Active Calories", "Resting Calories", 
    "Training Status", "VO2 Max", "Running Distance (km)", "Steps"
]

HEADER_TO_ATTRIBUTE_MAP = {
    "Day/Date": "date",
    "Sleep Score": "sleep_score",
    "Sleep Length": "sleep_length",
    "HRV (ms)": "overnight_hrv",
    "HRV Status": "hrv_status",
    "Body Battery High": "body_battery_high",
    "Body Battery Low": "body_battery_low",
    "Recovery Time (h)": "recovery_time",
    "Readiness": "training_readiness",
    "Resting Heart Rate": "resting_heart_rate",
    "Average Stress": "average_stress",
    "Active Calories": "active_calories",
    "Resting Calories": "resting_calories",
    "Training Status": "training_status",
    "VO2 Max": "vo2max_running",
    "Running Distance (km)": "running_distance",
    "Steps": "steps"
}

SHEET_DATE_FORMAT = "%A %B %-d,%Y" 
TARGET_SHEET_NAME = "Garmin_Data"
