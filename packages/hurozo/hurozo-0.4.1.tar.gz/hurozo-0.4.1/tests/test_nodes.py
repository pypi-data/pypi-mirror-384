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


BASE_MANIFEST = {
    "nodes": [
        {
            "name": "ConcatStrings",
            "category": "Text/String",
            "display_name": "Concat Strings",
            "inputs": [
                {"name": "execute", "type": "execution,boolean", "label": "execution"},
                {"name": "a", "type": "string"},
                {"name": "b", "type": "string"},
                {"name": "separator", "type": "string", "default": " "}
            ],
            "outputs": [{"name": "result", "type": "string"}]
        },
        {
            "name": "CleanString",
            "category": "Text/Processing",
            "display_name": "Clean String",
            "inputs": [
                {"name": "execute", "type": "execution,boolean", "label": "execution"},
                {"name": "text", "type": "string"}
            ],
            "outputs": [{"name": "cleaned_text", "type": "string"}]
        },
        {
            "name": "TextArea",
            "category": "Basic/Input",
            "display_name": "Text Area",
            "inputs": [
                {"name": "execute", "type": "execution,boolean", "label": "execution"}
            ],
            "outputs": [{"name": "text", "type": "string"}]
        },
        {
            "name": "Bool",
            "category": "Basic",
            "display_name": "Bool",
            "inputs": [],
            "outputs": [{"name": "value", "type": "boolean"}]
        },
        {
            "name": "ConstantNumber",
            "category": "Basic",
            "display_name": "Constant Number",
            "inputs": [],
            "outputs": [{"name": "value", "type": "number"}]
        }
    ]
}


def _load_sdk(tmp_path, monkeypatch, manifest=None):
    manifest_data = manifest or BASE_MANIFEST
    manifest_path = tmp_path / "nodes.json"
    manifest_path.write_text(json.dumps(manifest_data))
    monkeypatch.setenv("HUROZO_NODES_FILE", str(manifest_path))
    monkeypatch.setenv("HUROZO_API_TOKEN", "test-token")
    monkeypatch.setenv("HUROZO_SERVER_URI", "https://example.com")

    if "python_webchannel" not in sys.modules:
        stub = types.ModuleType("python_webchannel")

        class EventType:  # pragma: no cover - placeholder stub
            pass

        class WebChannelError(RuntimeError):  # pragma: no cover - placeholder stub
            pass

        class WebChannelOptions:  # pragma: no cover - placeholder stub
            def __init__(self, *args, **kwargs) -> None:
                self.args = args
                self.kwargs = kwargs

        async def _noop_close() -> None:  # pragma: no cover - placeholder stub
            return None

        class _Transport:  # pragma: no cover - placeholder stub
            async def close(self) -> None:
                await _noop_close()

        def create_web_channel_transport(*args, **kwargs):  # pragma: no cover - placeholder stub
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
                if method == "GET":
                    if var_name not in info.setdefault("env", {}):
                        raise requests.HTTPError(response=FakeResponse(status_code=404))
                    return FakeResponse(data={"name": var_name, "value": info["env"][var_name]})
                if method == "PUT":
                    info.setdefault("env", {})[var_name] = json_body["value"]
                    return FakeResponse(data={"status": "updated"})
                if method == "DELETE":
                    info.setdefault("env", {}).pop(var_name, None)
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
    setattr(sdk, "_test_agents_store", agents_store)
    return sdk


