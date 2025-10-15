"""
FastMCP quickstart example.

cd to the `examples/snippets/clients` directory and run:
    uv run server fastmcp_quickstart stdio
"""

from mcp.server.fastmcp import FastMCP
from istatapi import discovery, retrieval
from typing import Dict, Optional
import json
import datetime
import numpy as np
import pandas as pd
import requests
import os
from pathlib import Path
import logging
import sys
import platform
import traceback

# Configure logging to stderr (visible in Claude Desktop logs)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr,
    force=True
)
logger = logging.getLogger(__name__)

# --- Configuration ---

def detect_runtime_env() -> str:
    """Detects the current runtime environment (e.g., 'wsl', 'linux')."""
    system = platform.system()
    if system == "Linux" and "microsoft-standard" in platform.release():
        return "wsl"
    elif system == "Windows":
        return "windows"
    elif system == "Darwin":
        return "macos"
    return "linux" # Default for other Unix-like systems

RUNTIME_ENV = detect_runtime_env()
logger.info(f"Detected runtime environment: {RUNTIME_ENV}")

def get_default_storage_dir() -> Path:
    """Determines the default storage directory based on the runtime environment."""
    if RUNTIME_ENV == "wsl":
        # WSL default: /mnt/c/Users/Public/Downloads/mcp-data/
        return Path("/mnt/c/Users/Public/Downloads/mcp-data")
    elif RUNTIME_ENV == "windows":
        # Windows default: %USERPROFILE%\\Downloads\\mcp-data
        return Path.home() / "Downloads" / "mcp-data"
    else:
        # Linux, macOS, etc. default: ./data
        return Path("./data")

# Define storage directory from environment variable or smart default
STORAGE_DIR = Path(os.environ.get("MCP_STORAGE_DIR", get_default_storage_dir())).resolve()

def setup_storage():
    """Creates the storage directory at startup if it doesn't exist."""
    try:
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Using storage directory: {STORAGE_DIR}")
    except OSError as e:
        logger.error(f"Failed to create storage directory {STORAGE_DIR}: {e}", exc_info=True)
        # Depending on strictness, you might want to exit here
        # sys.exit(1)

def resolve_output_path(output_path: Optional[str], filename_from_url: str) -> Path:
    """
    Resolves and sanitizes the output path, ensuring it's within the STORAGE_DIR.

    Args:
        output_path: The user-provided path (can be None, relative, or absolute).
        filename_from_url: The fallback filename extracted from the URL.

    Returns:
        A secure, absolute Path object.

    Raises:
        PermissionError: If the resolved path is outside the allowed STORAGE_DIR.
    """
    if output_path is None:
        # Default to a filename from the URL inside the storage dir
        return STORAGE_DIR / filename_from_url

    # Expand user home ('~') and environment variables (e.g., '$HOME')
    path = Path(os.path.expandvars(os.path.expanduser(output_path)))

    # If path is relative, join it with the base storage directory
    if not path.is_absolute():
        path = STORAGE_DIR / path
    else:
        # For absolute paths, resolve immediately to check security
        path = path.resolve()

    # Security check: Ensure the final path is within the allowed storage directory
    # Use try_relative_to for Python 3.12+, fallback to manual check for older versions
    try:
        # Attempt to compute the relative path
        path.relative_to(STORAGE_DIR)
    except ValueError:
        # Path is not relative to STORAGE_DIR
        raise PermissionError(f"Invalid path. Output must be within the storage directory: {STORAGE_DIR}")

    return path

# Create an MCP server
mcp = FastMCP("ISTAT", host='0.0.0.0', port=8000)

@mcp.tool()
def get_list_of_available_datasets() -> str:
    """Get a list of available datasets from ISTAT
    
    Example:
        get_list_of_available_datasets()
    """
    datasets = discovery.all_available()
    return datasets.to_json(orient='records')

@mcp.tool()
def search_datasets(query: str) -> str:
    """Search datasets in ISTAT website by a query string
    
    Args:
        query: The query string to search for.
        
    Example:
        search_datasets(query="import")
    """
    results = discovery.search_dataset(query)
    return results.to_json(orient='records')

