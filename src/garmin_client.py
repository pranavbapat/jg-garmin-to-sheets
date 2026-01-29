import logging
from datetime import date
from typing import List, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from .config import GarminMetrics, HEADERS, HEADER_TO_ATTRIBUTE_MAP, TARGET_SHEET_NAME, SHEET_DATE_FORMAT

logger = logging.getLogger(__name__)

class SheetsClient:
    def __init__(self, spreadsheet_id: str, credentials_path: str):
        self.creds = service_account.Credentials.from_service_account_file(credentials_path, scopes=['https://www.googleapis.com/auth/spreadsheets'])
        self.service = build('sheets', 'v4', credentials=self.creds)
        self.spreadsheet_id = spreadsheet_id

    def update_metrics(self, metrics_list: List[Optional[GarminMetrics]]):
        valid_data = [m for m in metrics_list if m is not None]
        if not valid_data:
            return

        sheet = self.service.spreadsheets()
        
        # Prepare Rows
        rows = []
        for m in valid_data:
            row = []
            for header in HEADERS:
                attr = HEADER_TO_ATTRIBUTE_MAP.get(header)
                val = getattr(m, attr) if attr else ""
                if header == "Date" and isinstance(val, date):
                    row.append(val.strftime(SHEET_DATE_FORMAT))
                else:
                    row.append(val if val is not None else "")
            rows.append(row)

        # Append to Sheet (Google API handles the space in TARGET_SHEET_NAME automatically)
        sheet.values().append(
            spreadsheetId=self.spreadsheet_id,
            range=f"'{TARGET_SHEET_NAME}'!A2",
            valueInputOption="USER_ENTERED",
            body={'values': rows}
        ).execute()
        logger.info(f"Appended metrics to '{TARGET_SHEET_NAME}'")
