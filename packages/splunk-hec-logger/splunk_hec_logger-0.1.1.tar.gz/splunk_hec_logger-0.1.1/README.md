# Splunk Logger

A simple Python package for sending logs to Splunk using the HTTP Event Collector (HEC).

## Installation

```bash
pip install splunk-hec-logger # (or from your local wheel file)
```

## Configuration

The `SplunkLogger` class retrieves its configuration from environment variables. These are **required**:

*   `SPLUNK_HEC_URL`: The URL of your Splunk HEC endpoint (e.g., `https://your-splunk-instance:8088/services/collector`).
*   `SPLUNK_HEC_TOKEN`: Your Splunk HEC token.

These are optional:
*   `SPLUNK_HOST`: The host field for your Splunk events (defaults to the local hostname).
*   `SPLUNK_SOURCE`: The source field for your Splunk events (defaults to "RPA").
*   `SPLUNK_SOURCETYPE`: The sourcetype field for your Splunk events (defaults to "_json").
*   `SPLUNK_INDEX`: The index for your Splunk events (defaults to "rdb").

## Usage

```python
import os
from splunk_logger import SplunkLogger

# Set environment variables (for demonstration; normally set outside the script)
os.environ["SPLUNK_HEC_URL"] = "YOUR_SPLUNK_HEC_URL"
os.environ["SPLUNK_HEC_TOKEN"] = "YOUR_SPLUNK_HEC_TOKEN"
os.environ["SPLUNK_HOST"] = "my-application-host"
os.environ["SPLUNK_SOURCE"] = "my-app"
os.environ["SPLUNK_SOURCETYPE"] = "_json"
os.environ["SPLUNK_INDEX"] = "my_index"

logger = SplunkLogger()

logger.info("This is an informational message.", Module="my_module", TaskId="123")
logger.warning("A potential issue occurred.", Module="my_module", StatusCode=404)
logger.error("An error occurred.", Module="my_module", ErrorCode=500, Exception="ValueError")

# You can also log events with a custom level or provide a complete event dictionary
logger.log_event({
    "Level": "DEBUG",
    "Message": "Detailed debug information.",
    "Component": "Database",
    "Query": "SELECT * FROM users"
})
```
