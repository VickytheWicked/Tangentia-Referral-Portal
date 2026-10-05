# Azure Services & Cloud Cost Estimation Report

**Project:** Tangentia Employee Referral Portal  
**Azure Subscription:** Azure subscription 1 (`ef12b538-e115-47ce-bc93-71f2a690c658`)  
**Resource Group:** `tangentia-referral-portal` (Region: `Central India` / `East Asia`)  
**Architecture Model:** Fast In-Memory SQLite (`sqlite:///:memory:`) + Persistent Azure Blob Storage Excel Ledger (`Tangentia_Referrals.xlsx`)  
**Last Updated:** October 2026  

---

## 1. Services Actively Used by the Referral Portal

| Azure Service | Resource Name | SKU / Tier | Region | Purpose & Workload |
|:---|:---|:---|:---|:---|
| **Azure App Service Plan** | `tangentia-backend-plan` | **Basic B1** (Linux) | Central India | Dedicated App Service hosting environment (1 vCPU, 1.75 GB RAM) with Always-On enabled. |
| **Azure App Service (Web App)** | `tangentia-referral-api` | **Python 3.11** | Central India | Hosts FastAPI REST backend, in-memory SQLite (`:memory:`), CV parsing pipeline, and background workers. |
| **Azure Static Web Apps** | `tangentia-referral-portal` | **Free Tier** | East Asia (Global CDN) | Serves the production React 19 Single Page Application (SPA), routing, and static assets. |
| **Azure Storage Account** | `tangentiareferralstor` | **Standard_LRS** (StorageV2) | Central India | **`referral-data`**: Holds `Tangentia_Referrals.xlsx` (6 sheets) and `cv_intelligence.db`.<br>**`referral-cvs`**: Stores candidate resume files (.pdf, .docx). |
| **Application Insights** | `tangentia-referral-insights` | Pay-As-You-Go | Central India | Telemetry, HTTP response latency, and exception tracing. Linked to Log Analytics workspace. |
| **Log Analytics Workspace** | `tangentia-log-workspace` | Pay-As-You-Go | Central India | Centralized log ingestion for diagnostic logs and container runtime events. |

---

## 2. Monthly Cost Estimation (Active Referral Portal Workload)

The portal was deliberately designed to eliminate expensive database overheads by using **In-Memory SQLite with Azure Blob Storage write-through sync**. 

### Active Portal Monthly Cost Breakdown:

| Service | Meter / SKU Details | Monthly Estimate (USD) | Monthly Estimate (INR approx.) |
|:---|:---|:---:|:---:|
| **App Service (B1 Basic)** | Linux 1 vCPU, 1.75 GB RAM (~730 hrs/mo) | **$12.41** | **₹1,050** |
| **Azure Static Web Apps** | Free Tier (Up to 100 GB bandwidth, 2 custom domains) | **$0.00** | **₹0** |
| **Azure Blob Storage (LRS)** | Hot Tier: ~5 GB data storage + ~10,000 Read/Write API ops | **$0.15** | **₹13** |
| **Application Insights & Logs** | First 5 GB ingestion / month is completely **Free** | **$0.00** | **₹0** |
| **Outbound Data Transfer** | First 100 GB / month is free from Azure | **$0.00** | **₹0** |
| **Total Active Portal Running Cost** | | **~$12.56 / month** | **~₹1,063 / month** |

> [!NOTE]
> If your App Service is scaled down to the **F1 (Free)** tier during low-traffic testing, the entire portal hosting cost becomes **$0.00 / month**. On B1 Basic ($12.41/mo), you get continuous background processing without CPU throttling or thread sleeping.

---

## 3. Supplementary / Pre-Existing Resources in the Resource Group

While running live inspection on the resource group `tangentia-referral-portal`, the following additional resources were detected:

| Resource Name | Type & SKU | Status | Used by Portal? | Estimated Cost |
|:---|:---|:---:|:---:|:---:|
| `tangentia-pg-server` | PostgreSQL Flexible Server (`Standard_B1ms`) | Ready (Running) | **NO** (Portal uses In-Memory SQLite + Blob) | **~$15.00 / month** (~₹1,270) |
| `FirstVM*` (Disk, IP, NSG, Nic, VNet) | Virtual Machine network & OS disk resources | Deployed | **NO** | Variable disk cost (~$3–$5/mo) |
| `tangentia-kv-ref` | Azure Key Vault (`Standard`) | Active | Optional | ~$0.03 / month |

---

## 4. Cost Optimization Recommendations

1. **Stop or Delete `tangentia-pg-server`**:
   - Because the portal strictly runs on **In-Memory SQLite with Azure Blob Storage write-through** (`Tangentia_Referrals.xlsx`), the running PostgreSQL Flexible Server is not in use. Stopping or deleting it will save approximately **$15.00 / month (₹1,270/mo)** immediately.
2. **Clean up unused `FirstVM` networking resources**:
   - The OS disk (`FirstVM_OsDisk_1...`) and public IP incur idle charges if the VM is not in active use.
3. **Optimized Baseline**:
   - With non-portal resources cleaned up, the entire production Tangentia Referral Portal costs **under $13.00 (₹1,100) per month** to run at enterprise scale.
