# Cost Optimization - Scheduled Start/Stop

## Overview

The QA Compliance Assistant DEV environment is configured with **two-tier cost optimization**:

### Tier 1: Scale-to-Zero (Automatic)
All Container Apps automatically scale to 0 replicas when idle for 5+ minutes.

### Tier 2: Scheduled Shutdown (Daily)
All Container Apps are forcefully stopped at night and restarted in the morning to maximize cost savings.

---

## Schedule

| Event | Time (SGT) | Time (UTC) | Action |
|-------|-----------|-----------|--------|
| **STOP** | 8:00 PM | 12:00 PM | Scale all apps to min=0, max=0 |
| **START** | 8:00 AM | 12:00 AM | Restore scale-to-zero (min=0, max=3) |

**Business Hours:** 8 AM - 8 PM SGT (Monday - Sunday)
**Shutdown Hours:** 8 PM - 8 AM SGT (12 hours daily)

---

## Cost Savings Estimate

### Before Optimization
- API: 1 instance × 24 hours × 1.0 CPU = 24 CPU-hours/day
- Frontend: 1 instance × 24 hours × 0.5 CPU = 12 CPU-hours/day
- MCP: 1 instance × 24 hours × 0.5 CPU = 12 CPU-hours/day
- **Total:** 48 CPU-hours/day × 30 days = **1,440 CPU-hours/month**

### After Optimization
**During Business Hours (8 AM - 8 PM, 12 hours):**
- Average utilization with scale-to-zero: ~30% (intermittent usage)
- API: 0.3 instances × 12 hours × 1.0 CPU = 3.6 CPU-hours/day
- Frontend: 0.3 instances × 12 hours × 0.5 CPU = 1.8 CPU-hours/day
- MCP: 0.1 instances × 12 hours × 0.5 CPU = 0.6 CPU-hours/day

**During Off Hours (8 PM - 8 AM, 12 hours):**
- All apps: 0 instances = 0 CPU-hours/day

**Total:** ~6 CPU-hours/day × 30 days = **180 CPU-hours/month**

### Savings
- **87.5% reduction** in compute costs
- From: 1,440 CPU-hours/month
- To: 180 CPU-hours/month
- **Savings: 1,260 CPU-hours/month**

At ~$0.000012/CPU-second = $51.84/month → **~$6.48/month** (saving **$45/month**)

---

## Azure Automation Components

### 1. Automation Account
**Resource:** `aa-qca-dev`
- **Location:** West US 2
- **SKU:** Basic (Free tier - 500 minutes/month)
- **Identity:** System-assigned Managed Identity with Contributor role

### 2. Runbooks

#### Stop-ContainerApps
```powershell
# Scales all Container Apps to 0 replicas (complete shutdown)
az containerapp update --name <app> --min-replicas 0 --max-replicas 0
```

#### Start-ContainerApps
```powershell
# Restores scale-to-zero configuration (allows automatic scaling)
az containerapp update --name <app> --min-replicas 0 --max-replicas 3
```

### 3. Schedules
- **Stop-ContainerApps-8PM-SGT:** Runs daily at 8:00 PM
- **Start-ContainerApps-8AM-SGT:** Runs daily at 8:00 AM

---

## Manual Control

### Manually Start All Services
```bash
# Via Azure Portal
1. Go to Automation Account: aa-qca-dev
2. Runbooks → Start-ContainerApps
3. Click "Start"
4. Enter parameters (auto-filled)
5. Click "OK"

# Via Azure CLI
az automation job create \
  --automation-account-name aa-qca-dev \
  --resource-group rg-qca-dev \
  --runbook-name Start-ContainerApps \
  --parameters ResourceGroupName=rg-qca-dev \
               ApiAppName=ca-api-qca-dev \
               FrontendAppName=ca-frontend-qca-dev \
               McpAppName=ca-mcp-qca-dev
```

### Manually Stop All Services
```bash
az automation job create \
  --automation-account-name aa-qca-dev \
  --resource-group rg-qca-dev \
  --runbook-name Stop-ContainerApps \
  --parameters ResourceGroupName=rg-qca-dev \
               ApiAppName=ca-api-qca-dev \
               FrontendAppName=ca-frontend-qca-dev \
               McpAppName=ca-mcp-qca-dev
```

### Check Current Status
```bash
# Check Container Apps status
az containerapp list \
  --resource-group rg-qca-dev \
  --query "[].{Name:name, Replicas:properties.template.scale.minReplicas}" \
  --output table
```

### View Automation Job History
```bash
az automation job list \
  --automation-account-name aa-qca-dev \
  --resource-group rg-qca-dev \
  --output table
```

---

## Modifying Schedules

