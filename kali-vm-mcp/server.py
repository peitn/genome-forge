#!/usr/bin/env python3
"""
Kali Linux VM MCP Server
Controls a Kali Linux VirtualBox VM with virtual keyboard/mouse and ProtonVPN.
"""

import asyncio
import subprocess
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

server = Server("kali-vm-mcp")

VM_NAME = "KaliLinux"
VM_USER = "kali"
VM_PASS = "kali"
VM_ROOT_PASS = "kali"


def run_cmd(cmd: list[str], timeout: int = 60) -> tuple[int, str, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout}s"
    except FileNotFoundError as e:
        return -1, "", f"Command not found: {e}"
    except Exception as e:
        return -1, "", str(e)


def vbox(*args: str, timeout: int = 60) -> tuple[int, str, str]:
    return run_cmd(["VBoxManage"] + list(args), timeout=timeout)


def vm_run(command: str, user: str = VM_USER, password: str = VM_PASS, timeout: int = 60) -> tuple[int, str, str]:
    """Execute a shell command inside the running VM via Guest Additions."""
    return vbox(
        "guestcontrol", VM_NAME, "run",
        "--exe", "/bin/bash",
        "--username", user,
        "--password", password,
        "--wait-stdout", "--wait-stderr",
        "--", "-c", command,
        timeout=timeout
    )


def ok(text: str) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=text)]


