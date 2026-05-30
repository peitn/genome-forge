#!/usr/bin/env bash
# setup_kali.sh — Run this INSIDE the Kali Linux VM after first boot.
# Installs: VirtualBox Guest Additions, ProtonVPN CLI.
set -euo pipefail

echo "=== Updating packages ==="
sudo apt-get update -q
sudo apt-get upgrade -y

echo "=== Installing VirtualBox Guest Additions ==="
sudo apt-get install -y \
    virtualbox-guest-utils \
    virtualbox-guest-x11 \
    build-essential \
    linux-headers-$(uname -r)

echo "=== Installing ProtonVPN ==="
wget -qO /tmp/protonvpn.deb \
    https://repo.protonvpn.com/debian/dists/stable/main/binary-all/protonvpn-stable-release_1.0.3-2_all.deb
sudo dpkg -i /tmp/protonvpn.deb
sudo apt-get update -q
sudo apt-get install -y protonvpn-cli proton-vpn-gnome-desktop
rm /tmp/protonvpn.deb

echo "=== Installing useful security tools ==="
sudo apt-get install -y \
    nmap \
    wireshark \
    metasploit-framework \
    burpsuite \
    curl \
    git \
    python3-pip

echo "=== Enabling SSH for remote access ==="
sudo systemctl enable ssh
sudo systemctl start ssh

echo "=== Setup complete ==="
echo "Reboot to activate Guest Additions: sudo reboot"
echo "Then log in to ProtonVPN: protonvpn-cli login YOUR_USERNAME"
