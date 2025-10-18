"""TFA.me library for Home Assistant: validator.py"""

import re

class TFAmeValidator:
    """Helpful validator(s)."""

    def __init__(self) -> None:
        """Initialize."""

    def is_valid_ip_or_tfa_me(self, host_to_verify: str) -> bool:
        """Verify if input string is a valid IP V4 or valid TFA.me station ID."""

        # host = to_verify.get("ip_address")  # Get value as string
        if not isinstance(host_to_verify, str):
            return False  # ip_address not available or not a string

        # IPv4 verify:
        # ipv4_pattern: str = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
        ipv4_pattern = (
            r"^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}"
            r"(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"
        )
        if re.match(ipv4_pattern, host_to_verify):
            return True

        # Special format for mDNS name verification: "tfa-me-XXX-XXX-XXX.local"
        # mdns_pattern: str = r"^tfa-me-[0-9A-Fa-f]{3}-[0-9A-Fa-f]{3}-[0-9A-Fa-f]{3}\.local$"
        # Special format for mDNS name verification: "XXX-XXX-XXX"
        mdns_pattern: str = r"^[0-9A-Fa-f]{3}-[0-9A-Fa-f]{3}-[0-9A-Fa-f]{3}$"
        if re.match(mdns_pattern, host_to_verify):
            return True

        return False
    
