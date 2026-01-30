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
        overnight_hrv = None
        hrv_status = None
        if hrv_payload:
            hrv_summary = hrv_payload.get('hrvSummary')
            if hrv_summary:
                overnight_hrv = hrv_summary.get('lastNightAvg')
                hrv_status = hrv_summary.get('status')

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
            if not rec_min and isinstance(readiness_data, list) and len(readiness_data) > 0:
                rec_min = readiness_data[-1].get('recoveryTime', 0)
            if rec_min: 
                recovery_h = round(rec_min / 60, 1)

        # 4. Process Body Battery (from stats, not summary)
        bb_high = None
        bb_low = None
        if stats:
            bb_high = stats.get('bodyBatteryHighestValue')
            bb_low = stats.get('bodyBatteryLowestValue')

        # 5. Process Respiration (from stats)
        resp_avg = None
        if stats:
            resp_avg = stats.get('avgWakingRespirationValue')

        # 6. Process Activities - Count all types separately
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
        
        if activities:
            all_count = len(activities)
            for activity in activities:
                activity_type = activity.get('activityType', {})
                type_key = activity_type.get('typeKey', '').lower()
                parent_type_id = activity_type.get('parentTypeId')
                duration = activity.get('duration', 0) / 60  # Convert seconds to minutes
                
                if 'run' in type_key or parent_type_id == 1:  # 1 is running
                    run_count += 1
                    run_dist += activity.get('distance', 0) / 1000  # Convert to km
                elif 'virtual_ride' in type_key or 'cycling' in type_key or parent_type_id == 2:  # 2 is cycling
                    cycling_count += 1
                    cycling_dist += activity.get('distance', 0) / 1000
                elif 'strength' in type_key:
                    strength_count += 1
                    strength_dur += duration
                elif 'cardio' in type_key:
                    cardio_count += 1
                    cardio_dur += duration
                elif 'tennis' in type_key:
                    tennis_count += 1
                    tennis_dur += duration

        # 7. Process Sleep
        s_score = None
        s_length = None
        if sleep_data:
            sleep_dto = sleep_data.get('dailySleepDTO', {})
            if sleep_dto:
                s_score = sleep_dto.get('sleepScores', {}).get('overall', {}).get('value')
                sleep_time_seconds = sleep_dto.get('sleepTimeSeconds')
                if sleep_time_seconds is not None and sleep_time_seconds > 0:
                    s_length = round(sleep_time_seconds / 3600, 2)  # Convert to hours

        # 8. Get summary metrics (THIS IS WHERE THE MISSING FIELDS COME FROM!)
        active_cals = None
        resting_cals = None
        intensity_mins = None
        resting_hr = None
        avg_stress = None
        steps = None
        
        if summary:
            active_cals = summary.get('activeKilocalories')
            resting_cals = summary.get('bmrKilocalories')
            # Intensity minutes calculation from old code
            moderate = summary.get('moderateIntensityMinutes', 0) or 0
            vigorous = summary.get('vigorousIntensityMinutes', 0) or 0
            intensity_mins = moderate + (2 * vigorous)
            resting_hr = summary.get('restingHeartRate')
            avg_stress = summary.get('averageStressLevel')
            steps = summary.get('totalSteps')

        # 9. Get VO2 Max values and training status
        vo2_running = None
        vo2_cycling = None
        train_status_text = None
        
        if training_status:
            most_recent_vo2max = training_status.get('mostRecentVO2Max')
            if most_recent_vo2max:
                generic_vo2max = most_recent_vo2max.get('generic')
                if generic_vo2max:
                    vo2_running = generic_vo2max.get('vo2MaxValue')
                
                cycling_vo2max = most_recent_vo2max.get('cycling')
                if cycling_vo2max:
                    vo2_cycling = cycling_vo2max.get('vo2MaxValue')

            # Get training status phrase
            most_recent_training_status = training_status.get('mostRecentTrainingStatus')
            if most_recent_training_status:
                latest_training_status_data = most_recent_training_status.get('latestTrainingStatusData')
                if latest_training_status_data:
                    # Get the first device's training status
                    for device_data in latest_training_status_data.values():
                        train_status_text = device_data.get('trainingStatusFeedbackPhrase')
                        break

        # 10. Get Body Stats from stats (weight in grams, convert to kg)
        weight = None
        body_fat = None
        if stats:
            weight_grams = stats.get('weight')
            weight = weight_grams / 1000 if weight_grams else None
            body_fat = stats.get('bodyFat')

        # 11. Get SpO2 (from stats)
        spo2 = None
        if stats:
            spo2 = stats.get('avgSpo2Value')

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
            bmr_calories=resting_cals,
            resting_calories=resting_cals,  # Alias (BMR is resting)
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
            vo2_max=vo2_running,
            vo2max_running=vo2_running,  # Alias
            # Body Metrics
            weight=weight,
            body_fat=body_fat,
            # Cycling & Tennis
            vo2max_cycling=vo2_cycling,
            cycling_activity_count=cycling_count,
            cycling_distance=round(cycling_dist, 2) if cycling_dist else None,
            tennis_activity_count=tennis_count,
            tennis_activity_duration=round(tennis_dur, 1) if tennis_dur else None
        )
