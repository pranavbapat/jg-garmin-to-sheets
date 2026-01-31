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
    sheet_name = os.getenv(f"{profile_name}_SHEET_NAME", "Garmin Data")
    
    # Setup garth token directory
    token_dir = Path(f"./credentials/garmin_tokens_{profile_name}")
    os.environ["GARTH_HOME"] = str(token_dir)

    # 1. Authenticate / Resume
    garmin_client = None
    try:
        logger.info(f"Resuming Garmin session from {token_dir}")
        garth.resume(str(token_dir))
        logger.info("✅ Garth session resumed successfully")
        
        garmin_client = GarminClient(email, password)
        garmin_client.client.garth = garth.client
        
        # CRITICAL: Load profile data
        logger.info("Loading user profile...")
        try:
            # Access profile which triggers fetch if needed
            profile = garth.client.profile
            logger.info(f"Profile fetched: {profile}")
            
            if profile:
                garmin_client.client.display_name = profile.get("displayName")
                garmin_client.client.full_name = profile.get("fullName")
                garmin_client.client.unit_system = profile.get("measurementSystem")
                logger.info(f"✅ Profile loaded: display_name={garmin_client.client.display_name}")
            else:
                logger.error("❌ Profile is None - this will cause API failures!")
                
                # Try alternative method
                logger.info("Attempting alternative profile load via get_full_name()...")
                try:
                    full_name = garmin_client.client.get_full_name()
                    logger.info(f"✅ Profile loaded via get_full_name(): {full_name}")
                except Exception as alt_error:
                    logger.error(f"❌ Alternative profile load also failed: {alt_error}")
                    raise Exception("Failed to load profile - API calls will fail")
        except Exception as profile_error:
            logger.error(f"❌ Profile loading failed: {profile_error}")
            raise
        
        garmin_client._authenticated = True
        logger.info("✅ Garmin client ready")
        
    except Exception as e:
        logger.error(f"❌ Authentication/setup failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # 2. Fetch yesterday and today
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    logger.info(f"🚀 Fetching data for: {yesterday} and {today}")
    
    metrics_to_write = []
    for target_date in [yesterday, today]:
        try:
            logger.info(f"Fetching {target_date.isoformat()}...")
            daily_metrics = await garmin_client.get_metrics(target_date)
            metrics_to_write.append(daily_metrics)
            # 1-second pause to be kind to the API
            await asyncio.sleep(1) 
        except Exception as e:
            logger.error(f"Failed to fetch {target_date}: {e}")

    # 3. Push data to Google Sheets (with deduplication)
    if metrics_to_write:
        try:
            sheets_client = GoogleSheetsClient(
                credentials_path='credentials/client_secret.json',
                spreadsheet_id=sheet_id,
                sheet_name=sheet_name
            )
            sheets_client.update_metrics(metrics_to_write)
            logger.info(f"✅ Sync successful! {len(metrics_to_write)} days synced.")
        except Exception as e:
            logger.error(f"Sheets update failed: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
