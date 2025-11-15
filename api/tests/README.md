# AI Task Orchestrator - Test Suite

Automated testing for preventing unnecessary task creation on QUERY intents.

## 🎯 What This Tests

**QUERY Intents** (Should NOT create tasks):
- ❌ "list my controls"
- ❌ "show controls for project 1"
- ❌ "suggest related controls for network security"
- ❌ "what controls do I have"
- ❌ "view my controls"

**ACTION Intents** (Should create tasks):
- ✅ "upload evidence for control 5"
- ✅ "submit evidence for review"
- ✅ "analyze compliance"
- ✅ "generate report"

## 🚀 Quick Start

### Option 1: Run All Tests (Comprehensive)
```bash
cd c:\Users\surface\qa_compliance_assistant
python run_orchestrator_tests.py
```

### Option 2: Quick Validation (Fast)
```bash
python run_orchestrator_tests.py --quick
```

### Option 3: Analyze & Get Fix Suggestions
```bash
python run_orchestrator_tests.py --fix
```

## 📦 Installation

```bash
# Install test dependencies
cd api/tests
pip install -r requirements.txt
```

## 🧪 Run Specific Tests

```bash
# Run only intent detection tests
cd api
python -m pytest tests/test_ai_task_orchestrator.py::TestIntentDetection -v

# Run only task creation tests
python -m pytest tests/test_ai_task_orchestrator.py::TestTaskCreation -v

# Run with coverage report
python -m pytest tests/test_ai_task_orchestrator.py --cov=src/services/ai_task_orchestrator --cov-report=html
```

## 📊 Test Results Interpretation

### ✅ All Tests Pass
```
✅ ALL TESTS PASSED - No unnecessary task creation!
```
**Action:** Safe to deploy

### ❌ Tests Fail
```
❌ SOME TESTS FAILED - Review failures above
```
**Action:** 
1. Review which queries are creating tasks
2. Fix `ai_task_orchestrator.py` 
3. Re-run tests
4. Deploy only after all tests pass

## 🔧 Continuous Integration

Tests automatically run on:
- Every push to `main` or `develop`
- Every pull request
- When `ai_task_orchestrator.py` changes

See `.github/workflows/test_ai_orchestrator.yml`

## 📝 Adding New Test Cases

Edit `api/tests/test_ai_task_orchestrator.py`:

```python
def test_your_new_case(self):
    """Test: Your test description"""
    message = "your user message here"
    intent = self.orchestrator.detect_intent(message, has_file=False)
    assert intent is None, f"Should not create task for query"
```

## 🐛 Current Known Issues

**Issue #1:** "suggest related controls" creates Task #73
- **Test:** `test_suggest_controls_is_query()`
- **Status:** ❌ FAILING
- **Fix:** Add QUERY pattern detection before ACTION patterns

## 🎯 Success Criteria

- [ ] All 15+ query intent tests pass
- [ ] All 5+ action intent tests pass
- [ ] Zero false positives (queries creating tasks)
- [ ] Zero false negatives (actions not creating tasks)

## 📞 Support

If tests fail after deployment, check:
1. Test output for specific failures
2. User message patterns causing issues
3. `ai_task_orchestrator.py` changes since last passing test
