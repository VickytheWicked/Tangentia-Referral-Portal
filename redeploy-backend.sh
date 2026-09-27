#!/usr/bin/env bash
# ==============================================================================
# Tangentia Referral Portal — Backend Re-deploy Script
# ==============================================================================
# Use this script when you've only changed backend code (Python/FastAPI).
# Skips frontend build and static web app deployment entirely.
#
# Prerequisites:
#   1. Azure CLI installed:  curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
#   2. Logged in:            az login
#   3. Subscription set:     az account set --subscription "YOUR_SUBSCRIPTION"
#
# Usage:
#   chmod +x redeploy-backend.sh
#   ./redeploy-backend.sh
# ==============================================================================

set -euo pipefail

# ========== CONFIGURATION — must match deploy-azure.sh ==========
RESOURCE_GROUP="tangentia-referral-portal"
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
BACKEND_DIR="$SCRIPT_DIR/backend"
DEPLOY_ZIP="$SCRIPT_DIR/backend-deploy.zip"
BACKEND_URL="https://${BACKEND_APP_NAME}.azurewebsites.net"

# ==============================================================================
# Pre-flight checks
# ==============================================================================
log "Running pre-flight checks..."

command -v az  > /dev/null 2>&1 || err "Azure CLI not found. Install: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash"
command -v zip > /dev/null 2>&1 || err "zip not found. Install: sudo apt install zip"

az account show > /dev/null 2>&1 || err "Not logged into Azure. Run: az login"
SUBSCRIPTION=$(az account show --query "name" -o tsv)
ok "Azure CLI ready — Subscription: $SUBSCRIPTION"

# Verify the App Service exists
az webapp show \
  --name "$BACKEND_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --output none 2>/dev/null \
  || err "App Service '$BACKEND_APP_NAME' not found in '$RESOURCE_GROUP'. Run deploy-azure.sh first."

# ==============================================================================
# Step 1: Package backend (exclude dev artifacts)
# ==============================================================================
log "Packaging backend (excluding .venv, tests, cache, .env)..."
rm -f "$DEPLOY_ZIP"

cd "$BACKEND_DIR"
zip -r "$DEPLOY_ZIP" . \
  -x ".venv/*" \
  -x "__pycache__/*" \
  -x "*.pyc" \
  -x ".pytest_cache/*" \
  -x "tests/*" \
  -x ".env" \
  -x ".env.example" \
  -x "storage/mock_sharepoint/*" \
  -x "data/*.db" \
  -x "data/*.xlsx" \
  -x "data/*.json" \
  > /dev/null

ZIP_SIZE=$(du -sh "$DEPLOY_ZIP" | cut -f1)
ok "Package ready: backend-deploy.zip ($ZIP_SIZE)"

# ==============================================================================
# Step 2: Zip Deploy to Azure App Service
# ==============================================================================
log "Deploying to Azure App Service (this may take 2–3 minutes)..."
az webapp deploy \
  --name "$BACKEND_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --src-path "$DEPLOY_ZIP" \
  --clean true

rm -f "$DEPLOY_ZIP"
ok "Zip deployed. Azure is now running pip install + starting the app..."

# ==============================================================================
# Step 3: Health check
# ==============================================================================
log "Waiting 30s for the app to restart..."
sleep 30

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/health" || echo "000")

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}  Backend Re-deploy Complete!${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo -e "  App Service:  ${CYAN}${BACKEND_URL}${NC}"
echo -e "  API Docs:     ${CYAN}${BACKEND_URL}/api/docs${NC}"
echo -e "  Health:       ${CYAN}${BACKEND_URL}/api/health${NC}"
echo ""

if [ "$HTTP_STATUS" == "200" ]; then
  ok "Health check passed (HTTP 200) ✓"
else
  warn "Health check returned HTTP $HTTP_STATUS — the app may still be warming up."
  warn "Stream live logs with:"
  warn "  az webapp log tail --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP"
fi

echo ""
echo -e "${YELLOW}  NOTE: In-memory SQLite is used (DATABASE_URL=sqlite:///:memory:).${NC}"
echo -e "${YELLOW}  All data is reset on every deployment.${NC}"
echo ""
