"""FastAPI application for Child Allowance Tracker"""

import logging
import os
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Child Allowance Tracker",
    description="A web application to track children's allowances and chores",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class Child(BaseModel):
    id: str | None = None
    name: str
    age: int
    weekly_allowance: float
    current_balance: float = 0.0
    created_at: datetime | None = None


class Transaction(BaseModel):
    id: str | None = None
    child_id: str
    amount: float
    description: str
    transaction_type: str  # "allowance", "chore", "spending", "adjustment"
    date: datetime | None = None


class Chore(BaseModel):
    id: str | None = None
    name: str
    description: str
    value: float
    assigned_to: str | None = None  # child_id
    completed: bool = False
    completed_date: datetime | None = None


# In-memory storage (replace with database in production)
children_db: list[Child] = []
transactions_db: list[Transaction] = []
chores_db: list[Chore] = []


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "child-allowance-tracker",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Child Allowance Tracker API",
        "status": "running",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/health",
    }


# Debug endpoint
@app.get("/debug")
async def debug_info():
    """Debug information endpoint"""
    import sys

    return {
        "python_version": sys.version,
        "current_directory": os.getcwd(),
        "environment_variables": {
            "ENVIRONMENT": os.getenv("ENVIRONMENT", "not_set"),
            "AWS_REGION": os.getenv("AWS_REGION", "not_set"),
            "AWS_LAMBDA_FUNCTION_NAME": os.getenv(
                "AWS_LAMBDA_FUNCTION_NAME", "not_set"
            ),
        },
        "fastapi_working": True,
        "timestamp": datetime.now().isoformat(),
        "data_counts": {
            "children": len(children_db),
            "transactions": len(transactions_db),
            "chores": len(chores_db),
        },
    }


# Children endpoints
@app.get("/children", response_model=list[Child])
async def get_children():
    """Get all children"""
    return children_db


@app.post("/children", response_model=Child)
async def create_child(child: Child):
    """Create a new child"""
    # Generate ID and set creation time
    child.id = f"child_{len(children_db) + 1}"
    child.created_at = datetime.now()

    children_db.append(child)
    logger.info(f"Created child: {child.name}")
    return child


@app.get("/children/{child_id}", response_model=Child)
async def get_child(child_id: str):
    """Get a specific child by ID"""
    child = next((c for c in children_db if c.id == child_id), None)
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")
    return child


@app.put("/children/{child_id}", response_model=Child)
async def update_child(child_id: str, child_update: Child):
    """Update a child's information"""
    child_index = next((i for i, c in enumerate(children_db) if c.id == child_id), None)
    if child_index is None:
        raise HTTPException(status_code=404, detail="Child not found")

    # Preserve ID and creation time
    child_update.id = child_id
    child_update.created_at = children_db[child_index].created_at
    children_db[child_index] = child_update

    logger.info(f"Updated child: {child_id}")
    return child_update


@app.delete("/children/{child_id}")
async def delete_child(child_id: str):
    """Delete a child"""
    child_index = next((i for i, c in enumerate(children_db) if c.id == child_id), None)
    if child_index is None:
        raise HTTPException(status_code=404, detail="Child not found")

    deleted_child = children_db.pop(child_index)
    logger.info(f"Deleted child: {child_id}")
    return {"message": f"Child {deleted_child.name} deleted successfully"}


# Transaction endpoints
@app.get("/transactions", response_model=list[Transaction])
async def get_transactions(child_id: str | None = None):
    """Get all transactions, optionally filtered by child_id"""
    if child_id:
        return [t for t in transactions_db if t.child_id == child_id]
    return transactions_db


@app.post("/transactions", response_model=Transaction)
async def create_transaction(transaction: Transaction):
    """Create a new transaction"""
    # Verify child exists
    child = next((c for c in children_db if c.id == transaction.child_id), None)
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    # Generate ID and set date
    transaction.id = f"trans_{len(transactions_db) + 1}"
    transaction.date = datetime.now()

    # Update child's balance
    child_index = next(
        i for i, c in enumerate(children_db) if c.id == transaction.child_id
    )
    if transaction.transaction_type in ["allowance", "chore"]:
        children_db[child_index].current_balance += transaction.amount
    elif transaction.transaction_type == "spending":
        children_db[child_index].current_balance -= transaction.amount
    elif transaction.transaction_type == "adjustment":
        children_db[child_index].current_balance += transaction.amount

    transactions_db.append(transaction)
    logger.info(
        f"Created transaction: {transaction.transaction_type} for {transaction.child_id}"
    )
    return transaction


