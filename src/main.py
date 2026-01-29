import os
import asyncio
import logging
import garth
from datetime import date, timedelta
from src.garmin_client import GarminClient
from src.sheets_client import SheetsClient

# Simplified logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def sync():
    # 1. Load Credentials (USER1 prefix as per your env setup)
    email = os.getenv("USER1_GARMIN_EMAIL")
    password = os.getenv("USER1_GARMIN_PASSWORD")
    sheet_id = os.getenv("USER1_SHEET_ID")
    token_dir = "./credentials/garmin_tokens_USER1"
    
    # 2. Resume Garmin Session
    try:
        garth.resume(token_dir)
        garmin_client = GarminClient(email, password)
        garmin_client.client.garth = garth.client
        garmin_client._authenticated = True
        logger.info("Garmin session resumed.")
    except Exception as e:
        logger.error(f"Auth failed: {e}. Run locally to refresh tokens.")
        return

    # 3. Target: Yesterday and Today (To ensure no gaps)
    today = date.today()
    target_dates = [today - timedelta(days=1), today]
    
    metrics_to_write = []
    for target_date in target_dates:
        logger.info(f"Fetching {target_date}...")
        try:
            day_data = await garmin_client.get_metrics(target_date)
            metrics_to_write.append(day_data)
        except Exception as e:
            logger.error(f"Error for {target_date}: {e}")

    # 4. Update Google Sheets
    if metrics_to_write:
        sheets = SheetsClient(sheet_id, "credentials/gsheet_credentials.json")
        sheets.update_metrics(metrics_to_write)
        logger.info(f"Successfully updated {len(metrics_to_write)} days.")

if __name__ == "__main__":
    asyncio.run(sync())
