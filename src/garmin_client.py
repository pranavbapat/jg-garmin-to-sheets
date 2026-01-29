import os
import asyncio
import garth
import garminconnect
import logging
from .config import GarminMetrics

logger = logging.getLogger(__name__)

class GarminClient:
    # Restored email/password so main.py doesn't crash
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.client = garminconnect.Garmin(email, password)
        self._authenticated = False

    async def authenticate(self):
        """Uses your OAuth secrets to resume the session safely."""
        try:
            oauth1 = os.getenv("GARMIN_OAUTH1_TOKEN")
            oauth2 = os.getenv("GARMIN_OAUTH2_TOKEN")

            if oauth1 and oauth2:
                # Inject existing tokens into garth
                garth.client.oauth1_token = oauth1
                garth.client.oauth2_token = oauth2
                self.client.garth = garth.client
                self._authenticated = True
                logger.info("✅ Session resumed using OAuth tokens.")
            else:
                # Fallback to login if tokens are missing (might trigger MFA)
                await asyncio.get_event_loop().run_in_executor(
                    None, self.client.login
                )
                self._authenticated = True
                logger.info("✅ Logged in with email/password.")
        except Exception as e:
            logger.error(f"❌ Auth failed: {e}")
            raise

    async def get_metrics(self, target_date):
        if not self._authenticated:
            await self.authenticate()

        # Run all data fetches in parallel for speed
        tasks = [
            asyncio.get_event_loop().run_in_executor(None, self.client.get_user_summary, target_date.isoformat()),
            asyncio.get_event_loop().run_in_executor(None, self.client.get_training_readiness, target_date.isoformat()),
            asyncio.get_event_loop().run_in_executor(None, self.client.get_training_status, target_date.isoformat()),
            asyncio.get_event_loop().run_in_executor(None, self.client.get_sleep_data, target_date.isoformat()),
            asyncio.get_event_loop().run_in_executor(None, self.client.get_hrv_data, target_date.isoformat()),
            asyncio.get_event_loop().run_in_executor(None, self.client.get_activities_by_date, target_date.isoformat(), target_date.isoformat())
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        summary, readiness, status, sleep, hrv, activities = results

        # Activity Logic: Only Runs and Strength
        run_dist = 0
        strength_count = 0
        if isinstance(activities, list):
            for act in activities:
                type_key = act.get('activityType', {}).get('typeKey', '').lower()
                if 'run' in type_key and 'cycling' not in type_key:
                    run_dist += act.get('distance', 0) / 1000
                if 'strength' in type_key:
                    strength_count += 1

        # Readiness Parsing
        ready_data = readiness[-1] if isinstance(readiness, list) and readiness else {}

        return GarminMetrics(
            date=target_date,
            training_readiness=ready_data.get('score'),
            readiness_feedback=ready_data.get('feedbackShort'),
            recovery_time=round(ready_data.get('recoveryTime', 0) / 60, 1),
            acute_load=ready_data.get('acuteLoad'),
            acwr_status=ready_data.get('acwrFactorFeedback'),
            body_battery_high=summary.get('bodyBatteryHighestValue'),
            body_battery_low=summary.get('bodyBatteryLowestValue'),
            avg_stress=summary.get('averageStressLevel'),
            stress_qualifier=summary.get('stressQualifier'),
            sleep_score=ready_data.get('sleepScore'),
            sleep_feedback=ready_data.get('sleepScoreFactorFeedback'),
            overnight_hrv=hrv.get('hrvSummary', {}).get('lastNightAvg') if isinstance(hrv, dict) else None,
            resting_hr=summary.get('restingHeartRate'),
            respiration_avg=summary.get('avgWakingRespirationValue'),
            spo2_avg=summary.get('averageSpo2'),
            active_calories=summary.get('activeKilocalories'),
            bmr_calories=summary.get('bmrKilocalories'),
            steps=summary.get('totalSteps'),
            running_distance=round(run_dist, 2),
            strength_sessions=strength_count,
            vo2_max=status.get('mostRecentVO2Max', {}).get('generic', {}).get('vo2MaxValue') if isinstance(status, dict) else None
        )
