# Testing Guide

This document explains how to run tests for the ISTAT MCP server.

---

## ✅ Recent Fix: SDMX URL Generation Issue

### Problem
The `get_dataset_url` function was generating incomplete SDMX URLs that were missing dimension values. SDMX REST APIs require ALL dimensions to be specified in the URL, even if some dimensions are unfiltered.

Example error:
```
http://sdmx.istat.it/SDMXWS/rest/data/101_1033/A.IT.ALL
Error: "Not enough key values in query, expecting 5 got 3"
```

### Solution
1. **Fixed dimension handling**: Created `build_complete_url_key()` function that:
   - Gets all dimensions from the dataset in the correct order
   - Includes empty strings for unfiltered dimensions (e.g., `A.IT...` for 5 dimensions with 2 filtered)
   - Properly handles the istatapi library's use of `.` to represent "ALL" values

2. **Fixed HTTP request method**: Changed from HEAD to GET with `stream=True` because:
   - ISTAT SDMX API returns 404 for HEAD requests
   - GET with stream=True gets headers without downloading full content
   - Properly returns 200 status code and content-type metadata

### Verification

#### Dataset 139_176 (Import/Export)
```python
get_dataset_url('139_176', {'freq': 'M', 'tipo_dato': ['ISAV', 'ESAV'], 'paese_partner': 'WORLD'})
```
- **URL**: `http://sdmx.istat.it/SDMXWS/rest/data/139_176/M..WORLD..ISAV+ESAV`
- **Status**: 200 ✓

#### Dataset 101_1033 (Slaughtering)
```python
get_dataset_url('101_1033', {'freq': 'A', 'itter107': 'IT'})
```
- **URL**: `http://sdmx.istat.it/SDMXWS/rest/data/101_1033/A.IT...`
- **Status**: 200 ✓

---

## Setup

The project uses `uv` for dependency management. Development dependencies are already configured in `pyproject.toml`.

## Running Tests

### Run all tests

```bash
uv run pytest
```

### Run tests with coverage

```bash
uv run pytest --cov=main --cov-report=html --cov-report=term
```

This will generate a coverage report in `htmlcov/index.html`.

To see which lines are missing coverage:

```bash
uv run pytest --cov=main --cov-report=term-missing
```

### Run specific test classes

```bash
# Test only dataset discovery
uv run pytest test_main.py::TestDatasetDiscovery -v

# Test only data retrieval
uv run pytest test_main.py::TestDataRetrieval -v

# Test only URL and download
uv run pytest test_main.py::TestURLAndDownload -v
```

### Run specific test functions

```bash
uv run pytest test_main.py::TestDatasetDiscovery::test_search_datasets -v
```

### Run with different verbosity

```bash
# Quiet mode
uv run pytest -q

# Verbose mode
uv run pytest -v

# Very verbose mode (shows all output)
uv run pytest -vv
```

## Test Structure

The test suite is organized into the following classes:

- **TestDatasetDiscovery**: Tests for dataset discovery tools
  - `test_get_list_of_available_datasets()`
  - `test_search_datasets()`
  - `test_get_dataset_dimensions()`
  - `test_get_dimension_values()`

- **TestDataRetrieval**: Tests for data retrieval tools
  - `test_get_data_success()`
  - `test_get_data_exception_returns_url()`
  - `test_get_data_limited()`
  - `test_get_summary()`

- **TestURLAndDownload**: Tests for URL metadata and download tools
  - `test_get_url_metadata_success()`
  - `test_get_url_metadata_sizes()`
  - `test_get_url_metadata_error()`
  - `test_get_dataset_url()`
  - `test_download_dataset_success()`
  - `test_download_dataset_request_error()`
  - `test_download_dataset_io_error()`

- **TestResources**: Tests for MCP resources
  - `test_istat_overview()`

- **TestIntegration**: Integration tests
  - `test_full_workflow_mock()`

## Testing Approach

The tests use mocking to avoid making actual API calls to ISTAT. This ensures:
- Tests run quickly
- Tests are reliable and don't depend on network connectivity
- Tests don't consume API quota
- Tests can simulate error conditions

## Coverage

The test suite currently provides **88% code coverage**. To view coverage statistics:

```bash
uv run pytest --cov=main --cov-report=term-missing
```

This shows which lines are not covered by tests.

## Continuous Integration

You can add these tests to your CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install uv
        uses: astral-sh/setup-uv@v1
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Run tests
        run: uv run pytest --cov=main --cov-report=xml
```

## Adding New Tests

When adding new tools to the MCP server:

1. Add test functions to the appropriate test class
2. Use `@patch` to mock external dependencies
3. Test both success and error cases
4. Verify return types and data structures
5. Run tests to ensure they pass

Example:

```python
@patch("main.discovery.some_new_function")
def test_my_new_tool(self, mock_function):
    # Setup mock
    mock_function.return_value = expected_value

    # Execute
    result = my_new_tool("param")

    # Verify
    assert result == expected_result
    mock_function.assert_called_once_with("param")
```
