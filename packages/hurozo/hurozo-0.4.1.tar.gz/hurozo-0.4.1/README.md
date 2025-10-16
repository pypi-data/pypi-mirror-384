# Hurozo CLI

Hurozo is a visual agent builder and execution platform. You compose agents as graphs of nodes, connect inputs and outputs, and save them to run via API calls, webhooks, or the UI. The Hurozo CLI helps you:

- Scaffold runnable Python projects for your saved agents
- List available agents in your account
- Run agents programmatically using Python

The CLI is designed for quick prototyping and integration into scripts or services.

## Features

- Scaffold a minimal Python project with `main.py` for selected agents
- Instantiate agents by name (existing definitions are fetched automatically)
- Prefill input keys in the scaffolded script (when the agent defines required inputs)
- Lightweight `Agent` class for invoking agents via the Hurozo API
- Compose agents programmatically via the `Node` builder and run/save them with `Agent`

## Installation

Install from PyPI:

```
pip install hurozo
```

This will provide the `hurozo` console command and the `hurozo` Python package.

## Authentication

The CLI and the `Agent` class use a bearer token to access your Hurozo account.

- `HUROZO_API_TOKEN`: required. A user or org API token.

Example:

```
export HUROZO_API_TOKEN=...your token...
```

## Commands

- `hurozo init [dirname]`
  - Interactively select one or more agents from your account
  - Scaffolds a minimal project in `dirname` (creates `requirements.txt` and `main.py`)
  - `main.py` instantiates each selected agent by display name and pre-fills `.input({...})` if inputs are defined
  - When run, `main.py` will execute all selected agents and print their results

- `hurozo list`
  - Lists accessible agents with their display names and UUIDs
- `hurozo nodes list`
  - Prints the node catalog stored in `.hurozo/nodes.json`
- `hurozo nodes refresh`
  - Fetches the latest node catalog from the backend into `.hurozo/nodes.json` (requires `HUROZO_API_TOKEN`)

- `hurozo help [command]`
  - Shows help for a specific command

## Python API

The packaged Python module exposes helpers for both running existing agents and
for composing new graphs locally.

```
from hurozo import Agent

# Loads the remote agent (or creates an empty placeholder if it does not exist yet)
agent = Agent("My Remote Agent")

# Run the agent on Hurozo using the current input payload
agent.input({"naam": "De Hengst"})
print(agent.run())

# Inspect or update the agent's saved JSON graph
print(agent.to_agent_graph())

# Environment variables mirror the "Env" tab in the UI
agent.set_env("OPENAI_MODEL", "gpt-4o-mini")
print(agent.list_env())
```

If you already know the agent UUID you can pass `Agent("uuid-value", True)` to
skip the name lookup. When the provided identifier is not found the SDK creates
a new remote agent with an empty graph so subsequent operations behave
consistently.

### Building local graphs with `Node`

```
from hurozo import Agent, Node

inputs = Node("Basic/Input/TextArea").set_property("text", "Hello")
separator = Node("Basic/Input/TextArea").set_property("text", ", ")
name = Node("Basic/Input/TextArea").set_property("text", "world")

concat = Node("Text/String/ConcatStrings")
concat(inputs, name, separator=separator)

agent = Agent("CLI Demo")
agent.addNodes(concat)
result = agent.run()  # Executes locally while nodes are staged
agent.save("CLI Demo")  # Persists the graph via /api/agents
```

`Node` instances load their input/output definitions from `.hurozo/nodes.json`
and automatically wrap literal inputs with the appropriate constant nodes.
`Agent(name)` loads the remote definition if it already exists; otherwise it
creates an empty remote placeholder. When you call `addNodes(...)` the SDK keeps
the staged graph locally—`run()` executes it immediately, and `save()` replaces
the remote graph with the current staged version.

### Managing environment variables

Remote agents support lightweight environment variables that are hydrated at
execution time (the same values you configure in the web UI under **Env**).
The SDK exposes helpers for reading and mutating them:

```
from hurozo import Agent

agent = Agent("My Remote Agent")

agent.set_env("OPENAI_MODEL", "gpt-4o-mini")
print(agent.get_env("OPENAI_MODEL"))

for name, value in agent.list_env().items():
    print(name, value)

agent.delete_env("OPENAI_MODEL")
```

These methods require `HUROZO_API_TOKEN` and always target the remote agent.
If the agent does not exist yet, the SDK creates an empty placeholder so the
environment helpers operate consistently.

## Scaffolded Project Layout

When you run `hurozo init my-agent`, the CLI generates:

- `requirements.txt` – dependencies: `hurozo`, `python-dotenv`, `requests`
- `main.py` – a runnable script that:
  - imports `Agent` from `hurozo`
  - defines one variable per selected agent using its display name
  - fills in `.input({...})` from the agent’s defined input keys (if available)
  - calls `.run()` for each agent and prints the results
- `.env` (optional) – if not present, a template is created with a `HUROZO_API_TOKEN` placeholder

Run it with:

```
cd my-agent
pip install -r requirements.txt
export HUROZO_API_TOKEN=...your token... (or set it in .env)
python main.py
```

## Environment Variables

- `HUROZO_API_TOKEN` – required for both listing agents and executing them
- `HUROZO_TOKEN` – optional alias read by the `RemoteAgent` helper (falls back to `HUROZO_API_TOKEN`)
- `HUROZO_API_URL` / `HUROZO_SERVER_URI` – override the default backend host (`https://hurozo.com`)
- `HUROZO_NODES_FILE` – override the location of `.hurozo/nodes.json` when loading node definitions programmatically
- `HUROZO_DEBUG` – set to `1` to emit verbose RemoteAgent logs (registration attempts, Firebase token minting, Firestore events, etc.)
- `NO_COLOR` – if set, disables colored output in the CLI

## Remote Agents

The packaged `RemoteAgent` helper now mirrors the Hurozo UI: it listens to Firestore
for pending requests and writes results/events back in real time, no polling loop required.

```
from hurozo import RemoteAgent

def hello(name):
    return {"greeting": f"Hello {name}"}

RemoteAgent(hello, {
    "inputs": ["name"],
    "outputs": ["greeting"]
})
```

Requirements:

- Set `HUROZO_API_TOKEN` (or `HUROZO_TOKEN`) with a read/write API token.
- Optionally set `HUROZO_API_URL` if you are targeting a self-hosted deployment.

The helper:

1. Registers the remote agent metadata with `/api/remote_agents/register` (keeps it fresh).
2. Calls `/api/firebase_token` with your API token and exchanges the custom token for Firebase credentials.
3. Opens a Firestore gRPC watch on `users/<uid>/remote_requests` scoped to your agent.
4. Invokes your handler, patches the Firestore document with status/outputs (or error details), and emits execution events for the UI.

When `HUROZO_DEBUG=1` is present, the helper prints each handshake step (registration, Firebase token mint, Firestore listen, request updates) so you can trace the realtime flow end‑to‑end.

## Designing agents
- Go to https://hurozo.com/ to design your agents visually. Save your agent, create an API token, and scaffold a project with `hurozo init`.

## Troubleshooting

- Missing token: ensure `HUROZO_API_TOKEN` is set in your shell or `.env`
- Name resolution fails: the CLI falls back to using the provided string; switch to UUID-based invocation by passing `True` as the second `Agent` argument
- Inputs missing at runtime: open the agent in the Hurozo UI and ensure inputs are defined; re-run `hurozo init` to regenerate a script with updated keys
