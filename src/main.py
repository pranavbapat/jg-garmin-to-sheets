import os
import sys
import asyncio
import logging
import garth
from datetime import date, timedelta
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

from src.garmin_client import GarminClient
from src.sheets_client import GoogleSheetsClient

# Logging config
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    # Load .env variables
    env_file_path = find_dotenv(usecwd=True)
    if env_file_path:
        load_dotenv(dotenv_path=env_file_path)
    
    # Target Profile: USER1
    profile_name = "USER1"
    email = os.getenv(f"{profile_name}_GARMIN_EMAIL")
    password = os.getenv(f"{profile_name}_GARMIN_PASSWORD")
    sheet_id = os.getenv(f"{profile_name}_SHEET_ID")
    sheet_name = os.getenv(f"{profile_name}_SHEET_NAME", "Raw Data")
    
    # Setup garth token directory
    token_dir = Path(f"./credentials/garmin_tokens_{profile_name}")
    os.environ["GARTH_HOME"] = str(token_dir)

    # 1. Authenticate / Resume
    garmin_client = None
    try:
        logger.info(f"Resuming Garmin session from {token_dir}")
        garth.resume(str(token_dir))
        garmin_client = GarminClient(email, password)
        garmin_client.client.garth = garth.client
        
        # CRITICAL FIX: Load profile data after resuming
        if not garmin_client.client.display_name:
            profile = garth.client.profile
            garmin_client.client.display_name = profile.get("displayName")
            garmin_client.client.full_name = profile.get("fullName")
            garmin_client.client.unit_system = profile.get("measurementSystem")
            logger.info(f"✅ Profile loaded: {garmin_client.client.display_name}")
        
        garmin_client._authenticated = True
    except Exception as e:
        logger.error(f"Could not resume: {e}. Run a fresh login if tokens expired.")
        return

    # 2. Backfill Range: Jan 16, 2026 to Today
    start_date = date(2026, 1, 16)
    end_date = date.today()
    
    logger.info(f"🚀 STARTING BACKFILL: {start_date} to {end_date}")
    
    metrics_to_write = []
    current_date = start_date
    while current_date <= end_date:
        try:
            logger.info(f"Fetching {current_date.isoformat()}...")
            daily_metrics = await garmin_client.get_metrics(current_date)
            metrics_to_write.append(daily_metrics)
            # 1-second pause to be kind to the API
            await asyncio.sleep(1) 
        except Exception as e:
            logger.error(f"Failed to fetch {current_date}: {e}")
        current_date += timedelta(days=1)

    # 3. Push all data to Google Sheets
    if metrics_to_write:
        try:
            sheets_client = GoogleSheetsClient(
                credentials_path='credentials/client_secret.json',
                spreadsheet_id=sheet_id,
                sheet_name=sheet_name
            )
            sheets_client.update_metrics(metrics_to_write)
            logger.info(f"✅ Backfill successful! {len(metrics_to_write)} days synced.")
        except Exception as e:
            logger.error(f"Sheets update failed: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
