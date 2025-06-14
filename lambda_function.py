import json
from typing import Any

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext
from mangum import Mangum

# Initialize PowerTools
logger = Logger()
tracer = Tracer()
metrics = Metrics()

# Import FastAPI app
try:
    from app import app

    logger.info("FastAPI app imported successfully")
except ImportError as e:
    logger.error(f"Failed to import FastAPI app: {e}")
    raise

# Create Mangum handler
handler = Mangum(app, lifespan="off")


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    AWS Lambda handler using Mangum to run FastAPI
    """
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

        # Handle the request using Mangum
        response = handler(event, context)

        # Log response status
        status_code = response.get("statusCode", 500)
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
                }
            ),
            "headers": {"Content-Type": "application/json"},
        }
