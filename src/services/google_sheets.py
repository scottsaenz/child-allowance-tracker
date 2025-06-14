from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import os

# Load environment variables
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
RANGE_NAME = os.getenv('RANGE_NAME')

# Set up Google Sheets API credentials
def get_google_sheets_service():
    creds = Credentials.from_service_account_file(
        os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    )
    service = build('sheets', 'v4', credentials=creds)
    return service

# Function to read data from Google Sheets
def read_data_from_sheet():
    service = get_google_sheets_service()
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=GOOGLE_SHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])
    return values

# Function to write data to Google Sheets
def write_data_to_sheet(data):
    service = get_google_sheets_service()
    sheet = service.spreadsheets()
    body = {
        'values': data
    }
    sheet.values().append(
        spreadsheetId=GOOGLE_SHEET_ID,
        range=RANGE_NAME,
        valueInputOption='RAW',
        body=body
    ).execute()