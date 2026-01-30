import os
import asyncio
import logging
from datetime import date
from typing import Dict, Any, Optional
import garminconnect
import garth
from .config import GarminMetrics

logger = logging.getLogger(__name__)

class GarminClient:
    def __init__(self, email: str, password: str):
        self.client = garminconnect.Garmin(email, password)
        self._authenticated = False

    async def authenticate(self):
        try:
            # Reverting to your working auth logic
            await asyncio.get_event_loop().run_in_executor(None, self.client.login)
            self._authenticated = True
            logger.info("✅ Garmin Auth Successful")
        except Exception as e:
            logger.error(f"❌ Auth failed: {e}")
            raise

    async def get_metrics(self, target_date: date) -> GarminMetrics:
        if not self._authenticated:
            await self.authenticate()

        # Define data fetching tasks
        tasks = [
            asyncio.get_event_loop().run_in_executor(None, self.client.get_stats_and_body, target_date.isoformat()),
            asyncio.get_event_loop().run_in_executor(None, self.client.get_sleep_data, target_date.isoformat()),
            asyncio.get_event_loop().run_in_executor(None, self.client.get_activities_by_date, target_date.isoformat(), target_date.isoformat()),
            asyncio.get_event_loop().run_in_executor(None, self.client.get_user_summary, target_date.isoformat()),
            asyncio.get_event_loop().run_in_executor(None, self.client.get_training_status, target_date.isoformat()),
            asyncio.get_event_loop().run_in_executor(None, self.client.get_hrv_data, target_date.isoformat()),
            asyncio.get_event_loop().run_in_executor(None, self.client.get_training_readiness, target_date.isoformat())
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        stats, sleep_data, activities, summary, training_status, hrv_payload, readiness_data = results

        # 1. Process HRV
        overnight_hrv = hrv_payload.get('hrvSummary', {}).get('lastNightAvg') if isinstance(hrv_payload, dict) else None
        hrv_status = hrv_payload.get('hrvSummary', {}).get('status') if isinstance(hrv_payload, dict) else None

        # 2. Process Readiness & Acute Load (Handles the list format from Forerunner 970 logs)
        t_readiness = None
        ready_phrase = None
        acute_load = None
        acwr_status = None
        sleep_feedback = None
        
        if isinstance(readiness_data, list) and len(readiness_data) > 0:
            latest = readiness_data[-1]
            t_readiness = latest.get('score')
            ready_phrase = latest.get('feedbackShort')
            acute_load = latest.get('acuteLoad')
            acwr_status = latest.get('acwrFactorFeedback')
            sleep_feedback = latest.get('sleepScoreFactorFeedback')

        # 3. Process Recovery (Conversion to Hours)
        recovery_h = None
        if isinstance(training_status, dict):
            rec_min = training_status.get('most_recent_training_status', {}).get('recoveryTime', 0)
            if not rec_min and isinstance(readiness_data, list):
                rec_min = readiness_data[-1].get('recoveryTime', 0)
            if rec_min: recovery_h = round(rec_min / 60, 1)

        # 4. Process Body Battery & Respiration
        bb_high = summary.get('bodyBatteryHighestValue') if isinstance(summary, dict) else None
        bb_low = summary.get('bodyBatteryLowestValue') if isinstance(summary, dict) else None
        resp_avg = summary.get('avgWakingRespirationValue') if isinstance(summary, dict) else None

        # 5. Process Activities - Count all types separately
        run_dist = 0
        run_count = 0
        strength_count = 0
        strength_dur = 0
        cardio_count = 0
        cardio_dur = 0
        cycling_count = 0
        cycling_dist = 0
        tennis_count = 0
        tennis_dur = 0
        all_count = 0
        
        if isinstance(activities, list):
            all_count = len(activities)
            for a in activities:
                type_key = a.get('activityType', {}).get('typeKey', '').lower()
                duration = a.get('duration', 0) / 60  # Convert to minutes
                
                if 'run' in type_key and 'cycling' not in type_key:
                    run_dist += a.get('distance', 0) / 1000
                    run_count += 1
                elif 'strength' in type_key or 'training' in type_key:
                    strength_count += 1
                    strength_dur += duration
                elif 'cardio' in type_key or 'fitness' in type_key:
                    cardio_count += 1
                    cardio_dur += duration
                elif 'cycling' in type_key:
                    cycling_count += 1
                    cycling_dist += a.get('distance', 0) / 1000
                elif 'tennis' in type_key:
                    tennis_count += 1
                    tennis_dur += duration

        # 6. Process Sleep
        s_score = None
        s_length = None
        if isinstance(sleep_data, dict):
            s_score = sleep_data.get('dailySleepDTO', {}).get('sleepScores', {}).get('overall', {}).get('value')
            sleep_seconds = sleep_data.get('dailySleepDTO', {}).get('sleepTimeSeconds', 0)
            if sleep_seconds:
                s_length = round(sleep_seconds / 3600, 2)  # Convert to hours

        # 7. Get Training Status text
        train_status_text = None
        if isinstance(training_status, dict):
            train_status_text = training_status.get('trainingStatusKey')

        # 8. Get VO2 Max
        vo2 = None
        if isinstance(training_status, dict):
            vo2 = training_status.get('mostRecentVO2Max', {}).get('generic', {}).get('vo2MaxValue')

        # 9. Get Intensity Minutes and other summary data
        intensity_mins = summary.get('intensityMinutesGoal') if isinstance(summary, dict) else None
        resting_hr = summary.get('restingHeartRate') if isinstance(summary, dict) else None
        avg_stress = summary.get('averageStressLevel') if isinstance(summary, dict) else None
        active_cals = summary.get('activeKilocalories') if isinstance(summary, dict) else None
        bmr_cals = summary.get('bmrKilocalories') if isinstance(summary, dict) else None
        steps = summary.get('totalSteps') if isinstance(summary, dict) else None

        # 10. Get Body Stats (may not be available)
        weight = stats.get('weight') if isinstance(stats, dict) else None
        body_fat = stats.get('bodyFat') if isinstance(stats, dict) else None

        # 11. Get SpO2
        spo2 = summary.get('avgSpo2Value') if isinstance(summary, dict) else None

        return GarminMetrics(
            date=target_date,
            # Readiness & Recovery
            training_readiness=t_readiness,
            readiness_feedback=ready_phrase,
            recovery_time=recovery_h,
            acute_load=acute_load,
            acwr_status=acwr_status,
            # Body Battery & Stress
            body_battery_high=bb_high,
            body_battery_low=bb_low,
            avg_stress=avg_stress,
            average_stress=avg_stress,  # Alias
            stress_qualifier=None,  # Not available in current API
            # Sleep
            sleep_score=s_score,
            sleep_feedback=sleep_feedback,
            sleep_length=s_length,
            # Bio-markers
            overnight_hrv=overnight_hrv,
            hrv_status=hrv_status,
            resting_hr=resting_hr,
            resting_heart_rate=resting_hr,  # Alias
            respiration_avg=resp_avg,
            spo2_avg=spo2,
            # Calories & Activity
            active_calories=active_cals,
            bmr_calories=bmr_cals,
            resting_calories=bmr_cals,  # Alias (BMR is resting)
            steps=steps,
            intensity_minutes=intensity_mins,
            # Activities
            all_activity_count=all_count,
            running_activity_count=run_count,
            running_distance=round(run_dist, 2) if run_dist else None,
            strength_sessions=strength_count,
            strength_activity_count=strength_count,  # Alias
            strength_duration=round(strength_dur, 1) if strength_dur else None,
            cardio_activity_count=cardio_count,
            cardio_duration=round(cardio_dur, 1) if cardio_dur else None,
            # Training
            training_status=train_status_text,
            vo2_max=vo2,
            vo2max_running=vo2,  # Alias
            # Body Metrics
            weight=weight,
            body_fat=body_fat,
            # Cycling & Tennis
            cycling_activity_count=cycling_count,
            cycling_distance=round(cycling_dist, 2) if cycling_dist else None,
            tennis_activity_count=tennis_count,
            tennis_activity_duration=round(tennis_dur, 1) if tennis_dur else None
        )