def test_node_graph_builds_literals(tmp_path, monkeypatch):
    sdk = _load_sdk(tmp_path, monkeypatch)
    Node = sdk.Node

    concat = Node("Text/String/ConcatStrings")
    concat("foo", "bar", separator="-")

    graph = concat.to_agent_graph()

    assert graph["last_node_id"] == 4
    assert len(graph["links"]) == 3
    assert graph["groups"] == []
    assert graph["config"] == {}
    assert graph["extra"] == {}
    assert graph["version"] == 0.4
    types = [node["type"] for node in graph["nodes"]]
    assert types.count("Basic/Input/TextArea") == 3
    assert graph["nodes"][-1]["type"] == "Text/String/ConcatStrings"
    input_links = [entry for entry in graph["nodes"][-1].get("inputs", []) if entry["name"] != "execute"]
    assert all(item["link"] is not None for item in input_links)
    execute_input = next(inp for inp in graph["nodes"][-1]["inputs"] if inp["name"] == "execute")
    assert execute_input.get("label") == "execution"
    assert execute_input["link"] is None
    result_output = graph["nodes"][-1]["outputs"][0]
    assert result_output["links"] is None


def test_agent_combines_node_graphs(tmp_path, monkeypatch):
    sdk = _load_sdk(tmp_path, monkeypatch)
    Node = sdk.Node
    Agent = sdk.Agent

    text1 = Node("Basic/Input/TextArea").set_property("text", "Hello")
    text2 = Node("Basic/Input/TextArea").set_property("text", "World")
    concat = Node("Text/String/ConcatStrings")
    concat(text1, text2, separator="-")

    agent = Agent("builder-agent-1")
    agent.addNodes(concat)

    graph = agent.to_agent_graph()

    assert graph["last_node_id"] == 4
    assert len(graph["links"]) == 3
    root = graph["nodes"][-1]
    assert root["type"] == "Text/String/ConcatStrings"
    assert len([entry for entry in root.get("inputs", []) if entry["link"]]) == 3
    clean_nodes = [node for node in graph["nodes"] if node["type"] == "Text/Processing/CleanString"]
    for node_payload in clean_nodes:
        execute_slot = next(inp for inp in node_payload["inputs"] if inp["name"] == "execute")
        assert execute_slot.get("label") == "execution"
        assert execute_slot["link"] is None


def test_agent_merge_with_remote_graph(tmp_path, monkeypatch):
    sdk = _load_sdk(tmp_path, monkeypatch)
    Node = sdk.Node
    Agent = sdk.Agent
    agents_store = sdk._test_agents_store

    base_cleaner = Node("Text/Processing/CleanString")("  Remote plan  ")
    remote_graph = base_cleaner.to_agent_graph()
    stored_graph = json.loads(json.dumps(remote_graph))
    agents_store["agent-existing"] = {
        "id": "agent-existing",
        "agent_uuid": "uuid-existing",
        "name": "bruno",
        "agent": stored_graph,
        "env": {},
    }
    stored_snapshot = json.loads(json.dumps(stored_graph))

    clean_title = Node("Text/Processing/CleanString")("  Launch plan draft   \n\n")
    clean_summary = Node("Text/Processing/CleanString")(
        "Outline   goals, timeline, and owners."
    )
    concat = Node("Text/String/ConcatStrings")
    concat(clean_title, clean_summary, separator=" ")

    local_graph = concat.to_agent_graph()

    agent = Agent("bruno")
    agent.addNodes(concat)

    merged_graph = agent.to_agent_graph()

    remote_nodes = remote_graph.get("nodes", [])
    remote_links = remote_graph.get("links", [])
    assert merged_graph["nodes"][: len(remote_nodes)] == remote_nodes
    assert len(merged_graph["nodes"]) == len(remote_nodes) + len(local_graph.get("nodes", []))
    assert len(merged_graph["links"]) == len(remote_links) + len(local_graph.get("links", []))

    new_nodes = merged_graph["nodes"][len(remote_nodes) :]
    assert new_nodes
    remote_last_node_id = remote_graph.get("last_node_id", 0)
    assert all(node.get("id", 0) > remote_last_node_id for node in new_nodes)

    remote_links_len = len(remote_links)
    new_links = merged_graph["links"][remote_links_len:]
    remote_last_link_id = remote_graph.get("last_link_id", 0)
    assert all(link[0] > remote_last_link_id for link in new_links)

    concat_node = new_nodes[-1]
    assert concat_node["type"] == "Text/String/ConcatStrings"
    concat_inputs = [entry for entry in concat_node.get("inputs", []) if entry["name"] in {"a", "b"}]
    assert len(concat_inputs) == 2
    assert all(entry["link"] is not None for entry in concat_inputs)

    assert agents_store["agent-existing"]["agent"] == stored_snapshot


