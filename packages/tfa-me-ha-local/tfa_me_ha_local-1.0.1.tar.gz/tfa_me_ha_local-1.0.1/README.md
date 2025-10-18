# tfa_me_ha_local

Async Python client for **TFA.me** weather station and measurement system.

## About

This package allows you to fetch data from a TFA.me station.
This module communicates directly towards the IP address of your TFA.me WiFi station in your local network.
It is used to connect TFA.me stations to Home Assistant via an integration.

See also on GitHub:

This project **tfa_me_ha_local**:

- [Source code](https://github.com/DrMatthiasBlaschke/tfa_me_ha_local).

TFA.me integration for Home Assistant:

- [Documenation](https://www.home-assistant.io/integrations/tfa_me)
- [Source code](https://github.com/home-assistant/core/tree/dev/homeassistant/components/tfa_me)

## Installation

```bash
pip install tfa_me_ha_local
```

## Usage

```python

import json
import logging
import asyncio
from tfa_me_ha_local.client import TFAmeClient
from tfa_me_ha_local.data import TFAmeDataForHA
from tfa_me_ha_local.exceptions import TFAmeException

_LOGGER = logging.getLogger(__name__)

async def main() -> None:
    """Make a client connection to a TFA.me device and request sensor data."""

    host = "192.168.1.38" # Existing IP in local network
    path = "sensors"      # Default path to request measurement data for all sensors
    timeout = 10          # Timeout to establish the connection
    msg = f"Establish connection to '{host}/{path}' ....."
    _LOGGER.info(msg)

    try:
        tfa_me_client = TFAmeClient(host, path, timeout=timeout)
        data = await tfa_me_client.async_get_sensors()
        if not data:
            _LOGGER.error("Error, no data")
            return None
        else:
            _LOGGER.info("Data received:\n'%s'", json.dumps(data, indent=2))
            return data
    except TFAmeException as err:
        _LOGGER.error("Failed to fetch sensors: '%s'", err)


# Main entry point
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
```

## Author

The content is by [DrMatthiasBlaschke](https://github.com/DrMatthiasBlaschke).

## License

MIT License

Copyright (c) 2025 synertronixx

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
