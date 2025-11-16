# AI Bug Testing - Comprehensive Test Suite

## Overview

This directory contains comprehensive automated test suites for all 4 critical AI bugs identified in the QA Compliance Assistant system.

## Test Files

### 1. **test_unnecessary_task_creation.py** (Issue #1)
**Bug**: AI creates tasks for query intents (list, show, suggest) instead of just answering

**Test Coverage**:
- ✅ 20 test cases covering query vs action intent detection
- Tests for: list, show, suggest, view, what, which, display (7 query verbs)
- Tests for: upload, add, submit, attach, analyze (5 action verbs)
- Edge cases: mixed keywords, file uploads, empty messages
- Real scenario reproduction: Task #73 ("suggest related controls")

**Current Status**: 19/20 passing (1 bug: "view evidence" incorrectly creates task)

**Run Command**:
```powershell
.\quick_test.ps1
# OR
pytest tests\test_unnecessary_task_creation.py -v
```

---

### 2. **test_timestamp_display.py** (Issue #2)
**Bug**: Timestamps show UTC time with SGT label (06:38 am SGT when actually 02:38 pm SGT)

**Test Coverage**:
- ✅ 25+ test cases covering UTC to SGT conversion
- Conversion accuracy (8-hour offset)
- Date boundary crossing (UTC 23:00 → next day SGT)
- Format validation (12-hour with AM/PM + SGT label)
- Real scenario: Task #73 screenshot timestamp reproduction
- Edge cases: null timestamps, invalid formats, leap years

**Test Classes**:
1. `TestTimestampConversion` - UTC+8 math validation
2. `TestTimestampFormatting` - Display format with correct SGT labels
3. `TestBackendTimestampStorage` - Backend UTC storage verification
4. `TestChatMessageTimestamps` - Chat UI timestamp display
5. `TestEdgeCases` - Null, invalid, far future/past dates
6. `TestRealWorldScenarios` - Screenshot bug reproduction

**Run Command**:
```powershell
pytest tests\test_timestamp_display.py -v
```

---