### Change Stop Time
```bash
# Update to 10 PM instead of 8 PM
az automation schedule update \
  --automation-account-name aa-qca-dev \
  --resource-group rg-qca-dev \
  --name Stop-ContainerApps-8PM-SGT \
  --start-time "2025-11-08T22:00:00+08:00"
```

### Change Start Time
```bash
# Update to 7 AM instead of 8 AM
az automation schedule update \
  --automation-account-name aa-qca-dev \
  --resource-group rg-qca-dev \
  --name Start-ContainerApps-8AM-SGT \
  --start-time "2025-11-08T07:00:00+08:00"
```

### Disable Scheduled Automation
```bash
# Disable stop schedule
az automation schedule update \
  --automation-account-name aa-qca-dev \
  --resource-group rg-qca-dev \
  --name Stop-ContainerApps-8PM-SGT \
  --is-enabled false

# Disable start schedule
az automation schedule update \
  --automation-account-name aa-qca-dev \
  --resource-group rg-qca-dev \
  --name Start-ContainerApps-8AM-SGT \
  --is-enabled false
```

---

## Weekend/Holiday Configuration

### Disable for Weekends
To keep services running 24/7 on weekends, modify schedules to skip Saturdays and Sundays:

```bash
# This requires updating the runbook to check day of week
# Alternative: Disable schedules on Friday, re-enable on Monday
```

### Extended Hours for Special Events
```bash
# Temporarily extend hours (e.g., demo day)
# Stop at 11 PM instead of 8 PM
az automation schedule update \
  --automation-account-name aa-qca-dev \
  --resource-group rg-qca-dev \
  --name Stop-ContainerApps-8PM-SGT \
  --start-time "2025-11-08T23:00:00+08:00"
```

---

## Monitoring & Alerts

### Create Alert for Failed Automation Jobs
```bash
az monitor metrics alert create \
  --name "Automation-Job-Failed" \
  --resource-group rg-qca-dev \
  --scopes /subscriptions/<sub-id>/resourceGroups/rg-qca-dev/providers/Microsoft.Automation/automationAccounts/aa-qca-dev \
  --condition "count JobStreamCount where JobStatus = 'Failed'" \
  --description "Alert when automation job fails"
```

### View Runbook Execution Logs
1. Azure Portal → Automation Account → aa-qca-dev
2. Jobs → Select job
3. All Logs (see detailed execution output)

---

## Troubleshooting

### Services Don't Start at 8 AM
**Check:**
1. Automation job status: `az automation job list --automation-account-name aa-qca-dev`
2. Managed Identity permissions: Should have Contributor role on RG
3. Schedule enabled: `az automation schedule show --name Start-ContainerApps-8AM-SGT`

**Solution:**
```bash
# Manually trigger start runbook
az automation job create \
  --automation-account-name aa-qca-dev \
  --resource-group rg-qca-dev \
  --runbook-name Start-ContainerApps
```

### Services Still Running After 8 PM
**Check:**
1. Stop job execution logs
2. Container App current replica count

**Solution:**
```bash
# Manually scale down
az containerapp update --name ca-api-qca-dev --resource-group rg-qca-dev --min-replicas 0 --max-replicas 0
az containerapp update --name ca-frontend-qca-dev --resource-group rg-qca-dev --min-replicas 0 --max-replicas 0
az containerapp update --name ca-mcp-qca-dev --resource-group rg-qca-dev --min-replicas 0 --max-replicas 0
```

---

## Production Considerations

**For Production Environment:**
- **Remove scheduled shutdown** (keep 24/7 availability)
- **Keep scale-to-zero** for cost optimization during low traffic
- **Set min_replicas = 1** for critical services (no cold start)
- **Configure alerts** for scaling events and performance

**Example Production Config:**
```hcl
# terraform/environments/prod.tfvars
api_min_replicas = 2  # Always at least 2 instances for HA
api_max_replicas = 10
enable_scheduled_shutdown = false
```

---

## Cost Monitoring

### View Current Month Costs
```bash
az consumption usage list \
  --start-date 2025-11-01 \
  --end-date 2025-11-30 \
  --query "[?contains(instanceName, 'qca')].{Resource:instanceName, Cost:pretaxCost}" \
  --output table
```

### Set Budget Alert
```bash
az consumption budget create \
  --budget-name qca-dev-monthly \
  --amount 50 \
  --time-grain Monthly \
  --start-date 2025-11-01 \
  --end-date 2026-11-01 \
  --resource-group rg-qca-dev
```

---

## Summary

✅ **Automatic optimization:** Scale-to-zero when idle
✅ **Scheduled shutdown:** 8 PM - 8 AM SGT daily
✅ **Cost savings:** ~87.5% reduction
✅ **Manual control:** Start/stop on demand
✅ **Flexible scheduling:** Easily adjust times
✅ **Monitoring:** Job logs and alerts available

For questions or issues, check Automation Account job logs in Azure Portal.
