from services.database import DynamoDBService
from services.google_sheets import GoogleSheetsService
from utils.logger import get_logger

logger = get_logger(__name__)


def calculate_totals():
    """Calculate total allowances and expenditures for each child"""
    logger.info("Calculating totals for all children")

    try:
        # Get allowance data from Google Sheets
        sheets_service = GoogleSheetsService()
        allowance_data = sheets_service.get_allowance_data()

        # Get expenditure data from DynamoDB
        db_service = DynamoDBService()

        children = ["child1", "child2", "child3"]
        totals = {}

        for child in children:
            logger.debug(f"Calculating totals for {child}")

            # Calculate total allowance earned
            total_earned = sum(
                row.get(child, 0)
                for row in allowance_data
                if row.get("Before Today", False)
            )

            # Calculate total spent
            total_spent = db_service.get_total_spent(child)

            # Calculate balance
            balance = total_earned - total_spent

            totals[child] = {
                "earned": total_earned,
                "spent": total_spent,
                "balance": balance,
            }

            logger.debug(
                f"{child}: earned=${total_earned}, spent=${total_spent}, balance=${balance}"
            )

        logger.info("Successfully calculated totals for all children")
        return totals

    except Exception as e:
        logger.error(f"Error calculating totals: {e}")
        return {}
