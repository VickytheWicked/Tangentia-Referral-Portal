#!/usr/bin/env bash
# ==============================================================================
# Tangentia Referral Portal — Frontend Re-deploy Script
# ==============================================================================
# Use this script when you've only changed frontend code (React/Vite/TSX/CSS).
# Skips backend packaging and App Service deployment entirely.
#
# Prerequisites:
#   1. Azure CLI installed:  curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
#   2. Logged in:            az login
#   3. Subscription set:     az account set --subscription "YOUR_SUBSCRIPTION"
#   4. Node.js / npm installed
#
# Usage:
#   chmod +x redeploy-frontend.sh
#   ./redeploy-frontend.sh
# ==============================================================================

set -euo pipefail

# ========== CONFIGURATION — must match deploy-azure.sh ==========
RESOURCE_GROUP="tangentia-referral-portal"
FRONTEND_APP_NAME="tangentia-referral-portal"
BACKEND_APP_NAME="tangentia-referral-api"
# =================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${CYAN}[INFO]${NC}  $1"; }
ok()   { echo -e "${GREEN}[OK]${NC}    $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
BACKEND_URL="https://${BACKEND_APP_NAME}.azurewebsites.net"

# ==============================================================================
# Pre-flight checks
# ==============================================================================
log "Running pre-flight checks..."

command -v az  > /dev/null 2>&1 || err "Azure CLI not found. Install: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash"
command -v npm > /dev/null 2>&1 || err "npm not found. Install Node.js first."
command -v npx > /dev/null 2>&1 || err "npx not found. Install Node.js first."

az account show > /dev/null 2>&1 || err "Not logged into Azure. Run: az login"
SUBSCRIPTION=$(az account show --query "name" -o tsv)
ok "Azure CLI ready — Subscription: $SUBSCRIPTION"

# Verify the Static Web App exists
az staticwebapp show \
  --name "$FRONTEND_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --output none 2>/dev/null \
  || err "Static Web App '$FRONTEND_APP_NAME' not found in '$RESOURCE_GROUP'. Run deploy-azure.sh first."

# ==============================================================================
# Step 1: Write production environment file
# ==============================================================================
log "Writing .env.production (pointing to live backend)..."
cat > "$FRONTEND_DIR/.env.production" <<EOF
VITE_API_BASE_URL=${BACKEND_URL}/api
VITE_AZURE_CLIENT_ID=00000000-0000-0000-0000-000000000000
VITE_AZURE_TENANT_ID=common
EOF
ok ".env.production written."

# ==============================================================================
# Step 2: Install dependencies & build
# ==============================================================================
log "Installing npm dependencies..."
cd "$FRONTEND_DIR"
npm ci --silent

log "Building frontend for production (Vite)..."
npm run build
ok "Build complete → frontend/dist/"

# ==============================================================================
# Step 3: Fetch deployment token and deploy
# ==============================================================================
log "Fetching Static Web App deployment token..."
DEPLOY_TOKEN=$(az staticwebapp secrets list \
  --name "$FRONTEND_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.apiKey" -o tsv)

log "Deploying dist/ to Azure Static Web Apps..."
npx -y @azure/static-web-apps-cli deploy ./dist \
  --deployment-token "$DEPLOY_TOKEN" \
  --env production

ok "Frontend deployed to Azure Static Web Apps."

# ==============================================================================
# Done
# ==============================================================================
FRONTEND_HOSTNAME=$(az staticwebapp show \
  --name "$FRONTEND_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query "defaultHostname" -o tsv 2>/dev/null)
FRONTEND_URL="https://${FRONTEND_HOSTNAME}"

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}  Frontend Re-deploy Complete!${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo -e "  Frontend:  ${CYAN}${FRONTEND_URL}${NC}"
echo -e "  Backend:   ${CYAN}${BACKEND_URL}${NC}"
echo -e "  API Docs:  ${CYAN}${BACKEND_URL}/api/docs${NC}"
echo ""
echo -e "${YELLOW}  Tip: It may take ~30s for CDN propagation to reflect changes.${NC}"
echo ""
