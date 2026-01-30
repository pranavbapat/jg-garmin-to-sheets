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
        self._profile_loaded = False

    async def authenticate(self):
        try:
            await asyncio.get_event_loop().run_in_executor(None, self.client.login)
            self._authenticated = True
            logger.info("✅ Garmin Auth Successful")
        except Exception as e:
            logger.error(f"❌ Auth failed: {e}")
            raise

    async def _ensure_profile_loaded(self):
        """Ensure user profile is loaded - critical for API calls to work"""
        if self._profile_loaded:
            return
            
        try:
            # Check if profile data exists
            if hasattr(self.client, 'garth') and self.client.garth:
                # Try to access profile - this triggers a fetch if not cached
                profile_data = self.client.garth.profile
                
                if profile_data:
                    self.client.display_name = profile_data.get("displayName")
                    self.client.full_name = profile_data.get("fullName") 
                    self.client.unit_system = profile_data.get("measurementSystem")
                    logger.info(f"✅ Profile loaded: {self.client.display_name}")
                    self._profile_loaded = True
                    return
                    
            # Fallback: try to get full name which also loads profile
            if not self._profile_loaded:
                logger.info("Attempting to load profile via get_full_name()...")
                await asyncio.get_event_loop().run_in_executor(None, self.client.get_full_name)
                self._profile_loaded = True
                logger.info("✅ Profile loaded via get_full_name()")
                
        except Exception as e:
            logger.error(f"⚠️  Profile load failed: {e}")
            # Don't raise - let the API calls fail with better error messages

    async def get_metrics(self, target_date: date) -> GarminMetrics:
        if not self._authenticated:
            await self.authenticate()
        
        # CRITICAL: Always ensure profile is loaded before making API calls
        await self._ensure_profile_loaded()

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

        # Log errors
        result_names = ['stats', 'sleep_data', 'activities', 'summary', 'training_status', 'hrv_payload', 'readiness_data']
        for result, name in zip(results, result_names):
            if isinstance(result, Exception):
                logger.error(f"❌ Error fetching {name} for {target_date}: {result}")

        # 1. Process HRV
        overnight_hrv = None
        hrv_status = None
        if hrv_payload and isinstance(hrv_payload, dict):
            hrv_summary = hrv_payload.get('hrvSummary')
            if hrv_summary:
                overnight_hrv = hrv_summary.get('lastNightAvg')
                hrv_status = hrv_summary.get('status')

        # 2. Process Readiness & Acute Load
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

        # 4. Process Body Battery & Bio-markers (from stats)
        bb_high = None
        bb_low = None
        resp_avg = None
        spo2 = None
        weight = None
        body_fat = None
        
        if stats and isinstance(stats, dict):
            bb_high = stats.get('bodyBatteryHighestValue')
            bb_low = stats.get('bodyBatteryLowestValue')
            resp_avg = stats.get('avgWakingRespirationValue')
            spo2 = stats.get('avgSpo2Value')
            weight_grams = stats.get('weight')
            weight = weight_grams / 1000 if weight_grams else None
            body_fat = stats.get('bodyFat')

        # 5. Process Activities
        run_dist = 0
        run_count = 0
        strength_count = 0
        strength_dur = 0
        cardio_count = 0
        cardio_dur = 0
        all_count = 0
        
        if activities and isinstance(activities, list):
            all_count = len(activities)
            for activity in activities:
                activity_type = activity.get('activityType', {})
                type_key = activity_type.get('typeKey', '').lower()
                parent_type_id = activity_type.get('parentTypeId')
                duration = activity.get('duration', 0) / 60  # Convert seconds to minutes
                
                if 'run' in type_key or parent_type_id == 1:  # 1 is running
                    run_count += 1
                    run_dist += activity.get('distance', 0) / 1000  # Convert to km
                elif 'strength' in type_key:
                    strength_count += 1
                    strength_dur += duration
                elif 'cardio' in type_key:
                    cardio_count += 1
                    cardio_dur += duration

        # 6. Process Sleep
        s_score = None
        s_length = None
        if sleep_data and isinstance(sleep_data, dict):
            sleep_dto = sleep_data.get('dailySleepDTO', {})
            if sleep_dto:
                s_score = sleep_dto.get('sleepScores', {}).get('overall', {}).get('value')
                sleep_time_seconds = sleep_dto.get('sleepTimeSeconds')
                if sleep_time_seconds is not None and sleep_time_seconds > 0:
                    s_length = round(sleep_time_seconds / 3600, 2)  # Convert to hours

        # 7. Get summary metrics (Steps, Calories, HR, Stress, Intensity)
        active_cals = None
        resting_cals = None
        intensity_mins = None
        resting_hr = None
        avg_stress = None
        steps = None
        
        if summary and isinstance(summary, dict):
            active_cals = summary.get('activeKilocalories')
            resting_cals = summary.get('bmrKilocalories')
            moderate = summary.get('moderateIntensityMinutes', 0) or 0
            vigorous = summary.get('vigorousIntensityMinutes', 0) or 0
            intensity_mins = moderate + (2 * vigorous)
            resting_hr = summary.get('restingHeartRate')
            avg_stress = summary.get('averageStressLevel')
            steps = summary.get('totalSteps')
        else:
            # Fallback to stats if summary failed
            if stats and isinstance(stats, dict):
                resting_hr = stats.get('restingHeartRate')
                avg_stress = stats.get('averageStressLevel')

        # 8. Get VO2 Max and training status
        vo2_running = None
        train_status_text = None
        
        if training_status and isinstance(training_status, dict):
            most_recent_vo2max = training_status.get('mostRecentVO2Max')
            if most_recent_vo2max:
                generic_vo2max = most_recent_vo2max.get('generic')
                if generic_vo2max:
                    vo2_running = generic_vo2max.get('vo2MaxValue')

            most_recent_training_status = training_status.get('mostRecentTrainingStatus')
            if most_recent_training_status:
                latest_training_status_data = most_recent_training_status.get('latestTrainingStatusData')
                if latest_training_status_data:
                    for device_data in latest_training_status_data.values():
                        train_status_text = device_data.get('trainingStatusFeedbackPhrase')
                        break

        return GarminMetrics(
            date=target_date,
            sleep_score=s_score,
            sleep_length=s_length,
            sleep_feedback=sleep_feedback,
            overnight_hrv=overnight_hrv,
            hrv_status=hrv_status,
            resting_heart_rate=resting_hr,
            resting_hr=resting_hr,
            training_readiness=t_readiness,
            readiness_feedback=ready_phrase,
            recovery_time=recovery_h,
            acute_load=acute_load,
            acwr_status=acwr_status,
            body_battery_high=bb_high,
            body_battery_low=bb_low,
            average_stress=avg_stress,
            avg_stress=avg_stress,
            stress_qualifier=None,
            respiration_avg=resp_avg,
            spo2_avg=spo2,
            active_calories=active_cals,
            resting_calories=resting_cals,
            bmr_calories=resting_cals,
            steps=steps,
            intensity_minutes=intensity_mins,
            training_status=train_status_text,
            vo2max_running=vo2_running,
            vo2_max=vo2_running,
            all_activity_count=all_count,
            running_activity_count=run_count,
            running_distance=round(run_dist, 2) if run_dist else None,
            strength_activity_count=strength_count,
            strength_sessions=strength_count,
            strength_duration=round(strength_dur, 1) if strength_dur else None,
            cardio_activity_count=cardio_count,
            cardio_duration=round(cardio_dur, 1) if cardio_dur else None,
            weight=weight,
            body_fat=body_fat,
            blood_pressure_systolic=None,
            blood_pressure_diastolic=None,
            vo2max_cycling=None,
            cycling_activity_count=None,
            cycling_distance=None,
            tennis_activity_count=None,
            tennis_activity_duration=None
        )
