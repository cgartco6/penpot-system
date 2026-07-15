#!/bin/bash
# ============================================================
# Penpot System - Ubuntu 24.04 LTS Fully Automated Setup
# ============================================================
set -e
echo "===== Penpot System: Ubuntu Auto-Installer ====="

# ---- Install dependencies ----
sudo apt update -qq
sudo apt install -y -qq git curl wget python3 python3-pip net-tools

# ---- Docker ----
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    newgrp docker <<EONG
EONG
fi

if ! docker compose version &> /dev/null; then
    sudo apt install -y -qq docker-compose-plugin
fi

# ---- Clone/Update ----
if [ ! -f "docker-compose.yml" ]; then
    git clone https://github.com/your-repo/penpot-system.git .
else
    git pull
fi

# ---- Port conflict resolution ----
check_port() { ss -tln | grep -q ":$1 "; }
find_free_port() { local port=$1; while check_port $port; do port=$((port+1)); done; echo $port; }

if [ ! -f ".env" ]; then cp .env.example .env; fi

declare -A defaults=(
    [NGINX_PORT]=8080 [PENPOT_PORT]=9001 [STRAPI_PORT]=1337
    [SALEOR_API_PORT]=8000 [SALEOR_DASHBOARD_PORT]=9000
    [APPSMITH_PORT]=8081 [PAYMENT_PORT]=8001
)

for key in "${!defaults[@]}"; do
    current=$(grep "^$key=" .env | cut -d'=' -f2)
    if [ -z "$current" ]; then current=${defaults[$key]}; fi
    if check_port $current; then
        new_port=$(find_free_port $((current+1)))
        echo "Port $current ($key) in use → $new_port"
        sed -i "s/^$key=.*/$key=$new_port/" .env
    fi
done

# ---- Pull & Start ----
docker compose pull
docker compose up -d

NGINX_PORT=$(grep "^NGINX_PORT=" .env | cut -d'=' -f2)
echo -e "\n========================================="
echo -e "\e[32m✅ Penpot System is RUNNING!\e[0m"
echo "Access via: http://localhost:$NGINX_PORT"
echo "  Design: /design/   CMS: /cms/admin   Store: /store/"
echo "  Apps: /apps/       API: /api/docs"
echo -e "========================================="
