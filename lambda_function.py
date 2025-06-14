import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from awsgi import response

from app import app


def lambda_handler(event, context):
    """AWS Lambda handler function"""
    return response(app, event, context)
