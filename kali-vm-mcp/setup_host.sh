#!/usr/bin/env bash
# setup_host.sh — Prepare the host machine: install VirtualBox, download Kali,
# create and configure the VM, then launch the MCP server.
set -euo pipefail

VM_NAME="KaliLinux"
VM_RAM=4096        # MB
VM_VRAM=128        # MB
VM_CPUS=2
VM_DISK_GB=40
VM_DIR="$HOME/VMs/${VM_NAME}"
KALI_ISO_URL="https://cdimage.kali.org/kali-2024.2/kali-linux-2024.2-installer-amd64.iso"
KALI_ISO="/tmp/kali-linux.iso"

echo "=== [1/6] Detecting OS ==="
if [[ "$(uname)" == "Darwin" ]]; then
    OS=macos
elif [[ -f /etc/debian_version ]]; then
    OS=debian
elif [[ -f /etc/redhat-release ]]; then
    OS=redhat
else
    echo "Unsupported OS. Install VirtualBox manually from https://www.virtualbox.org/" && exit 1
fi

echo "=== [2/6] Installing VirtualBox ==="
if command -v VBoxManage &>/dev/null; then
    echo "VirtualBox already installed: $(VBoxManage --version)"
else
    case "$OS" in
        macos)
            if command -v brew &>/dev/null; then
                brew install --cask virtualbox
            else
                echo "Install Homebrew first: https://brew.sh"
                exit 1
            fi
            ;;
        debian)
            sudo apt-get update -q
            sudo apt-get install -y virtualbox virtualbox-ext-pack
            ;;
        redhat)
            sudo dnf install -y VirtualBox
            ;;
    esac
fi

echo "=== [3/6] Downloading Kali Linux ISO ==="
if [[ -f "$KALI_ISO" ]]; then
    echo "ISO already present at $KALI_ISO"
else
    echo "Downloading from $KALI_ISO_URL ..."
    wget -q --show-progress -O "$KALI_ISO" "$KALI_ISO_URL"
fi

echo "=== [4/6] Creating VirtualBox VM ==="
mkdir -p "$VM_DIR"

if VBoxManage showvminfo "$VM_NAME" &>/dev/null; then
    echo "VM '$VM_NAME' already exists — skipping creation."
else
    VBoxManage createvm --name "$VM_NAME" --ostype Debian_64 --register --basefolder "$VM_DIR"
    VBoxManage modifyvm "$VM_NAME" \
        --memory "$VM_RAM" \
        --vram "$VM_VRAM" \
        --cpus "$VM_CPUS" \
        --graphicscontroller vmsvga \
        --audio-driver none \
        --nic1 nat \
        --natpf1 "ssh,tcp,,2222,,22" \
        --boot1 dvd --boot2 disk

    # Storage: SATA controller + virtual disk
    VBoxManage storagectl "$VM_NAME" --name SATA --add sata --controller IntelAhci --portcount 2
    VBoxManage createmedium disk \
        --filename "$VM_DIR/${VM_NAME}.vdi" \
        --size $((VM_DISK_GB * 1024)) \
        --format VDI
    VBoxManage storageattach "$VM_NAME" --storagectl SATA --port 0 --device 0 \
        --type hdd --medium "$VM_DIR/${VM_NAME}.vdi"
    VBoxManage storageattach "$VM_NAME" --storagectl SATA --port 1 --device 0 \
        --type dvddrive --medium "$KALI_ISO"

    echo "VM '$VM_NAME' created."
fi

echo "=== [5/6] Installing Python dependencies ==="
cd "$(dirname "$0")"
python3 -m pip install -r requirements.txt

echo "=== [6/6] Done ==="
cat <<'EOF'

Next steps:
  1. Start the VM and complete the Kali Linux installer (default credentials: kali/kali):
       VBoxManage startvm KaliLinux

  2. Inside Kali, install VirtualBox Guest Additions (for keyboard/mouse/command execution):
       sudo apt-get install -y virtualbox-guest-utils virtualbox-guest-x11

  3. Start the MCP server:
       python3 server.py

  4. Add the MCP server to your Claude config (see mcp_config.json).

EOF
