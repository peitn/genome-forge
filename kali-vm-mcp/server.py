#!/usr/bin/env python3
"""
Kali Linux VM MCP Server
Controls a Kali Linux VirtualBox VM with virtual keyboard/mouse, ProtonVPN,
Gemini AI (screenshot analysis, chat) and HuggingFace integration.
API keys are loaded at startup via PHANTOM_AUTH_TOKEN from Cloudflare Worker.
"""

import asyncio
import base64
import os
import subprocess
from typing import Any

import requests
import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

# ---------------------------------------------------------------------------
# Startup: fetch all API keys via PHANTOM_AUTH_TOKEN
# ---------------------------------------------------------------------------
PHANTOM_SECRETS_URL = "https://phantom-secrets.alena-rejdova.workers.dev"
PHANTOM_AUTH_TOKEN = os.environ.get(
    "PHANTOM_AUTH_TOKEN",
    "pat_aec7a8cd8ee9453ffb1a1a47bcb62f81e4ead43fbadb3845eb885f74ee54f666",
)

_KEYS: dict[str, str] = {}


def load_keys() -> None:
    """Fetch all API keys from Cloudflare Worker at server startup."""
    global _KEYS
    try:
        r = requests.get(
            PHANTOM_SECRETS_URL,
            headers={"Authorization": f"Bearer {PHANTOM_AUTH_TOKEN}"},
            timeout=10,
        )
        r.raise_for_status()
        _KEYS = r.json()
    except Exception as e:
        print(f"[WARN] Could not load PHANTOM keys: {e}")


def key(name: str) -> str:
    if not _KEYS:
        load_keys()
    return _KEYS.get(name, "")


# ---------------------------------------------------------------------------
# VirtualBox helpers
# ---------------------------------------------------------------------------
VM_NAME = "KaliLinux"
VM_USER = "kali"
VM_PASS = "kali"
VM_ROOT_PASS = "kali"


def run_cmd(cmd: list[str], timeout: int = 60) -> tuple[int, str, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Timed out after {timeout}s"
    except FileNotFoundError as e:
        return -1, "", f"Not found: {e}"
    except Exception as e:
        return -1, "", str(e)


def vbox(*args: str, timeout: int = 60) -> tuple[int, str, str]:
    return run_cmd(["VBoxManage"] + list(args), timeout=timeout)


def vm_run(command: str, user: str = VM_USER, password: str = VM_PASS, timeout: int = 60) -> tuple[int, str, str]:
    return vbox(
        "guestcontrol", VM_NAME, "run",
        "--exe", "/bin/bash",
        "--username", user,
        "--password", password,
        "--wait-stdout", "--wait-stderr",
        "--", "-c", command,
        timeout=timeout,
    )


def ok(text: str) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=text)]


