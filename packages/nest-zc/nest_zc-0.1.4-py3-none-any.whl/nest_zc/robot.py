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
    last_error: Optional[str] = field(default=None, init=False)

    def connect(self, ip: str) -> bool:
        """
        Connect to the robot and return True if the expected zenoh namespace
        information is returned.
        """
        self.namespace = None
        self.last_error = None

        url = f"http://{ip}:5000/zenoh/zenoh"
        http_request = request.Request(url, method="GET")
        try:
            with request.urlopen(http_request, timeout=self.timeout) as response:
                if response.status != 200:
                    self.last_error = f"Unexpected status code: {response.status}"
                    return False
                payload = response.read()
        except error.HTTPError as exc:
            self.last_error = f"HTTP error {exc.code}: {exc.reason}"
            return False
        except error.URLError as exc:
            self.last_error = f"URL error: {exc.reason}"
            return False
        except TimeoutError:
            self.last_error = "Connection timed out"
            return False

        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            self.last_error = f"Invalid JSON response: {exc}"
            return False

        if (
            isinstance(data, dict)
            and data.get("code") == 0
            and isinstance(data.get("data"), dict)
            and "namespace" in data["data"]
        ):
            self.namespace = data["data"]["namespace"]
            return True

        self.last_error = "Unexpected response payload"
        return False
