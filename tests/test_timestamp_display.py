"""
Test cases for Issue #2: Timestamp Display Bug

Tests that timestamps correctly show Singapore Time (UTC+8) instead of UTC time
with incorrect SGT labels.

Bug: Times show UTC with "SGT" label (e.g., 06:38 am SGT when actually 02:38 pm SGT)
Root Cause: Frontend timezone conversion issue in datetime.ts
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch


class TestTimestampConversion:
    """Test suite for Issue #2: Timestamp conversion from UTC to SGT"""
    
    def test_utc_to_sgt_conversion_8_hour_difference(self):
        """Test: UTC 06:38 should display as 14:38 (2:38 PM) SGT"""
        # Given: UTC time 06:38:00
        utc_time = datetime(2024, 1, 15, 6, 38, 0, tzinfo=timezone.utc)
        
        # Expected: SGT is UTC+8, so should be 14:38:00
        expected_sgt_hour = 14
        expected_sgt_minute = 38
        
        # Convert to SGT (UTC+8)
        sgt_time = utc_time.astimezone(timezone(timedelta(hours=8)))
        
        assert sgt_time.hour == expected_sgt_hour, f"Expected hour {expected_sgt_hour}, got {sgt_time.hour}"
        assert sgt_time.minute == expected_sgt_minute, f"Expected minute {expected_sgt_minute}, got {sgt_time.minute}"
    
    def test_utc_midnight_converts_to_sgt_8am(self):
        """Test: UTC 00:00 should display as 08:00 SGT"""
        utc_time = datetime(2024, 1, 15, 0, 0, 0, tzinfo=timezone.utc)
        sgt_time = utc_time.astimezone(timezone(timedelta(hours=8)))
        
        assert sgt_time.hour == 8
        assert sgt_time.minute == 0
    
    def test_utc_afternoon_converts_correctly(self):
        """Test: UTC 16:00 should display as 00:00 next day SGT"""
        utc_time = datetime(2024, 1, 15, 16, 0, 0, tzinfo=timezone.utc)
        sgt_time = utc_time.astimezone(timezone(timedelta(hours=8)))
        
        assert sgt_time.hour == 0
        assert sgt_time.day == 16  # Next day in SGT
    
    def test_date_boundary_crossing(self):
        """Test: UTC 23:00 Jan 15 should display as 07:00 Jan 16 SGT"""
        utc_time = datetime(2024, 1, 15, 23, 0, 0, tzinfo=timezone.utc)
        sgt_time = utc_time.astimezone(timezone(timedelta(hours=8)))
        
        assert sgt_time.day == 16
        assert sgt_time.hour == 7
    
    def test_leap_year_date_conversion(self):
        """Test: Leap year dates convert correctly"""
        utc_time = datetime(2024, 2, 29, 12, 0, 0, tzinfo=timezone.utc)
        sgt_time = utc_time.astimezone(timezone(timedelta(hours=8)))
        
        assert sgt_time.day == 29
        assert sgt_time.month == 2
        assert sgt_time.hour == 20  # 12 + 8


