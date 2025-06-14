import json
import os
import boto3
from src.handlers.auth import is_authorized
from src.handlers.expenditures import post_expenditure
from src.handlers.calculations import calculate_totals

def lambda_handler(event, context):
    # Check if the user is authorized
    user_id = event.get('requestContext', {}).get('identity', {}).get('userArn')
    if not is_authorized(user_id):
        return {
            'statusCode': 403,
            'body': json.dumps({'message': 'Access denied'})
        }

    # Determine the HTTP method
    http_method = event.get('httpMethod')

    if http_method == 'POST':
        # Handle posting an expenditure
        body = json.loads(event.get('body', '{}'))
        amount = body.get('amount')
        description = body.get('description')
        date = body.get('date')
        
        if post_expenditure(amount, description, date):
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Expenditure posted successfully'})
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'Failed to post expenditure'})
            }

    elif http_method == 'GET':
        # Handle calculating totals
        totals = calculate_totals()
        return {
            'statusCode': 200,
            'body': json.dumps(totals)
        }

    return {
        'statusCode': 400,
        'body': json.dumps({'message': 'Unsupported method'})
    }