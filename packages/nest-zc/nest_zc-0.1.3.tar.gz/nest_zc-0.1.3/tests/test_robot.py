from urllib.error import URLError

import pytest

from nest_zc import Robot


class DummyResponse:
    def __init__(self, payload: bytes, status: int = 200):
        self._payload = payload
        self.status = status

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> "DummyResponse":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        return None


def test_robot_connect_success(monkeypatch: pytest.MonkeyPatch) -> None:
    response = DummyResponse(
        b'{"code": 0, "data": {"namespace": "nest_2777af2b92e0fa78_798e8abd6e"}}'
    )

    def fake_urlopen(req, timeout):
        assert req.full_url == "http://127.0.0.1:5000/zenoh/zenoh"
        assert timeout == 5.0
        return response

    monkeypatch.setattr("nest_zc.robot.request.urlopen", fake_urlopen)

    robot = Robot()
    assert robot.connect("127.0.0.1") is True
    assert robot.namespace == "nest_2777af2b92e0fa78_798e8abd6e"


def test_robot_connect_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(*args, **kwargs):
        raise URLError("boom")

    monkeypatch.setattr("nest_zc.robot.request.urlopen", fake_urlopen)

    robot = Robot()
    assert robot.connect("127.0.0.1") is False
    assert robot.namespace is None
