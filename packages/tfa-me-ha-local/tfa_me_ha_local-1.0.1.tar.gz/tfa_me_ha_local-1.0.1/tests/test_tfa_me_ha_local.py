"""TFA.me library for Home Assistant: test_tfa_me_ha_local.py."""

import json
import logging
import asyncio
from tfa_me_ha_local.client import TFAmeClient
from tfa_me_ha_local.data import TFAmeDataForHA
from tfa_me_ha_local.exceptions import TFAmeException

_LOGGER = logging.getLogger(__name__)

# (ha-venv) vscode ➜ /workspaces/tfa_me_ha_local/tfa_me_ha_local $ execute
"""
pip uninstall tfa-me-ha-local -y
pip install -e .

Set source to local path for library:
source /Users/xxxxxxxx/ha_tfa_me/core/venv/bin/activate
pip install -e .

In HA terminal:
pip show tfa-me-ha-local
"""


async def main() -> None:
    "Test some connections to real TFA.me devices."

    # Use here: Valid IP and path
    json_data = {}  # dict
    json_data = await client_test("192.168.1.38", "sensors", timeout=7)
    tfa_me_data = TFAmeDataForHA(multiple_entities=False)

    parsed_data = {}  # dict
    parsed_data = tfa_me_data.json_to_entities(json_data=json_data)
    _LOGGER.info("TFA.me data:\n'%s'", json.dumps(parsed_data, indent=2))

    # Use here: IP not existing
    await client_test("192.168.1.37", "sensors")

    # Use here: Path/URL wrong
    await client_test("192.168.1.38", "xxx")


async def client_test(host: str, path: str, timeout: int = 5) -> None:
    """Test a client connection to a TFA.me device."""
    msg = f"Test connection to '{host}/{path}' ....."
    _LOGGER.info(msg)

    try:
        tfa_me_client = TFAmeClient(host, path, timeout=timeout, log_level=1)
        data = await tfa_me_client.async_get_sensors()
        if not data:
            _LOGGER.error("Error, no data")
            return None
        else:
            _LOGGER.info("Data:\n'%s'", json.dumps(data, indent=2))
            return data
    except TFAmeException as err:
        _LOGGER.error("Failed to fetch sensors: '%s'", err)


# Main entry point
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
