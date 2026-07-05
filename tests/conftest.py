"""Shared test fixtures for CodeTruth test suite."""

import os
import sys
import tempfile
from pathlib import Path

import pytest


# Add the project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def sample_python_file(temp_dir):
    """Create a sample Python file for testing."""
    file_path = temp_dir / "sample.py"
    content = '''
"""Sample module for testing."""

def calculate_sum(numbers: list[int]) -> int:
    """Calculate the sum of a list of numbers."""
    return sum(numbers)


def calculate_average(numbers: list[float]) -> float:
    """Calculate the arithmetic mean."""
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)


class DataProcessor:
    """A simple data processing class."""

    def __init__(self, data: list):
        self.data = data

    def process(self) -> list:
        """Process the data."""
        return [x * 2 for x in self.data]
'''
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture
def sample_code_with_issues():
    """Sample code with various quality issues."""
    return '''
def f():
    password = "admin123"
    api_key = "sk-abc"
    exec(user_input)
    x = 1
    return x
'''


@pytest.fixture
def sample_large_code():
    """Large code sample for compression testing."""
    functions = []
    for i in range(100):
        functions.append(f'''
def function_{i}(param1, param2):
    """Function number {i}."""
    result = param1 + param2 * {i}
    return result
''')
    return '\n'.join(functions)