@mcp.tool()
def get_dataset_dimensions(dataflow_identifier: str) -> str:
    """Get the dimensions of a dataset

    Args:
        dataflow_identifier: The identifier of the dataset.

    Example:
        get_dataset_dimensions(dataflow_identifier="139_176")
    """
    logger.info(f"[START] get_dataset_dimensions called with dataflow_identifier={dataflow_identifier}")

    try:
        logger.debug(f"[STEP 1] Creating DataSet object for {dataflow_identifier}")
        ds = discovery.DataSet(dataflow_identifier=dataflow_identifier)
        logger.debug(f"[STEP 2] DataSet created successfully, fetching dimensions_info()")

        dimensions_df = ds.dimensions_info()
        logger.debug(f"[STEP 3] dimensions_info() returned DataFrame with shape {dimensions_df.shape}")

        result = dimensions_df.to_json(orient='records')
        logger.info(f"[SUCCESS] Returning result, length={len(result)}")
        return result
    except Exception as e:
        error_msg = f"Error in get_dataset_dimensions: {str(e)}"
        logger.error(f"[ERROR] {error_msg}", exc_info=True)

        error_response = {
            "error": str(e),
            "error_type": type(e).__name__,
            "dataflow_identifier": dataflow_identifier,
            "suggestion": "This dataset may not exist or the ISTAT API may be slow/unavailable. Check the dataflow_identifier or try again later."
        }

        if os.environ.get("MCP_DEBUG", "").lower() == "true":
            error_response["traceback"] = traceback.format_exc()

        return json.dumps(error_response)

@mcp.tool()
def get_dimension_values(dataflow_identifier: str, dimension: str) -> str:
    """Get the values of a dimension for a given dataset

    Args:
        dataflow_identifier: The identifier of the dataset.
        dimension: The dimension to get the values for.

    Example:
        get_dimension_values(dataflow_identifier="139_176", dimension="TIPO_DATO")
    """
    logger.info(f"[START] get_dimension_values for dataset={dataflow_identifier}, dimension={dimension}")
    try:
        logger.debug(f"[STEP 1] Creating DataSet object")
        ds = discovery.DataSet(dataflow_identifier=dataflow_identifier)
        logger.debug(f"[STEP 2] Fetching values for dimension: {dimension}")
        result_df = ds.get_dimension_values(dimension)
        logger.debug(f"[STEP 3] Got {len(result_df)} values for dimension {dimension}")
        result = result_df.to_json(orient='records')
        logger.info(f"[SUCCESS] Returning {len(result)} bytes")
        return result
    except Exception as e:
        logger.error(f"[ERROR] Failed to get dimension values: {str(e)}", exc_info=True)
        error_response = {
            "error": str(e),
            "error_type": type(e).__name__,
            "dataflow_identifier": dataflow_identifier,
            "dimension": dimension
        }
        if os.environ.get("MCP_DEBUG", "").lower() == "true":
            error_response["traceback"] = traceback.format_exc()
        return json.dumps(error_response)

@mcp.tool()
def get_data(dataflow_identifier: str, filters: Dict) -> str:
    """
    Get data from a dataset with filters. Attempt to retrieve data, if it times out or is too big,
    return the URL of the file to download.

    Args:
        dataflow_identifier: The identifier of the dataset.
        filters: A dictionary of filters to apply to the dataset.

    Example:
        get_data(dataflow_identifier="139_176", filters={"freq": "M", "tipo_dato": ["ISAV", "ESAV"], "paese_partner": "WORLD"})
    """
    logger.info(f"[START] get_data for dataset={dataflow_identifier}, filters={filters}")
    try:
        logger.debug(f"[STEP 1] Creating DataSet object")
        ds = discovery.DataSet(dataflow_identifier=dataflow_identifier)
        logger.debug(f"[STEP 2] Setting filters")
        ds.set_filters(**filters)
        logger.debug(f"[STEP 3] Calling retrieval.get_data() - this may take a while for large datasets")
        df = retrieval.get_data(ds)
        logger.debug(f"[STEP 4] Got DataFrame with shape {df.shape}, converting to JSON")
        result = df.to_json(orient='records')
        logger.info(f"[SUCCESS] Returning {len(result)} bytes of data")
        return result
    except Exception as e:
        logger.warning(f"[FALLBACK] get_data failed ({type(e).__name__}: {str(e)}), falling back to get_dataset_url")
        # Return the url in case of Errors/timeouts/too much data
        return get_dataset_url(dataflow_identifier, filters)

