from urllib.error import URLError

import pytest

from nest_zc import Robot
import nest_zc.robot as robot_module


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
        assert req.headers["x-api-key"] == "1234567890"
        return response

    monkeypatch.setattr("nest_zc.robot.request.urlopen", fake_urlopen)

    robot = Robot()
    assert robot.connect("127.0.0.1") is True
    assert robot.namespace == "nest_2777af2b92e0fa78_798e8abd6e"
    assert robot.last_error is None


def test_robot_connect_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(*args, **kwargs):
        raise URLError("boom")

    monkeypatch.setattr("nest_zc.robot.request.urlopen", fake_urlopen)

    robot = Robot()
    assert robot.connect("127.0.0.1") is False
    assert robot.namespace is None
    assert robot.last_error == "URL error: boom"


def test_robot_connect_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    response = DummyResponse(b"")

    def fake_urlopen(req, timeout):
        return response

    monkeypatch.setattr("nest_zc.robot.request.urlopen", fake_urlopen)

    robot = Robot()
    assert robot.connect("127.0.0.1") is False
    assert robot.namespace is None
    assert robot.last_error == (
        "Invalid JSON response (''): Expecting value: line 1 column 1 (char 0)"
    )


def test_robot_subscribe_pose_requires_connection() -> None:
    robot = Robot()
    with pytest.raises(RuntimeError):
        robot.subscribe_pose()


def test_robot_subscribe_pose_success(monkeypatch: pytest.MonkeyPatch) -> None:
    robot = Robot()
    robot.namespace = "demo"
    robot._ip = "10.0.0.2"

    configs = []

    class DummyConfig:
        def __init__(self):
            self.inserted = []

        def insert_json5(self, key, value):
            self.inserted.append((key, value))

    def fake_config():
        cfg = DummyConfig()
        configs.append(cfg)
        return cfg

    monkeypatch.setattr(robot_module.zenoh, "Config", fake_config)

    captured = {}

    class DummySubscriber:
        def __init__(self, listener):
            self.listener = listener

        def undeclare(self):
            pass

    class DummySession:
        def declare_subscriber(self, key_expr, listener):
            captured["key"] = key_expr
            captured["listener"] = listener
            return DummySubscriber(listener)

        def close(self):
            pass

    monkeypatch.setattr(robot_module.zenoh, "open", lambda config: DummySession())

    payload_bytes = b"serialized-pose"

    class DummyPose:
        @classmethod
        def deserialize(cls, data):
            captured["deserialized"] = data
            return "pose-object"

    monkeypatch.setattr(robot_module.Robot, "_resolve_pose_type", lambda self: DummyPose)

    subscriber = robot.subscribe_pose()
    assert isinstance(subscriber, DummySubscriber)
    assert captured["key"] == "demo/robot_pose"
    assert len(configs) == 1
    assert (
        ("connect/endpoints", '["tcp/10.0.0.2:7447"]')
        in configs[0].inserted
    )

    class DummyPayload:
        def to_bytes(self):
            return payload_bytes

    class DummySample:
        def __init__(self):
            self.payload = DummyPayload()

    captured["listener"](DummySample())
    assert captured["deserialized"] == payload_bytes
    assert robot.current_pose == "pose-object"
    assert robot.last_error is None


def test_robot_subscribe_pose_deserialize_error(monkeypatch: pytest.MonkeyPatch) -> None:
    robot = Robot()
    robot.namespace = "demo"
    robot._ip = "10.0.0.2"

    class DummyConfig:
        def insert_json5(self, key, value):
            pass

    monkeypatch.setattr(robot_module.zenoh, "Config", lambda: DummyConfig())

    class DummySubscriber:
        def __init__(self, listener):
            self.listener = listener

        def undeclare(self):
            pass

    class DummySession:
        def declare_subscriber(self, key, listener):
            return DummySubscriber(listener)

        def close(self):
            pass

    monkeypatch.setattr(robot_module.zenoh, "open", lambda config: DummySession())

    class DummyPose:
        @classmethod
        def deserialize(cls, data):
            raise ValueError("bad pose")

    monkeypatch.setattr(robot_module.Robot, "_resolve_pose_type", lambda self: DummyPose)

    subscriber = robot.subscribe_pose()
    listener = subscriber.listener

    class DummyPayload:
        def to_bytes(self):
            return b"bad"

    class DummySample:
        def __init__(self):
            self.payload = DummyPayload()

    listener(DummySample())
    assert robot.last_error == "Failed to deserialize pose: bad pose"
    assert robot.current_pose is None


def test_robot_subscribe_pose_missing_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    robot = Robot()
    robot.namespace = "demo"
    robot._ip = "10.0.0.2"

    def missing_pose_type(self):
        raise RuntimeError("Pose type dependency not available")

    monkeypatch.setattr(robot_module.Robot, "_resolve_pose_type", missing_pose_type)

    with pytest.raises(RuntimeError):
        robot.subscribe_pose()
    assert robot.last_error == "Pose type dependency not available"