# ---------------------------------------------------------------------------
# Keyboard scan-code map
# ---------------------------------------------------------------------------
KEY_SCANCODES: dict[str, list[str]] = {
    "Return":        ["0x1c", "0x9c"],
    "Enter":         ["0x1c", "0x9c"],
    "Escape":        ["0x01", "0x81"],
    "Tab":           ["0x0f", "0x8f"],
    "Space":         ["0x39", "0xb9"],
    "BackSpace":     ["0x0e", "0x8e"],
    "Delete":        ["0xe0", "0x53", "0xe0", "0xd3"],
    "Up":            ["0xe0", "0x48", "0xe0", "0xc8"],
    "Down":          ["0xe0", "0x50", "0xe0", "0xd0"],
    "Left":          ["0xe0", "0x4b", "0xe0", "0xcb"],
    "Right":         ["0xe0", "0x4d", "0xe0", "0xcd"],
    "Home":          ["0xe0", "0x47", "0xe0", "0xc7"],
    "End":           ["0xe0", "0x4f", "0xe0", "0xcf"],
    "PageUp":        ["0xe0", "0x49", "0xe0", "0xc9"],
    "PageDown":      ["0xe0", "0x51", "0xe0", "0xd1"],
    "F1":            ["0x3b", "0xbb"],
    "F2":            ["0x3c", "0xbc"],
    "F3":            ["0x3d", "0xbd"],
    "F4":            ["0x3e", "0xbe"],
    "F5":            ["0x3f", "0xbf"],
    "F12":           ["0x58", "0xd8"],
    "ctrl-c":        ["0x1d", "0x2e", "0xae", "0x9d"],
    "ctrl-v":        ["0x1d", "0x2f", "0xaf", "0x9d"],
    "ctrl-z":        ["0x1d", "0x2c", "0xac", "0x9d"],
    "ctrl-x":        ["0x1d", "0x2d", "0xad", "0x9d"],
    "ctrl-a":        ["0x1d", "0x1e", "0x9e", "0x9d"],
    "ctrl-s":        ["0x1d", "0x1f", "0x9f", "0x9d"],
    "ctrl-l":        ["0x1d", "0x26", "0xa6", "0x9d"],
    "ctrl-alt-t":    ["0x1d", "0x38", "0x14", "0x94", "0xb8", "0x9d"],
    "ctrl-alt-del":  ["0x1d", "0x38", "0xe0", "0x53", "0xe0", "0xd3", "0xb8", "0x9d"],
    "alt-F4":        ["0x38", "0x3e", "0xbe", "0xb8"],
    "alt-tab":       ["0x38", "0x0f", "0x8f", "0xb8"],
    "super":         ["0xe0", "0x5b", "0xe0", "0xdb"],
}


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------
server = Server("kali-vm-mcp")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        # ── VM management ──────────────────────────────────────────────────
        types.Tool(
            name="vm_start",
            description="Start the Kali Linux VirtualBox VM.",
            inputSchema={
                "type": "object",
                "properties": {
                    "headless": {"type": "boolean", "default": True,
                                 "description": "Headless (no GUI window)"}
                },
                "required": [],
            },
        ),
        types.Tool(
            name="vm_stop",
            description="Stop the Kali Linux VM.",
            inputSchema={
                "type": "object",
                "properties": {
                    "force": {"type": "boolean", "default": False,
                              "description": "Force power-off"}
                },
                "required": [],
            },
        ),
        types.Tool(
            name="vm_status",
            description="Get current state and info of the Kali VM.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="vm_run_command",
            description="Run a shell command inside the Kali VM (requires Guest Additions).",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                    "as_root": {"type": "boolean", "default": False},
                    "timeout": {"type": "integer", "default": 60},
                },
                "required": ["command"],
            },
        ),
        types.Tool(
            name="vm_screenshot",
            description="Take a PNG screenshot of the VM screen.",
            inputSchema={
                "type": "object",
                "properties": {
                    "output_path": {"type": "string", "default": "/tmp/kali_screen.png"}
                },
                "required": [],
            },
        ),
        types.Tool(
            name="vm_snapshot_create",
            description="Create a VM snapshot.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="vm_snapshot_restore",
            description="Restore the VM to a snapshot.",
            inputSchema={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        ),
        types.Tool(
            name="vm_list_snapshots",
            description="List all VM snapshots.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        # ── Virtual keyboard ───────────────────────────────────────────────
        types.Tool(
            name="keyboard_type",
            description="Type text into the VM.",
            inputSchema={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        ),
        types.Tool(
            name="keyboard_key",
            description=(
                "Press a named key/shortcut. Supported: Return, Escape, Tab, Space, "
                "BackSpace, Delete, Up/Down/Left/Right, Home, End, PageUp, PageDown, "
                "F1-F5, F12, ctrl-c/v/z/x/a/s/l, ctrl-alt-t, ctrl-alt-del, "
                "alt-F4, alt-tab, super."
            ),
            inputSchema={
                "type": "object",
                "properties": {"key": {"type": "string"}},
                "required": ["key"],
            },
        ),
        # ── Virtual mouse ──────────────────────────────────────────────────
        types.Tool(
            name="mouse_move",
            description="Move the cursor to absolute coordinates on the VM screen.",
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                },
                "required": ["x", "y"],
            },
        ),
        types.Tool(
            name="mouse_click",
            description="Click at coordinates in the VM.",
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                    "button": {"type": "string", "enum": ["left", "right", "middle"], "default": "left"},
                    "double": {"type": "boolean", "default": False},
                },
                "required": ["x", "y"],
            },
        ),
        types.Tool(
            name="mouse_scroll",
            description="Scroll the mouse wheel in the VM.",
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                    "direction": {"type": "string", "enum": ["up", "down"]},
                    "amount": {"type": "integer", "default": 3},
                },
                "required": ["x", "y", "direction"],
            },
        ),
        # ── ProtonVPN ──────────────────────────────────────────────────────────
        types.Tool(
            name="vpn_install",
            description="Install ProtonVPN CLI inside the Kali VM.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="vpn_login",
            description="Log in to ProtonVPN inside the VM.",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {"type": "string"},
                    "password": {"type": "string"},
                },
                "required": ["username", "password"],
            },
        ),
        types.Tool(
            name="vpn_connect",
            description="Connect to ProtonVPN (leave server empty for fastest).",
            inputSchema={
                "type": "object",
                "properties": {
                    "server": {"type": "string", "default": "",
                               "description": "e.g. 'CZ', 'US', 'NL#5'"}
                },
                "required": [],
            },
        ),
        types.Tool(
            name="vpn_disconnect",
            description="Disconnect ProtonVPN inside the VM.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="vpn_status",
            description="ProtonVPN connection status inside the VM.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        # ── Gemini AI ─────────────────────────────────────────────────────────
        types.Tool(
            name="ai_analyze_screen",
            description=(
                "Take a screenshot of the VM, send it to Gemini Vision and get an AI description "
                "of what is currently displayed on screen."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "default": "What do you see on this screen? Describe the current state of the VM.",
                        "description": "What to ask Gemini about the screenshot",
                    }
                },
                "required": [],
            },
        ),
        types.Tool(
            name="ai_chat",
            description="Send a message to Gemini AI and get a response (no screenshot).",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Message to send to Gemini"},
                    "model": {
                        "type": "string",
                        "default": "gemini-2.0-flash",
                        "description": "Gemini model to use",
                    },
                },
                "required": ["message"],
            },
        ),
        types.Tool(
            name="ai_suggest_next_command",
            description=(
                "Take a screenshot, analyse the VM screen with Gemini, "
                "and suggest the best next shell command to run."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "goal": {"type": "string", "description": "What you are trying to accomplish"}
                },
                "required": ["goal"],
            },
        ),
        # ── HuggingFace ────────────────────────────────────────────────────────
        types.Tool(
            name="hf_inference",
            description="Run inference on a HuggingFace model via the Inference API.",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {"type": "string", "description": "e.g. 'meta-llama/Llama-3-8b-instruct'"},
                    "inputs": {"type": "string", "description": "Input text / prompt"},
                    "task": {
                        "type": "string",
                        "enum": ["text-generation", "text-classification", "summarization", "translation"],
                        "default": "text-generation",
                    },
                },
                "required": ["model", "inputs"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:

    # ── VM management ──────────────────────────────────────────────────
    if name == "vm_start":
        mode = "headless" if arguments.get("headless", True) else "gui"
        rc, out, err = vbox("startvm", VM_NAME, "--type", mode)
        return ok(f"VM started ({mode})." if rc == 0 else f"Error: {err or out}")

    if name == "vm_stop":
        action = "poweroff" if arguments.get("force", False) else "acpipowerbutton"
        rc, out, err = vbox("controlvm", VM_NAME, action)
        return ok("VM stopped." if rc == 0 else f"Error: {err or out}")

    if name == "vm_status":
        rc, out, err = vbox("showvminfo", VM_NAME, "--machinereadable")
        if rc != 0:
            return ok(f"Error: {err}")
        data = {}
        for line in out.splitlines():
            if "=" in line:
                k, _, v = line.partition("=")
                data[k.strip()] = v.strip().strip('"')
        return ok(
            f"VM     : {VM_NAME}\n"
            f"State  : {data.get('VMState', '?')}\n"
            f"Memory : {data.get('memory', '?')} MB\n"
            f"VRAM   : {data.get('vram', '?')} MB\n"
            f"CPUs   : {data.get('cpus', '?')}"
        )

    if name == "vm_run_command":
        user = "root" if arguments.get("as_root") else VM_USER
        pwd = VM_ROOT_PASS if arguments.get("as_root") else VM_PASS
        rc, out, err = vm_run(arguments["command"], user=user, password=pwd,
                              timeout=arguments.get("timeout", 60))
        parts = [f"Exit: {rc}"]
        if out:
            parts.append(f"STDOUT:\n{out.rstrip()}")
        if err:
            parts.append(f"STDERR:\n{err.rstrip()}")
        return ok("\n".join(parts))

    if name == "vm_screenshot":
        path = arguments.get("output_path", "/tmp/kali_screen.png")
        rc, out, err = vbox("controlvm", VM_NAME, "screenshotpng", path)
        return ok(f"Screenshot saved to {path}" if rc == 0 else f"Error: {err or out}")

    if name == "vm_snapshot_create":
        cmd = ["snapshot", VM_NAME, "take", arguments["name"]]
        if arguments.get("description"):
            cmd += ["--description", arguments["description"]]
        rc, out, err = vbox(*cmd)
        return ok(f"Snapshot '{arguments['name']}' created." if rc == 0 else f"Error: {err or out}")

    if name == "vm_snapshot_restore":
        rc, out, err = vbox("snapshot", VM_NAME, "restore", arguments["name"])
        return ok(f"Restored to '{arguments['name']}'." if rc == 0 else f"Error: {err or out}")

    if name == "vm_list_snapshots":
        rc, out, err = vbox("snapshot", VM_NAME, "list")
        return ok(out.strip() or "No snapshots." if rc == 0 else f"Error: {err or out}")

    # ── Virtual keyboard ───────────────────────────────────────────────
    if name == "keyboard_type":
        text = arguments["text"]
        rc, out, err = vbox("controlvm", VM_NAME, "keyboardputstring", text)
        return ok(f"Typed {len(text)} chars." if rc == 0 else f"Error: {err or out}")

    if name == "keyboard_key":
        k = arguments["key"]
        codes = KEY_SCANCODES.get(k)
        if not codes:
            return ok(f"Unknown key '{k}'. Supported: {', '.join(sorted(KEY_SCANCODES))}")
        rc, out, err = vbox("controlvm", VM_NAME, "keyboardputscancode", *codes)
        return ok(f"Key: {k}" if rc == 0 else f"Error: {err or out}")

    # ── Virtual mouse ────────────────────────────────────────────────────
    if name == "mouse_move":
        x, y = arguments["x"], arguments["y"]
        rc, out, err = vbox("controlvm", VM_NAME, "mousemove", str(x), str(y))
        return ok(f"Mouse → ({x},{y})" if rc == 0 else f"Error: {err or out}")

    if name == "mouse_click":
        x, y = arguments["x"], arguments["y"]
        btn = {"left": "1", "right": "2", "middle": "4"}.get(arguments.get("button", "left"), "1")
        vbox("controlvm", VM_NAME, "mousemove", str(x), str(y))
        for _ in range(2 if arguments.get("double") else 1):
            vbox("controlvm", VM_NAME, "mousebuttonevent", btn)
            vbox("controlvm", VM_NAME, "mousebuttonevent", "0")
        label = "Double-click" if arguments.get("double") else "Click"
        return ok(f"{label} at ({x},{y}).")

    if name == "mouse_scroll":
        x, y = arguments["x"], arguments["y"]
        amount = arguments.get("amount", 3)
        wheel = str(-amount) if arguments["direction"] == "up" else str(amount)
        vbox("controlvm", VM_NAME, "mousemove", str(x), str(y))
        rc, out, err = vbox("controlvm", VM_NAME, "mousewheel", wheel)
        return ok(f"Scrolled {arguments['direction']} {amount}x." if rc == 0 else f"Error: {err or out}")

    # ── ProtonVPN ──────────────────────────────────────────────────────────
    if name == "vpn_install":
        script = (
            "set -e && "
            "wget -qO /tmp/protonvpn.deb "
            "https://repo.protonvpn.com/debian/dists/stable/main/binary-all/protonvpn-stable-release_1.0.3-2_all.deb && "
            "dpkg -i /tmp/protonvpn.deb && apt-get update -q && "
            "apt-get install -y proton-vpn-gnome-desktop protonvpn-cli"
        )
        rc, out, err = vm_run(script, user="root", password=VM_ROOT_PASS, timeout=300)
        return ok("ProtonVPN installed." if rc == 0 else f"Error:\n{out}\n{err}")

    if name == "vpn_login":
        cmd = f"echo {arguments['password']!r} | protonvpn-cli login {arguments['username']} --password-stdin"
        rc, out, err = vm_run(cmd, timeout=30)
        return ok("Logged in to ProtonVPN." if rc == 0 else f"Error:\n{out}\n{err}")

    if name == "vpn_connect":
        srv = arguments.get("server", "").strip()
        cmd = f"protonvpn-cli connect {srv}" if srv else "protonvpn-cli connect --fastest"
        rc, out, err = vm_run(cmd, user="root", password=VM_ROOT_PASS, timeout=60)
        label = f"({srv})" if srv else "(fastest)"
        return ok(f"Connected to ProtonVPN {label}." if rc == 0 else f"Error:\n{out}\n{err}")

    if name == "vpn_disconnect":
        rc, out, err = vm_run("protonvpn-cli disconnect", user="root", password=VM_ROOT_PASS)
        return ok("Disconnected." if rc == 0 else f"Error: {err or out}")

    if name == "vpn_status":
        rc, out, err = vm_run("protonvpn-cli status", timeout=15)
        return ok(out.strip() or err.strip() or "No output.")

    # ── Gemini AI ─────────────────────────────────────────────────────────
    if name in ("ai_analyze_screen", "ai_suggest_next_command"):
        screenshot_path = "/tmp/kali_ai_screen.png"
        rc, _, err = vbox("controlvm", VM_NAME, "screenshotpng", screenshot_path)
        if rc != 0:
            return ok(f"Screenshot failed: {err}")

        with open(screenshot_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()

        if name == "ai_analyze_screen":
            prompt = arguments.get(
                "question",
                "What do you see on this screen? Describe the current state of the VM.",
            )
        else:
            goal = arguments.get("goal", "general task")
            prompt = (
                f"I am working on a Kali Linux VM trying to: {goal}.\n"
                "Look at this screenshot and suggest the single best next shell command I should run. "
                "Reply with just the command and a one-sentence explanation."
            )

        gemini_key = key("GEMINI_API_KEY")
        if not gemini_key:
            return ok("GEMINI_API_KEY not available.")

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/png", "data": img_b64}},
                ]
            }]
        }
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}",
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        answer = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        return ok(answer)

    if name == "ai_chat":
        gemini_key = key("GEMINI_API_KEY")
        if not gemini_key:
            return ok("GEMINI_API_KEY not available.")
        model = arguments.get("model", "gemini-2.0-flash")
        payload = {"contents": [{"parts": [{"text": arguments["message"]}]}]}
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}",
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        answer = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        return ok(answer)

    # ── HuggingFace ───────────────────────────────────────────────────────
    if name == "hf_inference":
        hf_token = key("HF_TOKEN")
        if not hf_token:
            return ok("HF_TOKEN not available.")
        model = arguments["model"]
        resp = requests.post(
            f"https://api-inference.huggingface.co/models/{model}",
            headers={"Authorization": f"Bearer {hf_token}"},
            json={"inputs": arguments["inputs"]},
            timeout=60,
        )
        if resp.status_code != 200:
            return ok(f"HF error {resp.status_code}: {resp.text}")
        data = resp.json()
        if isinstance(data, list) and data:
            first = data[0]
            text = first.get("generated_text") or first.get("summary_text") or str(first)
            return ok(text)
        return ok(str(data))

    return ok(f"Unknown tool: {name}")


async def main() -> None:
    load_keys()
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="kali-vm-mcp",
                server_version="2.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
