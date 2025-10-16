import importlib
import json
import os
import sys
import types
from pathlib import Path
from typing import Any

import pytest

CLI_DIR = Path(__file__).resolve().parents[1]
if str(CLI_DIR) not in sys.path:
    sys.path.insert(0, str(CLI_DIR))


def _load_sdk(monkeypatch, tmp_path):
    manifest_path = tmp_path / "nodes.json"
    manifest_path.write_text(json.dumps({"nodes": []}))
    monkeypatch.setenv("HUROZO_NODES_FILE", str(manifest_path))
    monkeypatch.setenv("HUROZO_API_TOKEN", "test-token")
    monkeypatch.setenv("HUROZO_SERVER_URI", "https://example.com")

    if "python_webchannel" not in sys.modules:
        stub = types.ModuleType("python_webchannel")

        class EventType:  # pragma: no cover - placeholder
            pass

        class WebChannelError(RuntimeError):  # pragma: no cover - placeholder
            pass

        class WebChannelOptions:  # pragma: no cover - placeholder
            def __init__(self, *args, **kwargs) -> None:
                self.args = args
                self.kwargs = kwargs

        async def _noop_close() -> None:  # pragma: no cover - placeholder
            return None

        class _Transport:  # pragma: no cover - placeholder
            async def close(self) -> None:
                await _noop_close()

        def create_web_channel_transport(*args, **kwargs):  # pragma: no cover - placeholder
            return _Transport()

        stub.EventType = EventType
        stub.WebChannelError = WebChannelError
        stub.WebChannelOptions = WebChannelOptions
        stub.create_web_channel_transport = create_web_channel_transport
        sys.modules["python_webchannel"] = stub

    agents_store: dict[str, dict[str, Any]] = {}

    def empty_graph() -> dict[str, Any]:
        return {
            "last_node_id": 0,
            "last_link_id": 0,
            "nodes": [],
            "links": [],
            "groups": [],
            "config": {},
            "extra": {},
            "version": 0.4,
        }

    class FakeResponse:
        def __init__(self, status_code=200, data=None):
            self.status_code = status_code
            self._data = data if data is not None else {}

        @property
        def ok(self) -> bool:
            return 200 <= self.status_code < 300

        @property
        def text(self) -> str:
            return json.dumps(self._data)

        @property
        def content(self) -> bytes:
            return json.dumps(self._data).encode()

        def json(self):
            return self._data

        def raise_for_status(self):
            if not self.ok:
                import requests

                raise requests.HTTPError(response=self)

    def fake_authorized_request(method: str, path: str, json_body=None, params=None):
        import requests

        if path == "/api/agents":
            agents = [
                {
                    "id": info["id"],
                    "agent_uuid": info["agent_uuid"],
                    "name": info["name"],
                }
                for info in agents_store.values()
            ]
            return FakeResponse(data={"agents": agents, "template_agents": []})

        if path.startswith("/api/agents/"):
            agent_id = path.split("/")[-1]
            info = agents_store.get(agent_id)
            if info is None:
                raise requests.HTTPError(response=FakeResponse(status_code=404))
            if path.endswith("/variables"):
                return FakeResponse(data={"variables": info.setdefault("env", {}).copy()})
            if "/variables/" in path:
                var_name = path.split("/")[-1]
                env = info.setdefault("env", {})
                if method == "GET":
                    if var_name not in env:
                        raise requests.HTTPError(response=FakeResponse(status_code=404))
                    return FakeResponse(data={"name": var_name, "value": env[var_name]})
                if method == "PUT":
                    env[var_name] = json_body["value"]
                    return FakeResponse(data={"status": "updated"})
                if method == "DELETE":
                    env.pop(var_name, None)
                    return FakeResponse(data={"status": "deleted"})
            return FakeResponse(
                data={
                    "id": info["id"],
                    "agent_uuid": info["agent_uuid"],
                    "name": info["name"],
                    "agent": info.get("agent", empty_graph()),
                }
            )

        raise AssertionError(f"Unexpected request {method} {path}")

    def fake_save_agent(graph, *, name, description=None, published=None, emoji=None):
        agent_id = f"agent-{len(agents_store) + 1}"
        agent_uuid = f"uuid-{len(agents_store) + 1}"
        agents_store[agent_id] = {
            "id": agent_id,
            "agent_uuid": agent_uuid,
            "name": name,
            "agent": graph,
            "env": {},
        }
        return {"status": "saved", "id": agent_id, "agent_uuid": agent_uuid}

    sys.modules.pop("hurozo", None)
    sdk = importlib.import_module("hurozo")
    monkeypatch.setattr(sdk, "_authorized_request", fake_authorized_request)
    monkeypatch.setattr(sdk, "_save_agent", fake_save_agent)
    return sdk


def test_agent_env_crud(monkeypatch, tmp_path):
    sdk = _load_sdk(monkeypatch, tmp_path)
    agent = sdk.Agent("My Agent")
    assert agent.set_env("FOO", "bar")["status"] == "saved"
    assert agent.get_env("FOO") == "bar"
    assert agent.list_env() == {"FOO": "bar"}
    assert agent.delete_env("FOO")["status"] == "deleted"
    assert agent.list_env() == {}


def test_agent_env_local_blocked(monkeypatch, tmp_path):
    sdk = _load_sdk(monkeypatch, tmp_path)
    agent = sdk.Agent("Another Agent")
    # Newly created agent has no variables but still returns dict
    assert agent.list_env() == {}
*** End Patch
PATCH
