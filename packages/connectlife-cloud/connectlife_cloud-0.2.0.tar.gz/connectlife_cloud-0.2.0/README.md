# ConnectLife Cloud API Client

A Python client library for the ConnectLife Cloud API, designed for Home Assistant integrations.

## Features

- Async/await support
- Full type hints
- Comprehensive error handling
- Device management
- Real-time status updates
- Power consumption tracking
- Self-check diagnostics

## Installation

```bash
pip install connectlife-cloud
```

## Usage

```python
import asyncio
from connectlife_cloud import ConnectLifeCloudClient

async def main():
    client = ConnectLifeCloudClient(
        client_id="your_client_id",
        client_secret="your_client_secret"
    )
    
    try:
        # Get devices
        devices = await client.get_devices(access_token="your_token")
        print(f"Found {len(devices)} devices")
        
        # Control a device
        result = await client.control_device(
            puid="device_puid",
            properties={"power": True, "mode": "cool"},
            access_token="your_token"
        )
        print(f"Control result: {result}")
        
    finally:
        await client.close()

asyncio.run(main())
```

## API Reference

### ConnectLifeCloudClient

The main client class for interacting with the ConnectLife Cloud API.

#### Methods

- `get_devices(access_token)`: Get list of devices
- `control_device(puid, properties, access_token)`: Control a device
- `get_property_list(device_type_code, device_feature_code, access_token)`: Get device properties
- `query_static_data(puid, access_token)`: Query static device data
- `get_hour_power(date, puid, access_token)`: Get hourly power consumption
- `get_self_check(no_record, puid, access_token)`: Get device self-check info

## License

MIT License
