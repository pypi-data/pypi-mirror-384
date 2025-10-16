"""Lightweight Hurozo client library.

Exports:
  - :class:`Agent` for invoking existing agents or building graphs locally.
  - :class:`Node` for composing agent graphs in Python.
  - :class:`RemoteAgent` to register long-lived remote workers.

Quick usage:
  - ``Agent("My Agent")`` loads the remote definition (or creates a new empty agent).
  - ``Agent("My Agent").addNodes(...)`` stages local graph changes before saving.
  - ``agent.run()`` executes the staged graph locally unless it matches the remote definition.
  - Remote worker: ``RemoteAgent(handler, {"inputs": [...], "outputs": [...]})``.

Configuration:
  - ``HUROZO_API_TOKEN``: Bearer token for API calls (required for execution/saves).
  - ``HUROZO_SERVER_URI``: Base URL for the API (default: ``https://hurozo.com``).
  - ``HUROZO_TOKEN`` / ``HUROZO_API_URL``: Optional aliases used by :class:`RemoteAgent`.
  - ``HUROZO_NODES_FILE``: Optional path to ``nodes.json`` if not in ``.hurozo``.
"""

from __future__ import annotations

import json
import os
import queue
import re
import sys
import threading
import time
from pathlib import Path
from copy import deepcopy
from typing import Any, Callable, Dict, Iterable, Optional, Sequence, Union

import requests

from .firebase import FirebaseAuthError, FirebaseRealtimeBridge, RemoteRequest


NODES_RELATIVE_PATH = Path(".hurozo") / "nodes.json"

_NODE_MANIFEST_CACHE: Dict[str, Any] | None = None
_NODE_MANIFEST_PATH: Path | None = None
_NODE_FULL_MAP: Dict[str, Dict[str, Any]] | None = None
_NODE_SHORT_MAP: Dict[str, list[Dict[str, Any]]] | None = None
_NODE_SUGAR_MAP: Dict[str, str] | None = None
_NODE_SUGAR_AMBIGUOUS: set[str] | None = None


def _server_base_uri() -> str:
    """Return the configured Hurozo server base URI without trailing slash."""
    return os.environ.get("HUROZO_SERVER_URI", "https://hurozo.com").rstrip("/")


def _require_token() -> str:
    token = os.environ.get("HUROZO_API_TOKEN")
    if not token:
        raise RuntimeError("HUROZO_API_TOKEN environment variable is required")
    return token


def _authorized_request(
    method: str,
    path: str,
    *,
    json_body: Any | None = None,
    params: Dict[str, Any] | None = None,
) -> requests.Response:
    token = _require_token()
    base_uri = _server_base_uri()
    url = f"{base_uri}{path}"
    headers = {"Authorization": f"Bearer {token}"}
    if json_body is not None:
        headers.setdefault("Content-Type", "application/json")
    response = requests.request(
        method,
        url,
        headers=headers,
        json=json_body,
        params=params,
        timeout=120,
    )
    response.raise_for_status()
    return response


def _locate_manifest_path() -> Path | None:
    env_path = os.environ.get("HUROZO_NODES_FILE")
    if env_path:
        candidate = Path(env_path).expanduser()
        if candidate.exists():
            return candidate
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        candidate = parent / NODES_RELATIVE_PATH
        if candidate.exists():
            return candidate
    return None


def _canonicalize_identifier(value: str) -> str:
    return re.sub(r"[^0-9a-zA-Z]+", "", value).lower()


