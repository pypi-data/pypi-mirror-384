"""TFA.me library for Home Assistant: client.py."""

# https://packaging.python.org/en/latest/tutorials/packaging-projects/

import asyncio
import json
import logging
import socket
from typing import Any
import aiohttp

from .exceptions import (
    TFAmeHTTPError,
    TFAmeJSONError,
    TFAmeTimeoutError,
    TFAmeException,
    TFAmeConnectionError,
)

# Debugging
_LOGGER = logging.getLogger(__name__)


class TFAmeClient:
    """Simple client to fetch sensor data from a TFA.me station."""

    def __init__(
        self,
        host: str,
        path: str = "sensors",
        timeout: int = 5,
        session: aiohttp.ClientSession | None = None,
        log_level: int = 0,
    ):
        """Initialize the TFA.me client.

        Args:
            host: IP address or hostname of the station.
            path: Endpoint path (default: "sensors").
            timeout: Timeout time to establish a connection
            session: Optional aiohttp.ClientSession. If not provided, a new one will be created and closed automatically.
            log_level: Log level for debug output.
        """
        self._host = host
        self._path = path
        self._timeout = timeout
        self._session = session
        self._data: dict = {}
        self._log_level = log_level

    async def async_get_sensors(self) -> dict:
        """Fetch sensor data from the gateway.

        Raises:
            TFAmeTimeoutError: Request timed out.
            TFAmeConnectionError: Network or DNS issue.
            TFAmeHTTPError: Non-200 HTTP status code.
            TFAmeJSONError: Response was not valid JSON.
            TFAmeException: Any other unexpected error.

        Returns:
            Parsed JSON data as a dictionary.
        """
        url = f"http://{self._host}/{self._path}"
        if self._log_level >= 1:
            # Show the URL to the device
            msg: str = "Request URL '" + url + "'"
            _LOGGER.info(msg)

        try:
            # Reuse provided session or create a new one
            session = self._session or aiohttp.ClientSession()

            if session:
                self._session = session

            async with asyncio.timeout(self._timeout):
                async with session.get(url) as resp:
                    if resp.status != 200:
                        raise TFAmeHTTPError(f"HTTP error: {resp.status}")
                    try:
                        data = await resp.json()
                    except aiohttp.ContentTypeError as err:
                        raise TFAmeJSONError(f"Invalid JSON response: {err}") from err

                    if self._log_level >= 2:
                        _LOGGER.debug(
                            "TFAmeClient received data:\n%s", json.dumps(data, indent=2)
                        )
                    self._data = data
                    return data

        except asyncio.TimeoutError as err:
            raise TFAmeTimeoutError("Request to TFA.me sation timed out") from err
        except aiohttp.ClientConnectorError as err:
            raise TFAmeConnectionError(f"Connection error: {err}") from err
        except socket.gaierror as err:
            raise TFAmeConnectionError(f"DNS resolution failed: {err}") from err
        except TFAmeException:
            # Re-raise any already wrapped TFAmeException
            raise
        except Exception as err:
            raise TFAmeException(f"Unexpected error: {err}") from err
        finally:
            # Close the session only if it was created before
            if self._session is not None:
                await session.close()

    async def close(self) -> None:
        """Close open client session."""
        if self._session:
            await self._session.close()

    async def __aenter__(self) -> Any:
        """Async enter, retrun the TFAmeClient object."""
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        """Async exit.

        Args:
        ----
            _exc_info: Exec type.

        """
        await self.close()

