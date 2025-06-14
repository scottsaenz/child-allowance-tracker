"""Basic tests that don't require external dependencies"""

import os
import sys


def test_python_version():
    """Test that we're running on Python 3.13+"""
    assert sys.version_info >= (3, 13)


def test_project_structure():
    """Test that basic project structure exists"""
    project_root = os.path.dirname(os.path.dirname(__file__))

    # Check that key files exist
    assert os.path.exists(os.path.join(project_root, "pyproject.toml"))
    assert os.path.exists(os.path.join(project_root, "lambda_function.py"))
    assert os.path.exists(os.path.join(project_root, "src"))


def test_imports():
    """Test that we can import standard library modules"""
    import json
    import os
    import sys

    # Basic smoke test
    assert json.dumps({"test": True}) == '{"test": true}'
    assert os.path.exists("/")
    assert len(sys.path) > 0
