"""Simplified AWS Lambda handler without X-Ray"""

import json
import os
import sys
from typing import Any

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

print(f"[INIT] Lambda starting with Python {sys.version}")
print(f"[INIT] Current working directory: {os.getcwd()}")

# Test imports step by step without PowerTools initially
try:
    print("[INIT] Testing basic imports...")
    from mangum import Mangum

    print("[INIT] ✅ Mangum imported")
except Exception as e:
    print(f"[INIT] ❌ Mangum import failed: {e}")
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
    print("[INIT] ✅ Mangum handler created")
except Exception as e:
    print(f"[INIT] ❌ Mangum handler creation failed: {e}")
    raise

# Now try to import PowerTools (optional)
try:
    from aws_lambda_powertools import Logger

    logger = Logger(level="DEBUG")
    logger.info("PowerTools loaded successfully")
except Exception as e:
    print(f"[INIT] ⚠️ PowerTools not available: {e}")
    import logging

    logger = logging.getLogger(__name__)


def lambda_handler(event: dict[str, Any], context) -> dict[str, Any]:
    """Simplified Lambda handler"""
    try:
        print(
            f"[HANDLER] Request received: {event.get('httpMethod', 'unknown')} {event.get('path', event.get('rawPath', 'unknown'))}"
        )

        # Call Mangum handler
        response = handler(event, context)

        print(f"[HANDLER] Response status: {response.get('statusCode', 'unknown')}")
        return response

    except Exception as e:
        print(f"[ERROR] Handler error: {e}")
        import traceback

        traceback.print_exc()

        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Internal Server Error", "message": str(e)}),
        }
