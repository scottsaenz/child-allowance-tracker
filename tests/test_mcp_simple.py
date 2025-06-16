"""
Simple MCP-style testing without full MCP server
Tests FastAPI models with enhanced capabilities
"""

import json
from datetime import datetime
from typing import Any

# Import our models
try:
    from fastapi.testclient import TestClient

    from app import app
    from handlers.auth import User, create_access_token, users_db
    from models import Child, Expenditure

    HAS_ALL_DEPS = True
except ImportError as e:
    HAS_ALL_DEPS = False
    IMPORT_ERROR = str(e)


class FastAPIModelTester:
    """Enhanced FastAPI model testing with MCP-style capabilities"""

    def __init__(self):
        self.has_deps = HAS_ALL_DEPS
        self.import_error = IMPORT_ERROR if not HAS_ALL_DEPS else None
        self.client = TestClient(app) if HAS_ALL_DEPS else None

    def get_status(self) -> dict[str, Any]:
        """Get testing system status"""
        return {
            "dependencies_available": self.has_deps,
            "import_error": self.import_error,
            "timestamp": datetime.now().isoformat(),
            "capabilities": {
                "model_validation": self.has_deps,
                "schema_analysis": self.has_deps,
                "endpoint_testing": self.has_deps,
                "relationship_testing": self.has_deps,
            },
        }

    def analyze_child_model(self) -> dict[str, Any]:
        """Analyze Child model structure and capabilities"""
        if not self.has_deps:
            return {"error": "Dependencies not available"}

        # Create a test child to analyze
        child = Child(name="Test Analysis", age=10, weekly_allowance=5.0)

        return {
            "model_name": "Child",
            "fields": {
                "id": {"type": "str", "value": child.id, "required": True},
                "name": {"type": "str", "value": child.name, "required": True},
                "age": {"type": "int", "value": child.age, "required": True},
                "weekly_allowance": {
                    "type": "float",
                    "value": child.weekly_allowance,
                    "required": True,
                },
                "expenditures": {
                    "type": "List[Expenditure]",
                    "value": len(child.expenditures),
                    "required": False,
                },
            },
            "methods": {
                "total_earnings": {
                    "returns": "float",
                    "current_value": child.total_earnings(),
                },
                "add_expenditure": {
                    "accepts": "Expenditure",
                    "modifies": "expenditures",
                },
            },
            "validation_tests": self._validate_child_model(),
        }

    def analyze_user_model(self) -> dict[str, Any]:
        """Analyze User model structure and capabilities"""
        if not self.has_deps:
            return {"error": "Dependencies not available"}

        user = User(email="test@example.com", name="Test User", google_id="google123")

        return {
            "model_name": "User",
            "fields": {
                "email": {"type": "str", "value": user.email, "required": True},
                "name": {"type": "str", "value": user.name, "required": True},
                "google_id": {"type": "str", "value": user.google_id, "required": True},
                "picture": {"type": "str", "value": user.picture, "required": False},
                "is_active": {"type": "bool", "value": user.is_active, "default": True},
                "is_admin": {"type": "bool", "value": user.is_admin, "default": False},
            },
            "authentication_context": True,
            "validation_tests": self._validate_user_model(),
        }

    def test_model_relationships(self) -> dict[str, Any]:
        """Test relationships between models"""
        if not self.has_deps:
            return {"error": "Dependencies not available"}

        # Test Child -> Expenditure relationship
        child = Child(name="Relationship Test", age=8, weekly_allowance=4.0)
        expenditure = Expenditure(
            amount=1.50, description="Test purchase", date=datetime.now()
        )

        # Test adding expenditure
        initial_count = len(child.expenditures)
        child.add_expenditure(expenditure)
        final_count = len(child.expenditures)

        return {
            "child_expenditure_relationship": {
                "test": "Child.add_expenditure(Expenditure)",
                "initial_expenditures": initial_count,
                "final_expenditures": final_count,
                "relationship_working": final_count > initial_count,
                "expenditure_details": {
                    "amount": expenditure.amount,
                    "description": expenditure.description,
                    "id": expenditure.id,
                },
            }
        }

    def test_authentication_flow(self) -> dict[str, Any]:
        """Test authentication flow with models"""
        if not self.has_deps:
            return {"error": "Dependencies not available"}

        # Clear users for clean test
        users_db.clear()

        # Create test user
        user = User(
            email="auth-test@example.com", name="Auth Test User", google_id="auth123"
        )
        users_db[user.email] = user

        # Create JWT token
        token = create_access_token({"sub": user.email, "google_id": user.google_id})

        # Test authenticated endpoint
        response = self.client.get(
            "/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

        return {
            "authentication_test": {
                "user_created": True,
                "token_created": bool(token),
                "auth_endpoint_status": response.status_code,
                "auth_endpoint_working": response.status_code == 200,
                "user_data": {
                    "email": user.email,
                    "name": user.name,
                    "is_active": user.is_active,
                },
            }
        }

    def test_protected_endpoints(self) -> dict[str, Any]:
        """Test protected endpoints with authentication"""
        if not self.has_deps:
            return {"error": "Dependencies not available"}

        # Clear users
        users_db.clear()

        # Create test user
        user = User(
            email="protected-test@example.com",
            name="Protected Test User",
            google_id="protected123",
        )
        users_db[user.email] = user
        token = create_access_token({"sub": user.email, "google_id": user.google_id})

        results = {}

        # Test GET /children (should require auth)
        no_auth_response = self.client.get("/children")
        auth_response = self.client.get(
            "/children", headers={"Authorization": f"Bearer {token}"}
        )

        results["children_endpoint"] = {
            "without_auth": {
                "status": no_auth_response.status_code,
                "protected": no_auth_response.status_code == 403,
            },
            "with_auth": {
                "status": auth_response.status_code,
                "working": auth_response.status_code == 200,
            },
        }

        # Test POST /children (should require auth and add owner)
        child_data = {"name": "Protected Test Child", "age": 9, "weekly_allowance": 6.0}

        create_response = self.client.post(
            "/children", headers={"Authorization": f"Bearer {token}"}, json=child_data
        )

        results["create_child_endpoint"] = {
            "status": create_response.status_code,
            "working": create_response.status_code == 200,
            "has_owner_email": False,
        }

        if create_response.status_code == 200:
            response_data = create_response.json()
            results["create_child_endpoint"]["response_data"] = response_data
            results["create_child_endpoint"]["has_owner_email"] = (
                "owner_email" in response_data
            )

        return results

    def generate_test_scenarios(
        self, model_type: str, count: int = 5
    ) -> dict[str, Any]:
        """Generate test scenarios for models"""
        if not self.has_deps:
            return {"error": "Dependencies not available"}

        scenarios = {
            "model_type": model_type,
            "generated_count": count,
            "scenarios": {},
        }

        if model_type == "Child":
            scenarios["scenarios"]["valid"] = [
                {"name": f"Child {i}", "age": 5 + i, "weekly_allowance": 2.0 + i}
                for i in range(count)
            ]
            scenarios["scenarios"]["edge_cases"] = [
                {"name": "A", "age": 1, "weekly_allowance": 0.01},
                {"name": "Very Long Name Here", "age": 18, "weekly_allowance": 100.0},
            ]
            scenarios["scenarios"]["boundary_tests"] = [
                {"name": "Boundary Test", "age": 0, "weekly_allowance": 0.0},
                {"name": "Max Test", "age": 21, "weekly_allowance": 1000.0},
            ]

        elif model_type == "User":
            scenarios["scenarios"]["valid"] = [
                {
                    "email": f"user{i}@example.com",
                    "name": f"User {i}",
                    "google_id": f"google{i}",
                }
                for i in range(count)
            ]
            scenarios["scenarios"]["admin_users"] = [
                {
                    "email": "admin@example.com",
                    "name": "Admin User",
                    "google_id": "admin123",
                    "is_admin": True,
                }
            ]

        return scenarios

    def run_comprehensive_test_suite(self) -> dict[str, Any]:
        """Run comprehensive test suite"""
        if not self.has_deps:
            return {
                "error": "Dependencies not available",
                "import_error": self.import_error,
            }

        suite_results = {
            "timestamp": datetime.now().isoformat(),
            "test_results": {},
            "summary": {"total_tests": 0, "passed": 0, "failed": 0},
        }

        # Run all tests
        tests = [
            ("status", self.get_status),
            ("child_model_analysis", self.analyze_child_model),
            ("user_model_analysis", self.analyze_user_model),
            ("model_relationships", self.test_model_relationships),
            ("authentication_flow", self.test_authentication_flow),
            ("protected_endpoints", self.test_protected_endpoints),
        ]

        for test_name, test_func in tests:
            try:
                result = test_func()
                suite_results["test_results"][test_name] = {
                    "status": "passed",
                    "result": result,
                }
                suite_results["summary"]["passed"] += 1
            except Exception as e:
                suite_results["test_results"][test_name] = {
                    "status": "failed",
                    "error": str(e),
                }
                suite_results["summary"]["failed"] += 1

            suite_results["summary"]["total_tests"] += 1

        return suite_results

    def _validate_child_model(self) -> list[dict[str, Any]]:
        """Internal method to validate Child model"""
        tests = []

        # Test valid child creation
        try:
            child = Child(name="Valid Child", age=10, weekly_allowance=5.0)
            tests.append(
                {"test": "valid_child_creation", "passed": True, "child_id": child.id}
            )
        except Exception as e:
            tests.append(
                {"test": "valid_child_creation", "passed": False, "error": str(e)}
            )

        # Test invalid child creation (missing fields)
        try:
            Child()  # Should fail
            tests.append(
                {
                    "test": "invalid_child_creation",
                    "passed": False,
                    "note": "Should have failed but didn't",
                }
            )
        except Exception:
            tests.append(
                {
                    "test": "invalid_child_creation",
                    "passed": True,
                    "note": "Correctly failed for missing required fields",
                }
            )

        return tests

    def _validate_user_model(self) -> list[dict[str, Any]]:
        """Internal method to validate User model"""
        tests = []

        # Test valid user creation
        try:
            user = User(
                email="valid@example.com", name="Valid User", google_id="valid123"
            )
            tests.append(
                {
                    "test": "valid_user_creation",
                    "passed": True,
                    "user_email": user.email,
                }
            )
        except Exception as e:
            tests.append(
                {"test": "valid_user_creation", "passed": False, "error": str(e)}
            )

        return tests


def main():
    """Main function to run the enhanced testing"""
    print("🚀 FastAPI Model Tester (MCP-Style)")
    print("=" * 50)

    tester = FastAPIModelTester()

    # Run comprehensive test suite
    results = tester.run_comprehensive_test_suite()

    # Print results
    print(json.dumps(results, indent=2))

    # Summary
    summary = results.get("summary", {})
    total = summary.get("total_tests", 0)
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)

    print("\n📊 Test Summary:")
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/total*100):.1f}%" if total > 0 else "No tests run")


if __name__ == "__main__":
    main()
