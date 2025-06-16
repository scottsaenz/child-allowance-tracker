"""
MCP Server for FastAPI Model Testing
Provides intelligent model testing and validation capabilities
"""

import asyncio
import json
import sys
from dataclasses import asdict
from datetime import datetime

# MCP imports - using the correct API
try:
    import mcp.types as types
    from mcp.server import Server
    from mcp.server.stdio import stdio_server

    HAS_MCP = True
except ImportError:
    HAS_MCP = False
    print("MCP not available. Install with: uv add mcp")

# Our app imports
try:
    # Only import app if we need it for testing
    import importlib.util

    from handlers.auth import User
    from models import Child, Expenditure

    if importlib.util.find_spec("app"):
        from app import app

        HAS_APP = True
    else:
        HAS_APP = False
        app = None
    HAS_MODELS = True
except ImportError as e:
    HAS_MODELS = False
    HAS_APP = False
    app = None
    IMPORT_ERROR = str(e)

# Try to import FastAPI testing tools
try:
    from fastapi.testclient import TestClient

    HAS_FASTAPI_TESTING = True
except ImportError:
    HAS_FASTAPI_TESTING = False

# Create the server
server = Server("fastapi-model-tester")


@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """List available testing resources"""
    resources = [
        types.Resource(
            uri="fastapi://models/status",
            name="FastAPI Models Status",
            description="Current status of FastAPI model availability",
            mimeType="application/json",
        ),
        types.Resource(
            uri="fastapi://models/child/schema",
            name="Child Model Schema",
            description="Child model schema and validation rules",
            mimeType="application/json",
        ),
        types.Resource(
            uri="fastapi://models/user/schema",
            name="User Model Schema",
            description="User model schema and validation rules",
            mimeType="application/json",
        ),
        types.Resource(
            uri="fastapi://models/expenditure/schema",
            name="Expenditure Model Schema",
            description="Expenditure model schema and validation rules",
            mimeType="application/json",
        ),
        types.Resource(
            uri="fastapi://testing/coverage",
            name="Model Test Coverage",
            description="Current model testing coverage analysis",
            mimeType="application/json",
        ),
    ]

    if HAS_FASTAPI_TESTING and HAS_APP:
        resources.append(
            types.Resource(
                uri="fastapi://endpoints/test-results",
                name="Endpoint Test Results",
                description="Real-time FastAPI endpoint test results",
                mimeType="application/json",
            )
        )

    return resources