def test_node_attribute_factory(tmp_path, monkeypatch):
    sdk = _load_sdk(tmp_path, monkeypatch)
    factory = sdk.text_processing_cleanstring

    node = factory("  messy  ")
    assert isinstance(node, sdk.Node)
    assert node.type == "Text/Processing/CleanString"

    other = sdk.text_processing_cleanstring()
    assert isinstance(other, sdk.Node)
    assert other.type == "Text/Processing/CleanString"
    assert other is not node

    with pytest.raises(AttributeError):
        getattr(sdk, "not_a_real_node")


def test_enable_sugar_injects_shortcuts(tmp_path, monkeypatch):
    sdk = _load_sdk(tmp_path, monkeypatch)
    namespace: dict[str, Any] = {}

    sdk.enable_sugar(namespace)

    assert namespace["Agent"] is sdk.Agent
    assert namespace["Node"] is sdk.Node
    assert callable(namespace["text_processing_cleanstring"])

    node = namespace["text_processing_cleanstring"]("  messy  ")
    assert isinstance(node, sdk.Node)
    assert node.type == "Text/Processing/CleanString"

    shorthand = namespace["clean_string"]
    assert callable(shorthand)
    other = shorthand("trim me")
    assert other.type == "Text/Processing/CleanString"

    custom: dict[str, Any] = {}
    sdk.enable_sugar(custom, "text_processing_cleanstring", include_core=False)
    assert "Agent" not in custom
    assert callable(custom["text_processing_cleanstring"])


def test_default_literal_skips_node(tmp_path, monkeypatch):
    sdk = _load_sdk(tmp_path, monkeypatch)
    Node = sdk.Node

    concat = Node("Text/String/ConcatStrings")
    concat("foo", "bar", separator=" ")  # matches default separator

    graph = concat.to_agent_graph()

    separator_nodes = [
        node for node in graph["nodes"]
        if node["type"] == "Basic/Input/TextArea" and node.get("properties", {}).get("text") == " "
    ]
    assert not separator_nodes
    separator_inputs = [inp for inp in graph["nodes"][-1].get("inputs", []) if inp["name"] == "separator"]
    assert separator_inputs and separator_inputs[0]["link"] is None


def test_execute_defaults_and_overrides(tmp_path, monkeypatch):
    sdk = _load_sdk(tmp_path, monkeypatch)
    Node = sdk.Node

    cleaner = Node("Text/Processing/CleanString")(" messy ")
    assert "execute" not in cleaner.properties
    graph = cleaner.to_agent_graph()
    clean_node = graph["nodes"][-1]
    text_input = next(i for i in clean_node.get("inputs", []) if i.get("name") == "text")
    assert text_input.get("link")
    exec_input = next(i for i in clean_node.get("inputs", []) if i.get("name") == "execute")
    assert exec_input.get("label") == "execution"

    disabled = Node("Text/Processing/CleanString")(execute=False)
    graph_disabled = disabled.to_agent_graph()
    bool_nodes = [node for node in graph_disabled["nodes"] if node["type"] == "Basic/Bool"]
    assert bool_nodes and bool_nodes[0].get("properties", {}).get("value") is False

    upstream = Node("Text/Processing/CleanString")
    downstream = Node("Text/Processing/CleanString")(execute=upstream)
    assert "execute" not in downstream.properties
    payload = downstream.to_agent_graph()
    execute_inputs = [i for i in payload["nodes"][-1].get("inputs", []) if i.get("name") == "execute"]
    assert execute_inputs and execute_inputs[0]["link"] is not None