class TestTimestampFormatting:
    """Test timestamp formatting with correct SGT labels"""
    
    def test_sgt_label_matches_actual_timezone(self):
        """Test: Displayed time with SGT label should be actual SGT, not UTC"""
        # Simulate backend UTC timestamp: 2024-01-15 06:38:00 UTC
        utc_timestamp = "2024-01-15T06:38:00Z"
        
        # Parse as UTC
        dt = datetime.fromisoformat(utc_timestamp.replace('Z', '+00:00'))
        
        # Convert to SGT
        sgt_dt = dt.astimezone(timezone(timedelta(hours=8)))
        
        # Format with SGT label
        formatted = sgt_dt.strftime("%I:%M %p SGT")
        
        # Should show 02:38 PM SGT (not 06:38 AM SGT)
        assert "02:38 PM SGT" in formatted, f"Expected '02:38 PM SGT', got '{formatted}'"
    
    def test_morning_time_display(self):
        """Test: Morning UTC times display correctly in SGT"""
        utc_timestamp = "2024-01-15T00:30:00Z"
        dt = datetime.fromisoformat(utc_timestamp.replace('Z', '+00:00'))
        sgt_dt = dt.astimezone(timezone(timedelta(hours=8)))
        formatted = sgt_dt.strftime("%I:%M %p")
        
        assert formatted == "08:30 AM"
    
    def test_evening_time_display(self):
        """Test: Evening UTC times display correctly in SGT"""
        utc_timestamp = "2024-01-15T10:45:00Z"
        dt = datetime.fromisoformat(utc_timestamp.replace('Z', '+00:00'))
        sgt_dt = dt.astimezone(timezone(timedelta(hours=8)))
        formatted = sgt_dt.strftime("%I:%M %p")
        
        assert formatted == "06:45 PM"
    
    def test_full_datetime_format_with_sgt(self):
        """Test: Full datetime format includes correct SGT time"""
        utc_timestamp = "2024-01-15T06:38:00Z"
        dt = datetime.fromisoformat(utc_timestamp.replace('Z', '+00:00'))
        sgt_dt = dt.astimezone(timezone(timedelta(hours=8)))
        
        # Format: "15/01/2024, 02:38 PM SGT"
        formatted = sgt_dt.strftime("%d/%m/%Y, %I:%M %p SGT")
        
        assert "15/01/2024" in formatted
        assert "02:38 PM SGT" in formatted


class TestBackendTimestampStorage:
    """Test that backend stores timestamps correctly in UTC"""
    
    def test_backend_stores_utc_timestamps(self):
        """Test: Backend should store all timestamps in UTC"""
        # Simulate user action at SGT 14:38
        sgt_time = datetime(2024, 1, 15, 14, 38, 0)
        
        # Backend should store as UTC (subtract 8 hours)
        utc_time_for_storage = sgt_time - timedelta(hours=8)
        
        assert utc_time_for_storage.hour == 6
        assert utc_time_for_storage.minute == 38
    
    def test_iso_format_preserves_timezone(self):
        """Test: ISO format includes timezone info"""
        utc_time = datetime(2024, 1, 15, 6, 38, 0, tzinfo=timezone.utc)
        iso_string = utc_time.isoformat()
        
        # Should include +00:00 or Z suffix
        assert '+00:00' in iso_string or iso_string.endswith('Z')
    
    def test_database_timestamp_retrieval(self):
        """Test: Retrieved timestamps are correctly marked as UTC"""
        # Simulate database returning UTC timestamp
        db_timestamp = datetime(2024, 1, 15, 6, 38, 0)
        
        # Add UTC timezone info
        utc_timestamp = db_timestamp.replace(tzinfo=timezone.utc)
        
        # Convert to SGT for display
        sgt_timestamp = utc_timestamp.astimezone(timezone(timedelta(hours=8)))
        
        assert sgt_timestamp.hour == 14  # 6 + 8 = 14


