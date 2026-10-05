#!/usr/bin/env bash
# ==============================================================================
# Tangentia Referral Portal — Azure Deployment Script
# ==============================================================================
# Deploys the backend to Azure App Service and the frontend to Azure Static Web Apps.
# Runs in dev/mock mode on Azure without live cloud credentials.
#
# Prerequisites:
#   1. Azure CLI installed:  curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
#   2. Logged in:            az login
#   3. Subscription set:     az account set --subscription "YOUR_SUBSCRIPTION"
#   4. Node.js/npm installed (for frontend build)
#
# Usage:
#   chmod +x deploy-azure.sh
#   ./deploy-azure.sh
# ==============================================================================

set -euo pipefail

# ========== CONFIGURATION — EDIT THESE ==========
RESOURCE_GROUP="tangentia-referral-portal"
LOCATION="centralindia"                       # Azure region closest to your users
BACKEND_APP_NAME="tangentia-referral-api"      # Must be globally unique
BACKEND_PLAN_NAME="tangentia-backend-plan"
FRONTEND_APP_NAME="tangentia-referral-portal"  # Must be globally unique
# =================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log()  { echo -e "${CYAN}[INFO]${NC}  $1"; }
ok()   { echo -e "${GREEN}[OK]${NC}    $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# ==============================================================================
# Pre-flight checks
# ==============================================================================
log "Running pre-flight checks..."

command -v az >/dev/null 2>&1 || err "Azure CLI not found. Install: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash"
command -v npm >/dev/null 2>&1 || err "npm not found. Install Node.js first."
command -v zip >/dev/null 2>&1 || err "zip command not found. Install: sudo apt install zip"

# Verify Azure login
az account show >/dev/null 2>&1 || err "Not logged into Azure. Run: az login"
SUBSCRIPTION=$(az account show --query "name" -o tsv)
ok "Azure CLI ready — Subscription: $SUBSCRIPTION"

# ==============================================================================
# Step 1: Create Resource Group
# ==============================================================================
log "Creating resource group: $RESOURCE_GROUP in $LOCATION..."
az group create \
  --name "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --output none 2>/dev/null || true
ok "Resource group ready."

# ==============================================================================
# Step 2: Create App Service Plan + Backend Web App
# ==============================================================================
log "Creating App Service Plan (Linux B1)..."
az appservice plan create \
  --name "$BACKEND_PLAN_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --sku B1 \
  --is-linux \
  --output none 2>/dev/null

log "Creating backend Web App with Python 3.11..."
az webapp create \
  --name "$BACKEND_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --plan "$BACKEND_PLAN_NAME" \
  --runtime "PYTHON:3.11" \
  --output none 2>/dev/null

# Set startup command and enable Always On (prevents cold start sleep on B1 plan)
az webapp config set \
  --name "$BACKEND_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --startup-file "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000" \
  --always-on true \
  --output none 2>/dev/null

BACKEND_URL="https://${BACKEND_APP_NAME}.azurewebsites.net"
ok "Backend App Service ready: $BACKEND_URL"

# ==============================================================================
# Step 3: Create Azure Static Web App (Frontend)
# ==============================================================================
log "Creating Azure Static Web App (Free tier)..."
az staticwebapp create \
  --name "$FRONTEND_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "eastasia" \
  --sku Free \
  --output none 2>/dev/null || warn "Static Web App may already exist."

FRONTEND_HOSTNAME=$(az staticwebapp show \
  --name "$FRONTEND_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query "defaultHostname" -o tsv 2>/dev/null)
FRONTEND_URL="https://${FRONTEND_HOSTNAME}"
ok "Frontend Static Web App ready: $FRONTEND_URL"

STORAGE_ACCOUNT_NAME="${AZURE_STORAGE_ACCOUNT:-tangstrg$(echo -n "$RESOURCE_GROUP" | md5sum | cut -c1-8)}"

# ==============================================================================
# Step 4: Setup Azure Blob Storage (Excel Ledger & Candidate CVs)
# ==============================================================================
log "Setting up Azure Storage Account for Excel ledger & CV documents: $STORAGE_ACCOUNT_NAME..."
az storage account create \
  --name "$STORAGE_ACCOUNT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --sku Standard_LRS \
  --kind StorageV2 \
  --output none 2>/dev/null || true

STORAGE_CONN_STR=$(az storage account show-connection-string \
  --name "$STORAGE_ACCOUNT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query "connectionString" -o tsv 2>/dev/null || echo "")

if [ -n "$STORAGE_CONN_STR" ]; then
  ok "Storage account ready: $STORAGE_ACCOUNT_NAME"
  log "Ensuring blob containers exist ('referral-data' and 'referral-cvs')..."
  az storage container create \
    --name "referral-data" \
    --connection-string "$STORAGE_CONN_STR" \
    --output none 2>/dev/null || true

  az storage container create \
    --name "referral-cvs" \
    --connection-string "$STORAGE_CONN_STR" \
    --output none 2>/dev/null || true

  # Seed initial Excel ledger to blob storage if not present
  EXISTS=$(az storage blob exists \
    --container-name "referral-data" \
    --name "Tangentia_Referrals.xlsx" \
    --connection-string "$STORAGE_CONN_STR" \
    --query "exists" -o tsv 2>/dev/null || echo "false")

  if [ "$EXISTS" != "true" ] && [ -f "$BACKEND_DIR/data/Tangentia_Referrals.xlsx" ]; then
    log "Seeding initial Tangentia_Referrals.xlsx into Azure Blob Storage..."
    az storage blob upload \
      --container-name "referral-data" \
      --file "$BACKEND_DIR/data/Tangentia_Referrals.xlsx" \
      --name "Tangentia_Referrals.xlsx" \
      --connection-string "$STORAGE_CONN_STR" \
      --overwrite false \
      --output none 2>/dev/null || true
    ok "Tangentia_Referrals.xlsx seeded to Azure Blob Storage."
  fi
else
  warn "Could not retrieve Azure Storage connection string. Backend will fallback to local storage."
fi

# ==============================================================================
# Step 5: Configure Backend Environment Variables
# ==============================================================================
log "Setting backend environment variables..."
JWT_SECRET_KEY=$(openssl rand -hex 32)

az webapp config appsettings set \
  --name "$BACKEND_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --settings \
    PROJECT_NAME="Tangentia Employee Referral Portal" \
    ENVIRONMENT="production" \
    DEBUG="False" \
    DEV_MODE="False" \
    ALLOW_DEV_TOKENS="False" \
    JWT_SECRET_KEY="$JWT_SECRET_KEY" \
    DATABASE_URL="sqlite:///:memory:" \
    EXCEL_STORAGE_TYPE="blob" \
    STORAGE_TYPE="blob" \
    CV_STORAGE_TYPE="azure" \
    AZURE_STORAGE_CONNECTION_STRING="$STORAGE_CONN_STR" \
    BLOB_DATA_CONTAINER="referral-data" \
    BLOB_CV_CONTAINER="referral-cvs" \
    BLOB_CV_INTELLIGENCE_NAME="cv_intelligence.db" \
    CORS_ORIGINS_EXTRA="${FRONTEND_URL}" \
    WEBSITES_PORT="8000" \
    SCM_DO_BUILD_DURING_DEPLOYMENT="true" \
  --output none 2>/dev/null
ok "Backend environment configured."

# ==============================================================================
# Step 6: Deploy Backend (Zip Deploy)
# ==============================================================================
log "Packaging backend for deployment..."
DEPLOY_ZIP="$SCRIPT_DIR/backend-deploy.zip"
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
  -x "data/*.json" \
  > /dev/null

log "Deploying backend to Azure App Service (this may take 2-3 minutes)..."
az webapp deploy \
  --name "$BACKEND_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --src-path "$DEPLOY_ZIP" \
  --type zip \
  --output none 2>/dev/null

rm -f "$DEPLOY_ZIP"
ok "Backend deployed."

# Verify backend health
log "Waiting for backend to start (30s)..."
sleep 30
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/health" || echo "000")
if [ "$HEALTH_STATUS" == "200" ]; then
  ok "Backend health check passed!"
else
  warn "Backend returned HTTP $HEALTH_STATUS — it may still be starting. Check: $BACKEND_URL/api/health"
fi

# ==============================================================================
# Step 7: Build & Deploy Frontend
# ==============================================================================
log "Building frontend for production..."
cd "$FRONTEND_DIR"

# Write production env (no Entra ID required)
cat > .env.production <<EOF
VITE_API_BASE_URL=${BACKEND_URL}/api
EOF

npm ci --silent 2>/dev/null
npm run build

log "Deploying frontend to Azure Static Web Apps..."
DEPLOY_TOKEN=$(az staticwebapp secrets list \
  --name "$FRONTEND_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.apiKey" -o tsv 2>/dev/null)

npx -y @azure/static-web-apps-cli deploy ./dist \
  --deployment-token "$DEPLOY_TOKEN" \
  --env production 2>/dev/null

ok "Frontend deployed."

# ==============================================================================
# Done!
# ==============================================================================
echo ""
echo -e "${GREEN}================================================================${NC}"
echo -e "${GREEN}  Tangentia Referral Portal — Deployed to Azure!${NC}"
echo -e "${GREEN}================================================================${NC}"
echo ""
echo -e "  Frontend:  ${CYAN}${FRONTEND_URL}${NC}"
echo -e "  Backend:   ${CYAN}${BACKEND_URL}${NC}"
echo -e "  API Docs:  ${CYAN}${BACKEND_URL}/api/docs${NC}"
echo -e "  Health:    ${CYAN}${BACKEND_URL}/api/health${NC}"
echo ""
echo -e "  Auth:      Portal JWT Authentication (@tangentia.com HR login, zero-friction employee workspace)"
echo -e "  Storage:   Azure Blob Storage (Tangentia_Referrals.xlsx + Candidate Resumes)"
echo -e "  Plan:      Azure App Service (B1) + Azure Static Web App (Free) + Azure Blob Storage"
echo ""
echo -e "${GREEN}  System is fully configured with persistent Azure Blob Storage for the Excel ledger.${NC}"
echo ""
