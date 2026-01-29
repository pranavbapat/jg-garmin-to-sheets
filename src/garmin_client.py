from datetime import date
from typing import Dict, Any, Optional
import asyncio
import logging
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
            await asyncio.get_event_loop().run_in_executor(None, self.client.login)
            self._authenticated = True
        except Exception as e:
            logger.error(f"Auth failed: {e}")
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
            # Fetching Training Readiness (Newer Garmin devices)
            asyncio.get_event_loop().run_in_executor(None, self.client.get_training_readiness, target_date.isoformat())
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        stats, sleep_data, activities, summary, training_status, hrv_payload, readiness_data = results

        # 1. Process HRV
        overnight_hrv = hrv_payload.get('hrvSummary', {}).get('lastNightAvg') if isinstance(hrv_payload, dict) else None
        hrv_status = hrv_payload.get('hrvSummary', {}).get('status') if isinstance(hrv_payload, dict) else None

        # 2. Process Recovery & Readiness
        recovery_h = None
        if isinstance(training_status, dict):
            # Garmin stores recovery minutes in mostRecentTrainingStatus
            rec_min = training_status.get('mostRecentTrainingStatus', {}).get('recoveryTime', 0)
            if rec_min: recovery_h = round(rec_min / 60)
        
        t_readiness = readiness_data.get('score') if isinstance(readiness_data, dict) else None

        # 3. Process Body Battery (From Stats)
        bb_high = stats.get('bodyBatteryHighestValue') if isinstance(stats, dict) else None
        bb_low = stats.get('bodyBatteryLowestValue') if isinstance(stats, dict) else None

        # 4. Process Activities
        run_dist = 0
        run_count = 0
        if isinstance(activities, list):
            for a in activities:
                if a.get('activityType', {}).get('typeKey') == 'running':
                    run_count += 1
                    run_dist += a.get('distance', 0) / 1000

        # 5. Process Sleep
        s_score = None
        s_len = None
        if isinstance(sleep_data, dict):
            dto = sleep_data.get('dailySleepDTO', {})
            s_score = dto.get('sleepScores', {}).get('overall', {}).get('value')
            s_sec = dto.get('sleepTimeSeconds', 0)
            if s_sec: s_len = s_sec / 3600

        return GarminMetrics(
            date=target_date,
            sleep_score=s_score,
            sleep_length=s_len,
            overnight_hrv=overnight_hrv,
            hrv_status=hrv_status,
            body_battery_high=bb_high,
            body_battery_low=bb_low,
            recovery_time=recovery_h,
            training_readiness=t_readiness,
            resting_heart_rate=summary.get('restingHeartRate') if isinstance(summary, dict) else None,
            average_stress=summary.get('averageStressLevel') if isinstance(summary, dict) else None,
            active_calories=summary.get('activeKilocalories') if isinstance(summary, dict) else None,
            resting_calories=summary.get('bmrKilocalories') if isinstance(summary, dict) else None,
            steps=summary.get('totalSteps') if isinstance(summary, dict) else None,
            running_distance=run_dist,
            running_activity_count=run_count,
            all_activity_count=len(activities) if isinstance(activities, list) else 0
        )