# Chore endpoints
@app.get("/chores", response_model=list[Chore])
async def get_chores(assigned_to: str | None = None, completed: bool | None = None):
    """Get all chores, optionally filtered by assignment and completion status"""
    filtered_chores = chores_db

    if assigned_to:
        filtered_chores = [c for c in filtered_chores if c.assigned_to == assigned_to]

    if completed is not None:
        filtered_chores = [c for c in filtered_chores if c.completed == completed]

    return filtered_chores


@app.post("/chores", response_model=Chore)
async def create_chore(chore: Chore):
    """Create a new chore"""
    chore.id = f"chore_{len(chores_db) + 1}"
    chores_db.append(chore)
    logger.info(f"Created chore: {chore.name}")
    return chore


@app.put("/chores/{chore_id}/complete")
async def complete_chore(chore_id: str):
    """Mark a chore as completed and create transaction"""
    chore_index = next((i for i, c in enumerate(chores_db) if c.id == chore_id), None)
    if chore_index is None:
        raise HTTPException(status_code=404, detail="Chore not found")

    chore = chores_db[chore_index]
    if chore.completed:
        raise HTTPException(status_code=400, detail="Chore already completed")

    # Mark chore as completed
    chores_db[chore_index].completed = True
    chores_db[chore_index].completed_date = datetime.now()

    # Create transaction if chore is assigned
    if chore.assigned_to:
        transaction = Transaction(
            child_id=chore.assigned_to,
            amount=chore.value,
            description=f"Completed chore: {chore.name}",
            transaction_type="chore",
        )
        await create_transaction(transaction)

    logger.info(f"Completed chore: {chore_id}")
    return {"message": f"Chore {chore.name} completed successfully"}


# Reports endpoint
@app.get("/reports/summary")
async def get_summary():
    """Get summary report of all data"""
    total_allowances = sum(
        t.amount for t in transactions_db if t.transaction_type == "allowance"
    )
    total_chore_earnings = sum(
        t.amount for t in transactions_db if t.transaction_type == "chore"
    )
    total_spending = sum(
        t.amount for t in transactions_db if t.transaction_type == "spending"
    )

    return {
        "summary": {
            "total_children": len(children_db),
            "total_transactions": len(transactions_db),
            "total_chores": len(chores_db),
            "completed_chores": len([c for c in chores_db if c.completed]),
            "total_allowances_paid": total_allowances,
            "total_chore_earnings": total_chore_earnings,
            "total_spending": total_spending,
            "total_balances": sum(c.current_balance for c in children_db),
        },
        "children": [
            {
                "id": child.id,
                "name": child.name,
                "balance": child.current_balance,
                "weekly_allowance": child.weekly_allowance,
            }
            for child in children_db
        ],
        "recent_transactions": sorted(
            transactions_db, key=lambda t: t.date or datetime.min, reverse=True
        )[:10],
    }


# Simple HTML interface (for basic testing)
@app.get("/ui", response_class=HTMLResponse)
async def get_ui():
    """Simple HTML interface for testing"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Child Allowance Tracker</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .card { background: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 8px; }
            .button { background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h1>Child Allowance Tracker</h1>
        <div class="card">
            <h2>API Documentation</h2>
            <p>Access the interactive API documentation:</p>
            <a href="/docs" class="button">OpenAPI Docs (Swagger)</a>
            <a href="/redoc" class="button">ReDoc</a>
        </div>
        <div class="card">
            <h2>Quick Links</h2>
            <ul>
                <li><a href="/health">Health Check</a></li>
                <li><a href="/children">View Children</a></li>
                <li><a href="/transactions">View Transactions</a></li>
                <li><a href="/chores">View Chores</a></li>
                <li><a href="/reports/summary">Summary Report</a></li>
            </ul>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    # For local development
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
