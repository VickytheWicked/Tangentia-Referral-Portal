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

# Ensure production settings on App Service
log "Verifying production App Service configuration..."
az webapp config appsettings set \
  --name "$BACKEND_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --settings \
    DEV_MODE="False" \
    ALLOW_DEV_TOKENS="False" \
    DATABASE_URL="sqlite:///:memory:" \
    EXCEL_STORAGE_TYPE="blob" \
    STORAGE_TYPE="blob" \
    CV_STORAGE_TYPE="azure" \
    BLOB_DATA_CONTAINER="referral-data" \
    BLOB_CV_CONTAINER="referral-cvs" \
    BLOB_CV_INTELLIGENCE_NAME="cv_intelligence.db" \
    WEBSITES_PORT="8000" \
    SCM_DO_BUILD_DURING_DEPLOYMENT="true" \
  --output none 2>/dev/null
ok "Production App Service settings verified (In-memory SQLite + Azure Blob Storage persistence)."


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
  -x "storage/mock_storage/*" \
  -x "data/*.db" \
  -x "data/*.xlsx" \
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
  --type zip \
  --clean true \
  --restart true


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
echo -e "${GREEN}  PERSISTENCE: Azure Blob Storage (referral-data/Tangentia_Referrals.xlsx)${NC}"
echo -e "${GREEN}  RESUMES:     Azure Blob Storage (referral-cvs/)${NC}"
echo -e "${GREEN}  ENGINE:      In-Memory SQLite (sqlite:///:memory:) with Blob Write-Through${NC}"
echo -e "${GREEN}  All data is persistently synced across restarts and redeployments.${NC}"
echo ""