### 3. **test_evidence_id_hallucination.py** (Issue #3)
**Bug**: AI makes up evidence IDs (uploaded #21, tried to submit #48 which doesn't exist)

**Test Coverage**:
- ✅ 25+ test cases covering evidence ID retention
- ID extraction from tool results (upload_evidence, request_evidence_upload)
- Context retention across conversation turns
- Type validation (integer, not string)
- Database existence validation
- Real scenario: Evidence #21 → #48 hallucination reproduction

**Test Classes**:
1. `TestEvidenceIDRetention` - ID extraction and memory
2. `TestEvidenceIDValidation` - Database existence checks
3. `TestToolResultParsing` - Parse evidence_id from tool outputs
4. `TestConversationContextRetention` - Multi-turn conversation tracking
5. `TestRealWorldScenarios` - Screenshot bug reproduction
6. `TestErrorHandling` - Non-existent IDs, wrong agency access

**Run Command**:
```powershell
pytest tests\test_evidence_id_hallucination.py -v
```

---

### 4. **test_cold_start_login.py** (Issue #4)
**Bug**: First login always fails, second attempt succeeds (cold start DB connection issue)

**Test Coverage**:
- ✅ 20+ test cases covering cold start scenarios
- Database connection pool initialization
- Health check with DB validation
- Startup event sequencing
- Azure Container Apps scale-to-zero behavior
- Retry logic with exponential backoff

**Test Classes**:
1. `TestDatabaseConnectionInitialization` - Startup DB warmup
2. `TestFirstLoginAfterColdStart` - Login attempts after scale-up
3. `TestConnectionPoolWarmup` - Pool configuration and pre-ping
4. `TestContainerScaleToZeroScenario` - Azure-specific cold start
5. `TestLoginRetryBehavior` - Auto-retry and user experience
6. `TestDatabaseHealthMonitoring` - Metrics and alerting
7. `TestRealWorldScenarios` - Monday morning, weekend scenarios

**Run Command**:
```powershell
pytest tests\test_cold_start_login.py -v
```

---

## Quick Start

### Run All Tests
```powershell
.\run_all_tests.ps1
```

This will:
1. Install test dependencies (pytest, pytest-asyncio, pytest-mock)
2. Run all 4 test suites sequentially
3. Display summary of pass/fail for each issue
4. Exit with status code 0 if all pass, 1 if any fail

### Run Individual Test Suite
```powershell
# Issue #1 only
pytest tests\test_unnecessary_task_creation.py -v

# Issue #2 only
pytest tests\test_timestamp_display.py -v

# Issue #3 only
pytest tests\test_evidence_id_hallucination.py -v

# Issue #4 only
pytest tests\test_cold_start_login.py -v
```

### Run Specific Test
```powershell
# Example: Run only the Task #73 scenario test
pytest tests\test_unnecessary_task_creation.py::TestUnnecessaryTaskCreation::test_real_scenario_task_73 -v
```

---

## Test Dependencies

**Required Python Packages**:
- `pytest >= 7.4.0` - Test framework
- `pytest-asyncio >= 0.21.0` - Async test support
- `pytest-mock >= 3.15.0` - Mocking support
- `pytest-cov >= 4.1.0` - Coverage reporting (optional)

**Installation**:
```powershell
pip install pytest pytest-asyncio pytest-mock pytest-cov
```

---

## Test Results Summary

| Issue | Test File | Total Tests | Status | Notes |
|-------|-----------|-------------|--------|-------|
| #1: Unnecessary Tasks | `test_unnecessary_task_creation.py` | 20 | 19/20 ✅ | 1 bug: "view evidence" |
| #2: Timestamps | `test_timestamp_display.py` | 25+ | ⏳ Not Run | Ready to test |
| #3: Evidence ID | `test_evidence_id_hallucination.py` | 25+ | ⏳ Not Run | Ready to test |
| #4: Cold Start Login | `test_cold_start_login.py` | 20+ | ⏳ Not Run | Ready to test |

---

## CI/CD Integration

A GitHub Actions workflow is available at `.github/workflows/test_ai_orchestrator.yml` to run tests on every push/PR.

**Workflow Features**:
- Runs on Python 3.12
- Installs dependencies automatically
- Runs all test suites
- Generates coverage report
- Fails CI if any tests fail

**Trigger Workflow**:
```bash
git add tests/
git commit -m "Add comprehensive test suites for all 4 AI bugs"
git push
```

---

## Test Design Philosophy

### 1. **Unit Tests First**
- Test individual functions and methods in isolation
- Use mocks for database, external services
- Fast execution (< 2 seconds per suite)

### 2. **Real Scenario Reproduction**
- Each test suite includes tests that reproduce exact user scenarios from bug reports
- Example: `test_real_scenario_task_73` reproduces Task #73 creation bug

### 3. **Edge Case Coverage**
- Null/empty values
- Invalid inputs
- Boundary conditions
- Date/time edge cases

### 4. **Integration Tests**
- Full workflow tests with mock database
- Multi-step conversation flows
- Tool calling sequences

---

## Maintenance Guide

### Adding New Tests

1. **Identify the Bug/Feature**
   - Write clear test name: `test_[scenario]_should_[expected_behavior]`
   - Add docstring explaining what is tested

2. **Create Test**
   ```python
   def test_new_scenario(self, orchestrator):
       """Test: Description of what should happen"""
       result = orchestrator.some_method("input")
       assert result == expected_value
   ```

3. **Run Test**
   ```powershell
   pytest tests/test_file.py::TestClass::test_new_scenario -v
   ```

### Debugging Failed Tests

1. **Run with verbose output**:
   ```powershell
   pytest tests/test_file.py -vv --tb=long
   ```

2. **Run single test**:
   ```powershell
   pytest tests/test_file.py::TestClass::test_name -v
   ```

3. **Add print debugging**:
   ```python
   def test_something(self):
       result = function_under_test()
       print(f"DEBUG: result = {result}")
       assert result == expected
   ```

---

## Next Steps

### 1. **Run All Tests**
```powershell
.\run_all_tests.ps1
```

### 2. **Fix Identified Bugs**
- Issue #1: Fix "view evidence" query intent detection
- Issue #2: Fix timezone conversion in frontend
- Issue #3: Add evidence ID retention in AI prompt
- Issue #4: Add startup event to initialize DB connection pool

### 3. **Re-run Tests After Fixes**
All tests should pass (100%) after fixes deployed

### 4. **Deploy to Production**
Once all tests pass:
```bash
# Build and deploy
az acr build --registry acrqcadev2f37g0 --image api:latest --file api/Dockerfile api
az containerapp update --name ca-api-qca-dev --resource-group rg-qca-dev --image acrqcadev2f37g0.azurecr.io/api:latest
```

---

## Support

For questions or issues with tests:
1. Check test output for detailed error messages
2. Review test code comments for context
3. Run with `-vv --tb=long` for full debugging output
4. Check `TEST_AUTOMATION_SUMMARY.md` for Issue #1 details

---

## Test Coverage Goals

- **Current**: ~90 total test cases across 4 issues
- **Target**: 100% coverage of identified bugs
- **Future**: Add tests for:
  - Permission/RBAC validation
  - File upload workflows
  - IM8 assessment parsing
  - Report generation
  - Multi-user concurrent access
