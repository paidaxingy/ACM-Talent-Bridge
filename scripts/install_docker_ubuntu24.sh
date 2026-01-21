#!/usr/bin/env bash
set -euo pipefail

# Install Docker Engine (docker-ce) + docker compose plugin on Ubuntu 24.04 (Noble).
# Reference: https://docs.docker.com/engine/install/ubuntu/
#
# Usage:
#   bash scripts/install_docker_ubuntu24.sh
#
# Notes:
# - Requires sudo privileges (will prompt for password).
# - On WSL with systemd enabled, this will enable & start the docker service.

if ! command -v sudo >/dev/null 2>&1; then
  echo "sudo not found. Please install sudo first."
  exit 1
fi

if [ "$(id -u)" -eq 0 ]; then
  echo "Do not run as root; run as a normal user with sudo."
  exit 1
fi

echo "[1/6] Install prerequisites..."
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg

echo "[2/6] Add Docker's official GPG key..."
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "[3/6] Set up Docker apt repository..."
. /etc/os-release
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  ${VERSION_CODENAME} stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

echo "[4/6] Install Docker Engine + compose plugin..."
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "[5/6] Enable and start Docker service..."
if command -v systemctl >/dev/null 2>&1; then
  sudo systemctl enable --now docker
else
  sudo service docker start || true
fi

echo "[6/6] Allow current user to run docker without sudo..."
sudo usermod -aG docker "$USER"

echo
echo "Docker installed."
echo "- Open a NEW terminal (or re-login) so group changes take effect."
echo "- Then verify:"
echo "    docker version"
echo "    docker compose version"
echo "    docker run --rm hello-world"

