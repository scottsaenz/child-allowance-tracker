import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app import app
import awsgi

def lambda_handler(event, context):
    return awsgi.response(app, event, context, base64_content_types={"image/png", "image/jpg"})