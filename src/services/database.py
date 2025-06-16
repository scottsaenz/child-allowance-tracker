import os
from datetime import datetime
from decimal import Decimal

import boto3

from utils.logger import get_logger

logger = get_logger(__name__)


class DynamoDBService:
    def __init__(self):
        logger.info("Initializing DynamoDB service")
        # For development, create mock service if no AWS credentials
        try:
            self.dynamodb = boto3.resource("dynamodb")
            self.table_name = os.environ.get("DYNAMODB_TABLE", "allowance-data-dev")
            self.table = self.dynamodb.Table(self.table_name)
            self.mock_mode = False
            logger.info(f"DynamoDB service initialized with table: {self.table_name}")
        except Exception as e:
            logger.warning(f"Failed to initialize DynamoDB, using mock mode: {e}")
            self.mock_mode = True
            self.mock_data = []

    def save_expenditure(self, child_name, amount, date, description):
        """Save expenditure to DynamoDB"""
        if self.mock_mode:
            expenditure = {
                "child": child_name,
                "amount": float(amount),
                "date": date,
                "description": description,
                "created_at": datetime.now().isoformat(),
            }
            self.mock_data.append(expenditure)
            logger.info(f"Mock: Saved expenditure for {child_name}: ${amount}")
            return True

        try:
            item = {
                "pk": f"CHILD#{child_name}",
                "sk": f"EXPENDITURE#{datetime.now().isoformat()}",
                "amount": Decimal(str(amount)),
                "date": date,
                "description": description,
                "created_at": datetime.now().isoformat(),
            }

            self.table.put_item(Item=item)
            logger.info(f"Saved expenditure for {child_name}: ${amount}")
            return True
        except Exception as e:
            logger.error(f"Error saving expenditure: {e}")
            return False

    def get_expenditures(self, child_name=None):
        """Get expenditures from DynamoDB"""
        if self.mock_mode:
            if child_name:
                data = [exp for exp in self.mock_data if exp["child"] == child_name]
                logger.info(
                    f"Mock: Retrieved {len(data)} expenditures for {child_name}"
                )
                return data
            logger.info(f"Mock: Retrieved {len(self.mock_data)} total expenditures")
            return self.mock_data

        try:
            if child_name:
                response = self.table.query(
                    KeyConditionExpression="pk = :pk AND begins_with(sk, :sk)",
                    ExpressionAttributeValues={
                        ":pk": f"CHILD#{child_name}",
                        ":sk": "EXPENDITURE#",
                    },
                )
            else:
                response = self.table.scan(
                    FilterExpression="begins_with(sk, :sk)",
                    ExpressionAttributeValues={":sk": "EXPENDITURE#"},
                )

            # Convert Decimal to float for JSON serialization
            items = []
            for item in response["Items"]:
                item["amount"] = float(item["amount"])
                items.append(item)

            logger.info(f"Retrieved {len(items)} expenditures from DynamoDB")
            return items
        except Exception as e:
            logger.error(f"Error getting expenditures: {e}")
            return []

    def get_total_spent(self, child_name):
        """Calculate total spent by a child"""
        expenditures = self.get_expenditures(child_name)
        total = sum(exp["amount"] for exp in expenditures)
        logger.debug(f"Total spent by {child_name}: ${total}")
        return total
