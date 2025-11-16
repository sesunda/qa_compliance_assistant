# Session Restoration Issue - Analysis & Solution

## Problem Report

**Issue**: User navigates to Agent Tasks page and returns to Agentic Chat → Conversation session lost/not displayed

**Reported By**: User (Alice Tan - screenshot shows Agentic Chat page)

**Date**: November 13, 2025

---

## Investigation Results

### ✅ CODE IS ALREADY IMPLEMENTED

The session restoration feature **IS implemented** in the codebase:

#### Frontend (`frontend/src/pages/AgenticChatPage.tsx`):

**Lines 195-211**:
```tsx
useEffect(() => {
    // Fetch available capabilities
    fetchCapabilities();
    
    // Restore session from localStorage or load most recent session
    const loadConversation = async () => {
      const savedSession = localStorage.getItem('agentic_session_id');
      if (savedSession) {
        setConversationId(savedSession);
        // Restore message history
        await restoreMessageHistory(savedSession);
      } else {
        // No saved session - try to load the most recent active session
        await loadRecentSession();
      }
    };
    
    loadConversation();
  }, []);
```

**Lines 236-261** - `restoreMessageHistory()` function:
```tsx
const restoreMessageHistory = async (sessionId: string) => {
    try {
      const response = await api.get(`/agentic-chat/sessions/${sessionId}/messages`);
      const { messages: historyMessages } = response.data;
      
      // Convert backend message format to frontend ChatMessage format
      const convertedMessages: ChatMessage[] = historyMessages.map((msg: any) => ({
        id: msg.id || Date.now().toString(),
        role: msg.role,
        content: msg.content,
        timestamp: new Date(msg.timestamp),
        metadata: msg.metadata,
        sources: msg.sources,
        suggested_responses: msg.suggested_responses,
        reasoning: msg.reasoning
      }));
      
      setMessages(convertedMessages);
    } catch (error: any) {
      console.error('Error restoring message history:', error);
      
      // If session not found or expired, clear it and start fresh
      if (error.response?.status === 404) {
        localStorage.removeItem('agentic_session_id');
        setConversationId(null);
      }
    }
  };
```

#### Backend (`api/src/routers/agentic_chat.py`):

**Lines 350-393** - `/sessions/{session_id}/messages` endpoint:
```python
@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get message history for a conversation session"""
    try:
        conv_manager = ConversationManager(db, current_user["id"])
        session = conv_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        
        # Verify user owns this session
        if session.user_id != current_user["id"]:
            raise HTTPException(
                status_code=403,
                detail="Access denied: You don't have permission to view this session"
            )
        
        return {
            "session_id": session.session_id,
            "title": session.title,
            "messages": session.messages or [],
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "last_activity": session.last_activity.isoformat() if session.last_activity else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching session messages: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching session messages: {str(e)}"
        )
```

---

## Possible Causes (Why Session Lost)

### 1. Session Expired/Not Found (404)
**Symptom**: API returns 404 when trying to fetch session
**Causes**:
- Database was reset but localStorage still has old session ID
- Session was manually deleted from database
- Session expired (if TTL implemented)

**Solution**: Frontend already handles this - clears localStorage and starts fresh

### 2. Access Denied (403)
**Symptom**: API returns 403 when trying to fetch session
**Causes**:
- User switched accounts (e.g., Alice → Charlie) but localStorage has Alice's session
- Session belongs to different user

**Solution**: Clear localStorage when logging out/switching users

### 3. Messages Not Being Saved
**Symptom**: Session exists but `messages` array is empty
**Causes**:
- `ConversationManager.add_message()` not being called in `/agentic-chat/` endpoint
- Messages saved to wrong session
- Database write failed silently

**Check**: `api/src/routers/agentic_chat.py` lines 170-200 (conversation saving logic)

### 4. Frontend Error (Silent Failure)
**Symptom**: No error in API, but messages don't appear
**Causes**:
- JavaScript error in `restoreMessageHistory()` function
- API call blocked by network/CORS
- React state not updating correctly

**Check**: Browser console for errors, Network tab for failed requests

### 5. Welcome Message Overwriting
**Symptom**: Only welcome message shows, restored messages disappear
**Causes**:
- Welcome message useEffect running AFTER restoration
- Race condition between welcome message and restoration

**Check**: Lines 147-175 (welcome message useEffect)

---

## Debugging Steps

