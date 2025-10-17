# DayBetter Python Client

A Python client library for interacting with DayBetter devices and services.

## Features

- Device management and control
- MQTT configuration retrieval
- Authentication handling
- Async/await support

## Installation

```bash
pip install daybetter-services-python
```

## Usage

```python
import asyncio
from daybetter_python import DayBetterClient

async def main():
    async with DayBetterClient(token="your_token") as client:
        # Fetch devices
        devices = await client.fetch_devices()
        print(f"Found {len(devices)} devices")
        
        # Control a device
        result = await client.control_device(
            device_name="device_001",
            action=True,
            brightness=80
        )
        print(f"Control result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

## API Reference

### DayBetterClient

#### Methods

- `fetch_devices()`: Get list of devices
- `fetch_pids()`: Get device type PIDs
- `control_device(device_name, action, brightness, hs_color, color_temp)`: Control a device
- `fetch_mqtt_config()`: Get MQTT configuration

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
