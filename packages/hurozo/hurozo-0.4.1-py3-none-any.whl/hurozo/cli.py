import argparse
import importlib.resources as resources
import json
import os
import re
import sys
from pathlib import Path

import requests
from importlib.metadata import PackageNotFoundError, version as pkg_version


NODES_RELATIVE_PATH = Path(".hurozo") / "nodes.json"


def _to_snake(name: str) -> str:
    """Convert a name to snake_case suitable for env vars."""
    name = re.sub(r"[^0-9a-zA-Z]+", "_", name)
    name = re.sub(r"(?<!^)(?=[A-Z])", "_", name)
    return name.strip("_").lower()


def _server_base_uri() -> str:
    """Return the configured Hurozo server base URI without trailing slash."""
    return os.environ.get("HUROZO_SERVER_URI", "https://hurozo.com").rstrip("/")


def _fetch_nodes_manifest() -> dict | None:
    """Fetch the node manifest from the backend.

    Returns the parsed JSON payload or ``None`` on failure.
    """
    base_uri = _server_base_uri()
    url = f"{base_uri}/nodes_defs"
    headers = {}
    token = os.environ.get("HUROZO_API_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        resp = requests.get(url, headers=headers, timeout=120)
        if not resp.ok:
            auth_hint = " (set HUROZO_API_TOKEN)" if resp.status_code == 401 and not token else ""
            _eprint(_red(f"Failed to fetch nodes from {url}: {resp.status_code}{auth_hint}"))
            return None
        payload = resp.json()
        if not isinstance(payload, dict):
            _eprint(_red("Unexpected response when fetching node manifest."))
            return None
        return payload
    except Exception as exc:
        _eprint(_red(f"Fetching node manifest failed: {exc}"))
        return None


def _load_packaged_nodes_manifest() -> dict | None:
    """Load the bundled node manifest shipped with the CLI."""
    try:
        data_path = resources.files("hurozo") / "data" / "nodes.json"
        with data_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
            if isinstance(payload, dict):
                return payload
    except FileNotFoundError:
        pass
    except Exception as exc:
        _eprint(_yellow(f"Bundled node manifest could not be read: {exc}"))
    return None


def _write_nodes_manifest(target_dir: Path, manifest: dict) -> Path | None:
    """Persist the node manifest under ``target_dir/.hurozo/nodes.json``."""
    try:
        manifest_dir = target_dir / ".hurozo"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / "nodes.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
        return manifest_path
    except Exception as exc:
        _eprint(_red(f"Unable to write node manifest: {exc}"))
        return None


def _find_nodes_manifest(start: Path | None = None) -> Path | None:
    """Search upwards from ``start`` for ``.hurozo/nodes.json``."""
    current = (start or Path.cwd()).resolve()
    for parent in [current, *current.parents]:
        candidate = parent / NODES_RELATIVE_PATH
        if candidate.exists():
            return candidate
    return None


def fetch_agents() -> list[dict]:
    """Return a list of agents for the authenticated user."""
    token = os.environ.get("HUROZO_API_TOKEN")
    if not token:
        return []
    base_uri = os.environ.get("HUROZO_SERVER_URI", "https://hurozo.com").rstrip("/")
    try:
        resp = requests.get(
            f"{base_uri}/api/agents",
            headers={"Authorization": f"Bearer {token}"},
            timeout=120,
        )
        if resp.ok:
            data = resp.json() or {}
            return data.get("agents", [])
    except Exception:
        pass
    return []


def _fetch_agent_inputs(agent_id: str) -> list[str]:
    """Return a list of input keys for a saved agent id.

    Tries GET /api/agents/<agent_id> and extracts extra.inputs (or top-level inputs) keys.
    Returns an empty list on any error or if none are defined.
    """
    token = os.environ.get("HUROZO_API_TOKEN")
    if not token:
        return []
    base_uri = os.environ.get("HUROZO_SERVER_URI", "https://hurozo.com").rstrip("/")
    try:
        resp = requests.get(
            f"{base_uri}/api/agents/{agent_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=120,
        )
        if not resp.ok:
            return []
        data = resp.json() or {}
        agent = data.get("agent") or {}
        inputs = (agent.get("extra", {}) or {}).get("inputs") or agent.get("inputs") or []
        keys: list[str] = []
        for inp in inputs:
            key = inp.get("key") or inp.get("name")
            if key and key not in keys:
                keys.append(str(key))
        return keys
    except Exception:
        return []


def init_agent(dirname: str, agents: list[dict] | None = None) -> None:
    """Scaffold a minimal agent project.

    - Creates requirements.txt and main.py
    - If agents are provided (from the API selection), it will:
      - Instantiate each by display name using hurozo.Agent (name->uuid resolver is built-in)
      - Prefill input keys by querying /api/agents/<id>
      - Call .run() for every instantiated agent
    """
    target = Path(dirname)
    target.mkdir(parents=True, exist_ok=True)

    (target / "requirements.txt").write_text(
        "hurozo\npython-dotenv\nrequests\n"
    )

    # Prepare main.py contents
    agent_blocks: list[str] = []
    inputs_blocks: list[str] = []
    run_blocks: list[str] = []
    if agents:
        for ag in agents:
            display_name = ag.get("name", "agent")
            agent_var = _to_snake(display_name) or "agent"
            name_literal = json.dumps(display_name)
            agent_blocks.append(f"{agent_var} = Agent({name_literal})")
            # discover inputs
            ag_id = ag.get("id") or ""
            input_keys = _fetch_agent_inputs(ag_id) if ag_id else []
            if input_keys:
                # Create a readable example mapping
                pairs = ",\n        ".join([f"\"{k}\": \"Some input {i+1}\"" for i, k in enumerate(input_keys)])
                inputs_blocks.append(f"    {agent_var}.input({{\n        {pairs}\n    }})")
            else:
                inputs_blocks.append(f"    {agent_var}.input({{}})")
            run_blocks.append(
                f"    result = {agent_var}.run()\n"
                f"    print(result)\n"
                f"    # {agent_var}.save({name_literal})  # Persist graph changes back to Hurozo"
            )
    else:
        default_prompt = json.dumps("Hello from the Hurozo CLI!")
        agent_blocks.append("agent = Agent('HurozoChat')  # loads existing agent or creates a new one")
        inputs_blocks.append(
            "    agent.input({\n"
            "        \"prompt\": " + default_prompt + "\n"
            "    })"
        )
        run_blocks.append(
            "    result = agent.run()\n"
            "    print(result)\n"
            "    # agent.save('HurozoChat')  # Persist updates back to Hurozo once ready"
        )

    agent_init_block = "\n".join(agent_blocks)
    inputs_block_joined = "\n".join(inputs_blocks)
    runs_block_joined = "\n\n".join(run_blocks)
    node_stub = (
        "#def my_remote_agent(name):\n"
        "#    outputs = {\n"
        "#        'greeting': f'Gwuaaak {name}',\n"
        "#        'shout': f'GWUAAAAK {name.upper()}'\n"
        "#    }\n"
        "#    return outputs\n"
    )

    script = f"""from dotenv import load_dotenv
import hurozo

load_dotenv()  # Load environment variables from .env if present
hurozo.enable_sugar(globals())  # Populate Agent, Node, and node shortcuts

{agent_init_block}

{node_stub}
# Example: build a new agent graph programmatically using node shortcuts.
#clean_title = text_processing_cleanstring("  Launch plan draft   \\n\\n")
#clean_summary = text_processing_cleanstring("Outline   goals, timeline, and owners.")
#concat = text_string_concatstrings(separator=" ")
#concat(clean_title, clean_summary)
#assembled_agent = Agent("launch-plan-draft")
#assembled_agent.addNodes(concat)
#assembled_agent.run()  # Execute locally before saving
#assembled_agent.save("Launch Plan Draft")  # Persist the agent graph to Hurozo


def main():
{inputs_block_joined}
{runs_block_joined}
    ## Example of how you could run a remote agent. Implementation is in the my_remote_agent() method above.
    #RemoteAgent(my_remote_agent, {{
    #    'inputs': ['name'],
    #    'outputs': ['greeting', 'shout']
    #}})


if __name__ == '__main__':
    main()
"""
    (target / "main.py").write_text(script)

    # Create an .env with a token placeholder (do not overwrite if present)
    env_path = target / ".env"
    if not env_path.exists():
        env_path.write_text(
            '# set HUROZO_API_TOKEN=""\n# set HUROZO_TOKEN=""\n# set HUROZO_API_URL="https://hurozo.com"\n'
        )

    manifest = _fetch_nodes_manifest()
    manifest_source = "remote" if manifest else None
    if not manifest:
        manifest = _load_packaged_nodes_manifest()
        if manifest:
            manifest_source = "bundled"

    if manifest:
        manifest_path = _write_nodes_manifest(target, manifest)
        if manifest_path:
            node_count = len(manifest.get("nodes", []))
            if manifest_source == "remote":
                print(_green(f"Fetched {node_count} nodes -> {manifest_path}"))
            else:
                print(_green(f"Copied bundled node manifest ({node_count} nodes) -> {manifest_path}"))
    else:
        _eprint(_yellow("Unable to locate a node manifest; run 'hurozo nodes refresh' when ready."))

    print(_green(f"Initialized project in {target}"))


def _read_key() -> str:
    """Read a single keypress from stdin (raw), cross-platform best-effort.

    - Normal keys return a one-character string.
    - Arrow keys and similar return a full escape sequence like "\x1b[A".
    """
    try:
        import msvcrt  # type: ignore

        ch = msvcrt.getwch()
        # Normalize Windows special keys to ANSI-like sequences the UI understands
        if ch in ("\x00", "\xe0"):
            second = msvcrt.getwch()
            mapping = {
                "H": "\x1b[A",  # Up
                "P": "\x1b[B",  # Down
                "M": "\x1b[C",  # Right
                "K": "\x1b[D",  # Left
            }
            seq = mapping.get(second, ch + second)
            return seq
        return ch
    except ImportError:
        import termios
        import tty
        import select
        import time
        import os as _os

        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            b = _os.read(fd, 1)
            if not b:
                return ""
            first = b.decode("utf-8", errors="ignore")
            if first != "\x1b":
                return first
            # Read the remainder of an escape sequence with a slightly longer window
            seq_b = [b"\x1b"]
            deadline = time.time() + 0.25  # up to 250ms to collect the sequence
            while time.time() < deadline:
                r, _, _ = select.select([fd], [], [], 0.03)
                if not r:
                    break
                nb = _os.read(fd, 1)
                if not nb:
                    break
                seq_b.append(nb)
                nxt = nb.decode("utf-8", errors="ignore")
                # Stop if we detect a typical CSI/SS3 final byte (ASCII @ to ~)
                if len(seq_b) >= 2:
                    if seq_b[1] in (b"[", b"O") and ("@" <= nxt <= "~"):
                        break
                if len(seq_b) >= 8:
                    break
            seq = b"".join(seq_b).decode("utf-8", errors="ignore")
            return seq
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _enable_windows_ansi() -> None:
    """Enable ANSI escape sequence processing on Windows terminals, if possible."""
    if os.name != "nt":
        return
    try:
        import ctypes  # type: ignore

        kernel32 = ctypes.windll.kernel32
        # STD_OUTPUT_HANDLE = -11
        handle = kernel32.GetStdHandle(ctypes.c_int(-11))
        mode = ctypes.c_uint()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            new_mode = mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING
            kernel32.SetConsoleMode(handle, ctypes.c_uint(new_mode))
    except Exception:
        # Best-effort only; silently continue if enabling fails
        pass


def _fancy_input(prompt_title: str = "Create a new agent", placeholder: str = "my-agent") -> str:
    """Render a lightweight ASCII input UI and return the entered name.

    Falls back to builtin input() if not attached to a TTY.
    """
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        # Non-interactive environment
        return input(f"{prompt_title}\nProject directory name: ")

    # Ensure Windows consoles understand ANSI sequences
    _enable_windows_ansi()

    # Simple ASCII UI with a block cursor inside brackets
    title = _bold(_cyan(prompt_title)) if _color_enabled() else prompt_title
    instructions = "Type a project directory name and press Enter."
    field_width = 34
    value = ""
    cursor = "█" if _color_enabled() else "#"

    # Hide the terminal cursor
    sys.stdout.write("\x1b[?25l")
    try:
        print(title)
        print(instructions)
        print("")
        while True:
            # Sanitize display text to keep within field width
            shown = value[-field_width:]
            pad = max(0, field_width - len(shown))
            line = f"[{shown}{cursor}{' ' * pad}]"
            sys.stdout.write("\r" + line)
            sys.stdout.flush()

            ch = _read_key()
            # Enter
            if ch in ("\r", "\n"):
                if value.strip():
                    sys.stdout.write("\r" + " " * (len(line)) + "\r")
                    print(f"[{value}]")
                    return value.strip()
                else:
                    # If empty, seed with placeholder
                    value = placeholder
                    continue
            # Ctrl+C
            if ch == "\x03":
                raise KeyboardInterrupt
            # Backspace (Unix "\x7f" or Windows "\x08")
            if ch in ("\x7f", "\b"):
                value = value[:-1]
                continue
            # Ignore escape sequences (arrows, etc.)
            if ch.startswith("\x1b"):
                # ignore any ANSI sequence (arrows, Home/End, etc.)
                continue
            # Basic filtering: allow letters, digits, '-', '_', and spaces (later trimmed)
            if re.match(r"[0-9A-Za-z_\- ]", ch):
                # Soft limit overall length to 64
                if len(value) < 64:
                    value += ch
            # Otherwise ignore
    finally:
        # Restore terminal cursor
        sys.stdout.write("\x1b[?25h")
        sys.stdout.flush()


def _fancy_select(options: list[str], title: str = "Select agents") -> list[int]:
    """Interactive multi-select (requires TTY) using InquirerPy."""
    if not options:
        return []
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        raise RuntimeError("Interactive TTY required for selection; run in a terminal.")

    from InquirerPy import inquirer  # type: ignore

    result = inquirer.checkbox(
        message=title,
        choices=[{"name": opt, "value": i} for i, opt in enumerate(options)],
        instruction="Space to toggle, Enter to confirm.",
        transformer=lambda res: f"{len(res)} selected",
    ).execute()
    return list(result) if isinstance(result, list) else []

    # Ensure Windows consoles understand ANSI sequences
    _enable_windows_ansi()

    selected = [False] * len(options)
    idx = 0
    sys.stdout.write("\x1b[?25l")
    try:
        print(_bold(_cyan(title)) if _color_enabled() else title)
        while True:
            for i, opt in enumerate(options):
                mark = "[x]" if selected[i] else "[ ]"
                line = f"{mark} {opt}"
                if i == idx:
                    line = "> " + line
                    if _color_enabled():
                        line = _cyan(line)
                else:
                    line = "  " + line
                print(line)
            ch = _read_key()
            if ch in ("\r", "\n"):
                break
            if ch == " ":
                selected[idx] = not selected[idx]
            # Support vim-style navigation as a fallback
            elif ch.lower() == "k":
                idx = (idx - 1) % len(options)
            elif ch.lower() == "j":
                idx = (idx + 1) % len(options)
            # Common ANSI sequences for arrows
            # Up: normal CSI and SS3 variants
            elif ch in ("\x1b[A", "\x1bOA"):
                idx = (idx - 1) % len(options)
            # Down: normal CSI and SS3 variants
            elif ch in ("\x1b[B", "\x1bOB"):
                idx = (idx + 1) % len(options)
            # Be tolerant of longer CSI forms like "\x1b[1;5A"
            elif ch.startswith("\x1b") and ch.endswith("A"):
                idx = (idx - 1) % len(options)
            elif ch.startswith("\x1b") and ch.endswith("B"):
                idx = (idx + 1) % len(options)
            # move cursor up to redraw
            print(f"\x1b[{len(options)}A", end="")
            sys.stdout.flush()
        print("\x1b[J", end="")
        return [i for i, s in enumerate(selected) if s]
    finally:
        sys.stdout.write("\x1b[?25h")
        sys.stdout.flush()


def deploy_agent() -> None:
    _eprint(_red("The 'deploy' command has been removed. Agents run via the API; no deployment is required."))
    raise SystemExit(2)


def list_agents_cmd() -> None:
    agents = fetch_agents()
    if not agents:
        print("No agents found.")
        return
    for ag in agents:
        status = "published" if ag.get("published") else "draft"
        print(f"{ag.get('name')} ({ag.get('agent_uuid')}) - {status}")


def _load_nodes_manifest(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text())
    except Exception as exc:
        _eprint(_red(f"Failed to read node manifest at {path}: {exc}"))
        return None
    if not isinstance(data, dict):
        _eprint(_red(f"Unexpected node manifest structure at {path}"))
        return None
    return data


def nodes_list_cmd() -> None:
    manifest_path = _find_nodes_manifest()
    if not manifest_path:
        _eprint(_red("Could not find .hurozo/nodes.json. Run 'hurozo init' first."))
        return
    manifest = _load_nodes_manifest(manifest_path)
    if not manifest:
        return
    nodes = manifest.get("nodes") or []
    if not nodes:
        print("No nodes defined in manifest.")
        return
    def _sort_key(entry):
        category = entry.get("category") or ""
        name = entry.get("name") or ""
        return (category, name)

    sorted_nodes = sorted(nodes, key=_sort_key)
    print(_green(f"Found {len(sorted_nodes)} nodes:"))
    for node in sorted_nodes:
        category = node.get("category") or ""
        name = node.get("name") or ""
        display = node.get("display_name") or name
        full = f"{category}/{name}" if category else name
        print(f"- {full} — {display}")


def nodes_refresh_cmd() -> None:
    manifest_path = _find_nodes_manifest()
    if not manifest_path:
        _eprint(_red("No .hurozo/nodes.json found. Run 'hurozo init' first."))
        return
    project_root = manifest_path.parent.parent
    manifest = _fetch_nodes_manifest()
    if not manifest:
        return
    if _write_nodes_manifest(project_root, manifest):
        print(_green(f"Updated node manifest with {len(manifest.get('nodes', []))} entries."))


## undeploy removed (no-op)


# ---- Coloring helpers -----------------------------------------------------

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"


def _color_enabled() -> bool:
    # Respect NO_COLOR and only color when attached to a TTY
    return os.environ.get("NO_COLOR") is None and sys.stdout.isatty()


def _style(txt: str, code: str) -> str:
    if _color_enabled():
        return f"{code}{txt}{RESET}"
    return txt


def _green(txt: str) -> str:
    return _style(txt, GREEN)


def _red(txt: str) -> str:
    return _style(txt, RED)


def _bold(txt: str) -> str:
    return _style(txt, BOLD)


def _cyan(txt: str) -> str:
    return _style(txt, CYAN)


def _yellow(txt: str) -> str:
    return _style(txt, YELLOW)


def _eprint(txt: str) -> None:
    stream = sys.stderr
    if os.environ.get("NO_COLOR") is None and stream.isatty():
        print(txt, file=stream)
    else:
        # Strip ANSI if stderr is not a TTY
        print(re.sub(r"\x1b\[[0-9;]*m", "", txt), file=stream)


def _package_version() -> str:
    """Return the installed package version or a sensible fallback."""
    try:
        # Project package name per pyproject
        return pkg_version("hurozo")
    except PackageNotFoundError:
        # Fallback to the version declared in pyproject in dev checkouts
        return "0.1.0"


def _make_examples_block() -> str:
    return (
        f"{_bold('Examples:')}\n"
        "  # Create a new agent project in ./my-agent\n"
        "  hurozo init my-agent\n\n"
        f"  # List available agents (requires {_yellow('HUROZO_API_TOKEN')})\n"
        "  hurozo list\n\n"
        "  # Show nodes recorded in .hurozo/nodes.json\n"
        "  hurozo nodes list\n\n"
        f"  # Run locally via API (requires {_yellow('HUROZO_API_TOKEN')})\n"
        "  cd my-agent && export HUROZO_API_TOKEN=... && python main.py\n"
    )


def _show_help(topic_parts, parser, init_top, list_top, nodes_top, nodes_list_parser, nodes_refresh_parser) -> None:
    # No topic -> top-level help
    if not topic_parts:
        parser.print_help()
        return
    # One part
    if len(topic_parts) == 1:
        if topic_parts[0] == "init":
            init_top.print_help()
            return
        if topic_parts[0] == "list":
            list_top.print_help()
            return
        if topic_parts[0] == "nodes":
            nodes_top.print_help()
            return
    if len(topic_parts) == 2 and topic_parts[0] == "nodes":
        if topic_parts[1] == "list":
            nodes_list_parser.print_help()
            return
        if topic_parts[1] == "refresh":
            nodes_refresh_parser.print_help()
            return
        
    # Fallback
    _eprint(_red("Unknown help topic. Try 'hurozo --help' or 'hurozo help init'."))
    raise SystemExit(2)


def main() -> None:
    description = (
        _cyan("Hurozo CLI — tools to scaffold and execute agent projects.")
        + "\n\nUse 'init' and 'list' commands."
    )
    epilog = _make_examples_block()

    parser = argparse.ArgumentParser(
        prog="hurozo",
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"hurozo { _package_version() }",
        help="Show the hurozo version and exit.",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="<command>")

    # Shared descriptions for top-level commands
    init_desc = (
        _cyan("Create a minimal agent project at the given directory.")
        + "\n\nGenerates:\n"
        + "  - requirements.txt (with hurozo)\n"
        + "  - main.py (example runner)\n"
    )

    # Wire up command handlers
    def _handle_init(a):
        dirname = a.dirname
        if not dirname:
            try:
                dirname = _fancy_input()
            except KeyboardInterrupt:
                _eprint(_red("Initialization canceled."))
                raise SystemExit(130)
        agents = fetch_agents()
        selected = []
        if agents:
            idxs = _fancy_select([ag.get("name", "") for ag in agents], "Select agents")
            selected = [agents[i] for i in idxs]
        init_agent(dirname, selected if selected else None)

    # Top-level commands
    init_top = subparsers.add_parser(
        "init",
        help="Scaffold a new agent project.",
        description=init_desc,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    init_top.add_argument(
        "dirname",
        nargs="?",
        help="Target directory for the new project. If omitted, an interactive prompt appears.",
    )
    init_top.set_defaults(func=_handle_init)

    list_top = subparsers.add_parser(
        "list",
        help="List agents for the authenticated user.",
        description=None,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    list_top.set_defaults(func=lambda a: list_agents_cmd())

    nodes_top = subparsers.add_parser(
        "nodes",
        help="Manage the local node manifest.",
        description=(
            _cyan("Inspect or refresh the node manifest stored in .hurozo/nodes.json.")
            + "\n\nSubcommands:\n  list     Show nodes from the local manifest.\n  refresh  Fetch the latest manifest from the server."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    nodes_sub = nodes_top.add_subparsers(dest="nodes_command", metavar="<nodes-command>")
    nodes_list_parser = nodes_sub.add_parser(
        "list",
        help="List available nodes from the local manifest.",
        description=None,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    nodes_list_parser.set_defaults(func=lambda a: nodes_list_cmd())
    nodes_refresh_parser = nodes_sub.add_parser(
        "refresh",
        help="Refresh the node manifest from the server.",
        description=None,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    nodes_refresh_parser.set_defaults(func=lambda a: nodes_refresh_cmd())
    nodes_top.set_defaults(func=lambda a, p=nodes_top: p.print_help())

    # help alias: `hurozo help [topic]`
    help_parser = subparsers.add_parser(
        "help",
        help="Show help for a command.",
        description=(
            _cyan("Show detailed help for a given command.")
            + "\n\nExamples:\n"
            + "  hurozo help\n"
            + "  hurozo help init\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    help_parser.add_argument("topic", nargs="*", help="Command/topic to show help for.")
    help_parser.set_defaults(
        func=lambda a, p=parser, it=init_top, lt=list_top, nt=nodes_top,
        nl=nodes_list_parser, nr=nodes_refresh_parser: _show_help(a.topic, p, it, lt, nt, nl, nr)
    )

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
