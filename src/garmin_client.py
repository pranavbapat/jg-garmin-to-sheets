from datetime import date
from typing import Dict, Any, Optional
import asyncio
import logging
import json  # Added for raw data dumping
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
        # These prints will show up in your GitHub Actions 'Run sync' step logs
        # =========================================================================
        print(f"\n{'='*30} RAW DATA DUMP FOR {target_date} {'='*30}")
        
        print("\n[DEBUG] RAW STATS & BODY (Weight, Body Battery, etc.):")
        print(json.dumps(stats, indent=2) if isinstance(stats, dict) else f"Error/None: {stats}")

        print("\n[DEBUG] RAW USER SUMMARY (Calories, Steps, RHR, Stress):")
        print(json.dumps(summary, indent=2) if isinstance(summary, dict) else f"Error/None: {summary}")

        print("\n[DEBUG] RAW TRAINING STATUS (Recovery Time, VO2 Max):")
        print(json.dumps(training_status, indent=2) if isinstance(training_status, dict) else f"Error/None: {training_status}")

        print("\n[DEBUG] RAW TRAINING READINESS:")
        print(json.dumps(readiness_data, indent=2) if isinstance(readiness_data, dict) else f"Error/None: {readiness_data}")
        
        print(f"{'='*80}\n")
        # =========================================================================

        # 1. Process HRV
        overnight_hrv = hrv_payload.get('hrvSummary', {}).get('lastNightAvg') if isinstance(hrv_payload, dict) else None
        hrv_status = hrv_payload.get('hrvSummary', {}).get('status') if isinstance(hrv_payload, dict) else None

        # 2. Process Recovery & Readiness
        recovery_h = None
        if isinstance(training_status, dict):
