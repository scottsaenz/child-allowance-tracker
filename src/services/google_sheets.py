import json
import os

import gspread
from google.oauth2.service_account import Credentials

from utils.logger import get_logger

logger = get_logger(__name__)


class GoogleSheetsService:
    def __init__(self):
        logger.info("Initializing Google Sheets service")
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]

        # Get credentials from environment variable
        service_account_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
        if not service_account_json:
            logger.warning("No Google service account JSON found, using mock service")
            self.client = None
            self.sheet_id = None
            return

        try:
            service_account_info = json.loads(service_account_json)

            creds = Credentials.from_service_account_info(
                service_account_info, scopes=scope
            )

            self.client = gspread.authorize(creds)
            self.sheet_id = os.environ.get("GOOGLE_SHEETS_ID")
            logger.info("Google Sheets service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets service: {e}")
            self.client = None
            self.sheet_id = None

    def get_allowance_data(self):
        if not self.client:
            logger.info("Using mock allowance data")
            return [
                {
                    "Week_Date": "6/23/2024",
                    "Before Today": True,
                    "child1": 7,
                    "child2": 8,
                    "child3": 10,
                },
                {
                    "Week_Date": "6/30/2024",
                    "Before Today": True,
                    "child1": 7,
                    "child2": 8,
                    "child3": 10,
                },
            ]

        try:
            sheet = self.client.open_by_key(self.sheet_id).worksheet("Allowance Earned")
            data = sheet.get_all_records()
            logger.info(f"Retrieved {len(data)} allowance records")
            return data
        except Exception as e:
            logger.error(f"Error retrieving allowance data: {e}")
            return []

    def get_expenditures(self):
        if not self.client:
            logger.info("Using mock expenditure data")
            return []

        try:
            sheet = self.client.open_by_key(self.sheet_id).worksheet("Sheet1")
            data = sheet.get_all_records()
            logger.info(f"Retrieved {len(data)} expenditure records")
            return data
        except Exception as e:
            logger.error(f"Error retrieving expenditure data: {e}")
            return []

    def add_expenditure(self, who, cost, date, description):
        if not self.client:
            logger.info(
                f"Mock: Adding expenditure for {who}: ${cost} on {date} - {description}"
            )
            return True

        try:
            sheet = self.client.open_by_key(self.sheet_id).worksheet("Sheet1")
            sheet.append_row([who, cost, date, description])
            logger.info(f"Added expenditure for {who}: ${cost}")
            return True
        except Exception as e:
            logger.error(f"Error adding expenditure: {e}")
            return False
