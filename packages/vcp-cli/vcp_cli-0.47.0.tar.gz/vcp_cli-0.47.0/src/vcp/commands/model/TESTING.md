# Model Commands Testing Guide

This document explains how to run different types of tests for the VCP CLI model commands.

## Test Categories

### 1. Unit Tests
Run all unit tests (excludes E2E and integration tests):
```bash
make test
```

### 2. Model-Specific Tests
Run all model-related tests (unit + integration):
```bash
make test-model
```

### 3. Integration Tests
Run integration tests that test real-world scenarios:
```bash
make test-integration
```

### 4. E2E Tests
Run end-to-end tests (requires APP_ENV):
```bash
make test-e2e
```

### 5. All Tests
Run all tests including E2E (requires APP_ENV):
```bash
make test-all
```

### 6. All Tests with Integration
Run all tests including integration tests:
```bash
make test-all-with-integration
```

## Test Configuration

### Default Test Behavior
- **Unit tests**: Run by default with `make test`
- **Integration tests**: Excluded by default, run with `make test-integration`
- **E2E tests**: Excluded by default, require `APP_ENV` environment variable

### Test Markers
Tests are organized using pytest markers:
- `unit`: Unit tests
- `integration`: Integration tests requiring network access
- `e2e`: End-to-end tests requiring APP_ENV

## Running Specific Test Files

### Model-Specific Tests
```bash
# Run all model-related tests (recommended)
make test-model

# Run only model command tests
uv run pytest tests/test_model_*.py

# Run integration tests for model commands
uv run pytest tests/integration/test_model_init_workflow.py -v

# Run GitHub operations integration tests
uv run pytest tests/integration/test_github_operations.py -v
```

### GitHub Authentication Tests
```bash
# Run GitHub auth unit tests
uv run pytest tests/test_github_auth_token_caching.py -v

# Run GitHub auth integration tests
uv run pytest tests/test_github_auth_integration.py -v
```

## Test Environment Setup

### Prerequisites
- Python 3.13+
- `uv` package manager
- Git installed
- Network access (for integration tests)

### Environment Variables
- `APP_ENV`: Required for E2E tests (e.g., `staging`, `production`)
- `VCP_CONFIG_PATH`: Optional, path to config file

## Test Output

### Verbose Output
Add `-v` flag for verbose output:
```bash
make test-integration -v
```

### Coverage Reports
```bash
uv run pytest --cov=src/vcp --cov-report=html
```

## Troubleshooting

### Common Issues

1. **Integration tests failing**: Ensure network access and valid authentication
2. **E2E tests failing**: Check `APP_ENV` environment variable
3. **Permission errors**: Ensure write access to temp directories

### Debug Mode
Run tests with debug logging:
```bash
VCP_LOG_LEVEL=DEBUG make test-integration
```

## Test Development

### Adding New Tests

1. **Unit tests**: Add to `tests/test_*.py` files
2. **Integration tests**: Add to `tests/integration/` directory
3. **E2E tests**: Add to `tests/e2e/` directory

### Test Structure
```python
import pytest
from unittest.mock import Mock, patch

class TestModelCommand:
    def test_basic_functionality(self):
        # Test implementation
        pass
    
    @pytest.mark.integration
    def test_integration_scenario(self):
        # Integration test implementation
        pass
```

## Continuous Integration

### GitHub Actions
Tests run automatically on:
- Pull requests
- Pushes to main branch
- Manual workflow dispatch

### Test Matrix
- Python 3.13
- macOS, Linux, Windows
- Unit, Integration, and E2E tests

## Performance

### Test Execution Time
- **Unit tests**: ~10 seconds
- **Integration tests**: ~30 seconds
- **E2E tests**: ~60 seconds
- **All tests**: ~100 seconds

### Optimization Tips
- Use `make test` for quick feedback during development
- Use `make test-integration` for comprehensive testing
- Use `make test-all` only before merging