def _ensure_manifest_loaded() -> None:
    global _NODE_MANIFEST_CACHE, _NODE_MANIFEST_PATH, _NODE_FULL_MAP, _NODE_SHORT_MAP
    global _NODE_SUGAR_MAP, _NODE_SUGAR_AMBIGUOUS
    if _NODE_MANIFEST_CACHE is not None:
        return
    manifest_path = _locate_manifest_path()
    if not manifest_path:
        raise RuntimeError(
            "Unable to locate .hurozo/nodes.json. Run 'hurozo init' or set HUROZO_NODES_FILE."
        )
    try:
        raw = json.loads(manifest_path.read_text())
    except Exception as exc:
        raise RuntimeError(f"Failed to read node manifest at {manifest_path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise RuntimeError("Node manifest must be a JSON object with a 'nodes' key.")
    nodes = raw.get("nodes")
    if not isinstance(nodes, list):
        raise RuntimeError("Node manifest missing 'nodes' list.")

    full_map: Dict[str, Dict[str, Any]] = {}
    short_map: Dict[str, list[Dict[str, Any]]] = {}
    sugar_map: Dict[str, str] = {}
    sugar_ambiguous: set[str] = set()

    def register_alias(alias: str, full_type_name: str) -> None:
        key = _canonicalize_identifier(alias)
        if not key:
            return
        if key in sugar_ambiguous:
            return
        existing = sugar_map.get(key)
        if existing and existing != full_type_name:
            sugar_map.pop(key, None)
            sugar_ambiguous.add(key)
            return
        if existing is None:
            sugar_map[key] = full_type_name

    for entry in nodes:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        category = entry.get("category") or ""
        if not name:
            continue
        full_type = f"{category}/{name}" if category else str(name)
        full_map[full_type] = entry
        short_map.setdefault(str(name), []).append(entry)

        alias_candidates = {
            full_type,
            full_type.replace("/", "_"),
            full_type.lower().replace("/", "_"),
            str(name),
            re.sub(r"(?<!^)(?=[A-Z])", "_", str(name)).lower(),
        }
        for alias in alias_candidates:
            register_alias(alias, full_type)

    _NODE_MANIFEST_CACHE = raw
    _NODE_MANIFEST_PATH = manifest_path
    _NODE_FULL_MAP = full_map
    _NODE_SHORT_MAP = short_map
    _NODE_SUGAR_MAP = sugar_map
    _NODE_SUGAR_AMBIGUOUS = sugar_ambiguous


def _node_manifest_entry(type_name: str) -> Dict[str, Any]:
    _ensure_manifest_loaded()
    assert _NODE_FULL_MAP is not None
    assert _NODE_SHORT_MAP is not None
    type_name = type_name.strip()
    entry = _NODE_FULL_MAP.get(type_name)
    if entry:
        return entry
    short_candidates = _NODE_SHORT_MAP.get(type_name)
    if short_candidates:
        if len(short_candidates) == 1:
            return short_candidates[0]
        categories = ", ".join(sorted({c.get("category") or "" for c in short_candidates}))
        raise RuntimeError(
            f"Node '{type_name}' is ambiguous across categories ({categories}). "
            "Use 'Category/Name' notation."
        )
    raise RuntimeError(
        f"Node '{type_name}' not found in manifest. Run 'hurozo nodes refresh' to update."
    )


def _resolve_node_type_from_identifier(identifier: str) -> str:
    _ensure_manifest_loaded()
    key = _canonicalize_identifier(identifier)
    if not key:
        raise AttributeError(identifier)
    if _NODE_SUGAR_MAP is None:
        raise AttributeError(identifier)
    type_name = _NODE_SUGAR_MAP.get(key)
    if type_name:
        return type_name
    if _NODE_SUGAR_AMBIGUOUS and key in _NODE_SUGAR_AMBIGUOUS:
        raise AttributeError(
            f"Multiple nodes match identifier '{identifier}'. Use 'Category/Name' notation."
        )
    raise AttributeError(f"Node shortcut '{identifier}' not found in manifest")


def _flatten_nodes_args(items: Sequence[Union['Node', Sequence['Node']]]) -> list['Node']:
    result: list['Node'] = []
    for item in items:
        if isinstance(item, Node):
            if item not in result:
                result.append(item)
        elif isinstance(item, (list, tuple, set)):
            for inner in _flatten_nodes_args(list(item)):
                if inner not in result:
                    result.append(inner)
        else:
            raise TypeError("agent.addNodes expects Node instances")
    return result


def _json_dumps(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True)



class NodeOutput:
    """Represents the output slot of a node for graph wiring."""  # pragma: no cover - repr only

    __slots__ = ("node", "index")

    def __init__(self, node: "Node", index: int = 0):
        self.node = node
        self.index = index


def _same_binding(a: "NodeOutput", b: "NodeOutput") -> bool:
    return a.node is b.node and a.index == b.index


class Node:
    """Programmatic representation of a Hurozo node."""

    def __init__(self, node_type: str, *, properties: Optional[Dict[str, Any]] = None):
        entry = _node_manifest_entry(node_type)
        self._entry = entry
        self.category: str = entry.get("category") or ""
        self.name: str = entry.get("name") or node_type
        self.display_name: str = entry.get("display_name") or self.name
        self.type: str = f"{self.category}/{self.name}" if self.category else self.name
        self.properties: Dict[str, Any] = dict(properties or {})
        self._inputs_def: list[Dict[str, Any]] = list(entry.get("inputs") or [])
        self._outputs_def: list[Dict[str, Any]] = list(entry.get("outputs") or [])
        self._input_bindings: Dict[str, Union[NodeOutput, list[NodeOutput]]] = {}
        self._input_lookup: Dict[str, str] = {
            str(inp.get("name")).lower(): str(inp.get("name"))
            for inp in self._inputs_def
            if inp.get("name")
        }
        self._multi_inputs: set[str] = {
            str(inp.get("name"))
            for inp in self._inputs_def
            if inp.get("multi_input") and inp.get("name")
        }
        self._input_order: list[str] = [str(inp.get("name")) for inp in self._inputs_def if inp.get("name")]
        self._last_run: Dict[str, Any] | None = None
        self._has_execute_input = "execute" in self._input_lookup

    def __repr__(self) -> str:
        return f"Node({self.type})"

    def __call__(self, *args: Any, **kwargs: Any) -> "Node":
        if len(args) == 1 and isinstance(args[0], dict) and not kwargs:
            for key, value in args[0].items():
                self._set_input(key, value)
            return self

        if args:
            remaining = [name for name in self._input_order if name not in self._input_bindings]
            if len(remaining) == 1:
                for value in args:
                    self._set_input(remaining[0], value)
            else:
                ordering = list(remaining)
                if self._has_execute_input and "execute" in ordering:
                    ordering.remove("execute")
                    ordering.append("execute")
                for value, name in zip(args, ordering):
                    self._set_input(name, value)

        for key, value in kwargs.items():
            self._set_input(key, value)
        return self

    def set_property(self, name: str, value: Any) -> "Node":
        self.properties[name] = value
        return self

    def output(self, index: int = 0) -> NodeOutput:
        return NodeOutput(self, index)

    @property
    def last_result(self) -> Any:
        if not self._last_run:
            return None
        return self._last_run.get("result")

    def to_agent_graph(self) -> Dict[str, Any]:
        graph, _ = _GraphBuilder([self]).build()
        return graph

    def run(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        if args or kwargs:
            self(*args, **kwargs)
        graph, id_map = _GraphBuilder([self]).build()
        response = _execute_graph(graph)
        node_id = id_map.get(self)
        result = None
        if node_id is not None:
            result = (response.get("results") or {}).get(str(node_id))
        self._last_run = {"response": response, "node_id": node_id, "result": result}
        return response

    def print(self) -> None:
        print(_json_dumps(self.to_agent_graph()))

    def _set_input(self, name: str, value: Any) -> None:
        actual = self._resolve_input_name(name)
        if actual == "execute" and self._has_execute_input:
            # Allow explicit boolean control without wiring additional nodes.
            if isinstance(value, bool):
                if value:
                    self._input_bindings.pop(actual, None)
                    return
                binding = self._normalize_binding(value)
                self._input_bindings[actual] = binding
                return
            if isinstance(value, (Node, NodeOutput, list, tuple)):
                binding = self._normalize_binding(value)
                self._input_bindings[actual] = binding
                return
            binding = self._normalize_binding(value)
            self._input_bindings[actual] = binding
            return

        binding = None
        meta = None
        for entry in self._inputs_def:
            if str(entry.get("name")) == actual:
                meta = entry
                break

        if (
            meta is not None
            and not isinstance(value, (Node, NodeOutput, list, tuple))
        ):
            default_val = meta.get("default")
            if default_val is not None and value == default_val:
                self._input_bindings.pop(actual, None)
                return
            binding = self._normalize_binding(value)
        else:
            binding = self._normalize_binding(value)
        if actual in self._multi_inputs:
            existing = self._input_bindings.get(actual)
            if existing is None:
                self._input_bindings[actual] = binding if isinstance(binding, list) else [binding]
            else:
                if not isinstance(existing, list):
                    existing = [existing]
                if isinstance(binding, list):
                    for item in binding:
                        if all(not _same_binding(item, other) for other in existing):
                            existing.append(item)
                else:
                    if all(not _same_binding(binding, other) for other in existing):
                        existing.append(binding)
                self._input_bindings[actual] = existing
        else:
            if isinstance(binding, list):
                if not binding:
                    return
                binding = binding[0]
            self._input_bindings[actual] = binding

    def _resolve_input_name(self, name: str) -> str:
        if name in self._input_order:
            return name
        lower = name.lower()
        if lower in self._input_lookup:
            return self._input_lookup[lower]
        raise KeyError(f"Input '{name}' not found on node {self.type}")

    def _normalize_binding(self, value: Any) -> Union[NodeOutput, list[NodeOutput]]:
        if isinstance(value, NodeOutput):
            return value
        if isinstance(value, Node):
            return NodeOutput(value, 0)
        if isinstance(value, (list, tuple)):
            bindings: list[NodeOutput] = []
            for item in value:
                normalized = self._normalize_binding(item)
                if isinstance(normalized, list):
                    bindings.extend(normalized)
                else:
                    bindings.append(normalized)
            return bindings
        return _create_literal_binding(value)


def _create_literal_binding(value: Any) -> NodeOutput:
    if isinstance(value, NodeOutput):
        return value
    if isinstance(value, bool):
        node = Node("Basic/Bool")
        node.set_property("value", value)
        return NodeOutput(node, 0)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        node = Node("Basic/ConstantNumber")
        node.set_property("value", value)
        return NodeOutput(node, 0)
    if isinstance(value, str):
        node = Node("Basic/Input/TextArea")
        node.set_property("text", value)
        return NodeOutput(node, 0)
    if value is None:
        node = Node("Basic/Input/TextArea")
        node.set_property("text", "")
        return NodeOutput(node, 0)
    node = Node("Basic/Input/TextArea")
    try:
        serialized = json.dumps(value)
    except TypeError:
        serialized = str(value)
    node.set_property("text", serialized)
    return NodeOutput(node, 0)


class _GraphBuilder:
    """Construct LiteGraph-compatible payloads from Node instances."""

    def __init__(self, roots: Sequence[Node]):
        self.roots = [node for node in roots if isinstance(node, Node)]
        self._order: list[Node] = []
        self._node_ids: Dict[Node, int] = {}
        self._payloads: Dict[Node, Dict[str, Any]] = {}
        self._links: list[list[Any]] = []
        self._link_counter = 0

    def build(self) -> tuple[Dict[str, Any], Dict[Node, int]]:
        self._collect_nodes()
        for idx, node in enumerate(self._order, start=1):
            self._node_ids[node] = idx
        for order_index, node in enumerate(self._order):
            payload = self._build_node_payload(node, order_index)
            self._payloads[node] = payload
        graph = {
            "last_node_id": len(self._order),
            "last_link_id": self._link_counter,
            "nodes": [self._payloads[node] for node in self._order],
            "links": self._links,
            "groups": [],
            "config": {},
            "extra": {},
            "version": 0.4,
        }
        return graph, dict(self._node_ids)

    def _collect_nodes(self) -> None:
        seen: set[Node] = set()

        def visit(node: Node) -> None:
            if node in seen:
                return
            seen.add(node)
            for binding in node._input_bindings.values():
                if isinstance(binding, list):
                    for sub in binding:
                        visit(sub.node)
                elif isinstance(binding, NodeOutput):
                    visit(binding.node)
            self._order.append(node)

        for root in self.roots:
            visit(root)

    def _build_node_payload(self, node: Node, order_index: int) -> Dict[str, Any]:
        node_id = self._node_ids[node]
        payload: Dict[str, Any] = {
            "id": node_id,
            "type": node.type,
            "properties": dict(node.properties),
            "flags": {},
            "order": order_index,
            "mode": 0,
        }

        outputs_payload: list[Dict[str, Any]] = []
        for idx, output_def in enumerate(node._outputs_def):
            out_meta = dict(output_def) if isinstance(output_def, dict) else {}
            out_name = out_meta.get("name") or f"out{idx}"
            out_entry: Dict[str, Any] = {
                "name": out_name,
                "type": out_meta.get("type") or "*",
                "slot_index": idx,
                "links": [],
            }
            if "label" in out_meta:
                out_entry["label"] = out_meta["label"]
            outputs_payload.append(out_entry)
        if outputs_payload:
            payload["outputs"] = outputs_payload
        self._payloads[node] = payload

        inputs_payload: list[Dict[str, Any]] = []
        for idx, input_def in enumerate(node._inputs_def):
            meta = dict(input_def) if isinstance(input_def, dict) else {}
            in_name = meta.get("name") or f"in{idx}"
            entry: Dict[str, Any] = {
                "name": in_name,
                "type": meta.get("type") or "*",
                "link": None,
            }
            if "label" in meta:
                entry["label"] = meta["label"]
            multi_input = bool(meta.get("multi_input"))
            if multi_input:
                entry["multi_input"] = True
                entry["links"] = []

            binding = node._input_bindings.get(in_name)
            if isinstance(binding, list):
                link_ids: list[int] = []
                for item in binding:
                    link_ids.append(self._register_link(item, node, idx, entry["type"]))
                entry["links"] = link_ids
                entry["link"] = link_ids[-1] if link_ids else None
            elif isinstance(binding, NodeOutput):
                link_id = self._register_link(binding, node, idx, entry["type"])
                entry["link"] = link_id
            else:
                entry["link"] = None
                if multi_input:
                    entry["links"] = []
            if not multi_input:
                entry.pop("links", None)
            inputs_payload.append(entry)
        if inputs_payload:
            payload["inputs"] = inputs_payload

        # Normalize empty link collections to match editor output
        if "outputs" in payload:
            for out_entry in payload["outputs"]:
                if isinstance(out_entry.get("links"), list) and not out_entry["links"]:
                    out_entry["links"] = None
        return payload

    def _register_link(self, binding: NodeOutput, target: Node, target_slot: int, link_type: Any) -> int:
        link_id = self._next_link_id()
        origin = binding.node
        origin_id = self._node_ids.get(origin)
        if origin_id is None:
            raise RuntimeError("Encountered unregistered node while building graph")
        link_type_str = link_type if isinstance(link_type, str) else str(link_type)
        self._links.append([
            link_id,
            origin_id,
            binding.index,
            self._node_ids[target],
            target_slot,
            link_type_str,
        ])
        origin_payload = self._payloads.get(origin)
        if origin_payload:
            outputs = origin_payload.get("outputs") or []
            if binding.index < len(outputs):
                slots = outputs[binding.index].get("links")
                if slots is None:
                    slots = []
                    outputs[binding.index]["links"] = slots
                slots.append(link_id)
        return link_id

    def _next_link_id(self) -> int:
        self._link_counter += 1
        return self._link_counter


def _execute_graph(graph: Dict[str, Any], inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    token = _require_token()
    base_uri = _server_base_uri()
    payload = {"graph": graph}
    if inputs:
        payload["inputs"] = inputs
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    response = requests.post(
        f"{base_uri}/execute",
        headers=headers,
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def _save_agent(
    graph: Dict[str, Any],
    *,
    name: str,
    description: str | None = None,
    published: bool | None = None,
    emoji: str | None = None,
) -> Dict[str, Any]:
    token = _require_token()
    base_uri = _server_base_uri()
    payload: Dict[str, Any] = {"name": name, "graph": graph}
    if description is not None:
        payload["agent_description"] = description
    if published is not None:
        payload["published"] = bool(published)
    if emoji:
        payload["emoji"] = emoji
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    response = requests.post(
        f"{base_uri}/api/agents",
        headers=headers,
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def _to_snake(name: str) -> str:
    """Convert a name to snake_case suitable for env vars."""
    name = re.sub(r"[^0-9a-zA-Z]+", "_", name)
    name = re.sub(r"(?<!^)(?=[A-Z])", "_", name)
    return name.strip("_").lower()


def _empty_graph() -> Dict[str, Any]:
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


def _merge_graphs(base: Dict[str, Any] | None, extra: Dict[str, Any]) -> Dict[str, Any]:
    """Merge an additional LiteGraph payload into an existing graph."""

    merged = deepcopy(base) if base else _empty_graph()
    extra_graph = deepcopy(extra) if extra else {}

    extra_nodes = extra_graph.get("nodes") or []
    extra_links = extra_graph.get("links") or []
    if not extra_nodes and not extra_links:
        return deepcopy(merged)

    merged_nodes = merged.setdefault("nodes", [])
    merged_links = merged.setdefault("links", [])
    merged.setdefault("groups", merged.get("groups", []))
    merged.setdefault("config", merged.get("config", {}))
    merged.setdefault("extra", merged.get("extra", {}))

    node_id_offset = max(
        [node.get("id", 0) for node in merged_nodes if isinstance(node.get("id"), int)] or [0]
    )
    link_id_offset = max(
        [link[0] for link in merged_links if isinstance(link, (list, tuple)) and link and isinstance(link[0], int)]
        or [0]
    )
    order_offset_source = [
        node.get("order", -1) for node in merged_nodes if isinstance(node.get("order"), int)
    ]
    order_offset = (max(order_offset_source) + 1) if order_offset_source else len(merged_nodes)

    for index, node in enumerate(extra_nodes):
        node_copy = deepcopy(node)
        original_id = node_copy.get("id")
        if isinstance(original_id, int):
            node_copy["id"] = node_id_offset + original_id
        else:
            node_copy["id"] = node_id_offset + index + 1
        node_copy["order"] = order_offset + index

        inputs = node_copy.get("inputs")
        if isinstance(inputs, list):
            for entry in inputs:
                link_val = entry.get("link")
                if isinstance(link_val, int):
                    entry["link"] = link_val + link_id_offset
                links_val = entry.get("links")
                if isinstance(links_val, list):
                    entry["links"] = [lid + link_id_offset for lid in links_val if isinstance(lid, int)]

        outputs = node_copy.get("outputs")
        if isinstance(outputs, list):
            for entry in outputs:
                links_val = entry.get("links")
                if isinstance(links_val, list):
                    entry["links"] = [lid + link_id_offset for lid in links_val if isinstance(lid, int)]

        merged_nodes.append(node_copy)

    for link in extra_links:
        if not isinstance(link, (list, tuple)) or len(link) < 5:
            continue
        link_copy = list(link)
        if isinstance(link_copy[0], int):
            link_copy[0] = link_copy[0] + link_id_offset
        if isinstance(link_copy[1], int):
            link_copy[1] = link_copy[1] + node_id_offset
        if len(link_copy) > 3 and isinstance(link_copy[3], int):
            link_copy[3] = link_copy[3] + node_id_offset
        merged_links.append(link_copy)

    merged["last_node_id"] = max(
        merged.get("last_node_id", 0),
        max([node.get("id", 0) for node in merged_nodes if isinstance(node.get("id"), int)] or [0]),
    )
    merged["last_link_id"] = max(
        merged.get("last_link_id", 0),
        max([link[0] for link in merged_links if isinstance(link, (list, tuple)) and link and isinstance(link[0], int)] or [0]),
    )

    if "version" not in merged and extra_graph.get("version") is not None:
        merged["version"] = extra_graph.get("version")

    return merged


class Agent:
    """Represents a remote agent or a locally constructed graph."""

    def __init__(self, identifier: str, is_uuid: bool = False):
        if not identifier:
            raise ValueError("Agent name or identifier must be provided")
        self.inputs: Dict[str, Any] = {}
        self._nodes: list[Node] = []
        self._identifier: str = identifier
        self._is_uuid = is_uuid
        self._remote_info: Dict[str, Any] | None = None
        self._remote_graph: Dict[str, Any] | None = None
        self._initialize_remote_state()

    def input(self, mapping: Dict[str, Any]) -> "Agent":
        self.inputs.update(mapping)
        return self

    def addNodes(self, *nodes: Union[Node, Sequence[Node]]) -> "Agent":
        flattened = _flatten_nodes_args(nodes)
        for node in flattened:
            if node not in self._nodes:
                self._nodes.append(node)
        return self

    def to_agent_graph(self) -> Dict[str, Any]:
        if self._nodes:
            graph, _ = _GraphBuilder(self._nodes).build()
            if self._remote_graph:
                return _merge_graphs(self._remote_graph, graph)
            return graph
        if self._remote_graph is not None:
            return json.loads(json.dumps(self._remote_graph))
        return _empty_graph()

    def print(self) -> None:
        print(_json_dumps(self.to_agent_graph()))

    def run(self, inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if inputs:
            self.input(inputs)
        if self._nodes:
            graph = self.to_agent_graph()
            return _execute_graph(graph, self.inputs)
        return self._run_remote()

    def save(
        self,
        name: str,
        *,
        description: str | None = None,
        published: bool | None = None,
        emoji: str | None = None,
    ) -> Dict[str, Any]:
        graph = self.to_agent_graph()
        result = _save_agent(
            graph,
            name=name,
            description=description,
            published=published,
            emoji=emoji,
        )
        agent_id = result.get("id")
        if agent_id:
            self._identifier = agent_id
            self._is_uuid = False
            self._remote_info = {
                "id": agent_id,
                "agent_uuid": result.get("agent_uuid"),
                "name": name,
            }
            self._remote_graph = graph
            self._nodes.clear()
        return result

    # ------------------------------------------------------------------
    # Remote agent helpers
    # ------------------------------------------------------------------
    def _run_remote(self) -> Dict[str, Any]:
        token = _require_token()
        base_uri = _server_base_uri()
        agent_key = self._resolve_uuid(token)
        url = f"{base_uri}/execute/{agent_key}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        response = requests.post(url, headers=headers, json={"inputs": self.inputs}, timeout=120)
        response.raise_for_status()
        try:
            return response.json()
        except Exception:
            return {"status": response.status_code, "text": response.text}

    def _initialize_remote_state(self) -> None:
        info = self._lookup_agent()
        if info:
            self._remote_info = info
            self._remote_graph = self._fetch_agent_graph(info["id"])
        else:
            graph = _empty_graph()
            result = _save_agent(
                graph,
                name=self._identifier,
                description=None,
                published=None,
                emoji=None,
            )
            agent_id = result.get("id") or self._identifier
            self._remote_info = {
                "id": agent_id,
                "agent_uuid": result.get("agent_uuid"),
                "name": self._identifier,
            }
            self._remote_graph = graph

    def _resolve_agent_metadata(self) -> Dict[str, Any]:
        if self._remote_info:
            return self._remote_info
        identifier = getattr(self, "_identifier", None)
        if not identifier:
            raise RuntimeError("Agent identifier is not set")

        # Attempt direct fetch (hashed id)
        try:
            resp = _authorized_request("GET", f"/api/agents/{identifier}")
            data = resp.json() or {}
            info = {
                "id": data.get("id", identifier),
                "agent_uuid": data.get("agent_uuid"),
                "name": data.get("name"),
            }
            self._remote_info = info
            return info
        except requests.HTTPError as exc:
            status = getattr(exc.response, "status_code", None)
            if status not in (404, 400):
                raise RuntimeError("Failed to load agent metadata") from exc

        # Fall back to agent list lookup
        info = self._lookup_agent()
        if not info:
            raise RuntimeError("Agent not found")
        self._remote_info = info
        return info

    def _ensure_remote_agent_id(self) -> str:
        info = self._resolve_agent_metadata()
        agent_id = info.get("id")
        if not agent_id:
            raise RuntimeError("Agent identifier could not be resolved")
        return agent_id

    def _resolve_uuid(self, token: str) -> str:
        if getattr(self, "_is_uuid", False) or not getattr(self, "_identifier", None):
            return self._identifier or ""
        try:
            resp = _authorized_request("GET", "/api/agents")
            agents = resp.json().get("agents", []) if resp.content else []
            identifier = self._identifier
            target: Optional[dict] = next((a for a in agents if a.get("id") == identifier), None)
            if not target:
                target = next((a for a in agents if a.get("name") == identifier), None)
            if not target:
                lid = identifier.lower()
                target = next((a for a in agents if str(a.get("name", "")).lower() == lid), None)
            return target.get("agent_uuid") if target and target.get("agent_uuid") else identifier
        except Exception:
            return self._identifier

    # ------------------------------------------------------------------
    # Environment variable helpers
    # ------------------------------------------------------------------

    def list_env(self) -> Dict[str, Any]:
        agent_id = self._ensure_remote_agent_id()
        resp = _authorized_request("GET", f"/api/agents/{agent_id}/variables")
        data = resp.json() or {}
        return data.get("variables", {})

    def get_env(self, name: str) -> Any:
        agent_id = self._ensure_remote_agent_id()
        resp = _authorized_request("GET", f"/api/agents/{agent_id}/variables/{name}")
        data = resp.json() or {}
        return data.get("value")

    def set_env(self, name: str, value: Any) -> Dict[str, Any]:
        agent_id = self._ensure_remote_agent_id()
        resp = _authorized_request(
            "PUT",
            f"/api/agents/{agent_id}/variables/{name}",
            json_body={"value": value},
        )
        return resp.json() or {}

    def delete_env(self, name: str) -> Dict[str, Any]:
        agent_id = self._ensure_remote_agent_id()
        resp = _authorized_request("DELETE", f"/api/agents/{agent_id}/variables/{name}")
        return resp.json() or {}

    def _lookup_agent(self) -> Dict[str, Any] | None:
        resp = _authorized_request("GET", "/api/agents")
        payload = resp.json() if resp.content else {}
        agents = payload.get("agents", [])
        identifier = self._identifier
        if self._is_uuid:
            return next(
                (
                    {
                        "id": ag.get("id"),
                        "agent_uuid": ag.get("agent_uuid"),
                        "name": ag.get("name"),
                    }
                    for ag in agents
                    if ag.get("agent_uuid") == identifier or ag.get("id") == identifier
                ),
                None,
            )
        match = next(
            (
                {
                    "id": ag.get("id"),
                    "agent_uuid": ag.get("agent_uuid"),
                    "name": ag.get("name"),
                }
                for ag in agents
                if ag.get("id") == identifier
            ),
            None,
        )
        if match:
            return match
        lowered = identifier.lower()
        return next(
            (
                {
                    "id": ag.get("id"),
                    "agent_uuid": ag.get("agent_uuid"),
                    "name": ag.get("name"),
                }
                for ag in agents
                if str(ag.get("name", "")).lower() == lowered
            ),
            None,
        )

    def _fetch_agent_graph(self, agent_id: str) -> Dict[str, Any]:
        try:
            resp = _authorized_request("GET", f"/api/agents/{agent_id}")
            data = resp.json() or {}
            graph = data.get("agent")
            if isinstance(graph, dict):
                return graph
        except requests.HTTPError:
            pass
        return _empty_graph()


class RemoteAgent:
    """Register a Python callable as a remote agent using REST polling."""

    def __init__(self, handler: Callable[..., Dict[str, Any]], meta: Dict[str, Any]):
        self.handler = handler
        self.name = meta.get("name") or handler.__name__
        self.inputs = meta.get("inputs", [])
        self.outputs = meta.get("outputs", [])

        self.token = (
            os.environ.get("HUROZO_TOKEN")
            or os.environ.get("HUROZO_API_TOKEN")
            or ""
        )
        if not self.token:
            raise RuntimeError("HUROZO_TOKEN or HUROZO_API_TOKEN must be set for RemoteAgent")
        self.base_url = (
            os.environ.get("HUROZO_API_URL")
            or os.environ.get("HUROZO_SERVER_URI", "https://hurozo.com")
        ).rstrip("/")
        self.poll_interval = float(os.environ.get("HUROZO_REMOTE_POLL_INTERVAL", "1.0"))

        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "hurozo-remote-agent/1.0"})

        self.debug = str(os.getenv("HUROZO_DEBUG", "")).strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

        self._stop = False
        self._stop_event = threading.Event()
        self._firebase: Optional[FirebaseRealtimeBridge] = None
        self._request_queue: "queue.Queue[RemoteRequest]" = queue.Queue()
        self._pending_request_ids: set[str] = set()

        threading.Thread(target=self._register_loop, daemon=True).start()
        if self._init_realtime():
            self._run_realtime_loop()
        else:
            self._run_polling_loop()

    def _log(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        if not self.debug:
            return
        line = f"[RemoteAgent:{self.name}] {message}"
        if extra:
            try:
                payload = json.dumps(extra, default=str)
            except Exception:
                payload = str(extra)
            line = f"{line} :: {payload}"
        print(line, flush=True)

    def _auth_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    def _register_loop(self) -> None:
        url = f"{self.base_url}/api/remote_agents/register"
        payload = {"name": self.name, "inputs": self.inputs, "outputs": self.outputs}
        self._log("registration loop started")
        while not self._stop_event.is_set():
            try:
                res = self._session.post(url, json=payload, headers=self._auth_headers(), timeout=30)
                if res.ok:
                    try:
                        data = res.json() or {}
                        keys = list(data.keys())
                    except Exception:
                        keys = []
                    self._log("registration succeeded", {"status": res.status_code, "response_keys": keys})
                else:
                    self._log("registration failed", {"status": res.status_code, "body": res.text})
            except Exception as exc:
                self._log("registration request errored", {"error": str(exc)})
            time.sleep(240)

    def _init_realtime(self) -> bool:
        try:
            bridge = FirebaseRealtimeBridge(debug=self.debug)
            bridge.bootstrap(self.base_url, self.token)
            self._firebase = bridge
            self._log("realtime bridge ready", {"user_id": bridge.user_id})
            return True
        except FirebaseAuthError as exc:
            self._log("realtime bridge auth failed", {"error": str(exc)})
        except Exception as exc:
            self._log("realtime bridge initialization failed", {"error": str(exc)})
        self._firebase = None
        return False

    def _run_realtime_loop(self) -> None:
        if not self._firebase:
            self._run_polling_loop()
            return
        listener_thread = threading.Thread(target=self._realtime_listener_loop, daemon=True)
        listener_thread.start()
        self._log("realtime loop started")
        try:
            while not self._stop_event.is_set():
                try:
                    request = self._request_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                try:
                    self._process_request({"uuid": request.uuid, "inputs": request.inputs, "_raw": request.raw})
                except KeyboardInterrupt:
                    self._stop = True
                    self._stop_event.set()
                    raise
                except Exception as exc:
                    self._log("realtime request handling failed", {"uuid": request.uuid, "error": str(exc)})
                finally:
                    self._pending_request_ids.discard(request.uuid)
        finally:
            self._stop = True
            self._stop_event.set()

    def _realtime_listener_loop(self) -> None:
        if not self._firebase:
            return

        def stop_check() -> bool:
            return self._stop_event.is_set()

        def enqueue(request: RemoteRequest) -> None:
            if request.uuid in self._pending_request_ids:
                return
            self._pending_request_ids.add(request.uuid)
            self._request_queue.put(request)
            self._log("enqueued realtime request", {"uuid": request.uuid})

        try:
            self._firebase.listen_remote_requests(self.name, enqueue, stop_check)
        except Exception as exc:
            self._log("realtime listener exited", {"error": str(exc)})

    def _run_polling_loop(self) -> None:
        self._log("polling loop started", {"poll_interval": self.poll_interval})
        try:
            while not self._stop_event.is_set():
                try:
                    requests_payload = self._fetch_pending_requests()
                except Exception as exc:
                    self._log("fetch pending failed; backing off", {"error": str(exc)})
                    time.sleep(self.poll_interval)
                    continue
                if not requests_payload:
                    self._log("no pending requests")
                    time.sleep(self.poll_interval)
                    continue
                self._log("fetched pending requests", {"count": len(requests_payload)})
                for request_payload in requests_payload:
                    try:
                        self._process_request(request_payload)
                    except KeyboardInterrupt:
                        self._stop = True
                        self._stop_event.set()
                        raise
                    except Exception as exc:
                        self._log("request handling failed", {"error": str(exc)})
                        time.sleep(0.1)
        finally:
            self._stop = True
            self._stop_event.set()

    def _fetch_pending_requests(self) -> Iterable[Dict[str, Any]]:
        url = f"{self.base_url}/api/remote_agents/requests"
        params = {"agent": self.name, "limit": 20}
        res = self._session.get(url, headers=self._auth_headers(), params=params, timeout=30)
        if not res.ok:
            self._log("pending requests http error", {"status": res.status_code, "body": res.text})
        res.raise_for_status()
        data = res.json() or {}
        requests_payload = data.get("requests") or []
        return [payload for payload in requests_payload if isinstance(payload, dict)]

    def _process_request(self, payload: Dict[str, Any]) -> None:
        uuid = payload.get("uuid") or payload.get("id")
        if not uuid:
            return
        inputs = payload.get("inputs") or {}
        if not isinstance(inputs, dict):
            inputs = {"input": inputs}
        self._log("processing request", {"uuid": uuid})
        if not self._update_request(uuid, "in_progress"):
            return
        self._emit_event("execution_started", {"runId": uuid})
        try:
            try:
                outputs = self.handler(**inputs)
            except TypeError:
                outputs = self.handler(inputs)
        except Exception as exc:
            message = getattr(exc, "message", None) or str(exc)
            self._update_request(uuid, "error", error={"message": message})
            self._log("wrote error response", {"uuid": uuid, "error": message})
            self._emit_event("execution_error", {"runId": uuid, "message": message})
            return
        result_map = self._normalize_outputs(outputs)
        if self._update_request(uuid, "done", outputs=result_map):
            self._log("wrote success response", {"uuid": uuid})
            self._emit_event("execution_finished", {"runId": uuid, "results": result_map})

    def _update_request(self, uuid: str, status: str, **payload: Any) -> bool:
        if self._firebase:
            try:
                outputs = payload.get("outputs") if status == "done" else None
                error = payload.get("error") if status == "error" else None
                if self._firebase.update_remote_request(uuid, status, outputs=outputs, error=error):
                    return True
            except Exception as exc:
                self._log("firestore update failed; falling back to REST", {"uuid": uuid, "status": status, "error": str(exc)})

        url = f"{self.base_url}/api/remote_agents/requests/{uuid}"
        body = {"status": status, "agent": self.name, **payload}
        res = self._session.post(url, headers=self._auth_headers(), json=body, timeout=15)
        if res.status_code == 409:
            self._log("request update conflict", {"uuid": uuid, "status": status})
            return False
        if not res.ok:
            self._log("request update failed", {"uuid": uuid, "status": status, "status_code": res.status_code, "body": res.text})
        res.raise_for_status()
        return True

    def _emit_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        if not self._firebase:
            return
        try:
            self._firebase.create_event(event_type, payload)
        except Exception as exc:
            self._log("failed to publish event", {"event": event_type, "error": str(exc)})

    def _normalize_outputs(self, outputs: Any) -> Dict[str, Any]:
        if outputs is None:
            return {name: None for name in self.outputs} if self.outputs else {}
        if isinstance(outputs, dict):
            if self.outputs:
                normalized = {name: outputs.get(name) for name in self.outputs}
                remaining = {k: v for k, v in outputs.items() if k not in normalized}
                normalized.update(remaining)
                return normalized
            return outputs
        if self.outputs:
            if len(self.outputs) == 1:
                return {self.outputs[0]: outputs}
            if isinstance(outputs, (list, tuple)):
                combined = {}
                for idx, name in enumerate(self.outputs):
                    combined[name] = outputs[idx] if idx < len(outputs) else None
                return combined
            return {self.outputs[0]: outputs}
        if isinstance(outputs, (list, tuple)):
            return {str(idx): value for idx, value in enumerate(outputs)}
        return {"output": outputs}


def __getattr__(name: str) -> Any:
    if name.startswith("_"):
        raise AttributeError(name)
    try:
        node_type = _resolve_node_type_from_identifier(name)
    except AttributeError as exc:
        raise exc

    def _factory(*args: Any, **kwargs: Any) -> Node:
        node = Node(node_type)
        if args or kwargs:
            return node(*args, **kwargs)
        return node

    _factory.__name__ = name
    _factory.__qualname__ = name
    _factory.__doc__ = f"Shortcut for Node('{node_type}')"
    return _factory


def enable_sugar(namespace: Dict[str, Any], *identifiers: str, include_core: bool = True) -> None:
    if not isinstance(namespace, dict):
        raise TypeError("enable_sugar expects a dict namespace, e.g., globals()")

    if include_core:
        namespace.setdefault("Agent", Agent)
        namespace.setdefault("Node", Node)
        namespace.setdefault("RemoteAgent", RemoteAgent)

    _ensure_manifest_loaded()
    assert _NODE_FULL_MAP is not None

    def assign(name: str) -> None:
        if not name:
            return
        if name in namespace:
            return
        try:
            namespace[name] = getattr(sys.modules[__name__], name)
        except AttributeError:
            pass

    if identifiers:
        for identifier in identifiers:
            assign(identifier)
        return

    for full_type in _NODE_FULL_MAP:
        snake = full_type.lower().replace("/", "_")
        assign(snake)
        simple = re.sub(r"(?<!^)(?=[A-Z])", "_", full_type.split("/")[-1]).lower()
        assign(simple)


__all__ = ["Agent", "Node", "RemoteAgent", "enable_sugar"]
