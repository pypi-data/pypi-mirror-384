"""
Tests for ISTAT MCP server.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from pathlib import Path
from main import (
    get_list_of_available_datasets,
    search_datasets,
    get_dataset_dimensions,
    get_dimension_values,
    get_data,
    get_data_limited,
    get_summary,
    get_url_metadata,
    get_dataset_url,
    download_dataset,
    istat_overview,
)


class TestDatasetDiscovery:
    """Tests for dataset discovery tools."""

    @patch("main.discovery.all_available")
    def test_get_list_of_available_datasets(self, mock_all_available):
        """Test getting list of all available datasets."""
        # Setup mock
        mock_df = pd.DataFrame({
            "id": ["139_176", "139_177"],
            "name": ["Dataset 1", "Dataset 2"]
        })
        mock_all_available.return_value = mock_df

        # Execute
        result = get_list_of_available_datasets()

        # Verify
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert len(parsed) == 2
        assert parsed[0]["id"] == "139_176"
        mock_all_available.assert_called_once()

    @patch("main.discovery.search_dataset")
    def test_search_datasets(self, mock_search):
        """Test searching datasets by query."""
        # Setup mock
        mock_df = pd.DataFrame({
            "id": ["139_176"],
            "name": ["Import Export Dataset"],
            "description": ["Trade statistics"]
        })
        mock_search.return_value = mock_df

        # Execute
        result = search_datasets("import")

        # Verify
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert len(parsed) == 1
        assert "Import Export" in parsed[0]["name"]
        mock_search.assert_called_once_with("import")

    @patch("main.discovery.DataSet")
    def test_get_dataset_dimensions(self, mock_dataset_class):
        """Test getting dimensions of a dataset."""
        # Setup mock
        mock_ds = Mock()
        mock_df = pd.DataFrame({
            "dimension": ["FREQ", "TIPO_DATO"],
            "description": ["Frequency", "Data Type"]
        })
        mock_ds.dimensions_info.return_value = mock_df
        mock_dataset_class.return_value = mock_ds

        # Execute
        result = get_dataset_dimensions("139_176")

        # Verify
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert len(parsed) == 2
        assert parsed[0]["dimension"] == "FREQ"
        mock_dataset_class.assert_called_once_with(dataflow_identifier="139_176")
        mock_ds.dimensions_info.assert_called_once()

    @patch("main.discovery.DataSet")
    def test_get_dimension_values(self, mock_dataset_class):
        """Test getting values of a specific dimension."""
        # Setup mock
        mock_ds = Mock()
        mock_df = pd.DataFrame({
            "code": ["ISAV", "ESAV"],
            "name": ["Import", "Export"]
        })
        mock_ds.get_dimension_values.return_value = mock_df
        mock_dataset_class.return_value = mock_ds

        # Execute
        result = get_dimension_values("139_176", "TIPO_DATO")

        # Verify
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert len(parsed) == 2
        assert parsed[0]["code"] == "ISAV"
        mock_dataset_class.assert_called_once_with(dataflow_identifier="139_176")
        mock_ds.get_dimension_values.assert_called_once_with("TIPO_DATO")

    @patch("main.discovery.DataSet")
    def test_get_dataset_dimensions_error(self, mock_dataset_class):
        """Test error handling in get_dataset_dimensions."""
        # Setup mock to raise exception
        mock_dataset_class.side_effect = Exception("API Error")

        # Execute
        result = get_dataset_dimensions("invalid_id")

        # Verify error response
        parsed = json.loads(result)
        assert "error" in parsed
        assert parsed["error_type"] == "Exception"
        assert parsed["dataflow_identifier"] == "invalid_id"
        assert "suggestion" in parsed

    @patch("main.discovery.DataSet")
    def test_get_dimension_values_error(self, mock_dataset_class):
        """Test error handling in get_dimension_values."""
        # Setup mock
        mock_ds = Mock()
        mock_ds.get_dimension_values.side_effect = Exception("Dimension not found")
        mock_dataset_class.return_value = mock_ds

        # Execute
        result = get_dimension_values("139_176", "INVALID_DIM")

        # Verify error response
        parsed = json.loads(result)
        assert "error" in parsed
        assert parsed["error_type"] == "Exception"
        assert parsed["dimension"] == "INVALID_DIM"


class TestDataRetrieval:
    """Tests for data retrieval tools."""

    @patch("main.retrieval.get_data")
    @patch("main.discovery.DataSet")
    def test_get_data_success(self, mock_dataset_class, mock_get_data):
        """Test successful data retrieval."""
        # Setup mock
        mock_ds = Mock()
        mock_dataset_class.return_value = mock_ds

        mock_df = pd.DataFrame({
            "TIME_PERIOD": ["2023-01", "2023-02"],
            "VALUE": [100, 200]
        })
        mock_get_data.return_value = mock_df

        # Execute
        filters = {"freq": "M", "tipo_dato": ["ISAV"]}
        result = get_data("139_176", filters)

        # Verify
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert len(parsed) == 2
        mock_ds.set_filters.assert_called_once_with(**filters)
        mock_get_data.assert_called_once_with(mock_ds)

    @patch("main.get_dataset_url")
    @patch("main.retrieval.get_data")
    @patch("main.discovery.DataSet")
    def test_get_data_exception_returns_url(self, mock_dataset_class, mock_get_data, mock_get_url):
        """Test that get_data returns URL when exception occurs."""
        # Setup mock
        mock_ds = Mock()
        mock_dataset_class.return_value = mock_ds
        mock_get_data.side_effect = Exception("Timeout")
        mock_get_url.return_value = json.dumps({"url": "http://example.com"})

        # Execute
        filters = {"freq": "M"}
        result = get_data("139_176", filters)

        # Verify
        assert "url" in result.lower()
        mock_get_url.assert_called_once_with("139_176", filters)

    @patch("main.retrieval.get_data")
    @patch("main.discovery.DataSet")
    def test_get_data_limited(self, mock_dataset_class, mock_get_data):
        """Test limited data retrieval."""
        # Setup mock
        mock_ds = Mock()
        mock_dataset_class.return_value = mock_ds

        # Create larger dataset
        mock_df = pd.DataFrame({
            "TIME_PERIOD": [f"2023-{i:02d}" for i in range(1, 13)],
            "VALUE": list(range(100, 112))
        })
        mock_get_data.return_value = mock_df

        # Execute with limit of 5
        filters = {"freq": "M"}
        result = get_data_limited("139_176", filters, 5)

        # Verify
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert len(parsed) == 5
        mock_ds.set_filters.assert_called_once_with(**filters)

    @patch("main.retrieval.get_data")
    @patch("main.discovery.DataSet")
    def test_get_summary(self, mock_dataset_class, mock_get_data):
        """Test getting dataset summary."""
        # Setup mock
        mock_ds = Mock()
        mock_dataset_class.return_value = mock_ds

        mock_df = pd.DataFrame({
            "TIME_PERIOD": ["2023-01", "2023-02", "2023-03"],
            "VALUE": [100.5, 200.3, 150.7]
        })
        mock_get_data.return_value = mock_df

        # Execute
        filters = {"freq": "M"}
        result = get_summary("139_176", filters)

        # Verify
        assert isinstance(result, str)
        summary = json.loads(result)
        assert summary["rows"] == 3
        assert "TIME_PERIOD" in summary["columns"]
        assert "VALUE" in summary["columns"]
        assert "file_size_mb" in summary
        assert "head" in summary
        assert len(summary["head"]) <= 5
        assert "column_stats" in summary


class TestURLAndDownload:
    """Tests for URL metadata and download tools."""

    @patch("main.requests.head")
    def test_get_url_metadata_success(self, mock_head):
        """Test successful URL metadata retrieval."""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {
            "Content-Type": "text/csv",
            "Content-Length": "2048000",
            "Last-Modified": "Mon, 01 Jan 2024 00:00:00 GMT",
            "Server": "nginx"
        }
        mock_head.return_value = mock_response

        # Execute
        result = get_url_metadata("http://example.com/data.csv")

        # Verify
        assert result["status_code"] == 200
        assert result["content_type"] == "text/csv"
        assert result["human_readable_size"] == "1.95 MB"
        mock_head.assert_called_once()

    @patch("main.requests.head")
    def test_get_url_metadata_sizes(self, mock_head):
        """Test URL metadata with different file sizes."""
        test_cases = [
            (500, "500 B"),
            (2048, "2.00 KB"),
            (2097152, "2.00 MB"),
            (2147483648, "2.00 GB"),
        ]

        for size_bytes, expected_size in test_cases:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"Content-Length": str(size_bytes)}
            mock_head.return_value = mock_response

            result = get_url_metadata("http://example.com/data.csv")
            assert result["human_readable_size"] == expected_size

    @patch("main.requests.head")
    def test_get_url_metadata_error(self, mock_head):
        """Test URL metadata retrieval with error."""
        # Setup mock to raise exception
        mock_head.side_effect = Exception("Network error")

        # Execute
        result = get_url_metadata("http://example.com/data.csv")

        # Verify
        assert "error" in result
        assert "status" in result
        assert result["status"] == "failed to retrieve metadata"

    @patch("main.get_url_metadata")
    @patch("main.discovery.DataSet")
    def test_get_dataset_url(self, mock_dataset_class, mock_get_metadata):
        """Test getting dataset URL with metadata."""
        # Setup mock
        mock_ds = Mock()
        mock_ds.identifiers = {"df_id": "139_176"}
        mock_ds.filters = {"FREQ": "M", "TIPO_DATO": ["ISAV"], "PAESE_PARTNER": "WORLD", "ITTER107": ".", "MERCE": "."}

        # Mock dimensions_info for build_complete_url_key
        mock_dimensions_df = pd.DataFrame({
            "dimension": ["FREQ", "TIPO_DATO", "PAESE_PARTNER", "ITTER107", "MERCE"],
            "description": ["Frequency", "Data Type", "Country", "Territory", "Commodity"]
        })
        mock_ds.dimensions_info.return_value = mock_dimensions_df
        mock_dataset_class.return_value = mock_ds

        mock_metadata = {
            "url": "http://sdmx.istat.it/SDMXWS/rest/data/139_176/M.ISAV.WORLD",
            "status_code": 200,
            "content_type": "application/vnd.sdmx.genericdata+xml",
            "content_length": "1024000",
            "human_readable_size": "1000.00 KB"
        }
        mock_get_metadata.return_value = mock_metadata

        # Execute
        filters = {"freq": "M", "tipo_dato": ["ISAV"]}
        result = get_dataset_url("139_176", filters)

        # Verify
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert "url" in parsed
        assert "sdmx.istat.it" in parsed["url"]
        assert parsed["status_code"] == 200
        mock_ds.set_filters.assert_called_once_with(**filters)
        mock_get_metadata.assert_called_once()
        # Verify that get_url_metadata was called with use_get=True
        call_args = mock_get_metadata.call_args
        assert call_args[1]["use_get"] == True

    @patch("main.requests.get")
    @patch("main.STORAGE_DIR", Path("/tmp/mcp_test_data"))
    def test_download_dataset_success_default_path(self, mock_get):
        """Test successful dataset download to default path."""
        # Setup mock
        storage_dir = Path("/tmp/mcp_test_data")
        storage_dir.mkdir(parents=True, exist_ok=True)

        mock_response = Mock()
        mock_response.headers = {"Content-Type": "text/csv"}
        mock_response.iter_content = lambda chunk_size: [b"data" * 100]
        mock_get.return_value = mock_response

        with patch("builtins.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            result = download_dataset("http://example.com/my_data.csv")

        parsed = json.loads(result)
        assert parsed["status"] == "success"
        assert parsed["output_path"] == str(storage_dir / "my_data.csv")
        assert parsed["size_bytes"] == 400
        mock_open.assert_called_with(storage_dir / "my_data.csv", 'wb')

    @patch("main.requests.get")
    @patch("main.STORAGE_DIR", Path("/tmp/mcp_test_data"))
    def test_download_dataset_success_relative_path(self, mock_get):
        """Test successful dataset download to a relative path."""
        storage_dir = Path("/tmp/mcp_test_data")
        storage_dir.mkdir(parents=True, exist_ok=True)

        mock_response = Mock()
        mock_response.headers = {"Content-Type": "text/csv"}
        mock_response.iter_content = lambda chunk_size: [b"data" * 100]
        mock_get.return_value = mock_response

        with patch("builtins.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            result = download_dataset("http://example.com/data.csv", output_path="subdir/custom_name.csv")

        parsed = json.loads(result)
        assert parsed["status"] == "success"
        assert parsed["output_path"] == str(storage_dir / "subdir" / "custom_name.csv")
        # Check that the parent directory was created
        mock_open.assert_called_with(storage_dir / "subdir" / "custom_name.csv", 'wb')


    @patch("main.requests.get")
    def test_download_dataset_request_error(self, mock_get):
        """Test download with a request error."""
        import requests
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        result = download_dataset("http://example.com/data.csv")

        parsed = json.loads(result)
        assert parsed["status"] == "error"
        assert parsed["error_type"] == "RequestException"
        assert "Network error" in parsed["error_message"]
        assert "suggestion" in parsed

    @patch("main.STORAGE_DIR", Path("/tmp/mcp_test_data"))
    def test_download_dataset_permission_error_outside_storage(self):
        """Test that downloading outside of STORAGE_DIR is forbidden."""
        result = download_dataset(
            "http://example.com/data.csv",
            output_path="/etc/passwd"
        )
        parsed = json.loads(result)
        assert parsed["status"] == "error"
        assert parsed["error_type"] == "PermissionError"
        assert "Output must be within the storage directory" in parsed["error_message"]
        assert "suggestion" in parsed

    @patch("main.requests.get")
    @patch("main.STORAGE_DIR", Path("/tmp/mcp_test_data"))
    def test_download_dataset_io_error_on_write(self, mock_get):
        """Test download with a file write (IOError) error."""
        storage_dir = Path("/tmp/mcp_test_data")
        storage_dir.mkdir(parents=True, exist_ok=True)

        mock_response = Mock()
        mock_response.headers = {"Content-Type": "text/csv"}
        mock_response.iter_content = lambda chunk_size: [b"data" * 100]
        mock_get.return_value = mock_response

        with patch("builtins.open", side_effect=IOError("Disk full")):
            result = download_dataset("http://example.com/data.csv")

        parsed = json.loads(result)
        assert parsed["status"] == "error"
        assert parsed["error_type"] == "OSError"
        assert "Failed to write file" in parsed["error_message"]
        assert "Disk full" in parsed["error_message"]
        assert "suggestion" in parsed

class TestResources:
    """Tests for MCP resources."""

    def test_istat_overview(self):
        """Test ISTAT overview resource."""
        result = istat_overview()

        assert isinstance(result, str)
        assert "ISTAT API" in result
        assert "get_data" in result
        assert "get_dataset_url" in result
        assert "download_dataset" in result


class TestIntegration:
    """Integration tests."""

    @patch("main.retrieval.get_data")
    @patch("main.discovery.DataSet")
    def test_full_workflow_mock(self, mock_dataset_class, mock_get_data):
        """Test a full workflow: search, inspect, retrieve data."""
        # Setup mock dataset
        mock_ds = Mock()
        mock_ds.identifiers = {"df_id": "139_176"}
        mock_ds.filters = {}
        mock_dataset_class.return_value = mock_ds

        # Mock dimensions
        mock_ds.dimensions_info.return_value = pd.DataFrame({
            "dimension": ["FREQ", "TIPO_DATO"],
            "description": ["Frequency", "Data Type"]
        })

        # Mock dimension values
        mock_ds.get_dimension_values.return_value = pd.DataFrame({
            "code": ["M", "Q"],
            "name": ["Monthly", "Quarterly"]
        })

        # Mock data retrieval
        mock_get_data.return_value = pd.DataFrame({
            "TIME_PERIOD": ["2023-01"],
            "VALUE": [100]
        })

        # Execute workflow
        dimensions = get_dataset_dimensions("139_176")
        assert len(json.loads(dimensions)) == 2

        dim_values = get_dimension_values("139_176", "FREQ")
        assert len(json.loads(dim_values)) == 2

        data = get_data("139_176", {"freq": "M"})
        assert len(json.loads(data)) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])