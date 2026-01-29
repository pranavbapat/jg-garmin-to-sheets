import os
import asyncio
import garth
import garminconnect
import logging
from .config import GarminMetrics

logger = logging.getLogger(__name__)

class GarminClient:
    def __init__(self):
        self.client = None
        self._authenticated = False

    async def authenticate(self):
        """Uses OAuth secrets to resume a session without MFA."""
        try:
            # 1. Grab tokens from your GitHub Secrets
            oauth1 = os.getenv("GARMIN_OAUTH1_TOKEN")
            oauth2 = os.getenv("GARMIN_OAUTH2_TOKEN")

            if not oauth1 or not oauth2:
                raise ValueError("Missing OAuth tokens in GitHub Secrets!")

            # 2. Inject tokens into Garth
            garth.client.oauth1_token = oauth1
            garth.client.oauth2_token = oauth2
            
            # 3. Initialize the Garmin Connect client using the resumed Garth session
            self.client = garminconnect.Garmin()
            self.client.garth = garth.client
            
            self._authenticated = True
            logger.info("Successfully resumed Garmin session using OAuth tokens.")
        except Exception as e:
            logger.error(f"Failed to resume session: {e}")
            raise

    async def get_metrics(self, target_date):
        if not self._authenticated:
            await self.authenticate()
        
        # ... (Rest of the get_metrics data extraction code stays the same) ...
