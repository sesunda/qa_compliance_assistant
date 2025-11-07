# Azure Deployment Access Guide

## 🌐 Application URLs

### Frontend Application
**URL**: Check Azure Portal for the actual URL  
**Resource**: `ca-frontend-qca-dev`  
**Location**: East US  

To get the URL:
```bash
az containerapp show \
  --name ca-frontend-qca-dev \
  --resource-group rg-qca-dev \
  --query "properties.configuration.ingress.fqdn" \
  -o tsv
```

### API Service
**URL**: Check Azure Portal for the actual URL  
**Resource**: `ca-api-qca-dev`  
**Location**: East US

To get the URL:
```bash
az containerapp show \
  --name ca-api-qca-dev \
  --resource-group rg-qca-dev \
  --query "properties.configuration.ingress.fqdn" \
  -o tsv
```

### API Documentation
Once you have the API URL:
- **Swagger UI**: `https://<API_URL>/docs`
- **ReDoc**: `https://<API_URL>/redoc`

---

## 🔑 Login Credentials

### Default Admin Account
**Username**: `admin`  
**Password**: `admin123`  
**Role**: Administrator (full access)

### Test Analyst Account
**Username**: `analyst`  
**Password**: `analyst123`  
**Role**: Analyst (read/write access)

### Test Auditor Account
**Username**: `auditor`  
**Password**: `auditor123`  
**Role**: Auditor (read-only access)

---

## 🧪 Testing Workflow

### 1. Access the Application

1. Get the frontend URL from Azure Portal or CLI
2. Open browser and navigate to the URL
3. Login with admin credentials

### 2. Create Assessment Workflow

**Step 1: Create Assessment**
1. Navigate to **Assessments** page
2. Click **"Create Assessment"** button
3. Fill in the form:
   - **Title**: "Q4 2025 SOC 2 Assessment"
   - **Description**: "Quarterly SOC 2 Type II compliance assessment"
   - **Framework**: "soc2"
   - **Start Date**: Current date
   - **End Date**: 30 days from now
   - **Assigned To**: Select user
4. Click **"Create"**

**Step 2: View Assessment Details**
1. Click on the newly created assessment
2. Verify all details are displayed correctly
3. Check progress bar (should be 0%)
4. Note the assessment ID for later use

**Step 3: Update Progress**
1. Click **"Update Progress"** button
2. Move slider to 25%
3. Click **"Update"**
4. Verify progress bar updates

### 3. Create and Manage Findings

**Step 1: Create Finding**
1. Navigate to **Findings** page
2. Click **"Add Finding"** button
3. Fill in the form:
   - **Title**: "Unencrypted Data Transmission Detected"
   - **Description**: "Application transmits sensitive data without TLS encryption"
   - **Severity**: "critical"
   - **Priority**: "high"
   - **Assessment**: Select the assessment created earlier
   - **Control**: Select a control (optional)
   - **Recommendation**: "Implement TLS 1.3 for all API communications"
4. Click **"Create"**

**Step 2: Assign Finding**
1. Click on the finding to open details
2. Click **"Assign"** button
3. Select an analyst from the dropdown
4. Click **"Assign"**
5. Verify finding shows as assigned

**Step 3: Update Status to In Progress**
1. In the finding detail page, note the status chip
2. Click **"Move to In Progress"** button
3. Verify status changes from "open" to "in_progress"

**Step 4: Add Comments**
1. Scroll to the Comments section
2. Click **"Add Comment"** button
3. Type: "Investigating TLS configuration across all services"
4. Click **"Post Comment"**
5. Verify comment appears in the thread

**Step 5: Resolve Finding**
1. Click **"Resolve"** button
2. Fill in resolution notes:
   ```
   Implemented TLS 1.3 across all API endpoints.
   - Updated nginx configuration
   - Validated with SSL Labs scan (A+ rating)
   - Updated documentation
   ```
3. Click **"Resolve"**
4. Verify status changes to "resolved"

### 4. QA Review Workflow

**Step 1: Navigate to QA Review**
1. Click **"QA Review"** in the navigation menu
2. View statistics dashboard:
   - Pending findings count
   - Critical findings count
   - High priority count
   - Overdue findings count

**Step 2: Validate Finding**
1. Locate the resolved finding in the table
2. Note the "Days in Review" column
3. Click **"Validate"** button
4. Review the resolution notes displayed

**Step 3: Approve Finding**
1. In the validation dialog, select **"Approve Resolution"**
2. Add validation notes:
   ```
   Resolution verified and approved:
   - TLS 1.3 configuration confirmed in production
   - SSL Labs scan results reviewed
   - All requirements satisfied
   ```
3. Click **"Approve & Close"**
4. Verify finding status changes to "validated"

**Alternative: Reject Finding**
1. Select **"Reject Resolution"**
2. Add validation notes explaining why:
   ```
   Resolution incomplete:
   - TLS not enabled on legacy API endpoints
   - Need evidence of certificate renewal process
   - Documentation missing deployment steps
   ```
3. Click **"Reject & Reopen"**
4. Verify finding returns to "in_progress" status

### 5. Test Remediation Tracking

**Step 1: View Remediation Progress**
1. Navigate to an assessment detail page
2. Scroll to the **Remediation Tracker** component
3. Verify:
   - Overall progress percentage
   - Status breakdown (open, in progress, resolved)
   - Critical findings alert
   - Overdue findings alert

