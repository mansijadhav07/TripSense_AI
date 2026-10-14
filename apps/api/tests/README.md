# TripSense AI - Backend Testing Guide

## Overview

This directory contains comprehensive test suites for the TripSense AI backend API. Tests are organized by functionality and follow pytest best practices.

## Test Structure

```
tests/
├── __init__.py                 # Package initialization
├── conftest.py                 # Pytest fixtures and configuration
├── test_health.py              # Health check endpoint tests
├── test_auth.py                # Authentication tests
├── test_security.py            # Security utility tests
└── test_models.py              # Database model tests
```

## Running Tests

### Run All Tests
```bash
cd apps/api
pytest
```

### Run with Coverage
```bash
pytest --cov=. --cov-report=html
```

### Run Specific Test File
```bash
pytest tests/test_auth.py
```

### Run Specific Test
```bash
pytest tests/test_auth.py::test_user_registration
```

### Run Tests by Marker
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Database tests only
pytest -m db
```

### Run in Verbose Mode
```bash
pytest -v
```

## Test Markers

- `@pytest.mark.unit` - Unit tests (isolated, no external dependencies)
- `@pytest.mark.integration` - Integration tests (test multiple components together)
- `@pytest.mark.slow` - Tests that take longer to run
- `@pytest.mark.db` - Tests that require database access

## Fixtures

### Database Fixtures

- `test_engine` - SQLite in-memory database engine for testing
- `db_session` - Fresh database session for each test
- `client` - FastAPI TestClient with database override

### Authentication Fixtures

- `sample_user_data` - Sample user registration data
- `authenticated_client` - Pre-authenticated TestClient with valid JWT
- `test_settings` - Testing configuration override

### Data Fixtures

- `sample_preference_data` - Sample user preference data

## Test Coverage

Coverage reports are generated in three formats:
- **Terminal**: Summary displayed after test run
- **HTML**: Detailed report in `htmlcov/index.html`
- **XML**: CI-compatible format in `coverage.xml`

### View HTML Coverage Report
```bash
pytest --cov=. --cov-report=html
open htmlcov/index.html  # macOS
```

## Writing New Tests

### Basic Test Structure

```python
import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_something(client: TestClient):
    """Test description"""
    response = client.get("/endpoint")
    
    assert response.status_code == 200
    assert "key" in response.json()
```

### Using Fixtures

```python
@pytest.mark.integration
def test_with_auth(authenticated_client: TestClient):
    """Test that requires authentication"""
    response = authenticated_client.get("/api/v1/protected")
    assert response.status_code == 200
```

### Database Tests

```python
@pytest.mark.unit
@pytest.mark.db
def test_model(db_session: Session):
    """Test database model"""
    user = User(email="test@test.com")
    db_session.add(user)
    db_session.commit()
    
    assert user.id is not None
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Descriptive Names**: Use clear, descriptive test names
3. **Single Assertion Focus**: Test one thing at a time
4. **Use Fixtures**: Reuse common setup via fixtures
5. **Mark Appropriately**: Use markers to categorize tests
6. **Document**: Add docstrings to complex tests

## CI/CD Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# .github/workflows/test.yml example
- name: Run tests
  run: |
    cd apps/api
    pytest --cov=. --cov-report=xml
    
- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./apps/api/coverage.xml
```

## Performance Testing

For performance testing, use pytest-benchmark:

```python
def test_performance(benchmark):
    result = benchmark(expensive_function)
    assert result is not None
```

## Debugging Tests

### Run with print statements
```bash
pytest -s
```

### Drop into debugger on failure
```bash
pytest --pdb
```

### Run last failed tests only
```bash
pytest --lf
```

## Test Data

Test data is managed through fixtures and should never touch production data. All tests use in-memory SQLite database that is created fresh for each test session.

## Next Steps

As the application grows, add tests for:
- [ ] Recommendation endpoints
- [ ] Preference management
- [ ] Hotel data endpoints
- [ ] Search functionality
- [ ] Rate limiting
- [ ] Error handling edge cases
- [ ] Performance benchmarks

## References

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)