# ---------------------------------------------------------------------------
# Keyboard scan-code map
# ---------------------------------------------------------------------------
KEY_SCANCODES: dict[str, list[str]] = {
    "Return":      ["0x1c", "0x9c"],
    "Enter":       ["0x1c", "0x9c"],
    "Escape":      ["0x01", "0x81"],
    "Tab":         ["0x0f", "0x8f"],
    "Space":       ["0x39", "0xb9"],
    "BackSpace":   ["0x0e", "0x8e"],
    "Delete":      ["0xe0", "0x53", "0xe0", "0xd3"],
    "Up":          ["0xe0", "0x48", "0xe0", "0xc8"],
    "Down":        ["0xe0", "0x50", "0xe0", "0xd0"],
    "Left":        ["0xe0", "0x4b", "0xe0", "0xcb"],
    "Right":       ["0xe0", "0x4d", "0xe0", "0xcd"],
    "Home":        ["0xe0", "0x47", "0xe0", "0xc7"],
    "End":         ["0xe0", "0x4f", "0xe0", "0xcf"],
    "PageUp":      ["0xe0", "0x49", "0xe0", "0xc9"],
    "PageDown":    ["0xe0", "0x51", "0xe0", "0xd1"],
    "F1":          ["0x3b", "0xbb"],
    "F2":          ["0x3c", "0xbc"],
    "F3":          ["0x3d", "0xbd"],
    "F4":          ["0x3e", "0xbe"],
    "F5":          ["0x3f", "0xbf"],
    "F12":         ["0x58", "0xd8"],
    # Ctrl combos (press Ctrl, key, release key, release Ctrl)
    "ctrl-c":      ["0x1d", "0x2e", "0xae", "0x9d"],
    "ctrl-v":      ["0x1d", "0x2f", "0xaf", "0x9d"],
    "ctrl-z":      ["0x1d", "0x2c", "0xac", "0x9d"],
    "ctrl-x":      ["0x1d", "0x2d", "0xad", "0x9d"],
    "ctrl-a":      ["0x1d", "0x1e", "0x9e", "0x9d"],
    "ctrl-s":      ["0x1d", "0x1f", "0x9f", "0x9d"],
    "ctrl-l":      ["0x1d", "0x26", "0xa6", "0x9d"],
    "ctrl-alt-t":  ["0x1d", "0x38", "0x14", "0x94", "0xb8", "0x9d"],
    "ctrl-alt-del": ["0x1d", "0x38", "0xe0", "0x53", "0xe0", "0xd3", "0xb8", "0x9d"],
    "alt-F4":      ["0x38", "0x3e", "0xbe", "0xb8"],
    "alt-tab":     ["0x38", "0x0f", "0x8f", "0xb8"],
    "super":       ["0xe0", "0x5b", "0xe0", "0xdb"],
}


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
                    "headless": {
                        "type": "boolean",
                        "description": "Start without GUI window (default true)",
                        "default": True,
                    }
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
                    "force": {
                        "type": "boolean",
                        "description": "Force power-off instead of graceful ACPI shutdown",
                        "default": False,
                    }
                },
                "required": [],
            },
        ),
        types.Tool(
            name="vm_status",
            description="Get the current state and basic info of the Kali Linux VM.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="vm_run_command",
            description="Run a shell command inside the Kali Linux VM (requires VirtualBox Guest Additions).",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute"},
                    "as_root": {
                        "type": "boolean",
                        "description": "Run as root user (default false)",
                        "default": False,
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default 60)",
                        "default": 60,
                    },
                },
                "required": ["command"],
            },
        ),
        types.Tool(
            name="vm_snapshot_create",
            description="Create a snapshot of the current VM state.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Snapshot name"},
                    "description": {"type": "string", "description": "Optional description"},
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="vm_snapshot_restore",
            description="Restore the VM to a previous snapshot.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Snapshot name to restore"}
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="vm_list_snapshots",
            description="List all snapshots for the Kali Linux VM.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="vm_screenshot",
            description="Take a PNG screenshot of the VM screen and save it on the host.",
            inputSchema={
                "type": "object",
                "properties": {
                    "output_path": {
                        "type": "string",
                        "description": "Host path to save the screenshot (default /tmp/kali_screen.png)",
                        "default": "/tmp/kali_screen.png",
                    }
                },
                "required": [],
            },
        ),
        # ── Virtual keyboard ───────────────────────────────────────────────
        types.Tool(
            name="keyboard_type",
            description="Type a string of text into the VM using the virtual keyboard.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to type"}
                },
                "required": ["text"],
            },
        ),
        types.Tool(
            name="keyboard_key",
            description=(
                "Press a named key or shortcut in the VM. "
                "Supported: Return, Escape, Tab, Space, BackSpace, Delete, "
                "Up, Down, Left, Right, Home, End, PageUp, PageDown, F1-F5, F12, "
                "ctrl-c, ctrl-v, ctrl-z, ctrl-x, ctrl-a, ctrl-s, ctrl-l, "
                "ctrl-alt-t, ctrl-alt-del, alt-F4, alt-tab, super."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Key name or shortcut"}
                },
                "required": ["key"],
            },
        ),
        # ── Virtual mouse ──────────────────────────────────────────────────
        types.Tool(
            name="mouse_move",
            description="Move the mouse cursor to absolute pixel coordinates on the VM screen.",
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X coordinate (pixels from left)"},
                    "y": {"type": "integer", "description": "Y coordinate (pixels from top)"},
                },
                "required": ["x", "y"],
            },
        ),
        types.Tool(
            name="mouse_click",
            description="Click a mouse button at specified coordinates in the VM.",
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X coordinate"},
                    "y": {"type": "integer", "description": "Y coordinate"},
                    "button": {
                        "type": "string",
                        "enum": ["left", "right", "middle"],
                        "description": "Which mouse button (default left)",
                        "default": "left",
                    },
                    "double": {
                        "type": "boolean",
                        "description": "Double-click (default false)",
                        "default": False,
                    },
                },
                "required": ["x", "y"],
            },
        ),
        types.Tool(
            name="mouse_scroll",
            description="Scroll the mouse wheel at specified coordinates.",
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X coordinate"},
                    "y": {"type": "integer", "description": "Y coordinate"},
                    "direction": {
                        "type": "string",
                        "enum": ["up", "down"],
                        "description": "Scroll direction",
                    },
                    "amount": {
                        "type": "integer",
                        "description": "Number of scroll steps (default 3)",
                        "default": 3,
                    },
                },
                "required": ["x", "y", "direction"],
            },
        ),
        # ── ProtonVPN ──────────────────────────────────────────────────────
        types.Tool(
            name="vpn_install",
            description="Download and install ProtonVPN CLI inside the Kali Linux VM.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="vpn_login",
            description="Log in to ProtonVPN inside the VM with your credentials.",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {"type": "string", "description": "ProtonVPN username"},
                    "password": {"type": "string", "description": "ProtonVPN password"},
                },
                "required": ["username", "password"],
            },
        ),
        types.Tool(
            name="vpn_connect",
            description="Connect to ProtonVPN inside the VM. Leave server empty for fastest.",
            inputSchema={
                "type": "object",
                "properties": {
                    "server": {
                        "type": "string",
                        "description": "Country code or server (e.g. 'CZ', 'US', 'NL#5'). Empty = fastest.",
                        "default": "",
                    }
                },
                "required": [],
            },
        ),
        types.Tool(
            name="vpn_disconnect",
            description="Disconnect from ProtonVPN inside the VM.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="vpn_status",
            description="Check ProtonVPN connection status inside the VM.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:

    # ── VM management ──────────────────────────────────────────────────────
    if name == "vm_start":
        headless = arguments.get("headless", True)
        mode = "headless" if headless else "gui"
        rc, out, err = vbox("startvm", VM_NAME, "--type", mode)
        if rc == 0:
            return ok(f"VM '{VM_NAME}' started ({mode}).")
        return ok(f"Error: {err or out}")

    if name == "vm_stop":
        force = arguments.get("force", False)
        action = "poweroff" if force else "acpipowerbutton"
        rc, out, err = vbox("controlvm", VM_NAME, action)
        if rc == 0:
            return ok(f"VM '{VM_NAME}' {'powered off' if force else 'shutdown requested'}.")
        return ok(f"Error: {err or out}")

    if name == "vm_status":
        rc, out, err = vbox("showvminfo", VM_NAME, "--machinereadable")
        if rc != 0:
            return ok(f"Error: {err}")
        data: dict[str, str] = {}
        for line in out.splitlines():
            if "=" in line:
                k, _, v = line.partition("=")
                data[k.strip()] = v.strip().strip('"')
        state = data.get("VMState", "unknown")
        memory = data.get("memory", "?")
        cpus = data.get("cpus", "?")
        vram = data.get("vram", "?")
        return ok(
            f"VM : {VM_NAME}\n"
            f"State  : {state}\n"
            f"Memory : {memory} MB\n"
            f"VRAM   : {vram} MB\n"
            f"CPUs   : {cpus}"
        )

    if name == "vm_run_command":
        command = arguments["command"]
        timeout = arguments.get("timeout", 60)
        as_root = arguments.get("as_root", False)
        user = "root" if as_root else VM_USER
        pwd = VM_ROOT_PASS if as_root else VM_PASS
        rc, out, err = vm_run(command, user=user, password=pwd, timeout=timeout)
        lines = [f"Exit: {rc}"]
        if out:
            lines.append(f"STDOUT:\n{out.rstrip()}")
        if err:
            lines.append(f"STDERR:\n{err.rstrip()}")
        return ok("\n".join(lines))

    if name == "vm_screenshot":
        path = arguments.get("output_path", "/tmp/kali_screen.png")
        rc, out, err = vbox("controlvm", VM_NAME, "screenshotpng", path)
        if rc == 0:
            return ok(f"Screenshot saved to {path}")
        return ok(f"Error: {err or out}")

    if name == "vm_snapshot_create":
        snap = arguments["name"]
        desc = arguments.get("description", "")
        cmd = ["snapshot", VM_NAME, "take", snap]
        if desc:
            cmd += ["--description", desc]
        rc, out, err = vbox(*cmd)
        if rc == 0:
            return ok(f"Snapshot '{snap}' created.")
        return ok(f"Error: {err or out}")

    if name == "vm_snapshot_restore":
        snap = arguments["name"]
        rc, out, err = vbox("snapshot", VM_NAME, "restore", snap)
        if rc == 0:
            return ok(f"Restored to snapshot '{snap}'.")
        return ok(f"Error: {err or out}")

    if name == "vm_list_snapshots":
        rc, out, err = vbox("snapshot", VM_NAME, "list")
        if rc == 0:
            return ok(out.strip() or "No snapshots found.")
        return ok(f"Error: {err or out}")

    # ── Virtual keyboard ───────────────────────────────────────────────────
    if name == "keyboard_type":
        text = arguments["text"]
        rc, out, err = vbox("controlvm", VM_NAME, "keyboardputstring", text)
        if rc == 0:
            return ok(f"Typed {len(text)} characters.")
        return ok(f"Error: {err or out}")

    if name == "keyboard_key":
        key = arguments["key"]
        scancodes = KEY_SCANCODES.get(key)
        if not scancodes:
            supported = ", ".join(sorted(KEY_SCANCODES))
            return ok(f"Unknown key '{key}'.\nSupported keys: {supported}")
        rc, out, err = vbox("controlvm", VM_NAME, "keyboardputscancode", *scancodes)
        if rc == 0:
            return ok(f"Key pressed: {key}")
        return ok(f"Error: {err or out}")

    # ── Virtual mouse ──────────────────────────────────────────────────────
    if name == "mouse_move":
        x, y = arguments["x"], arguments["y"]
        rc, out, err = vbox("controlvm", VM_NAME, "mousemove", str(x), str(y))
        if rc == 0:
            return ok(f"Mouse moved to ({x}, {y}).")
        return ok(f"Error: {err or out}")

    if name == "mouse_click":
        x, y = arguments["x"], arguments["y"]
        button = arguments.get("button", "left")
        double = arguments.get("double", False)
        btn_codes = {"left": "1", "right": "2", "middle": "4"}
        btn = btn_codes.get(button, "1")
        vbox("controlvm", VM_NAME, "mousemove", str(x), str(y))
        clicks = 2 if double else 1
        for _ in range(clicks):
            vbox("controlvm", VM_NAME, "mousebuttonevent", btn)
            vbox("controlvm", VM_NAME, "mousebuttonevent", "0")
        label = "Double-click" if double else "Click"
        return ok(f"{label} ({button}) at ({x}, {y}).")

    if name == "mouse_scroll":
        x, y = arguments["x"], arguments["y"]
        direction = arguments["direction"]
        amount = arguments.get("amount", 3)
        wheel = str(-amount) if direction == "up" else str(amount)
        vbox("controlvm", VM_NAME, "mousemove", str(x), str(y))
        rc, out, err = vbox("controlvm", VM_NAME, "mousewheel", wheel)
        if rc == 0:
            return ok(f"Scrolled {direction} {amount} steps at ({x}, {y}).")
        return ok(f"Error: {err or out}")

    # ── ProtonVPN ──────────────────────────────────────────────────────────
    if name == "vpn_install":
        script = (
            "set -e && "
            "wget -qO /tmp/protonvpn.deb "
            "https://repo.protonvpn.com/debian/dists/stable/main/binary-all/protonvpn-stable-release_1.0.3-2_all.deb && "
            "dpkg -i /tmp/protonvpn.deb && "
            "apt-get update -q && "
            "apt-get install -y proton-vpn-gnome-desktop protonvpn-cli"
        )
        rc, out, err = vm_run(script, user="root", password=VM_ROOT_PASS, timeout=300)
        if rc == 0:
            return ok("ProtonVPN installed successfully.")
        return ok(f"Install output:\nSTDOUT: {out}\nSTDERR: {err}")

    if name == "vpn_login":
        username = arguments["username"]
        password = arguments["password"]
        # Use expect-style piped login
        cmd = f"echo {password!r} | protonvpn-cli login {username} --password-stdin"
        rc, out, err = vm_run(cmd, timeout=30)
        if rc == 0:
            return ok("Logged in to ProtonVPN.")
        return ok(f"Login error:\n{out}\n{err}")

    if name == "vpn_connect":
        server = arguments.get("server", "").strip()
        cmd = f"protonvpn-cli connect {server}" if server else "protonvpn-cli connect --fastest"
        rc, out, err = vm_run(cmd, user="root", password=VM_ROOT_PASS, timeout=60)
        label = f"({server})" if server else "(fastest)"
        if rc == 0:
            return ok(f"Connected to ProtonVPN {label}.")
        return ok(f"VPN connect error:\n{out}\n{err}")

    if name == "vpn_disconnect":
        rc, out, err = vm_run("protonvpn-cli disconnect", user="root", password=VM_ROOT_PASS)
        if rc == 0:
            return ok("Disconnected from ProtonVPN.")
        return ok(f"Error: {err or out}")

    if name == "vpn_status":
        rc, out, err = vm_run("protonvpn-cli status", timeout=15)
        return ok(out.strip() or err.strip() or "No output.")

    return ok(f"Unknown tool: {name}")


async def main() -> None:
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="kali-vm-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
