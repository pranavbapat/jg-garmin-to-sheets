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

# Logging config matches your style
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
    
    if not email or not password:
        logger.error(f"Credentials not found for {profile_name}")
        return

    # Setup garth token directory (Same logic as your original)
    token_dir = Path(f"./credentials/garmin_tokens_{profile_name}")
    token_dir.mkdir(parents=True, exist_ok=True)
    os.environ["GARTH_HOME"] = str(token_dir)

    # Authentication Flow
    garmin_client = None
    try:
        logger.info(f"Attempting to resume Garmin session from {token_dir}")
        garth.resume(str(token_dir))
        garmin_client = GarminClient(email, password)
        garmin_client.client.garth = garth.client
        garmin_client._authenticated = True
        logger.info("Successfully resumed session!")
    except Exception as resume_error:
        logger.info(f"Could not resume: {resume_error}. Starting fresh login...")
        try:
            garth.login(email, password)
            garth.save(str(token_dir))
            garmin_client = GarminClient(email, password)
            garmin_client.client.garth = garth.client
            garmin_client._authenticated = True
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return

    # Date Range: Yesterday and Today
    end_date = date.today()
    start_date = end_date - timedelta(days=1)
    
    logger.info(f"Syncing {start_date} to {end_date}")
    
    metrics_to_write = []
    current_date = start_date
    while current_date <= end_date:
        try:
            daily_metrics = await garmin_client.get_metrics(current_date)
            metrics_to_write.append(daily_metrics)
        except Exception as e:
            logger.error(f"Failed to fetch {current_date}: {e}")
        current_date += timedelta(days=1)

    # Write to Google Sheets
    if metrics_to_write:
        try:
            sheets_client = GoogleSheetsClient(
                credentials_path='credentials/client_secret.json',
                spreadsheet_id=sheet_id,
                sheet_name=sheet_name
            )
            sheets_client.update_metrics(metrics_to_write)
            logger.info("✅ Google Sheets sync completed!")
        except Exception as e:
            logger.error(f"Sheets update failed: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
