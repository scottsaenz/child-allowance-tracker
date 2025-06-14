import json
import os
import sys
from typing import Any

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext
from mangum import Mangum

# Initialize PowerTools with DEBUG level
logger = Logger(level="DEBUG")
tracer = Tracer()
metrics = Metrics()

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(__file__))

logger.debug(f"Lambda starting with Python {sys.version}")
logger.debug(f"Current working directory: {os.getcwd()}")
logger.debug(f"Lambda handler file location: {__file__}")
logger.debug(f"Python path first 3 entries: {sys.path[:3]}")

# Import FastAPI app - removed duplicate Mangum import
try:
    from app import app

    logger.debug("FastAPI app imported successfully")
    logger.debug(f"FastAPI app type: {type(app)}")
except ImportError as e:
    logger.error(f"Failed to import FastAPI app: {e}")
    raise

# Create Mangum handler
try:
    handler = Mangum(app, lifespan="off")
    logger.debug("Mangum handler created successfully")
except Exception as e:
    logger.error(f"Failed to create Mangum handler: {e}")
    raise


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    AWS Lambda handler using Mangum to run FastAPI
    """
    logger.debug("Lambda handler called")
    logger.debug(f"Event type: {type(event)}")
    logger.debug(f"Context type: {type(context)}")

    # Log event details
    if isinstance(event, dict):
        http_method = event.get(
            "httpMethod",
            event.get("requestContext", {}).get("http", {}).get("method", "unknown"),
        )
        path = event.get(
            "path",
            event.get(
                "rawPath",
                event.get("requestContext", {}).get("http", {}).get("path", "unknown"),
            ),
        )
        version = event.get("version", "unknown")

        logger.debug(f"HTTP method: {http_method}")
        logger.debug(f"Path: {path}")
        logger.debug(f"Event version: {version}")
        logger.debug(f"Event keys: {list(event.keys())}")

    logger.info(
        "Lambda handler started",
        extra={
            "event_type": event.get("requestContext", {}).get("http", {}).get("method"),
            "path": event.get("rawPath"),
            "aws_request_id": context.aws_request_id,
        },
    )

    try:
        # Add custom metrics
        metrics.add_metadata(key="requestId", value=context.aws_request_id)
        metrics.add_metric(name="LambdaInvocations", unit=MetricUnit.Count, value=1)

        logger.debug("Calling Mangum handler...")
        # Handle the request using Mangum
        response = handler(event, context)

        # Log response details
        status_code = response.get("statusCode", 500)
        logger.debug(f"Response status: {status_code}")
        logger.debug(f"Response type: {type(response)}")
        logger.debug(f"Response headers: {response.get('headers', {})}")

        logger.info(f"Request completed with status: {status_code}")
        metrics.add_metric(
            name=f"Response{status_code}", unit=MetricUnit.Count, value=1
        )

        return response

    except Exception as e:
        logger.error(f"Lambda handler error: {e}", exc_info=True)
        metrics.add_metric(name="LambdaErrors", unit=MetricUnit.Count, value=1)

        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "error": "Internal server error",
                    "requestId": context.aws_request_id,
                    "message": str(e),
                }
            ),
            "headers": {"Content-Type": "application/json"},
        }