**Step 2: Navigate from Tracker**
1. Click on a finding in any status group
2. Verify navigation to finding detail page

### 6. Test Workload View

**Step 1: View Personal Workload**
1. Navigate to **Dashboard** page
2. Locate the **Workload View** component
3. Verify display of:
   - Capacity utilization percentage
   - Urgency breakdown (overdue, due soon, on track)
   - Active assessments count
   - Open findings count

**Step 2: Interpret Workload Data**
- **Green (< 70%)**: Capacity available
- **Yellow (70-90%)**: Near capacity
- **Red (> 90%)**: Over capacity

### 7. Test Control Testing

**Step 1: Navigate to Controls**
1. Go to **Controls** page
2. Select a control from the list
3. Click **"Test Control"** button

**Step 2: Record Test Result**
1. In the testing dialog:
   - **Test Result**: Select "Pass" or "Fail"
   - **Evidence**: Upload a file (optional)
   - **Notes**: "Verified access controls working as expected"
2. Click **"Submit Test Result"**
3. Verify test result recorded

### 8. Test Dashboard Metrics

**Step 1: View Dashboard**
1. Navigate to **Dashboard** page
2. Verify real-time statistics:
   - Active assessments count
   - Open findings count
   - Critical findings count
   - Overdue items count

**Step 2: Quick Actions**
1. Try quick action buttons:
   - Create Assessment
   - Create Finding
   - View Reports
2. Verify navigation works correctly

---

## 🔍 Troubleshooting

### Frontend Not Loading
**Check**:
```bash
# Get frontend logs
az containerapp logs show \
  --name ca-frontend-qca-dev \
  --resource-group rg-qca-dev \
  --tail 50
```

**Common Issues**:
- Container not running: Check replica count
- Build failure: Check GitHub Actions logs
- Environment variables missing: Check container app configuration

### API Errors
**Check**:
```bash
# Get API logs
az containerapp logs show \
  --name ca-api-qca-dev \
  --resource-group rg-qca-dev \
  --tail 100
```

**Common Issues**:
- Database connection: Check PostgreSQL connection string
- Migration not applied: Check startup.sh logs
- Authentication errors: Verify JWT secret configured

### Database Migration Issues
**Check**:
```bash
# Look for migration logs
az containerapp logs show \
  --name ca-api-qca-dev \
  --resource-group rg-qca-dev \
  --tail 200 | grep -E "(alembic|migration|Running upgrade)"
```

**Expected Output**:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade 009 -> 010, add assessment workflow tables
```

### Login Issues
**Default Credentials**:
- Username: `admin`
- Password: `admin123`

**Reset Password** (if needed):
```bash
# Connect to API container and run seed script
az containerapp exec \
  --name ca-api-qca-dev \
  --resource-group rg-qca-dev \
  --command "python /app/api/scripts/seed_auth.py"
```

---

## 📊 Verification Checklist

### ✅ Phase 3 Features to Verify

**Assessment Management**:
- [ ] Create new assessment
- [ ] View assessment list with filters
- [ ] Update assessment details
- [ ] Update progress percentage
- [ ] Mark assessment as complete
- [ ] Delete assessment

**Finding Management**:
- [ ] Create new finding
- [ ] View finding list with filters (severity, status, priority)
- [ ] Assign finding to user
- [ ] Update finding status
- [ ] Add comments to finding
- [ ] Resolve finding with notes
- [ ] Mark finding as false positive

**QA Review**:
- [ ] View pending findings dashboard
- [ ] Filter findings by severity/priority
- [ ] Validate resolved finding (approve)
- [ ] Reject finding with feedback
- [ ] View validation statistics

**Remediation Tracking**:
- [ ] View overall progress bar
- [ ] See status breakdown
- [ ] View critical findings alert
- [ ] View overdue findings alert
- [ ] Navigate to findings from tracker

**Workload View**:
- [ ] View capacity utilization
- [ ] See urgency breakdown
- [ ] View overdue count
- [ ] View due soon count
- [ ] See workload recommendations

**Control Testing**:
- [ ] Open test dialog
- [ ] Upload evidence
- [ ] Record test result
- [ ] Add testing notes
- [ ] Submit test result

**Dashboard**:
- [ ] View real-time metrics
- [ ] See active assessments count
- [ ] See open findings count
- [ ] View recent activity
- [ ] Use quick action buttons

---

## 🎯 Success Criteria

**Phase 3 is successful if**:
1. ✅ All pages load without errors
2. ✅ Assessment workflow works end-to-end
3. ✅ Finding lifecycle completes (create → assign → resolve → validate)
4. ✅ QA review can approve/reject findings
5. ✅ Remediation tracker shows accurate progress
6. ✅ Workload view displays user capacity
7. ✅ Control testing records results
8. ✅ Dashboard displays real-time metrics
9. ✅ Navigation works between all pages
10. ✅ All CRUD operations function correctly

---

## 📞 Support

**Issues Found?**
1. Document the error message
2. Check browser console for errors (F12)
3. Check API response in Network tab
4. Check container logs (commands above)
5. Report issue with full context

**Next Steps After Testing**:
Once Phase 3 testing is complete, we'll proceed to:
- **Phase 4**: Business Logic Services (risk scoring, SLA tracking, validation)
- **Phase 5**: AI Integration (analysis, PDF reports, notifications)
- **Phase 6**: Comprehensive testing and documentation

---

**Last Updated**: November 7, 2025  
**Deployment**: commit bafb3bc  
**Status**: Ready for Testing
