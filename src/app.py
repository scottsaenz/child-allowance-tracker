import os
from datetime import datetime
from typing import List

import boto3
from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.metrics import MetricUnit
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    EndpointConnectionError,
    NoCredentialsError,
    PartialCredentialsError,
)
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, ValidationError

# Initialize PowerTools
logger = Logger(level="DEBUG")
tracer = Tracer()
metrics = Metrics()

logger.debug("Starting FastAPI app initialization")

try:
    app = FastAPI(
        title="Child Allowance Tracker",
        description="Track and manage children's allowances",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    logger.debug("FastAPI app instance created successfully")
except Exception as e:
    logger.error(f"Failed to create FastAPI app: {e}")
    raise


# Custom exception classes
class DatabaseConnectionError(Exception):
    """Raised when cannot connect to database"""

    pass


class ChildNotFoundError(Exception):
    """Raised when child is not found"""

    pass


class DuplicateChildError(Exception):
    """Raised when trying to create a child that already exists"""

    pass


# Pydantic models
class Child(BaseModel):
    name: str
    age: int
    weekly_allowance: float


class AllowanceRecord(BaseModel):
    child_name: str
    amount: float
    date: datetime
    description: str | None = None


class AllowanceResponse(BaseModel):
    id: str
    child_name: str
    amount: float
    date: datetime
    description: str | None = None


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "Invalid input data",
            "details": exc.errors(),
        },
    )


@app.exception_handler(DatabaseConnectionError)
async def database_connection_exception_handler(
    request: Request, exc: DatabaseConnectionError
):
    logger.error(f"Database connection error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": "Database Connection Error",
            "message": "Unable to connect to database",
            "details": str(exc),
        },
    )


@app.exception_handler(ChildNotFoundError)
async def child_not_found_exception_handler(request: Request, exc: ChildNotFoundError):
    logger.error(f"Child not found: {exc}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "Child Not Found",
            "message": str(exc),
        },
    )


@app.exception_handler(DuplicateChildError)
async def duplicate_child_exception_handler(request: Request, exc: DuplicateChildError):
    logger.error(f"Duplicate child error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": "Duplicate Child",
            "message": str(exc),
        },
    )


# Dependency to get DynamoDB client
@tracer.capture_method
def get_dynamodb_client():
    """Get DynamoDB client with proper error handling"""
    try:
        return boto3.resource("dynamodb", region_name="us-east-1")
    except NoCredentialsError as e:
        logger.error("AWS credentials not found")
        raise DatabaseConnectionError("AWS credentials not configured") from e
    except PartialCredentialsError as e:
        logger.error("Incomplete AWS credentials")
        raise DatabaseConnectionError("AWS credentials incomplete") from e
    except EndpointConnectionError as e:
        logger.error("Cannot connect to DynamoDB endpoint")
        raise DatabaseConnectionError("Cannot connect to DynamoDB service") from e
    except BotoCoreError as e:
        logger.error(f"AWS service error: {e}")
        raise DatabaseConnectionError(f"AWS service error: {str(e)}") from e


@app.get("/", response_class=HTMLResponse)
@tracer.capture_method
async def root():
    """Root endpoint - serve main dashboard"""
    logger.info("Root endpoint called")
    metrics.add_metric(name="RootEndpointCalls", unit=MetricUnit.Count, value=1)

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Child Allowance Tracker</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
            .stat-card { background: #4CAF50; color: white; padding: 20px; border-radius: 8px; text-align: center; }
            .nav { margin: 20px 0; }
            .nav a { margin-right: 15px; padding: 10px 15px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
            .nav a:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏦 Child Allowance Tracker</h1>

            <div class="stats">
                <div class="stat-card">
                    <h3>Total Children</h3>
                    <p id="total-children">Loading...</p>
                </div>
                <div class="stat-card">
                    <h3>Weekly Total</h3>
                    <p id="weekly-total">Loading...</p>
                </div>
            </div>

            <div class="nav">
                <a href="/children">Manage Children</a>
                <a href="/allowances">View Allowances</a>
                <a href="/docs">API Documentation</a>
                <a href="/health">Health Check</a>
            </div>

            <div id="content">
                <h2>Welcome to the Child Allowance Tracker!</h2>
                <p>This application helps you track and manage your children's allowances.</p>
                <p>Use the navigation links above to get started.</p>
            </div>
        </div>

        <script>
            // Load dashboard data
            fetch('/api/dashboard')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('total-children').textContent = data.total_children || 0;
                    document.getElementById('weekly-total').textContent = '$' + (data.weekly_total || 0).toFixed(2);
                })
                .catch(error => {
                    console.error('Error loading dashboard:', error);
                    document.getElementById('total-children').textContent = 'Error';
                    document.getElementById('weekly-total').textContent = 'Error';
                });
        </script>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)


