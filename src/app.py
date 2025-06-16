"""Simplified FastAPI app for debugging"""

import os
from datetime import datetime

try:
    from fastapi import FastAPI

    print("✅ FastAPI imports successful")
except Exception as e:
    print(f"❌ FastAPI import failed: {e}")
    raise

# Create simple FastAPI app
app = FastAPI(
    title="Child Allowance Tracker",
    description="Track and manage children's allowances",
    version="1.0.0",
)


@app.get("/health")
async def health_check():
    """Simple health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "child-allowance-tracker",
        "python_version": "3.12",
    }


@app.get("/")
async def root():
    """Simple root endpoint"""
    return {"message": "Child Allowance Tracker API", "status": "running"}


@app.get("/debug")
async def debug_info():
    """Debug endpoint"""
    import sys

    return {
        "python_version": sys.version,
        "current_directory": os.getcwd(),
        "fastapi_working": True,
        "timestamp": datetime.now().isoformat(),
    }
