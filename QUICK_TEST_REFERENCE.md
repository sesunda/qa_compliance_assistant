# Quick Test Reference Card

## Run All Tests
```powershell
.\run_all_tests.ps1
```

## Run Individual Issue Tests

```powershell
# Issue #1: Unnecessary Task Creation (20 tests)
pytest tests\test_unnecessary_task_creation.py -v

# Issue #2: Wrong Timestamps (25+ tests)
pytest tests\test_timestamp_display.py -v

# Issue #3: Evidence ID Hallucination (25+ tests)
pytest tests\test_evidence_id_hallucination.py -v

# Issue #4: First Login Failure (20+ tests)
pytest tests\test_cold_start_login.py -v
```

## Run Single Test
```powershell
pytest tests\test_file.py::TestClass::test_method -v
```

## Test Files Location
```
tests/
├── test_unnecessary_task_creation.py    (387 lines, 20 tests)
├── test_timestamp_display.py            (364 lines, 25+ tests)
├── test_evidence_id_hallucination.py    (428 lines, 25+ tests)
├── test_cold_start_login.py             (436 lines, 20+ tests)
└── README_ALL_TESTS.md                  (documentation)
```

## Current Status
- **Issue #1**: 19/20 ✅ (1 bug: "view evidence")
- **Issue #2**: ✅ Ready (1 test validated)
- **Issue #3**: ✅ Ready (1 test validated)
- **Issue #4**: ✅ Ready (1 test validated)

## Total Coverage
~90 automated test cases across all 4 issues