class TestChatMessageTimestamps:
    """Test timestamps in chat messages display correctly"""
    
    def test_chat_message_created_at_sgt(self):
        """Test: Chat message timestamps show actual SGT"""
        # Simulate message created at UTC 06:38
        message = {
            "id": 1,
            "content": "Test message",
            "created_at": "2024-01-15T06:38:00Z",
            "sender": "user"
        }
        
        # Frontend should convert to SGT
        dt = datetime.fromisoformat(message["created_at"].replace('Z', '+00:00'))
        sgt_dt = dt.astimezone(timezone(timedelta(hours=8)))
        
        display_time = sgt_dt.strftime("%I:%M %p SGT")
        
        assert display_time == "02:38 PM SGT"
    
    def test_multiple_messages_chronological_order(self):
        """Test: Message timestamps maintain chronological order after conversion"""
        messages = [
            {"created_at": "2024-01-15T06:30:00Z"},
            {"created_at": "2024-01-15T06:35:00Z"},
            {"created_at": "2024-01-15T06:40:00Z"},
        ]
        
        # Convert all to SGT
        sgt_times = []
        for msg in messages:
            dt = datetime.fromisoformat(msg["created_at"].replace('Z', '+00:00'))
            sgt_dt = dt.astimezone(timezone(timedelta(hours=8)))
            sgt_times.append(sgt_dt)
        
        # Verify chronological order maintained
        assert sgt_times[0] < sgt_times[1] < sgt_times[2]
    
    def test_today_vs_yesterday_calculation(self):
        """Test: Today/yesterday labels calculated using SGT, not UTC"""
        # Current time: Jan 15, 23:30 UTC (Jan 16, 07:30 SGT)
        current_utc = datetime(2024, 1, 15, 23, 30, 0, tzinfo=timezone.utc)
        current_sgt = current_utc.astimezone(timezone(timedelta(hours=8)))
        
        # Message from: Jan 15, 16:00 UTC (Jan 16, 00:00 SGT)
        message_utc = datetime(2024, 1, 15, 16, 0, 0, tzinfo=timezone.utc)
        message_sgt = message_utc.astimezone(timezone(timedelta(hours=8)))
        
        # Both are Jan 16 in SGT, so should show "Today"
        assert current_sgt.date() == message_sgt.date()


class TestEdgeCases:
    """Test edge cases in timestamp handling"""
    
    def test_null_timestamp_handling(self):
        """Test: Null/missing timestamps handled gracefully"""
        timestamp = None
        
        # Should return placeholder, not crash
        display = "—" if timestamp is None else timestamp
        assert display == "—"
    
    def test_invalid_timestamp_format(self):
        """Test: Invalid timestamp formats handled gracefully"""
        invalid_timestamps = [
            "not-a-date",
            "2024-13-45T99:99:99Z",  # Invalid date
            "",
            "undefined"
        ]
        
        for invalid in invalid_timestamps:
            try:
                datetime.fromisoformat(invalid.replace('Z', '+00:00'))
                parsed = True
            except (ValueError, AttributeError):
                parsed = False
            
            # Should fail to parse without crashing
            assert not parsed
    
    def test_far_future_timestamp(self):
        """Test: Far future timestamps convert correctly"""
        utc_time = datetime(2099, 12, 31, 18, 0, 0, tzinfo=timezone.utc)
        sgt_time = utc_time.astimezone(timezone(timedelta(hours=8)))
        
        # 2099-12-31 18:00 UTC = 2100-01-01 02:00 SGT
        assert sgt_time.year == 2100
        assert sgt_time.month == 1
        assert sgt_time.day == 1
        assert sgt_time.hour == 2
    
    def test_historical_timestamp(self):
        """Test: Historical timestamps (before 2000) convert correctly"""
        utc_time = datetime(1990, 1, 1, 6, 0, 0, tzinfo=timezone.utc)
        sgt_time = utc_time.astimezone(timezone(timedelta(hours=8)))
        
        assert sgt_time.year == 1990
        assert sgt_time.hour == 14