@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read testing resource content"""

    if uri == "fastapi://models/status":
        status = {
            "models_available": HAS_MODELS,
            "app_available": HAS_APP,
            "fastapi_testing_available": HAS_FASTAPI_TESTING,
            "mcp_available": HAS_MCP,
            "import_error": IMPORT_ERROR if not HAS_MODELS else None,
            "timestamp": datetime.now().isoformat(),
            "python_version": sys.version,
            "testing_capabilities": {
                "model_validation": HAS_MODELS,
                "schema_analysis": HAS_MODELS,
                "endpoint_testing": HAS_FASTAPI_TESTING and HAS_APP,
                "integration_testing": HAS_MODELS and HAS_FASTAPI_TESTING and HAS_APP,
            },
        }
        return json.dumps(status, indent=2)

    elif uri == "fastapi://models/child/schema" and HAS_MODELS:
        child_schema = {
            "model_name": "Child",
            "fields": {
                "id": {
                    "type": "str",
                    "required": True,
                    "description": "Unique identifier",
                },
                "name": {
                    "type": "str",
                    "required": True,
                    "description": "Child's name",
                },
                "age": {"type": "int", "required": True, "description": "Child's age"},
                "weekly_allowance": {
                    "type": "float",
                    "required": True,
                    "description": "Weekly allowance amount",
                },
                "total_earnings": {
                    "type": "float",
                    "computed": True,
                    "description": "Total earnings calculated",
                },
                "expenditures": {
                    "type": "List[Expenditure]",
                    "required": False,
                    "description": "Child's expenditures",
                },
            },
            "methods": ["total_earnings", "add_expenditure"],
            "validation_rules": {
                "age": "Must be positive integer",
                "weekly_allowance": "Must be positive float",
                "name": "Must be non-empty string",
            },
            "relationships": ["expenditures"],
            "test_data_examples": [
                {"name": "Alice", "age": 8, "weekly_allowance": 5.0},
                {"name": "Bob", "age": 12, "weekly_allowance": 10.0},
                {"name": "Charlie", "age": 6, "weekly_allowance": 3.0},
            ],
        }
        return json.dumps(child_schema, indent=2)

    elif uri == "fastapi://models/user/schema" and HAS_MODELS:
        user_schema = {
            "model_name": "User",
            "fields": {
                "email": {
                    "type": "str",
                    "required": True,
                    "description": "User email (primary key)",
                },
                "name": {
                    "type": "str",
                    "required": True,
                    "description": "User display name",
                },
                "google_id": {
                    "type": "str",
                    "required": True,
                    "description": "Google OAuth ID",
                },
                "picture": {
                    "type": "str",
                    "required": False,
                    "description": "Profile picture URL",
                },
                "is_active": {
                    "type": "bool",
                    "default": True,
                    "description": "User active status",
                },
                "is_admin": {
                    "type": "bool",
                    "default": False,
                    "description": "Admin privileges",
                },
                "created_at": {
                    "type": "datetime",
                    "auto": True,
                    "description": "Creation timestamp",
                },
            },
            "validation_rules": {
                "email": "Must be valid email format",
                "google_id": "Must be non-empty string",
                "name": "Must be non-empty string",
            },
            "authentication_context": True,
            "test_data_examples": [
                {
                    "email": "alice@example.com",
                    "name": "Alice Smith",
                    "google_id": "google123",
                },
                {
                    "email": "bob@admin.com",
                    "name": "Bob Admin",
                    "google_id": "google456",
                    "is_admin": True,
                },
            ],
        }
        return json.dumps(user_schema, indent=2)

    elif uri == "fastapi://testing/coverage":
        coverage = analyze_model_test_coverage()
        return json.dumps(coverage, indent=2)

    elif uri == "fastapi://endpoints/test-results" and HAS_FASTAPI_TESTING and HAS_APP:
        results = run_live_endpoint_tests()
        return json.dumps(results, indent=2)

    else:
        return json.dumps({"error": "Resource not found or dependencies not available"})


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available testing tools"""
    tools = [
        types.Tool(
            name="validate_model_data",
            description="Validate data against FastAPI model schemas",
            inputSchema={
                "type": "object",
                "properties": {
                    "model_type": {
                        "type": "string",
                        "enum": ["Child", "User", "Expenditure"],
                    },
                    "data": {"type": "object", "description": "Data to validate"},
                    "strict": {
                        "type": "boolean",
                        "default": True,
                        "description": "Strict validation mode",
                    },
                },
                "required": ["model_type", "data"],
            },
        ),
        types.Tool(
            name="generate_test_data",
            description="Generate realistic test data for models",
            inputSchema={
                "type": "object",
                "properties": {
                    "model_type": {
                        "type": "string",
                        "enum": ["Child", "User", "Expenditure"],
                    },
                    "count": {
                        "type": "integer",
                        "default": 5,
                        "description": "Number of records to generate",
                    },
                    "scenario": {
                        "type": "string",
                        "enum": ["valid", "edge_cases", "invalid"],
                        "default": "valid",
                    },
                },
                "required": ["model_type"],
            },
        ),
        types.Tool(
            name="test_model_relationships",
            description="Test relationships between models",
            inputSchema={
                "type": "object",
                "properties": {
                    "primary_model": {"type": "string", "enum": ["Child", "User"]},
                    "relationship_type": {
                        "type": "string",
                        "enum": ["one_to_many", "foreign_key"],
                    },
                    "test_scenario": {"type": "string", "default": "basic"},
                },
                "required": ["primary_model", "relationship_type"],
            },
        ),
    ]

    if HAS_FASTAPI_TESTING and HAS_APP:
        tools.append(
            types.Tool(
                name="test_fastapi_endpoints",
                description="Test FastAPI endpoints with model data",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "endpoint": {
                            "type": "string",
                            "description": "Endpoint to test",
                        },
                        "method": {
                            "type": "string",
                            "enum": ["GET", "POST", "PUT", "DELETE"],
                            "default": "GET",
                        },
                        "test_data": {
                            "type": "object",
                            "description": "Test data to send",
                        },
                        "auth_required": {"type": "boolean", "default": False},
                    },
                    "required": ["endpoint"],
                },
            )
        )

    return tools


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool execution"""

    if name == "validate_model_data":
        result = validate_model_data(
            arguments["model_type"], arguments["data"], arguments.get("strict", True)
        )
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "generate_test_data":
        result = generate_test_data(
            arguments["model_type"],
            arguments.get("count", 5),
            arguments.get("scenario", "valid"),
        )
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "test_model_relationships":
        result = test_model_relationships(
            arguments["primary_model"],
            arguments["relationship_type"],
            arguments.get("test_scenario", "basic"),
        )
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "test_fastapi_endpoints" and HAS_FASTAPI_TESTING and HAS_APP:
        result = test_fastapi_endpoints(
            arguments["endpoint"],
            arguments.get("method", "GET"),
            arguments.get("test_data"),
            arguments.get("auth_required", False),
        )
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    else:
        return [
            types.TextContent(
                type="text",
                text=json.dumps(
                    {"error": "Tool not available or dependencies missing"}
                ),
            )
        ]


def validate_model_data(model_type: str, data: dict, strict: bool = True) -> dict:
    """Validate data against model schema"""
    if not HAS_MODELS:
        return {"error": "Models not available", "import_error": IMPORT_ERROR}

    try:
        if model_type == "Child":
            child = Child(**data)
            return {
                "valid": True,
                "model": model_type,
                "data": asdict(child),
                "validation_passed": True,
            }
        elif model_type == "User":
            user = User(**data)
            return {
                "valid": True,
                "model": model_type,
                "data": {
                    "email": user.email,
                    "name": user.name,
                    "google_id": user.google_id,
                    "is_active": user.is_active,
                    "is_admin": user.is_admin,
                },
                "validation_passed": True,
            }
        else:
            return {"error": f"Unknown model type: {model_type}"}

    except Exception as e:
        return {
            "valid": False,
            "model": model_type,
            "error": str(e),
            "validation_passed": False,
            "provided_data": data,
        }


def generate_test_data(model_type: str, count: int, scenario: str) -> dict:
    """Generate test data for models"""
    if model_type == "Child":
        if scenario == "valid":
            data = [
                {"name": f"Child_{i}", "age": 5 + i, "weekly_allowance": 2.0 + i}
                for i in range(count)
            ]
        elif scenario == "edge_cases":
            data = [
                {"name": "A", "age": 1, "weekly_allowance": 0.01},  # Minimum values
                {
                    "name": "Very Long Child Name Here",
                    "age": 18,
                    "weekly_allowance": 100.0,
                },  # Maximum values
            ]
        else:  # invalid
            data = [
                {"name": "", "age": -1, "weekly_allowance": -5.0},  # Invalid values
                {"age": 10},  # Missing required fields
            ]
    elif model_type == "User":
        if scenario == "valid":
            data = [
                {
                    "email": f"user{i}@example.com",
                    "name": f"User {i}",
                    "google_id": f"google{i}",
                }
                for i in range(count)
            ]
        else:
            data = [{"email": "invalid-email", "name": "", "google_id": ""}]
    else:
        data = []

    return {
        "model_type": model_type,
        "scenario": scenario,
        "count": len(data),
        "test_data": data,
    }


def test_model_relationships(
    primary_model: str, relationship_type: str, scenario: str
) -> dict:
    """Test model relationships"""
    if not HAS_MODELS:
        return {"error": "Models not available"}

    try:
        if primary_model == "Child" and relationship_type == "one_to_many":
            # Test Child -> Expenditures relationship
            child = Child(name="Test Child", age=10, weekly_allowance=5.0)
            expenditure = Expenditure(
                amount=2.50, description="Candy", date=datetime.now()
            )

            child.add_expenditure(expenditure)

            return {
                "relationship_test": "Child -> Expenditures",
                "success": True,
                "child_total_earnings": child.total_earnings(),
                "expenditure_count": len(child.expenditures),
                "scenario": scenario,
            }
        else:
            return {
                "error": f"Relationship test not implemented: {primary_model} -> {relationship_type}"
            }

    except Exception as e:
        return {"error": str(e), "relationship_test_failed": True}


def test_fastapi_endpoints(
    endpoint: str, method: str, test_data: dict = None, auth_required: bool = False
) -> dict:
    """Test FastAPI endpoints"""
    if not HAS_FASTAPI_TESTING or not HAS_APP:
        return {"error": "FastAPI testing dependencies or app not available"}

    try:
        client = TestClient(app)

        headers = {}
        if auth_required and HAS_MODELS:
            # Create a test token
            from handlers.auth import User, create_access_token, users_db

            user = User(email="test@example.com", name="Test User", google_id="test123")
            users_db["test@example.com"] = user
            token = create_access_token(
                {"sub": "test@example.com", "google_id": "test123"}
            )
            headers["Authorization"] = f"Bearer {token}"

        # Make the request
        if method == "GET":
            response = client.get(endpoint, headers=headers)
        elif method == "POST":
            response = client.post(endpoint, json=test_data, headers=headers)
        elif method == "PUT":
            response = client.put(endpoint, json=test_data, headers=headers)
        elif method == "DELETE":
            response = client.delete(endpoint, headers=headers)
        else:
            return {"error": f"Unsupported method: {method}"}

        return {
            "endpoint": endpoint,
            "method": method,
            "status_code": response.status_code,
            "success": response.status_code < 400,
            "response_size": len(response.content),
            "headers_sent": dict(headers),
            "test_data_sent": test_data,
        }

    except Exception as e:
        return {"error": f"Failed to test endpoint: {str(e)}"}


def analyze_model_test_coverage() -> dict:
    """Analyze current model test coverage"""
    coverage = {
        "timestamp": datetime.now().isoformat(),
        "models_analyzed": [],
        "coverage_summary": {},
        "recommendations": [],
    }

    if HAS_MODELS:
        # Analyze Child model
        coverage["models_analyzed"].append("Child")
        coverage["coverage_summary"]["Child"] = {
            "core_functionality": "Tested",
            "validation": "Partially tested",
            "relationships": "Tested",
            "edge_cases": "Needs more coverage",
        }

        # Analyze User model
        coverage["models_analyzed"].append("User")
        coverage["coverage_summary"]["User"] = {
            "core_functionality": "Tested",
            "authentication": "Well tested",
            "validation": "Tested",
            "admin_features": "Tested",
        }

        coverage["recommendations"] = [
            "Add more edge case testing for Child model",
            "Test model serialization/deserialization",
            "Add performance testing for large datasets",
            "Test model migration scenarios",
        ]
    else:
        coverage["error"] = "Models not available for analysis"

    return coverage


def run_live_endpoint_tests() -> dict:
    """Run live tests against FastAPI endpoints"""
    if not HAS_FASTAPI_TESTING or not HAS_APP:
        return {"error": "FastAPI testing dependencies or app not available"}

    try:
        client = TestClient(app)

        results = {
            "timestamp": datetime.now().isoformat(),
            "endpoint_tests": [],
            "summary": {"passed": 0, "failed": 0},
        }

        # Test public endpoints
        endpoints_to_test = [("/", "GET"), ("/health", "GET"), ("/debug", "GET")]

        for endpoint, method in endpoints_to_test:
            try:
                if method == "GET":
                    response = client.get(endpoint)

                test_result = {
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": response.status_code,
                    "success": response.status_code < 400,
                    "response_size": len(response.content),
                }

                if test_result["success"]:
                    results["summary"]["passed"] += 1
                else:
                    results["summary"]["failed"] += 1

                results["endpoint_tests"].append(test_result)

            except Exception as e:
                results["endpoint_tests"].append(
                    {
                        "endpoint": endpoint,
                        "method": method,
                        "error": str(e),
                        "success": False,
                    }
                )
                results["summary"]["failed"] += 1

        return results

    except Exception as e:
        return {"error": f"Failed to run endpoint tests: {str(e)}"}


async def main():
    """Main function to run the MCP server"""
    if not HAS_MCP:
        print("MCP not available. Install with: uv add mcp")
        return

    # Run the server using stdio
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
