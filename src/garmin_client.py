from datetime import date
from typing import Dict, Any, Optional
import asyncio
import logging
import json  # Needed for the raw data dump
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
            logger.info("Successfully authenticated with Garmin Connect.")
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise

    async def get_metrics(self, target_date: date) -> GarminMetrics:
        if not self._authenticated:
            await self.authenticate()

        logger.info(f"--- Starting data fetch for {target_date.isoformat()} ---")

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

        # =========================================================================
        # GITHUB LOG DUMP SECTION
        # =========================================================================
        print(f"\n{'='*30} RAW DATA DUMP FOR {target_date} {'='*30}")
        
        print("\n[DEBUG] RAW STATS (Body Battery/Weight):")
        print(json.dumps(stats, indent=2) if isinstance(stats, dict) else f"Data: {stats}")

        print("\n[DEBUG] RAW USER SUMMARY (Calories/Steps/RHR):")
        print(json.dumps(summary, indent=2) if isinstance(summary, dict) else f"Data: {summary}")

        print("\n[DEBUG] RAW TRAINING STATUS (Recovery):")
        print(json.dumps(training_status, indent=2) if isinstance(training_status, dict) else f"Data: {training_status}")

        print("\n[DEBUG] RAW TRAINING READINESS:")
        print(json.dumps(readiness_data, indent=2) if isinstance(readiness_data, dict) else f"Data: {readiness_data}")
        
        print(f"{'='*80}\n")
        # =========================================================================

        # 1. Process HRV
        overnight_hrv = hrv_payload.get('hrvSummary', {}).get('lastNightAvg') if isinstance(hrv_payload, dict) else None
        hrv_status = hrv_payload.get('hrvSummary', {}).get('status') if isinstance(hrv_payload, dict) else None

        # 2. Process Recovery & Readiness
        recovery_h = None
        if isinstance(training_status, dict):
            # We indent this block correctly now
            ts_data = training_status.get('mostRecentTrainingStatus', {})
            rec_min = ts_data.get('recoveryTime', 0) if ts_data else 0
            if rec_min: 
                recovery_h = round(rec_min / 60)
        
        t_readiness = readiness_data.get('score') if isinstance(readiness_data, dict) else None

        # 3. Process Body Battery
        bb_high = stats.get('bodyBatteryHighestValue') if isinstance(stats, dict) else None
        bb_low = stats.get('bodyBatteryLowestValue') if isinstance(stats, dict) else None

        # 4. Process Activities
        run_dist = 0
        run_count = 0
        if isinstance(activities, list):
            for a in activities:
                type_key = a.get('activityType', {}).get('typeKey', '').lower()
                if 'run' in type_key:
                    run_count += 1
                    run_dist += a.get('distance', 0) / 1000

        # 5. Process Sleep
        s_score = None
        s_len = None
        if isinstance(sleep_data, dict):
            dto = sleep_data.get('dailySleepDTO', {})
            s_score = dto.get('sleepScores', {}).get('overall', {}).get('value')
            s_sec = dto.get('sleepTimeSeconds', 0)
            if s_sec: 
                s_len = s_sec / 3600

        # 6. Extract Status Phrase
        status_phrase = None
        if isinstance(training_status, dict):
            ts_data = training_status.get('mostRecentTrainingStatus', {})
            status_phrase = ts_data.get('trainingStatusFeedbackPhrase') if ts_data else None

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