@app.get("/health")
@tracer.capture_method
async def health_check():
    """Health check endpoint"""
    logger.info("Health check called")
    metrics.add_metric(name="HealthCheckCalls", unit=MetricUnit.Count, value=1)

    # Test DynamoDB connection
    try:
        dynamodb = get_dynamodb_client()
        table_name = os.getenv("DYNAMODB_TABLE", "allowance-data-production")
        table = dynamodb.Table(table_name)

        # Simple operation to test connectivity
        table_status = table.table_status
        db_status = "healthy" if table_status else "unknown"

    except DatabaseConnectionError as e:
        logger.error(f"Database connection failed during health check: {e}")
        db_status = f"unhealthy: {str(e)}"
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "ResourceNotFoundException":
            logger.error(f"DynamoDB table not found: {table_name}")
            db_status = f"unhealthy: Table {table_name} not found"
        elif error_code == "AccessDeniedException":
            logger.error("Access denied to DynamoDB")
            db_status = "unhealthy: Access denied to DynamoDB"
        else:
            logger.error(f"DynamoDB client error: {e}")
            db_status = f"unhealthy: {error_code}"

    health_data = {
        "status": "healthy" if "healthy" in db_status else "degraded",
        "timestamp": datetime.now().isoformat(),
        "service": "child-allowance-tracker",
        "version": "1.0.0",
        "database": db_status,
        "environment": {
            "python_version": "3.13",
            "aws_region": os.getenv("AWS_REGION", "us-east-1"),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
        },
    }

    return health_data


@app.get("/api/dashboard")
@tracer.capture_method
async def get_dashboard_data():
    """Get dashboard statistics"""
    logger.info("Dashboard data requested")
    metrics.add_metric(name="DashboardCalls", unit=MetricUnit.Count, value=1)

    try:
        dynamodb = get_dynamodb_client()
        table_name = os.getenv("DYNAMODB_TABLE", "allowance-data-production")
        table = dynamodb.Table(table_name)

        # Scan for children
        response = table.scan()
        children = [
            item for item in response["Items"] if item.get("record_type") == "child"
        ]

        total_children = len(children)
        weekly_total = sum(
            float(child.get("weekly_allowance", 0)) for child in children
        )

        return {
            "total_children": total_children,
            "weekly_total": weekly_total,
            "last_updated": datetime.now().isoformat(),
        }

    except DatabaseConnectionError:
        raise  # Let the exception handler deal with it
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "ResourceNotFoundException":
            logger.error("Table not found during dashboard query")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database table not found",
            ) from e
        elif error_code == "AccessDeniedException":
            logger.error("Access denied during dashboard query")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database access denied",
            ) from e
        else:
            logger.error(f"DynamoDB error during dashboard query: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Database error: {error_code}",
            ) from e
    except ValueError as e:
        logger.error(f"Data conversion error in dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Data format error",
        ) from e


@app.get("/api/children", response_model=List[Child])
@tracer.capture_method
async def get_children():
    """Get all children"""
    logger.info("Get children called")
    metrics.add_metric(name="GetChildrenCalls", unit=MetricUnit.Count, value=1)

    try:
        dynamodb = get_dynamodb_client()
        table_name = os.getenv("DYNAMODB_TABLE", "allowance-data-production")
        table = dynamodb.Table(table_name)

        response = table.scan(
            FilterExpression="record_type = :type",
            ExpressionAttributeValues={":type": "child"},
        )

        children = []
        for item in response["Items"]:
            try:
                children.append(
                    Child(
                        name=item["name"],
                        age=int(item["age"]),
                        weekly_allowance=float(item["weekly_allowance"]),
                    )
                )
            except (KeyError, ValueError, ValidationError) as e:
                logger.warning(
                    f"Skipping invalid child record {item.get('id', 'unknown')}: {e}"
                )
                continue

        return children

    except DatabaseConnectionError:
        raise
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "ResourceNotFoundException":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database table not found",
            ) from e  # Fixed: Added 'from e'
        else:
            logger.error(f"DynamoDB error getting children: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Database error: {error_code}",
            ) from e  # Fixed: Added 'from e'


