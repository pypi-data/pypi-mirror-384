# Orb Cloud API Client

A Python client library for interacting with the Orb Cloud API. This package provides a simple interface to manage devices, configure data collection, and interact with Orb Cloud services.

## Installation

Install the package from the wheel file:

```bash
pip install orb-cloud-client
```

The package will automatically install its dependencies:
- `httpx>=0.24.0` (for HTTP requests)
- `pydantic>=2.0.0` (for data models)

## Quick Start

```python
from orb_cloud_client import OrbCloudClient

# Create client
client = OrbCloudClient(token="your-api-token")

# Get organization devices
devices = client.get_organization_devices("your-org-id")
print(f"Found {len(devices)} devices")

# Use as context manager (recommended)
with OrbCloudClient(token="your-api-token") as client:
    devices = client.get_organization_devices("your-org-id")
```

## API Reference

### OrbCloudClient

#### Constructor

```python
OrbCloudClient(base_url="https://panel.orb.net", token=None)
```

**Parameters:**
- `base_url` (str, optional): API base URL. Defaults to production environment.
- `token` (str, optional): Bearer authentication token.

#### Methods

##### get_organization_devices(organization_id)

Get a list of all devices for an organization.

```python
devices = client.get_organization_devices("org-123")
```

**Parameters:**
- `organization_id` (str): The organization ID

**Returns:**
- `List[Device]`: List of Device objects

**Example:**
```python
devices = client.get_organization_devices("org-123")
for device in devices:
    print(f"Device: {device.name} (ID: {device.id})")
    print(f"  Status: {'Connected' if device.is_connected else 'Disconnected'}")
    print(f"  Location: {device.geo_ip_info.city}, {device.geo_ip_info.state}")
```

##### configure_temporary_datasets(device_id, temp_datasets_request)

Configure temporary data collection for a device with custom data push endpoint.

```python
from orb_cloud_client.models import TempDatasetsRequest, Datasets, DataPush

temp_config = TempDatasetsRequest(
    duration="5m",  # Run for 5 minutes
    datasets_config=Datasets(
        enabled=True,
        datasets=["responsiveness_1s", "scores_1s"],  # Collect these datasets
        push=DataPush(
            enabled=True,
            url="https://your-endpoint.com/data",  # Your webhook URL
            datasets=["responsiveness_1s", "scores_1s"],
            format="json",
            interval_ms=500  # Push new data every 500ms (when available)
        )
    )
)

result = client.configure_temporary_datasets("device-456", temp_config)
```

**Parameters:**
- `device_id` (str): The device ID
- `temp_datasets_request` (TempDatasetsRequest): Configuration object

**Returns:**
- `Dict[str, Any]`: API response

##### request(method, endpoint, **kwargs)

Make a custom HTTP request to any API endpoint.

```python
response = client.request("GET", "/api/v2/custom-endpoint")
data = response.json()
```

**Parameters:**
- `method` (str): HTTP method (GET, POST, PUT, DELETE, etc.)
- `endpoint` (str): API endpoint path
- `**kwargs`: Additional arguments passed to httpx

**Returns:**
- `httpx.Response`: Raw HTTP response

##### close()

Close the HTTP client connection.

```python
client.close()
```

### Data Models

All API models are Pydantic models with full type validation and serialization.

#### Device

Represents an Orb device with all its properties.

```python
from orb_cloud_client.models import Device

# Device properties
device.id                    # str: Device UUID
device.name                  # str: Device name
device.is_connected          # IsConnected: Connection status (0 or 1)
device.last_seen             # Optional[str]: Last seen timestamp
device.geo_ip_info          # Optional[GeoIPInfo]: Geographic information
device.device_info          # Optional[DeviceInfo]: Hardware/software info
device.network_interfaces   # Optional[List[NetworkInterface]]: Network info
device.orb_score           # Optional[OrbScore]: Performance metrics
device.summary             # Optional[DeviceSummary]: Device summary
```

#### TempDatasetsRequest

Configuration for temporary data collection.

```python
from orb_cloud_client.models import TempDatasetsRequest, Datasets, DataPush

temp_request = TempDatasetsRequest(
    duration="5m",                    # Duration (e.g., "5m", "1h", "30m", "2h")
    datasets_config=Datasets(
        enabled=True,
        datasets=["responsiveness_1s", "scores_1s"],  # Dataset types to collect
        push=DataPush(                # Data push configuration
            enabled=True,
            url="https://your-server.com/webhook",
            datasets=["responsiveness_1s", "scores_1s"],
            format="json",
            interval_ms=500           # Push interval in milliseconds
        )
    )
)
```

#### Datasets

Data collection configuration with push settings.

```python
datasets = Datasets(
    enabled=True,                     # bool: Enable data collection
    datasets=[                        # List[str]: Dataset types to collect
        "responsiveness_1s",
        "scores_1s",
        "latency_1s",
        "throughput_1s"
    ],
    push=DataPush(                    # Optional: Push configuration
        enabled=True,
        url="https://api.example.com/webhook",
        datasets=["responsiveness_1s", "scores_1s"],
        format="json",                # Data format
        interval_ms=500               # Push interval in milliseconds
    )
)
```

#### DataPush

Configuration for pushing data to external endpoints.