@mcp.tool()
def get_data_limited(dataflow_identifier: str, filters: Dict, limit: int) -> str:
    """
    Get limited data from a dataset with filters. Returns only the first N records.
    Attempt to retrieve data, if it times out or is too big, return the URL of the file to download.

    Args:
        dataflow_identifier: The identifier of the dataset.
        filters: A dictionary of filters to apply to the dataset.
        limit: The maximum number of records to return.

    Example:
        get_data_limited(dataflow_identifier="139_176", filters={"freq": "M", "tipo_dato": ["ISAV", "ESAV"], "paese_partner": "WORLD"}, limit=100)
    """
    try:
        ds = discovery.DataSet(dataflow_identifier=dataflow_identifier)
        ds.set_filters(**filters)
        df = retrieval.get_data(ds)
        df = df.head(limit)
        return df.to_json(orient='records')
    except Exception as e:
        #return the url in case of Errors/timeouts/too much data
        return get_dataset_url(dataflow_identifier, filters)
    
@mcp.tool()
def get_summary(dataflow_identifier: str, filters: Dict) -> str:
    """
    Get a summary of a dataset from ISTAT.

    Args:
        dataflow_identifier: The identifier of the dataset.
        filters: A dictionary of filters to apply to the dataset.
        
    Example:
        get_summary(dataflow_identifier="139_176", filters={"freq": "M", "tipo_dato": ["ISAV", "ESAV"], "paese_partner": "WORLD"})
    """
    ds = discovery.DataSet(dataflow_identifier=dataflow_identifier)
    ds.set_filters(**filters)
    df = retrieval.get_data(ds)
    file_size_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)

    summary = {
        "rows": int(len(df)),
        "columns": df.columns.tolist(),
        "file_size_mb": float(file_size_mb),
        # head as list of plain Python dicts with ISO datetimes
        "head": json.loads(df.head(5).to_json(orient='records', date_format='iso')),
        # column stats as nested dict with native types
        "column_stats": json.loads(df.describe().to_json())
    }

    return json.dumps(summary)


def get_url_metadata(url: str, use_get: bool = False) -> Dict:
    """
    Get metadata for a URL using HTTP HEAD or GET request.

    Args:
        url: The URL to get metadata for.
        use_get: If True, use GET with stream=True to get accurate metadata.
                 Some APIs (like ISTAT SDMX) don't support HEAD requests properly.

    Returns:
        Dictionary containing metadata like content-type, content-length, etc.
    """
    try:
        if use_get:
            # Use GET with stream=True to get headers without downloading full content
            response = requests.get(url, stream=True, allow_redirects=True, timeout=10)
            # Close the connection after reading headers
            response.close()
        else:
            response = requests.head(url, allow_redirects=True, timeout=10)

        metadata = {
            "url": url,
            "status_code": response.status_code,
            "content_type": response.headers.get("Content-Type", "unknown"),
            "content_length": response.headers.get("Content-Length", "unknown"),
            "last_modified": response.headers.get("Last-Modified", "unknown"),
            "server": response.headers.get("Server", "unknown"),
        }

        # Calculate human-readable size if content-length is available
        if metadata["content_length"] != "unknown":
            try:
                size_bytes = int(metadata["content_length"])
                if size_bytes < 1024:
                    metadata["human_readable_size"] = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    metadata["human_readable_size"] = f"{size_bytes / 1024:.2f} KB"
                elif size_bytes < 1024 * 1024 * 1024:
                    metadata["human_readable_size"] = f"{size_bytes / (1024 * 1024):.2f} MB"
                else:
                    metadata["human_readable_size"] = f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
            except ValueError:
                metadata["human_readable_size"] = "unknown"
        else:
            metadata["human_readable_size"] = "unknown"

        return metadata
    except Exception as e:
        return {
            "url": url,
            "error": str(e),
            "status": "failed to retrieve metadata"
        }


