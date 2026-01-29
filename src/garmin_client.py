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

        # 5. Process Activities (Filters for Running and Strength, Ignores Tennis/Cycling)
        run_dist = 0
        strength_count = 0
        if isinstance(activities, list):
            for a in activities:
                type_key = a.get('activityType', {}).get('typeKey', '').lower()
                if 'run' in type_key and 'cycling' not in type_key:
                    run_dist += a.get('distance', 0) / 1000
                elif 'strength' in type_key:
                    strength_count += 1

        # 6. Process Sleep
        s_score = None
        if isinstance(sleep_data, dict):
            s_score = sleep_data.get('dailySleepDTO', {}).get('sleepScores', {}).get('overall', {}).get('value')

        return GarminMetrics(
            date=target_date,
            training_readiness=t_readiness,
            readiness_feedback=ready_phrase,
            recovery_time=recovery_h,
            acute_load=acute_load,
            acwr_status=acwr_status,
            body_battery_high=bb_high,
            body_battery_low=bb_low,
            avg_stress=summary.get('averageStressLevel') if isinstance(summary, dict) else None,
            sleep_score=s_score,
            sleep_feedback=sleep_feedback,
            overnight_hrv=overnight_hrv,
            resting_hr=summary.get('restingHeartRate') if isinstance(summary, dict) else None,
            respiration_avg=resp_avg,
            active_calories=summary.get('activeKilocalories') if isinstance(summary, dict) else None,
            bmr_calories=summary.get('bmrKilocalories') if isinstance(summary, dict) else None,
            steps=summary.get('totalSteps') if isinstance(summary, dict) else None,
            running_distance=round(run_dist, 2),
            strength_sessions=strength_count,
            vo2_max=training_status.get('mostRecentVO2Max', {}).get('generic', {}).get('vo2MaxValue') if isinstance(training_status, dict) else None
        )