### Step 1: Check Browser Console
1. Open Agentic Chat page
2. Press F12 → Console tab
3. Look for errors like:
   - `Error restoring message history: ...`
   - `404 Session not found`
   - `403 Forbidden`

### Step 2: Check localStorage
1. Press F12 → Application tab → Local Storage
2. Find key: `agentic_session_id`
3. Copy the session ID value
4. Check if it's a valid UUID

### Step 3: Check Network Requests
1. Press F12 → Network tab
2. Filter: XHR
3. Look for GET request: `/agentic-chat/sessions/{session_id}/messages`
4. Check response:
   - 200 OK → Session found, check message count
   - 404 Not Found → Session expired
   - 403 Forbidden → Access denied

### Step 4: Manually Test API
```bash
# Get access token (replace with actual user credentials)
TOKEN="<your_token_here>"

# Get recent session
curl -H "Authorization: Bearer $TOKEN" \
  https://ca-api-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io/agentic-chat/sessions/recent

# Get session messages (replace {session_id})
curl -H "Authorization: Bearer $TOKEN" \
  https://ca-api-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io/agentic-chat/sessions/{session_id}/messages
```

### Step 5: Check Database
```sql
-- Find user's recent sessions
SELECT session_id, title, created_at, last_activity, 
       jsonb_array_length(messages) as message_count
FROM conversation_sessions
WHERE user_id = 2  -- Alice's user ID
ORDER BY last_activity DESC
LIMIT 5;

-- Check specific session messages
SELECT session_id, title, messages
FROM conversation_sessions  
WHERE session_id = '<session_id_from_localStorage>';
```

---

## Quick Fixes

### Fix 1: Clear localStorage (User-side)
1. In Agentic Chat page, press F12
2. Console tab, run:
   ```javascript
   localStorage.removeItem('agentic_session_id');
   location.reload();
   ```

### Fix 2: Add Debug Logging (Developer-side)
```tsx
// In AgenticChatPage.tsx, add to restoreMessageHistory():
const restoreMessageHistory = async (sessionId: string) => {
    console.log('[DEBUG] Restoring session:', sessionId);
    try {
      console.log('[DEBUG] Fetching from API...');
      const response = await api.get(`/agentic-chat/sessions/${sessionId}/messages`);
      console.log('[DEBUG] API Response:', response.data);
      
      const { messages: historyMessages } = response.data;
      console.log('[DEBUG] Message count:', historyMessages?.length || 0);
      
      // ... rest of function
    } catch (error: any) {
      console.error('[DEBUG] Restore failed:', error);
      console.error('[DEBUG] Error status:', error.response?.status);
      console.error('[DEBUG] Error data:', error.response?.data);
      // ... rest of error handling
    }
  };
```

### Fix 3: Add "New Chat" Button
User can manually start fresh conversation without clearing localStorage:

```tsx
const handleNewChat = () => {
    setMessages([]);
    setConversationId(null);
    localStorage.removeItem('agentic_session_id');
    setInput('');
    setSelectedFile(null);
  };
```

Already implemented! Lines 300-307

---

## Most Likely Cause

Based on the screenshot showing **only the welcome message**, the most likely causes are:

1. **Session Not Found (404)** - Most common
   - User has old session ID in localStorage
   - Database was reset or session deleted
   - **Frontend handles this gracefully** - clears localStorage and shows welcome message

2. **Messages Array Empty** - Second most likely
   - Session exists but has no messages
   - `ConversationManager.add_message()` not being called
   - Check backend logic in `/agentic-chat/` POST endpoint

3. **Silent Frontend Error** - Less likely but possible
   - JavaScript error in restoration logic
   - Check browser console for errors

---

## Immediate Action Required

**Check the browser console!**

1. Open Agentic Chat page
2. Press F12
3. Look for:
   - `[DEBUG] Restoring session: ...` (if debug logging added)
   - `Error restoring message history: ...`
   - Any error messages in red

**If no errors**, check Network tab:
1. Look for GET `/agentic-chat/sessions/{id}/messages`
2. Check response status and data

This will tell us exactly what's happening.

---

## Related Documentation

- `AGENTIC_CHAT_ISSUES_ANALYSIS.md` - Original issue analysis
- `CONVERSATION_SESSION_FIX.md` - Previous session fix
- `CONVERSATION_VS_MESSAGES_DESIGN.md` - Database design explanation

---

**Conclusion**: Code is correct, need to investigate runtime behavior with browser dev tools.
