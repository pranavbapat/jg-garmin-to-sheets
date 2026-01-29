import logging
from datetime import date
from typing import List, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from .config import GarminMetrics, HEADERS, HEADER_TO_ATTRIBUTE_MAP, TARGET_SHEET_NAME, SHEET_DATE_FORMAT

logger = logging.getLogger(__name__)

class SheetsClient:
    def __init__(self, spreadsheet_id: str, credentials_path: str):
        self.spreadsheet_id = spreadsheet_id
        self.creds = service_account.Credentials.from_service_account_file(
            credentials_path, 
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        self.service = build('sheets', 'v4', credentials=self.creds)
        logger.info(f"Initialized Google Sheets client for ID: {spreadsheet_id}")

    def update_metrics(self, metrics_list: List[Optional[GarminMetrics]]):
        # Filter out any None values if Garmin failed to return data for a day
        valid_metrics = [m for m in metrics_list if m is not None]
        
        if not valid_metrics:
            logger.warning("No valid metrics to write to Google Sheets.")
            return

        sheet = self.service.spreadsheets()
        
        # 1. Ensure the tab exists
        try:
            sheet_metadata = sheet.get(spreadsheetId=self.spreadsheet_id).execute()
            sheets = sheet_metadata.get('sheets', '')
            exists = any(s.get('properties', {}).get('title') == TARGET_SHEET_NAME for s in sheets)
            
            if not exists:
                batch_update_request = {
                    'requests': [{'addSheet': {'properties': {'title': TARGET_SHEET_NAME}}}]
                }
                sheet.batchUpdate(spreadsheetId=self.spreadsheet_id, body=batch_update_request).execute()
                logger.info(f"Created sheet: {TARGET_SHEET_NAME}")
        except Exception as e:
            logger.error(f"Error checking/creating sheet: {e}")
            return

        # 2. Prepare Data Rows
        rows = []
        for metric in valid_metrics:
            row = []
            for header in HEADERS:
                attr = HEADER_TO_ATTRIBUTE_MAP.get(header)
                val = getattr(metric, attr) if attr else ""
                
                # Format Date
                if header == "Day/Date" and isinstance(val, date):
                    row.append(val.strftime(SHEET_DATE_FORMAT))
                else:
                    row.append(val if val is not None else "")
            rows.append(row)

        # 3. Append Data
        body = {'values': rows}
        range_name = f"{TARGET_SHEET_NAME}!A1"
        
        try:
            # Check if headers exist, if not, add them
            result = sheet.values().get(spreadsheetId=self.spreadsheet_id, range=f"{TARGET_SHEET_NAME}!A1:A1").execute()
            if not result.get('values'):
                sheet.values().update(
                    spreadsheetId=self.spreadsheet_id, 
                    range=f"{TARGET_SHEET_NAME}!A1", 
                    valueInputOption="RAW", 
                    body={'values': [HEADERS]}
                ).execute()

            sheet.values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f"{TARGET_SHEET_NAME}!A2",
                valueInputOption="USER_ENTERED",
                body=body
            ).execute()
            logger.info(f"Successfully appended {len(rows)} rows to {TARGET_SHEET_NAME}.")
        except Exception as e:
            logger.error(f"Failed to update sheet: {e}")