def build_complete_url_key(ds) -> str:
    """
    Build a complete SDMX URL key with all dimensions in the correct order.
    Unfiltered dimensions are represented as empty strings (which means ALL values).

    Args:
        ds: A DataSet instance with filters set

    Returns:
        A properly formatted key string with all dimensions
    """
    # Get all dimension names in order from the dataset
    dimensions_df = ds.dimensions_info()
    all_dimensions = dimensions_df['dimension'].tolist()

    # Build key parts for each dimension
    key_parts = []
    for dim in all_dimensions:
        # Look up the filter value (istatapi stores dimension names in uppercase)
        filter_value = ds.filters.get(dim)

        # Check if dimension is actually filtered (not None, not '.', and not empty)
        if filter_value and filter_value != '.':
            if isinstance(filter_value, list):
                # Multiple values: join with '+'
                key_parts.append('+'.join(str(v) for v in filter_value))
            else:
                # Single value
                key_parts.append(str(filter_value))
        else:
            # Dimension not filtered: use empty string to mean ALL
            key_parts.append('')

    return '.'.join(key_parts)


@mcp.tool()
def get_dataset_url(dataflow_identifier: str, filters: Dict) -> str:
    """
    Get the URL to download a dataset with metadata.

    Args:
        dataflow_identifier: The identifier of the dataset.
        filters: A dictionary of filters to apply to the dataset.
            Filter keys should be dimension names in lowercase.
            For unfiltered dimensions, omit them or set to None.

    Example:
        get_dataset_url(dataflow_identifier="139_176", filters={"freq": "M", "tipo_dato": ["ISAV", "ESAV"], "paese_partner": "WORLD"})

    Returns:
        JSON with URL and metadata (content-type, size, etc.)
    """
    ds = discovery.DataSet(dataflow_identifier=dataflow_identifier)
    ds.set_filters(**filters)

    flowRef = ds.identifiers["df_id"]
    # Use our custom function that properly handles all dimensions
    key = build_complete_url_key(ds)

    base_url = "http://sdmx.istat.it/SDMXWS/rest"
    path_parts = ["data", flowRef, key]
    path = "/".join(path_parts)
    url = "/".join([base_url, path])

    # Get metadata using GET request (ISTAT SDMX doesn't support HEAD properly)
    metadata = get_url_metadata(url, use_get=True)

    return json.dumps(metadata, indent=2)