```python
data_push = DataPush(
    enabled=True,                             # bool: Enable data pushing
    url="https://api.example.com/webhook",    # str: Webhook URL
    datasets=["responsiveness_1s", "scores_1s"],  # List[str]: Datasets to push
    format="json",                            # str: Data format
    interval_ms=500                           # int: Push interval in milliseconds
)
```

#### GeoIPInfo

Geographic information from device IP address.

```python
geo_info.city           # Optional[str]: City name
geo_info.state          # Optional[str]: State/region
geo_info.country        # Optional[str]: Country name
geo_info.country_code   # Optional[str]: Country code (e.g., "US")
geo_info.isp_name       # Optional[str]: Internet service provider
geo_info.latitude       # Optional[float]: Latitude coordinate
geo_info.longitude      # Optional[float]: Longitude coordinate
```

#### DeviceInfo

Device hardware and software information.

```python
device_info.name               # Optional[str]: Device hostname
device_info.version            # Optional[str]: Software version
device_info.cpu_count          # Optional[int]: Number of CPU cores
device_info.full_name          # Optional[str]: Full hostname
device_info.operating_system   # Optional[str]: OS name
```

#### NetworkInterface

Network interface information.

```python
interface.name          # Optional[str]: Interface name
interface.type          # Optional[str]: Interface type (e.g., "Ethernet")
interface.local_ip      # Optional[str]: Local IP address
interface.mac_address   # Optional[str]: MAC address
```

## Usage Examples

### Basic Device Management

```python
from orb_cloud_client import OrbCloudClient

with OrbCloudClient(token="your-token") as client:
    # Get all devices
    devices = client.get_organization_devices("org-123")

    # Filter connected devices
    connected_devices = [d for d in devices if d.is_connected == 1]

    # Find specific device
    target_device = next((d for d in devices if "hardy" in d.name.lower()), None)
    if target_device:
        print(f"Found device: {target_device.name}")
```

### Configure Data Collection

```python
from orb_cloud_client import OrbCloudClient
from orb_cloud_client.models import TempDatasetsRequest, Datasets, DataPush

with OrbCloudClient(token="your-token") as client:
    # Configure temporary datasets with custom endpoint
    config = TempDatasetsRequest(
        duration="5m",  # Run for 5 minutes
        datasets_config=Datasets(
            enabled=True,
            datasets=["responsiveness_1s", "scores_1s"],
            push=DataPush(
                enabled=True,
                url="https://your-analytics.com/orb-data",
                datasets=["responsiveness_1s", "scores_1s"],
                format="json",
                interval_ms=500  # Push every 500ms when data available
            )
        )
    )

    result = client.configure_temporary_datasets("device-456", config)
    print("Configuration successful:", result)
```

### Error Handling

```python
from orb_cloud_client import OrbCloudClient
import httpx

with OrbCloudClient(token="your-token") as client:
    try:
        devices = client.get_organization_devices("org-123")
    except httpx.HTTPStatusError as e:
        print(f"HTTP error {e.response.status_code}: {e.response.text}")
    except httpx.RequestError as e:
        print(f"Request error: {e}")
```

### Working with Device Data

```python
from orb_cloud_client import OrbCloudClient

with OrbCloudClient(token="your-token") as client:
    devices = client.get_organization_devices("org-123")

    for device in devices:
        print(f"\n--- {device.name} ---")
        print(f"ID: {device.id}")
        print(f"Connected: {'Yes' if device.is_connected else 'No'}")

        if device.geo_ip_info:
            print(f"Location: {device.geo_ip_info.city}, {device.geo_ip_info.state}")
            print(f"ISP: {device.geo_ip_info.isp_name}")

        if device.device_info:
            print(f"OS: {device.device_info.operating_system}")
            print(f"Version: {device.device_info.version}")

        if device.network_interfaces:
            for interface in device.network_interfaces:
                print(f"Interface: {interface.name} ({interface.local_ip})")
```

## Interactive Example

The package includes an interactive example that demonstrates the complete workflow:

```bash
export ORB_API_TOKEN="your-api-token"
export ORB_ORGANIZATION_ID="your-org-id"
python3 -m orb_cloud_client.example
```

The example will:
1. Fetch and display all devices
2. Configure temporary datasets for the selected device


See `example.py` for example code.


## Available Dataset Types

Common dataset types you can collect:
- `responsiveness_{timeframe}` - time-binned responsiveness (example `responiveness_1s`, `responsiveness_15s`)
- `scores_{timeframe}` - time-binned scores (example `scores_1s`, `scores_1m`)
- `speed_results` - Result-level speed measurements
- `web_responsiveness_results` - Result-level DNS resolve and TTFB measurements

## Authentication

The client uses Bearer token authentication. Get your API token from the Orb Cloud dashboard and pass it to the client constructor:

```python
client = OrbCloudClient(token="your-bearer-token")
```

## Environment Support

- **Staging**: `https://api.staging.orb.net` (default)
- **Production**: `https://api.orb.net`

```python
# Production client
client = OrbCloudClient(
    base_url="https://api.orb.net",
    token="your-token"
)
```

## Requirements

- Python 3.8+
- httpx >= 0.24.0
- pydantic >= 2.0.0

## Error Handling

The client raises standard httpx exceptions:
- `httpx.HTTPStatusError` - For HTTP error responses (4xx, 5xx)
- `httpx.RequestError` - For network/connection errors
- `httpx.TimeoutException` - For request timeouts

Always wrap API calls in try-catch blocks for production use.
