import boto3
import os
from datetime import datetime
from decimal import Decimal
import json

class DynamoDBService:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = os.environ.get('DYNAMODB_TABLE')
        self.table = self.dynamodb.Table(self.table_name)
    
    def save_expenditure(self, child_name, amount, date, description):
        """Save expenditure to DynamoDB"""
        item = {
            'pk': f'CHILD#{child_name}',
            'sk': f'EXPENDITURE#{datetime.now().isoformat()}',
            'amount': Decimal(str(amount)),
            'date': date,
            'description': description,
            'created_at': datetime.now().isoformat()
        }
        
        self.table.put_item(Item=item)
        return True
    
    def get_expenditures(self, child_name=None):
        """Get expenditures from DynamoDB"""
        if child_name:
            response = self.table.query(
                KeyConditionExpression='pk = :pk AND begins_with(sk, :sk)',
                ExpressionAttributeValues={
                    ':pk': f'CHILD#{child_name}',
                    ':sk': 'EXPENDITURE#'
                }
            )
        else:
            response = self.table.scan(
                FilterExpression='begins_with(sk, :sk)',
                ExpressionAttributeValues={
                    ':sk': 'EXPENDITURE#'
                }
            )
        
        # Convert Decimal to float for JSON serialization
        items = []
        for item in response['Items']:
            item['amount'] = float(item['amount'])
            items.append(item)
        
        return items
    
    def get_total_spent(self, child_name):
        """Calculate total spent by a child"""
        expenditures = self.get_expenditures(child_name)
        return sum(exp['amount'] for exp in expenditures)