@mcp.tool()
def download_dataset(url: str, output_path: str = None) -> str:
    """
    Download a dataset file from a URL to a local path with automatic format detection.
    Better for large datasets that cannot be handled in-memory or when Json responses are too large or not supported.
    The file extension is automatically determined from the Content-Type header.

    Args:
        url: The URL of the file to download.
        output_path: Optional. A relative or absolute path for the saved file.
                     If relative, it's resolved against the configured storage directory.
                     If absolute, it MUST be inside the storage directory.
                     If not provided, a filename is generated from the URL with the appropriate extension.

    Example:
        # Saves to <storage_dir>/my_data/export.xml (extension based on content type)
        download_dataset(url="http://.../data", output_path="my_data/export")

        # Saves to <storage_dir>/<generated_name>.<ext> (extension based on content type)
        download_dataset(url="http://.../data")
    """
    final_path_str = ""
    try:
        # Make the request with streaming to handle large files
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        # Detect file extension from Content-Type header
        content_type = response.headers.get("Content-Type", "").lower()
        extension = ".dat"  # Default fallback

        # Map common MIME types to extensions
        if "xml" in content_type or "sdmx" in content_type:
            extension = ".xml"
        elif "csv" in content_type or "comma-separated" in content_type:
            extension = ".csv"
        elif "json" in content_type:
            extension = ".json"
        elif "text/plain" in content_type:
            extension = ".txt"

        # Determine filename from URL or use default
        url_filename = url.split("/")[-1].split("?")[0]  # Remove query params
        if output_path:
            # User provided a path - use it as-is if it has an extension
            # Otherwise append the detected extension
            base_filename = output_path if "." in Path(output_path).name else output_path + extension
        else:
            # No output path provided - generate from URL or use default
            if url_filename and url_filename != "":
                # Use URL filename but replace/add correct extension
                base_name = Path(url_filename).stem or "dataset"
                base_filename = base_name + extension
            else:
                base_filename = "dataset" + extension

        # Resolve and validate the final output path
        final_path = resolve_output_path(None, base_filename) if not output_path else resolve_output_path(output_path if "." in Path(output_path).name else output_path + extension, base_filename)
        final_path_str = str(final_path)

        # Ensure the parent directory exists
        final_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Downloading dataset from {url} to {final_path} (detected format: {extension})")

        # Download the file in chunks
        total_size = 0
        with open(final_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    total_size += len(chunk)

        # Format size for human-readable output
        size_str = f"{total_size} B"
        if total_size > 1024 * 1024 * 1024:
            size_str = f"{total_size / (1024 * 1024 * 1024):.2f} GB"
        elif total_size > 1024 * 1024:
            size_str = f"{total_size / (1024 * 1024):.2f} MB"
        elif total_size > 1024:
            size_str = f"{total_size / 1024:.2f} KB"

        result = {
            "status": "success",
            "url": url,
            "output_path": final_path_str,
            "size_bytes": total_size,
            "human_readable_size": size_str,
            "content_type": response.headers.get("Content-Type", "unknown"),
            "detected_extension": extension,
            "file_format": extension.lstrip(".")
        }
        return json.dumps(result, indent=2)

    except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
        error_result = {
            "status": "error",
            "url": url,
            "error_type": type(e).__name__,
            "error_message": str(e),
            "suggestion": "Check the URL and your network connection."
        }
    except (IOError, PermissionError) as e:
        error_result = {
            "status": "error",
            "url": url,
            "output_path": final_path_str or output_path,
            "error_type": type(e).__name__,
            "error_message": f"Failed to write file: {str(e)}",
            "suggestion": "Ensure the path is valid and you have write permissions. Try setting the MCP_STORAGE_DIR environment variable to a writable directory."
        }
    
    if os.environ.get("MCP_DEBUG", "").lower() == "true" and 'error_result' in locals():
        error_result["traceback"] = traceback.format_exc()
        
    return json.dumps(error_result, indent=2)


@mcp.resource("istat:readme")
def istat_overview() -> str:
    """General info about ISTAT API usage."""
    return (
        "This MCP server exposes ISTAT API datasets and retrieval tools.\n\n"
        "You can use the available tools to list datasets, search them, "
        "inspect their dimensions, and download filtered data.\n\n"
        "Features:\n"
        "- get_data: Retrieves data directly or returns URL with metadata if too large\n"
        "- get_dataset_url: Gets URL with file metadata (size, type, etc.) using HTTP HEAD\n"
        "- download_dataset: Downloads large datasets to local filesystem\n\n"
        "Configuration:\n"
        "- MCP_STORAGE_DIR: Set this environment variable to control where files are saved.\n"
        f"- Default storage directory: {STORAGE_DIR}\n"
        "- MCP_DEBUG: Set to 'true' for detailed error tracebacks."
    )

def main():
    # Initialize storage and run the server
    logger.info("="*60)
    logger.info("ISTAT MCP Server starting...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Runtime environment: {RUNTIME_ENV}")
    setup_storage()
    logger.info("="*60)
    # For stdio transport:
    # mcp.run(transport='stdio')
    # For HTTP transport (uses host and port from FastMCP initialization):
    mcp.run()


if __name__ == "__main__":
    main()