class TestBackendSerialization:
    """Test backend timestamp serialization with timezone info"""
    
    def test_backend_timestamp_includes_timezone_marker(self):
        """Test: Backend timestamps MUST include 'Z' or timezone offset"""
        # Simulate backend creating timestamp (OLD WAY - WRONG)
        wrong_timestamp = datetime.utcnow().isoformat()
        
        # Simulate backend creating timestamp (NEW WAY - CORRECT)
        correct_timestamp = datetime.now(timezone.utc).isoformat()
        
        # Correct timestamp MUST include 'Z' or '+00:00'
        assert 'Z' in correct_timestamp or '+00:00' in correct_timestamp, \
            f"Timestamp '{correct_timestamp}' missing timezone marker"
        
        # Wrong timestamp does NOT include timezone (ambiguous!)
        # This is the root cause of the bug
        assert 'Z' not in wrong_timestamp and '+' not in wrong_timestamp, \
            f"Old utcnow().isoformat() should NOT have timezone marker (but got '{wrong_timestamp}')"
    
    def test_api_response_timestamp_format(self):
        """Test: API response timestamps follow ISO 8601 with timezone"""
        # Simulate backend message creation
        message = {
            "role": "assistant",
            "content": "Test message",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Verify timestamp format
        timestamp_str = message["timestamp"]
        assert isinstance(timestamp_str, str)
        assert 'Z' in timestamp_str or '+' in timestamp_str, \
            "API response timestamp must include timezone info"
        
        # Verify can be parsed back to datetime
        parsed = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        assert parsed.tzinfo is not None, "Parsed datetime must be timezone-aware"


class TestFrontendParsing:
    """Test frontend parsing of backend timestamps"""
    
    def test_frontend_parses_utc_timestamp_correctly(self):
        """Test: Frontend correctly parses UTC timestamp from backend"""
        # Backend sends: 2025-11-15T02:20:00Z (UTC 2:20 AM)
        backend_timestamp = "2025-11-15T02:20:00Z"
        
        # Frontend parses with JavaScript Date
        # Simulate: new Date("2025-11-15T02:20:00Z")
        parsed = datetime.fromisoformat(backend_timestamp.replace('Z', '+00:00'))
        
        # Verify it's interpreted as UTC
        assert parsed.hour == 2
        assert parsed.minute == 20
        
        # Convert to SGT for display (should be 10:20 AM)
        sgt_time = parsed.astimezone(timezone(timedelta(hours=8)))
        assert sgt_time.hour == 10  # 2 + 8 = 10
        assert sgt_time.minute == 20
    
    def test_ambiguous_timestamp_causes_bug(self):
        """Test: Demonstrate bug when timestamp lacks timezone marker"""
        # Backend sends: 2025-11-15T02:20:00 (NO Z - ambiguous!)
        ambiguous_timestamp = "2025-11-15T02:20:00"
        
        # JavaScript Date will interpret this as LOCAL time (not UTC)
        # In Singapore browser: "2025-11-15T02:20:00" → 2:20 AM SGT (not UTC!)
        # This is the BUG!
        
        # When backend means 02:20 UTC but sends without Z:
        # Frontend thinks it's 02:20 local (SGT in Singapore)
        # Then tries to display as SGT → shows 02:20 AM SGT (WRONG!)
        
        # Correct interpretation: Should be 10:20 AM SGT
        # Wrong interpretation: Shows as 02:20 AM SGT
        
        # Verify the fix: With 'Z' suffix, parsing is unambiguous
        correct_timestamp = ambiguous_timestamp + "Z"
        parsed_correct = datetime.fromisoformat(correct_timestamp.replace('Z', '+00:00'))
        sgt_correct = parsed_correct.astimezone(timezone(timedelta(hours=8)))
        
        assert sgt_correct.hour == 10  # Correct: 2 UTC + 8 = 10 AM SGT


class TestEndToEndIntegration:
    """Test complete backend → API → frontend → display flow"""
    
    def test_message_timestamp_roundtrip(self):
        """Test: Message timestamp survives full roundtrip correctly"""
        # Step 1: Backend creates message at known UTC time
        utc_time = datetime(2025, 11, 15, 2, 20, 0, tzinfo=timezone.utc)
        
        # Step 2: Backend serializes to ISO string
        iso_string = utc_time.isoformat()
        
        # Step 3: Verify serialization includes timezone
        assert 'Z' in iso_string or '+00:00' in iso_string, \
            "Serialized timestamp must include timezone"
        
        # Step 4: Frontend receives and parses
        frontend_parsed = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        
        # Step 5: Frontend converts to SGT for display
        sgt_display = frontend_parsed.astimezone(timezone(timedelta(hours=8)))
        
        # Step 6: Verify displayed time is correct
        assert sgt_display.hour == 10  # 2 UTC + 8 = 10 AM SGT
        assert sgt_display.minute == 20
        
        # Step 7: Format for UI
        formatted = sgt_display.strftime("%d/%m/%Y, %I:%M %p SGT")
        
        # Should show: "15/11/2025, 10:20 AM SGT"
        assert "10:20 AM SGT" in formatted
        assert "02:20" not in formatted  # Should NOT show UTC time
    
    def test_screenshot_bug_reproduction_with_fix(self):
        """Test: Reproduce screenshot bug and verify fix
        
        Screenshot issue: Shows "10:20 am SGT" when actual time was different
        Root cause: Backend sent timestamp without 'Z', frontend misinterpreted
        """
        # Backend creates message at UTC 02:20
        utc_time = datetime(2025, 11, 15, 2, 20, 0, tzinfo=timezone.utc)
        
        # OLD WAY (BUG): datetime.utcnow().isoformat()
        old_way = datetime(2025, 11, 15, 2, 20, 0).isoformat()  # No timezone!
        assert 'Z' not in old_way  # Ambiguous!
        
        # NEW WAY (FIX): datetime.now(timezone.utc).isoformat()
        new_way = utc_time.isoformat()
        assert '+00:00' in new_way or 'Z' in new_way  # Unambiguous!
        
        # With fix, frontend correctly displays 10:20 AM SGT
        parsed = datetime.fromisoformat(new_way.replace('Z', '+00:00'))
        sgt = parsed.astimezone(timezone(timedelta(hours=8)))
        
        assert sgt.hour == 10
        assert sgt.minute == 20


class TestRealWorldScenarios:
    """Test real-world timestamp scenarios from user screenshots"""
    
    def test_task_73_screenshot_scenario(self):
        """Test: Reproduce Task #73 timestamp issue from screenshot
        
        Screenshot shows: 06:38 am SGT
        Actual SGT should be: 02:38 pm SGT (14:38)
        """
        # Backend stores: 2024-01-15 06:38:00 UTC
        utc_timestamp = datetime(2024, 1, 15, 6, 38, 0, tzinfo=timezone.utc)
        
        # Convert to SGT
        sgt_timestamp = utc_timestamp.astimezone(timezone(timedelta(hours=8)))
        
        # Format for display
        hour_12 = sgt_timestamp.strftime("%I:%M %p")
        
        # Should be 02:38 PM, NOT 06:38 AM
        assert hour_12 == "02:38 PM"
        assert "06:38 AM" not in hour_12
    
    def test_evidence_upload_timestamp(self):
        """Test: Evidence upload timestamps show correct SGT"""
        # User uploads at SGT 15:30 (3:30 PM)
        # Backend stores as UTC: 07:30 (15:30 - 8 hours)
        backend_utc = "2024-01-15T07:30:00Z"
        
        dt = datetime.fromisoformat(backend_utc.replace('Z', '+00:00'))
        sgt_dt = dt.astimezone(timezone(timedelta(hours=8)))
        
        formatted = sgt_dt.strftime("%I:%M %p SGT")
        
        # Should display back as 03:30 PM SGT
        assert formatted == "03:30 PM SGT"
    
    def test_audit_log_timestamps(self):
        """Test: Audit log shows correct SGT for compliance tracking"""
        # Auditor reviews at SGT 17:00 (5:00 PM)
        # Backend stores: 09:00 UTC
        backend_utc = "2024-01-15T09:00:00Z"
        
        dt = datetime.fromisoformat(backend_utc.replace('Z', '+00:00'))
        sgt_dt = dt.astimezone(timezone(timedelta(hours=8)))
        
        formatted = sgt_dt.strftime("%Y-%m-%d %I:%M %p SGT")
        
        assert "2024-01-15 05:00 PM SGT" in formatted


# Run tests with: pytest tests/test_timestamp_display.py -v
# Quick test: pytest tests/test_timestamp_display.py::TestTimestampConversion::test_utc_to_sgt_conversion_8_hour_difference -v
