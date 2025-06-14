import json
import logging
import os
import sys
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    """AWS Lambda handler function"""
    logger.info("Lambda function started")
    logger.info(f"Event: {json.dumps(event, default=str)}")

    try:
        # Add current directory to Python path
        sys.path.insert(0, os.path.dirname(__file__))
        logger.info(f"Python path: {sys.path[:3]}")
        logger.info(f"Current directory: {os.getcwd()}")
        logger.info(f"Directory contents: {os.listdir('.')[:10]}")

        # Try to import required modules
        try:
            import awsgi

            logger.info("✅ awsgi imported successfully")
        except ImportError as e:
            logger.error(f"❌ Failed to import awsgi: {e}")
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": f"awsgi import failed: {e!s}"}),
            }

        try:
            from app import app

            logger.info("✅ Flask app imported successfully")
        except ImportError as e:
            logger.error(f"❌ Failed to import Flask app: {e}")
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": f"Flask app import failed: {e!s}"}),
            }

        # Check if this is a simple health check
        if event.get("rawPath") == "/":
            logger.info("Processing root path request")

        # Use awsgi to handle the request
        logger.info("Calling awsgi.response")
        result = awsgi.response(app, event, context)
        logger.info(f"awsgi response status: {result.get('statusCode')}")

        return result

    except Exception as e:
        error_msg = f"Lambda handler error: {e!s}"
        error_trace = traceback.format_exc()
        logger.error(error_msg)
        logger.error(error_trace)

        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
            },
            "body": json.dumps(
                {
                    "error": error_msg,
                    "traceback": error_trace.split("\n")[:10],  # First 10 lines
                }
            ),
        }
