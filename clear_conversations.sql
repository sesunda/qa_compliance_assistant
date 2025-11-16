-- Clear all conversation history for testing
-- Run this to reset agentic chat conversations

-- Delete all conversation sessions
DELETE FROM conversation_sessions;

-- Reset sequence (optional)
-- ALTER SEQUENCE conversation_sessions_id_seq RESTART WITH 1;

-- Verify deletion
SELECT COUNT(*) AS remaining_conversations FROM conversation_sessions;
