import os
from datetime import datetime

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.metrics import MetricUnit
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Initialize PowerTools
logger = Logger()
tracer = Tracer()
metrics = Metrics()

# Initialize FastAPI
app = FastAPI(
    title="Child Allowance Tracker",
    description="Track and manage children's allowances",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


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


# Dependency to get DynamoDB client
@tracer.capture_method
def get_dynamodb_client():
    """Get DynamoDB client"""
    import boto3

    return boto3.resource("dynamodb", region_name="us-east-1")


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

        # Simple operation to test connectivity - Remove useless expression
        status = table.table_status  # Store the result
        db_status = "healthy" if status else "unknown"
    except Exception as e:
        logger.error(f"DynamoDB health check failed: {e}")
        db_status = f"unhealthy: {str(e)}"

    health_data = {
        "status": "healthy",
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

        # Scan for children (in real app, you'd use better querying)
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

    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}") from e


@app.get("/api/children", response_model=list[Child])
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
            children.append(
                Child(
                    name=item["name"],
                    age=int(item["age"]),
                    weekly_allowance=float(item["weekly_allowance"]),
                )
            )

        return children

    except Exception as e:
        logger.error(f"Error getting children: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}") from e


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

        # Store child data
        table.put_item(
            Item={
                "id": f"child#{child.name}",
                "record_type": "child",
                "name": child.name,
                "age": child.age,
                "weekly_allowance": str(child.weekly_allowance),
                "created_at": datetime.now().isoformat(),
            }
        )

        logger.info(f"Child {child.name} created successfully")
        return child

    except Exception as e:
        logger.error(f"Error creating child: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}") from e


@app.get("/api/allowances", response_model=list[AllowanceResponse])
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
            allowances.append(
                AllowanceResponse(
                    id=item["id"],
                    child_name=item["child_name"],
                    amount=float(item["amount"]),
                    date=datetime.fromisoformat(item["date"]),
                    description=item.get("description"),
                )
            )

        return allowances

    except Exception as e:
        logger.error(f"Error getting allowances: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}") from e


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

    except Exception as e:
        logger.error(f"Error creating allowance: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}") from e


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
