"""AWS Lambda handler for Child Allowance Tracker"""

import json
import os
import sys
from typing import Any

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

print(f"[INIT] Lambda starting with Python {sys.version}")
print(f"[INIT] Current working directory: {os.getcwd()}")

# Set up environment
os.environ.setdefault("ENVIRONMENT", "production")

# Test imports step by step
try:
    print("[INIT] Testing Mangum import...")
    from mangum import Mangum

    print("[INIT] ✅ Mangum imported successfully")
except Exception as e:
    print(f"[INIT] ❌ Mangum import failed: {e}")
    import traceback

    traceback.print_exc()
    raise

try:
    print("[INIT] Testing FastAPI app import...")
    from app import app

    print(f"[INIT] ✅ FastAPI app imported: {type(app)}")
except Exception as e:
    print(f"[INIT] ❌ FastAPI app import failed: {e}")
    import traceback

    traceback.print_exc()
    raise

try:
    print("[INIT] Creating Mangum handler...")
    handler = Mangum(app, lifespan="off")
    print("[INIT] ✅ Mangum handler created successfully")
except Exception as e:
    print(f"[INIT] ❌ Mangum handler creation failed: {e}")
    import traceback

    traceback.print_exc()
    raise

# Set up logging with PowerTools
try:
    print("[INIT] Setting up AWS Lambda PowerTools...")
    from aws_lambda_powertools import Logger, Metrics, Tracer
    from aws_lambda_powertools.metrics import MetricUnit

    logger = Logger(service="child-allowance-tracker", level="INFO")
    tracer = Tracer(service="child-allowance-tracker")
    metrics = Metrics(
        namespace="ChildAllowanceTracker", service="child-allowance-tracker"
    )

    logger.info("PowerTools loaded successfully")
    print("[INIT] ✅ AWS Lambda PowerTools configured")

except Exception as e:
    print(f"[INIT] ⚠️ PowerTools setup failed, using basic logging: {e}")
    import logging

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    tracer = None
    metrics = None

print("[INIT] 🚀 Lambda initialization completed successfully")


def lambda_handler(event: dict[str, Any], context) -> dict[str, Any]:
    """
    AWS Lambda handler for Child Allowance Tracker FastAPI application

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response
    """
    try:
        # Extract request info for logging
        http_method = event.get(
            "httpMethod",
            event.get("requestContext", {}).get("http", {}).get("method", "UNKNOWN"),
        )
        path = event.get("path", event.get("rawPath", "UNKNOWN"))
        request_id = context.aws_request_id if context else "unknown"

        print(f"[HANDLER] Request {request_id}: {http_method} {path}")

        # Log with PowerTools if available
        if logger and hasattr(logger, "info"):
            logger.info(
                "Processing request",
                extra={
                    "request_id": request_id,
                    "http_method": http_method,
                    "path": path,
                    "user_agent": event.get("headers", {}).get("User-Agent", "unknown"),
                },
            )

        # Add metrics if available
        if metrics:
            metrics.add_metric(name="RequestCount", unit=MetricUnit.Count, value=1)
            metrics.add_metric(
                name=f"Request_{http_method}", unit=MetricUnit.Count, value=1
            )

        # Call the Mangum handler
        response = handler(event, context)

        # Log response
        status_code = response.get("statusCode", "unknown")
        print(f"[HANDLER] Response {request_id}: {status_code}")

        if logger and hasattr(logger, "info"):
            logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "status_code": status_code,
                    "response_size": len(str(response.get("body", ""))),
                },
            )

        # Add response metrics
        if metrics:
            metrics.add_metric(
                name=f"Response_{status_code}", unit=MetricUnit.Count, value=1
            )
            if 200 <= int(str(status_code)) < 300:
                metrics.add_metric(
                    name="SuccessfulRequests", unit=MetricUnit.Count, value=1
                )
            else:
                metrics.add_metric(
                    name="FailedRequests", unit=MetricUnit.Count, value=1
                )

        return response

    except Exception as e:
        error_id = f"error_{request_id if 'request_id' in locals() else 'unknown'}"
        print(f"[ERROR] {error_id}: {str(e)}")

        # Log error details
        import traceback

        traceback.print_exc()

        if logger and hasattr(logger, "error"):
            logger.error(
                "Request failed with exception",
                extra={
                    "error_id": error_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "traceback": traceback.format_exc(),
                },
            )

        # Add error metrics
        if metrics:
            metrics.add_metric(name="ErrorCount", unit=MetricUnit.Count, value=1)
            metrics.add_metric(
                name=f"Error_{type(e).__name__}", unit=MetricUnit.Count, value=1
            )

        # Return error response
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "GET,HEAD,OPTIONS,POST,PUT,DELETE",
            },
            "body": json.dumps(
                {
                    "error": "Internal Server Error",
                    "message": "An error occurred processing your request",
                    "error_id": error_id,
                    "timestamp": "2025-06-16T01:48:14.000Z",  # Should use actual timestamp
                }
            ),
        }

    finally:
        # Publish metrics if available
        if metrics:
            try:
                metrics.flush_metrics()
            except Exception as e:
                print(f"[WARNING] Failed to flush metrics: {e}")