@app.post("/api/children", response_model=Child)
@tracer.capture_method
async def create_child(child: Child):
    """Create a new child"""
    logger.info(f"Creating child: {child.name}")
    metrics.add_metric(name="CreateChildCalls", unit=MetricUnit.Count, value=1)

    try:
        dynamodb = get_dynamodb_client()
        table_name = os.getenv("DYNAMODB_TABLE", "allowance-data-production")
        table = dynamodb.Table(table_name)

        child_id = f"child#{child.name}"

        # Check if child already exists
        try:
            existing = table.get_item(Key={"id": child_id})
            if "Item" in existing:
                raise DuplicateChildError(f"Child '{child.name}' already exists")
        except ClientError as e:
            if e.response["Error"]["Code"] != "ResourceNotFoundException":
                raise

        # Store child data
        table.put_item(
            Item={
                "id": child_id,
                "record_type": "child",
                "name": child.name,
                "age": child.age,
                "weekly_allowance": str(child.weekly_allowance),
                "created_at": datetime.now().isoformat(),
            }
        )

        logger.info(f"Child {child.name} created successfully")
        return child

    except (DatabaseConnectionError, DuplicateChildError):
        raise
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "ResourceNotFoundException":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database table not found",
            ) from e  # Fixed: Added 'from e'
        elif error_code == "ConditionalCheckFailedException":
            raise DuplicateChildError(
                f"Child '{child.name}' already exists"
            ) from e  # Fixed: Added 'from e'
        else:
            logger.error(f"DynamoDB error creating child: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Database error: {error_code}",
            ) from e  # Fixed: Added 'from e'


@app.get("/api/allowances", response_model=List[AllowanceResponse])
@tracer.capture_method
async def get_allowances():
    """Get all allowance records"""
    logger.info("Get allowances called")
    metrics.add_metric(name="GetAllowancesCalls", unit=MetricUnit.Count, value=1)

    try:
        dynamodb = get_dynamodb_client()
        table_name = os.getenv("DYNAMODB_TABLE", "allowance-data-production")
        table = dynamodb.Table(table_name)

        response = table.scan(
            FilterExpression="record_type = :type",
            ExpressionAttributeValues={":type": "allowance"},
        )

        allowances = []
        for item in response["Items"]:
            try:
                allowances.append(
                    AllowanceResponse(
                        id=item["id"],
                        child_name=item["child_name"],
                        amount=float(item["amount"]),
                        date=datetime.fromisoformat(item["date"]),
                        description=item.get("description"),
                    )
                )
            except (KeyError, ValueError, ValidationError) as e:
                logger.warning(
                    f"Skipping invalid allowance record {item.get('id', 'unknown')}: {e}"
                )
                continue

        return allowances

    except DatabaseConnectionError:
        raise
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "ResourceNotFoundException":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database table not found",
            ) from e  # Fixed: Added 'from e'
        else:
            logger.error(f"DynamoDB error getting allowances: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Database error: {error_code}",
            ) from e  # Fixed: Added 'from e'


@app.post("/api/allowances", response_model=AllowanceResponse)
@tracer.capture_method
async def create_allowance(allowance: AllowanceRecord):
    """Create a new allowance record"""
    logger.info(f"Creating allowance for {allowance.child_name}: ${allowance.amount}")
    metrics.add_metric(name="CreateAllowanceCalls", unit=MetricUnit.Count, value=1)

    try:
        dynamodb = get_dynamodb_client()
        table_name = os.getenv("DYNAMODB_TABLE", "allowance-data-production")
        table = dynamodb.Table(table_name)

        # Generate ID
        allowance_id = (
            f"allowance#{allowance.child_name}#{int(allowance.date.timestamp())}"
        )

        # Store allowance data
        table.put_item(
            Item={
                "id": allowance_id,
                "record_type": "allowance",
                "child_name": allowance.child_name,
                "amount": str(allowance.amount),
                "date": allowance.date.isoformat(),
                "description": allowance.description or "",
                "created_at": datetime.now().isoformat(),
            }
        )

        logger.info(f"Allowance record created: {allowance_id}")

        return AllowanceResponse(
            id=allowance_id,
            child_name=allowance.child_name,
            amount=allowance.amount,
            date=allowance.date,
            description=allowance.description,
        )

    except DatabaseConnectionError:
        raise
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "ResourceNotFoundException":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database table not found",
            ) from e  # Fixed: Added 'from e'
        else:
            logger.error(f"DynamoDB error creating allowance: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Database error: {error_code}",
            ) from e  # Fixed: Added 'from e'


# Add debug endpoint for troubleshooting
@app.get("/debug")
@tracer.capture_method
async def debug_info():
    """Debug endpoint to check environment"""
    import sys

    return {
        "python_version": sys.version,
        "current_directory": os.getcwd(),
        "environment_variables": {
            k: v
            for k, v in os.environ.items()
            if k.startswith(("POWERTOOLS_", "LOG_", "DYNAMODB_", "AWS_"))
        },
        "sys_path_first_3": sys.path[:3],
        "fastapi_working": True,
        "timestamp": datetime.now().isoformat(),
    }


# Add CORS middleware for web development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
