# Solarman


Python client for interacting with Solarman devices over local network.

## Installation

```bash
pip install solarman-opendata
```

## Usage

### Basic Example

```python
import asyncio
from solarman_opendata import Solarman

async def main():
    async with aiohttp.ClientSession() as session:
        # Create API client
        api = Solarman(
            session=session,
            host="192.168.1.100"  # Device IP
        )
        
        # Get real-time data
        data = await api.fetch_data()
        print(f"Current Power: {data.get('power', 0)}W")
        print(f"Voltage: {data.get('voltage', 0)}V")
        

asyncio.run(main())
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.