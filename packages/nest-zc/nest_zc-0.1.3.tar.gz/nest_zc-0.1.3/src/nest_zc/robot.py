"""
Robot connection utilities.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional
from urllib import error, request


@dataclass
class Robot:
    """
    Represents a robot that exposes a zenoh endpoint.
    """

    timeout: float = 5.0
    namespace: Optional[str] = field(default=None, init=False)

    def connect(self, ip: str) -> bool:
        """
        Connect to the robot and return True if the expected zenoh namespace
        information is returned.
        """
        url = f"http://{ip}:5000/zenoh/zenoh"
        http_request = request.Request(url, method="GET")
        try:
            with request.urlopen(http_request, timeout=self.timeout) as response:
                if response.status != 200:
                    return False
                payload = response.read()
        except (error.URLError, error.HTTPError, TimeoutError):
            return False

        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return False

        if (
            isinstance(data, dict)
            and data.get("code") == 0
            and isinstance(data.get("data"), dict)
            and "namespace" in data["data"]
        ):
            self.namespace = data["data"]["namespace"]
            return True

        return False
