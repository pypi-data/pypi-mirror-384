"""TFA.me library for Home Assistant: exceptions.py."""


class TFAmeException(Exception):
    """Base exception for TFA.me client errors."""


class TFAmeTimeoutError(TFAmeException):
    """Timeout while fetching data."""


class TFAmeConnectionError(TFAmeException):
    """Network/DNS connection error."""


class TFAmeHTTPError(TFAmeException):
    """HTTP status code is not 200."""


class TFAmeJSONError(TFAmeException):
    """Response could not be parsed as JSON."""
