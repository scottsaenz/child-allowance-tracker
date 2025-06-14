from services.database import DynamoDBService
from services.google_sheets import GoogleSheetsService
from utils.logger import get_logger

logger = get_logger(__name__)


def post_expenditure(child_name, amount, date, description):
    """Post expenditure to both Google Sheets and DynamoDB"""
    logger.info(f"Posting expenditure for {child_name}: ${amount}")

    try:
        # Post to Google Sheets
        sheets_service = GoogleSheetsService()
        sheets_success = sheets_service.add_expenditure(
            child_name, amount, date, description
        )

        # Post to DynamoDB
        db_service = DynamoDBService()
        db_success = db_service.save_expenditure(child_name, amount, date, description)

        if sheets_success and db_success:
            logger.info(f"Successfully posted expenditure for {child_name}")
            return True
        else:
            logger.warning(f"Partial failure posting expenditure for {child_name}")
            return False

    except Exception as e:
        logger.error(f"Error posting expenditure for {child_name}: {e}")
        return False


def get_expenditures():
    """Get expenditures from DynamoDB"""
    logger.info("Retrieving all expenditures")

    try:
        db_service = DynamoDBService()
        expenditures = db_service.get_expenditures()
        logger.info(f"Retrieved {len(expenditures)} expenditures")
        return expenditures
    except Exception as e:
        logger.error(f"Error getting expenditures: {e}")
        return []
