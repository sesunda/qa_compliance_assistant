import React, { useState, useRef, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  TextField,
  Box,
  Card,
  CardContent,
  Chip,
  Alert,
  CircularProgress,
  IconButton,
  Button
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PersonIcon from '@mui/icons-material/Person';
import TaskIcon from '@mui/icons-material/Task';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import AddIcon from '@mui/icons-material/Add';
import api from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { formatSingaporeDateTime } from '../utils/datetime';
import EvidenceUploadWidget from '../components/EvidenceUploadWidget';
import EvidenceCard from '../components/EvidenceCard';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  task_id?: number;
  task_type?: string;
  timestamp: Date;
  
  // Multi-turn conversation fields
  is_clarifying?: boolean;
  suggested_responses?: string[];
  conversation_id?: string;
  parameters_collected?: Record<string, any>;
  parameters_missing?: string[];
  can_edit?: boolean;
  
  // RAG features
  sources?: Array<{
    document_name: string;
    page?: number;
    control_id?: number;
    score?: number;
  }>;
  file_uploaded?: boolean;
}

interface ChatResponse {
  response: string;
  task_created: boolean;
  task_id?: number;
  task_type?: string;
  intent?: any;
  
  // Multi-turn conversation fields
  is_clarifying?: boolean;
  clarifying_question?: string;
  suggested_responses?: string[];
  conversation_context?: any;
  parameters_collected?: Record<string, any>;
  parameters_missing?: string[];
  conversation_id?: string;
  can_edit?: boolean;
  
  // RAG features
  sources?: Array<{
    document_name: string;
    page?: number;
    control_id?: number;
    score?: number;
  }>;
  file_uploaded?: boolean;
}

const AgenticChatPage: React.FC = () => {
  const { user } = useAuth();
  
  // Role-based welcome message (memoized to prevent unnecessary recalculations)
  const welcomeMessage = React.useMemo(() => {
    const userRole = user?.role?.name?.toLowerCase();
    
    if (userRole === 'analyst') {
      return `👋 Hello! I'm your AI Compliance Assistant for Evidence Management.

**As an Analyst, you can:**

📤 **Upload Evidence** - "Upload evidence for Control 5" or "Add evidence to MFA control"
🔍 **Analyze Evidence** - "Analyze my evidence for Control 3" 
📊 **Get Suggestions** - "Suggest related controls for network security evidence"
✅ **Submit for Review** - "Submit evidence #12 for review"

**Evidence Workflow:**
1. I'll help you upload evidence documents via chat
2. AI will automatically analyze and validate your evidence
3. Graph RAG will suggest related controls
4. You can submit for auditor review

💡 **Tip**: Just say "upload evidence" and I'll guide you through the process!`;
    } else if (userRole === 'auditor') {
      return `👋 Hello! I'm your AI Compliance Assistant for Control Setup and Evidence Review.

**As an Auditor, you can:**

🛡️ **Set Up Controls** - "Set up IM8 controls for project 1"
🔍 **Create Findings** - "Generate findings: SQL injection (critical), XSS (high)"
📊 **Query Evidence** - "Show me evidence relationships for Control 5"
🔗 **Graph Analysis** - "What controls are related to network security?"
📄 **Generate Reports** - "Generate executive compliance report"

**Evidence Workflow:**
- Analysts upload evidence documents
- You review and approve/reject via the Evidence page
- Use chat to query evidence relationships with Graph RAG

💡 **Tip**: Go to Evidence page to approve/reject submissions!`;
    } else {
      return `👋 Hello! I'm your AI Compliance Assistant. I can help you automate compliance workflows using natural language.

**Here's what I can do:**

🛡️ **Create Controls** - "Upload IM8 controls"
🔍 **Create Findings** - "Generate findings: SQL injection (critical), XSS (high)"
📄 **Analyze Evidence** - "Analyze evidence items for IM8-01 controls"
📊 **Generate Reports** - "Generate executive compliance report"

**Just describe what you need, and I'll guide you through the process!**

💡 **Tip**: I'll ask clarifying questions if I need more information.`;
    }
  }, [user?.role?.name]);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [capabilities, setCapabilities] = useState<any>(null);
  const [conversationContext, setConversationContext] = useState<any>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  
  // Evidence workflow state
  const [pendingUpload, setPendingUpload] = useState<{
    evidenceId: number;
    uploadId: string;
    controlId: number;
    controlTitle: string;
    title: string;
    acceptedTypes: string[];
  } | null>(null);
  const [evidenceResults, setEvidenceResults] = useState<{
    evidence: any;
    analysis?: any;
    suggestions?: any[];
  } | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const isRestoringSession = useRef(false);

  // Initialize welcome message when user loads (but NOT when restoring session)
  useEffect(() => {
    if (user && messages.length === 0 && !isRestoringSession.current) {
      setMessages([{
        id: '0',
        role: 'assistant',
        content: welcomeMessage,
        timestamp: new Date()
      }]);
    }
  }, [user, welcomeMessage, messages.length]);

  // Update welcome message when user role changes
  useEffect(() => {
    if (user && messages.length > 0) {
      setMessages(prev => {
        // Update the first message (welcome message) with role-specific content
        if (prev.length > 0 && prev[0].id === '0') {
          return [
            {
              ...prev[0],
              content: welcomeMessage
            },
            ...prev.slice(1)
          ];
        }
        return prev;
      });
    }
  }, [welcomeMessage, user, messages.length]);

  useEffect(() => {
    // Fetch available capabilities
    fetchCapabilities();
    
    // Restore session from localStorage or load most recent session
    const loadConversation = async () => {
      const savedSession = localStorage.getItem('agentic_session_id');
      if (savedSession) {
        isRestoringSession.current = true;
        setConversationId(savedSession);
        // Restore message history
        await restoreMessageHistory(savedSession);
        isRestoringSession.current = false;
      } else {
        // No saved session - try to load the most recent active session
        isRestoringSession.current = true;
        await loadRecentSession();
        isRestoringSession.current = false;
      }
    };
    
    loadConversation();
  }, []);

  useEffect(() => {
    // Scroll to bottom when messages change
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  useEffect(() => {
    // Persist session to localStorage
    if (conversationId) {
      localStorage.setItem('agentic_session_id', conversationId);
    }
  }, [conversationId]);

  const fetchCapabilities = async () => {
    try {
      const response = await api.get('/agentic-chat/capabilities');
      setCapabilities(response.data);
    } catch (error) {
      console.error('Error fetching capabilities:', error);
    }
  };

  const restoreMessageHistory = async (sessionId: string) => {
    try {
      const response = await api.get(`/agentic-chat/sessions/${sessionId}/messages`);
      const { messages: historyMessages } = response.data;
      
      // Only restore if there are messages
      if (historyMessages && historyMessages.length > 0) {
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
      } else {
        // Session exists but no messages - show welcome message
        isRestoringSession.current = false;
      }
    } catch (error: any) {
      console.error('Error restoring message history:', error);
      
      // If session not found or expired, clear it and start fresh
      if (error.response?.status === 404) {
        localStorage.removeItem('agentic_session_id');
        setConversationId(null);
      }
      
      // Allow welcome message to show
      isRestoringSession.current = false;
    }
  };

  const loadRecentSession = async () => {
    try {
      const response = await api.get('/agentic-chat/sessions/recent');
      const { session_id, messages: historyMessages } = response.data;
      
      // If no recent session exists, let welcome message show
      if (!session_id) {
        return;
      }
      
      // Set conversation ID and restore messages
      setConversationId(session_id);
      localStorage.setItem('agentic_session_id', session_id);
      
      // Convert backend message format to frontend ChatMessage format
      if (historyMessages && historyMessages.length > 0) {
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
      }
    } catch (error) {
      console.error('Error loading recent session:', error);
      // Silently fail - user will start with fresh conversation
    }
  };

  const handleNewChat = () => {
    // Clear current conversation
    setMessages([]);
    setConversationId(null);
    localStorage.removeItem('agentic_session_id');
    setInput('');
    setSelectedFile(null);
  };

  const handleSendMessage = async (messageText?: string) => {
    const textToSend = messageText || input;
    
    // PROACTIVE VALIDATION: Check if message is empty
    if (!textToSend.trim() && !selectedFile) {
      return; // Silently ignore empty messages
    }
    
    // PROACTIVE VALIDATION: Prevent double submissions
    if (loading) return;
    
    // PROACTIVE VALIDATION: Check message length (avoid huge requests)
    if (textToSend.length > 10000) {
      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: '❌ Error: Message is too long. Please keep messages under 10,000 characters.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
      return;
    }
    
    // PROACTIVE VALIDATION: Check file size (avoid huge uploads)
    if (selectedFile && selectedFile.size > 10 * 1024 * 1024) { // 10MB limit
      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `❌ Error: File "${selectedFile.name}" is too large (${(selectedFile.size / 1024 / 1024).toFixed(2)}MB). Maximum size is 10MB.`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
      setSelectedFile(null);
      return;
    }
    
    // PROACTIVE VALIDATION: Check file type (only allow specific extensions)
    if (selectedFile) {
      const allowedExtensions = ['.pdf', '.docx', '.txt', '.csv', '.json', '.xml', '.jpg', '.jpeg', '.png'];
      const fileExtension = selectedFile.name.substring(selectedFile.name.lastIndexOf('.')).toLowerCase();
      if (!allowedExtensions.includes(fileExtension)) {
        const errorMessage: ChatMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: `❌ Error: File type "${fileExtension}" is not supported. Allowed types: ${allowedExtensions.join(', ')}`,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, errorMessage]);
        setSelectedFile(null);
        return;
      }
    }

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: textToSend + (selectedFile ? ` [📎 ${selectedFile.name}]` : ''),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    if (!messageText) setInput('');  // Only clear if typing manually
    setLoading(true);

    try {
      // Use FormData for file upload support
      const formData = new FormData();
      formData.append('message', textToSend);
      if (conversationContext) {
        formData.append('context', JSON.stringify(conversationContext));
      }
      if (conversationId) {
        formData.append('conversation_id', conversationId);
      }
      if (selectedFile) {
        formData.append('file', selectedFile);
      }

      // Use native fetch for FormData to avoid axios header issues
      const token = document.cookie.split('; ').find(row => row.startsWith('auth_token='))?.split('=')[1];
      const fetchResponse = await fetch(`${api.defaults.baseURL}/agentic-chat/`, {
        method: 'POST',
        body: formData, // Native fetch handles FormData correctly
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
        },
        signal: AbortSignal.timeout(120000), // 2 minute timeout
      });

      // Convert to axios-like response format
      const responseData = await fetchResponse.json().catch(() => ({})) as ChatResponse;
      const response = {
        status: fetchResponse.status,
        data: responseData,
        statusText: fetchResponse.statusText,
      };
      
      // Handle non-200 responses gracefully
      if (response.status >= 400) {
        const errorData = response.data as any;
        throw new Error(errorData?.detail || 'Request failed');
      }

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.data.response,
        task_id: response.data.task_id,
        task_type: response.data.task_type,
        timestamp: new Date(),
        is_clarifying: response.data.is_clarifying,
        suggested_responses: response.data.suggested_responses,
        conversation_id: response.data.conversation_id,
        parameters_collected: response.data.parameters_collected,
        parameters_missing: response.data.parameters_missing,
        can_edit: response.data.can_edit,
        sources: response.data.sources,
        file_uploaded: response.data.file_uploaded
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      // Evidence workflow detection
      if (response.data.task_type === 'request_evidence_upload' && response.data.task_id) {
        // Poll for task completion to get upload details
        pollEvidenceUploadTask(response.data.task_id);
      } else if (response.data.task_type === 'analyze_evidence' && response.data.task_id) {
        // Poll for analysis results
        pollAnalysisTask(response.data.task_id);
      } else if (response.data.task_type === 'suggest_related_controls' && response.data.task_id) {
        // Poll for suggestions
        pollSuggestionsTask(response.data.task_id);
      }
      
      // Update conversation state
      if (response.data.is_clarifying) {
        setConversationContext(response.data.conversation_context);
        setConversationId(response.data.conversation_id || null);
      } else if (response.data.task_created) {
        // Task created, preserve conversation for follow-up questions
        setConversationContext(null);
        // Keep conversationId so messages persist across navigation
      }
      
      // Clear file after upload
      setSelectedFile(null);
    } catch (error: any) {
      let errorText = 'Failed to process your request. Please try again.';
      
      // Network errors (no response from server)
      if (!error.response) {
        if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
          errorText = '⏱️ Request timed out. The operation took too long. Please try a simpler request or try again later.';
        } else if (error.message?.includes('Network Error')) {
          errorText = '🌐 Network error. Please check your internet connection and try again.';
        } else {
          // Safely stringify error message
          const errMsg = typeof error.message === 'string' 
            ? error.message 
            : (error.message ? JSON.stringify(error.message) : 'Unable to reach server');
          errorText = `⚠️ Connection error: ${errMsg}`;
        }
      }
      // Server returned an error response
      else if (error.response?.data?.detail) {
        // Handle FastAPI validation errors (array of objects)
        if (Array.isArray(error.response.data.detail)) {
          errorText = error.response.data.detail
            .map((err: any) => {
              const field = err.loc?.slice(1).join('.') || 'Field';
              return `${field}: ${err.msg}`;
            })
            .join(', ');
        } else if (typeof error.response.data.detail === 'string') {
          errorText = error.response.data.detail;
        } else {
          errorText = JSON.stringify(error.response.data.detail);
        }
      }
      // HTTP status code errors
      else if (error.response?.status) {
        switch (error.response.status) {
          case 401:
            errorText = '🔒 Authentication failed. Please log in again.';
            break;
          case 403:
            errorText = '🚫 You don\'t have permission to perform this action.';
            break;
          case 404:
            errorText = '❓ Resource not found. The requested item may have been deleted.';
            break;
          case 413:
            errorText = '📦 Request too large. Please reduce the size of your message or file.';
            break;
          case 429:
            errorText = '⏳ Too many requests. Please wait a moment and try again.';
            break;
          case 500:
            errorText = '💥 Server error. Our team has been notified. Please try again later.';
            break;
          case 503:
            errorText = '🔧 Service temporarily unavailable. Please try again in a few moments.';
            break;
          default:
            errorText = `❌ Error ${error.response.status}: ${error.response.statusText || 'Request failed'}`;
        }
      }
      
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: errorText,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
      
      // Reset conversation on error
      setConversationContext(null);
      setConversationId(null);
    } finally {
      setLoading(false);
    }
  };

  const pollEvidenceUploadTask = async (taskId: number) => {
    try {
      // Poll task status
      const response = await api.get(`/agent-tasks/${taskId}`);
      const task = response.data;
      
      if (task.status === 'completed' && task.result?.status === 'success') {
        // Show upload widget
        setPendingUpload({
          evidenceId: task.result.evidence_id,
          uploadId: task.result.upload_id,
          controlId: task.result.control_id,
          controlTitle: task.result.control_title || `Control ${task.result.control_id}`,
          title: task.result.instructions || 'Upload evidence',
          acceptedTypes: task.result.accepted_types || ['document', 'screenshot']
        });
      } else if (task.status === 'pending' || task.status === 'running') {
        // Keep polling
        setTimeout(() => pollEvidenceUploadTask(taskId), 2000);
      }
    } catch (error) {
      console.error('Error polling evidence upload task:', error);
    }
  };

  const pollAnalysisTask = async (taskId: number) => {
    try {
      const response = await api.get(`/agent-tasks/${taskId}`);
      const task = response.data;
      
      if (task.status === 'completed' && task.result?.status === 'success') {
        setEvidenceResults(prev => ({
          ...prev,
          evidence: prev?.evidence,
          analysis: task.result.analysis
        }));
      } else if (task.status === 'pending' || task.status === 'running') {
        setTimeout(() => pollAnalysisTask(taskId), 2000);
      }
    } catch (error) {
      console.error('Error polling analysis task:', error);
    }
  };

  const pollSuggestionsTask = async (taskId: number) => {
    try {
      const response = await api.get(`/agent-tasks/${taskId}`);
      const task = response.data;
      
      if (task.status === 'completed' && task.result?.status === 'success') {
        setEvidenceResults(prev => ({
          ...prev,
          evidence: prev?.evidence,
          analysis: prev?.analysis,
          suggestions: task.result.suggestions
        }));
      } else if (task.status === 'pending' || task.status === 'running') {
        setTimeout(() => pollSuggestionsTask(taskId), 2000);
      }
    } catch (error) {
      console.error('Error polling suggestions task:', error);
    }
  };

  const handleEvidenceUploadComplete = (evidence: any) => {
    setPendingUpload(null);
    setEvidenceResults({ evidence, analysis: undefined, suggestions: undefined });
    
    // Auto-trigger analysis
    handleSendMessage(`Analyze evidence ${evidence.id} for compliance`);
  };

  const handleSuggestedResponse = (suggestion: string) => {
    handleSendMessage(suggestion);
  };

  const handleEditParameter = (paramName: string) => {
    // Allow user to correct a previously provided value
    const newValue = prompt(`Edit ${paramName}:`, conversationContext?.parameters?.[paramName] || '');
    if (newValue !== null && newValue.trim()) {
      handleSendMessage(`Change ${paramName} to ${newValue}`);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Role-based example prompts (recalculates when user changes)
  const examplePrompts = React.useMemo(() => {
    const userRole = user?.role?.name?.toLowerCase();
    
    if (userRole === 'analyst') {
      return [
        "Upload evidence for Control 5",
        "Analyze my evidence for MFA control",
        "Suggest related controls for network security",
        "Submit evidence #12 for review"
      ];
    } else if (userRole === 'auditor') {
      return [
        "Set up IM8 controls",
        "Create security findings",
        "Show evidence relationships for Control 3",
        "Generate compliance report"
      ];
    } else {
      return [
        "Generate compliance report",
        "Show project status",
        "List all controls",
        "View evidence summary"
      ];
    }
  }, [user]);

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <SmartToyIcon sx={{ fontSize: 40, mr: 2, color: 'primary.main' }} />
          <Box>
            <Typography variant="h4" gutterBottom>
              Agentic AI Assistant
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Natural language interface for compliance automation
              {capabilities && (
                <Chip 
                  label={`${capabilities.provider || 'AI'} Active`} 
                  color="success" 
                  size="small" 
                  sx={{ ml: 1 }} 
                />
              )}
            </Typography>
          </Box>
        </Box>
        <Button
          variant="outlined"
          startIcon={<AddIcon />}
          onClick={handleNewChat}
          disabled={messages.length === 0}
        >
          New Chat
        </Button>
      </Box>

      {/* Example Prompts */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="subtitle2" gutterBottom>
            💡 Try these example prompts:
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
            {examplePrompts.map((prompt, index) => (
              <Chip
                key={index}
                label={prompt}
                onClick={() => handleSendMessage(prompt)}
                sx={{ cursor: 'pointer' }}
                variant="outlined"
              />
            ))}
          </Box>
        </CardContent>
      </Card>

      {/* Chat Messages */}
      <Paper sx={{ height: '60vh', overflow: 'auto', p: 2, mb: 2 }}>
        {messages.map((message) => (
          <Box
            key={message.id}
            sx={{
              display: 'flex',
              justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
              mb: 2
            }}
          >
            <Box
              sx={{
                maxWidth: '70%',
                display: 'flex',
                flexDirection: message.role === 'user' ? 'row-reverse' : 'row',
                alignItems: 'flex-start',
                gap: 1
              }}
            >
              <Box
                sx={{
                  width: 40,
                  height: 40,
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  bgcolor: message.role === 'user' ? 'primary.main' : 'secondary.main',
                  color: 'white',
                  flexShrink: 0
                }}
              >
                {message.role === 'user' ? <PersonIcon /> : <SmartToyIcon />}
              </Box>

              <Box>
                <Paper
                  sx={{
                    p: 2,
                    bgcolor: message.role === 'user' ? 'primary.light' : 'grey.100',
                    color: message.role === 'user' ? 'primary.contrastText' : 'text.primary'
                  }}
                >
                  <Typography 
                    variant="body1" 
                    sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}
                  >
                    {message.content}
                  </Typography>

                  {/* Template download links if mentioned in the message */}
                  {message.role === 'assistant' && (
                    message.content.includes('/api/templates/') || 
                    message.content.includes('Download Template') ||
                    message.content.includes('📥')
                  ) && (
                    <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid rgba(0,0,0,0.1)' }}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                        📥 Download Templates:
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                        <Chip
                          icon={<AttachFileIcon />}
                          label="Evidence CSV Template"
                          size="small"
                          color="primary"
                          component="a"
                          href={`${api.defaults.baseURL}/templates/evidence-upload.csv`}
                          download
                          clickable
                        />
                        <Chip
                          icon={<AttachFileIcon />}
                          label="Evidence JSON Template"
                          size="small"
                          color="secondary"
                          component="a"
                          href={`${api.defaults.baseURL}/templates/evidence-upload.json`}
                          download
                          clickable
                        />
                        <Chip
                          icon={<AttachFileIcon />}
                          label="Sample IM8 Controls"
                          size="small"
                          color="success"
                          component="a"
                          href={`${api.defaults.baseURL}/templates/im8-controls-sample.csv`}
                          download
                          clickable
                        />
                      </Box>
                    </Box>
                  )}

                  {message.task_id && (
                    <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid rgba(0,0,0,0.1)' }}>
                      <Chip
                        icon={<TaskIcon />}
                        label={`Task #${message.task_id} - ${message.task_type}`}
                        size="small"
                        color="primary"
                        onClick={() => window.location.href = '/agent-tasks'}
                        sx={{ cursor: 'pointer' }}
                      />
                    </Box>
                  )}

                  {/* Suggested responses for multi-turn conversation */}
                  {message.suggested_responses && message.suggested_responses.length > 0 && (
                    <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid rgba(0,0,0,0.1)' }}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                        💡 Quick responses:
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {message.suggested_responses.map((suggestion, idx) => (
                          <Chip
                            key={idx}
                            label={suggestion}
                            size="small"
                            variant="outlined"
                            color="primary"
                            onClick={() => handleSuggestedResponse(suggestion)}
                            sx={{ cursor: 'pointer' }}
                          />
                        ))}
                      </Box>
                    </Box>
                  )}

                  {/* Show collected parameters with edit option */}
                  {message.parameters_collected && Object.keys(message.parameters_collected).length > 0 && (
                    <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid rgba(0,0,0,0.1)' }}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                        ℹ️ Information collected:
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {Object.entries(message.parameters_collected).map(([key, value]) => (
                          <Chip
                            key={key}
                            label={`${key}: ${JSON.stringify(value)}`}
                            size="small"
                            color="info"
                            variant="filled"
                            onDelete={message.can_edit ? () => handleEditParameter(key) : undefined}
                            sx={{ fontSize: '0.7rem' }}
                          />
                        ))}
                      </Box>
                    </Box>
                  )}
                  
                  {/* Show document sources from RAG search */}
                  {message.sources && message.sources.length > 0 && (
                    <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid rgba(0,0,0,0.1)' }}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                        📚 Sources:
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {message.sources.map((source, idx) => (
                          <Chip
                            key={idx}
                            label={`${source.document_name}${source.page ? ` (p.${source.page})` : ''}${source.score ? ` - ${(source.score * 100).toFixed(0)}%` : ''}`}
                            size="small"
                            color="secondary"
                            variant="outlined"
                            sx={{ fontSize: '0.7rem' }}
                          />
                        ))}
                      </Box>
                    </Box>
                  )}
                </Paper>
                <Typography variant="caption" color="text.secondary" sx={{ ml: 1, mt: 0.5, display: 'block' }}>
                  {formatSingaporeDateTime(message.timestamp.toISOString())}
                </Typography>
              </Box>
            </Box>
          </Box>
        ))}

        {/* Evidence Upload Widget */}
        {pendingUpload && (
          <Box sx={{ mb: 3 }}>
            <EvidenceUploadWidget
              evidenceId={pendingUpload.evidenceId}
              uploadId={pendingUpload.uploadId}
              controlId={pendingUpload.controlId}
              controlTitle={pendingUpload.controlTitle}
              title={pendingUpload.title}
              acceptedTypes={pendingUpload.acceptedTypes}
              onUploadComplete={handleEvidenceUploadComplete}
              onCancel={() => setPendingUpload(null)}
            />
          </Box>
        )}

        {/* Evidence Results Card */}
        {evidenceResults && (
          <Box sx={{ mb: 3 }}>
            <EvidenceCard
              evidence={evidenceResults.evidence}
              showAnalysis={true}
            />
            {evidenceResults.suggestions && evidenceResults.suggestions.length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="h6" gutterBottom>
                  📊 Related Controls (Graph RAG)
                </Typography>
                {evidenceResults.suggestions.map((suggestion: any) => (
                  <Paper key={suggestion.control_id} sx={{ p: 2, mb: 1 }}>
                    <Typography variant="subtitle2">
                      {suggestion.control_id}: {suggestion.control_title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Relevance: {(suggestion.relevance_score * 100).toFixed(0)}% | 
                      Relationship: {suggestion.relationship_type}
                    </Typography>
                    <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                      {suggestion.reasoning}
                    </Typography>
                  </Paper>
                ))}
              </Box>
            )}
          </Box>
        )}

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box
                sx={{
                  width: 40,
                  height: 40,
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  bgcolor: 'secondary.main',
                  color: 'white'
                }}
              >
                <SmartToyIcon />
              </Box>
              <Paper sx={{ p: 2, bgcolor: 'grey.100' }}>
                <CircularProgress size={20} />
                <Typography variant="body2" sx={{ ml: 2, display: 'inline' }}>
                  Processing your request...
                </Typography>
              </Paper>
            </Box>
          </Box>
        )}

        <div ref={messagesEndRef} />
      </Paper>

      {/* Input Area */}
      <Paper sx={{ p: 2 }}>
        {/* File upload input (hidden) */}
        <input
          ref={fileInputRef}
          type="file"
          style={{ display: 'none' }}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) setSelectedFile(file);
          }}
          accept=".pdf,.doc,.docx,.txt,.csv,.json,.xml,.xls,.xlsx,.png,.jpg,.jpeg"
        />
        
        {/* Show selected file */}
        {selectedFile && (
          <Box sx={{ mb: 1 }}>
            <Chip
              label={`📎 ${selectedFile.name} (${(selectedFile.size / 1024).toFixed(1)} KB)`}
              onDelete={() => setSelectedFile(null)}
              size="small"
              color="primary"
              variant="outlined"
            />
          </Box>
        )}
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          {/* File Upload Button */}
          <IconButton
            color={selectedFile ? "primary" : "default"}
            onClick={() => fileInputRef.current?.click()}
            disabled={loading}
            title="Attach file (max 10MB)"
          >
            <AttachFileIcon />
          </IconButton>
          
          <TextField
            fullWidth
            multiline
            maxRows={4}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Describe what you need... (e.g., 'Upload 30 IM8 controls' or attach a document)"
            disabled={loading}
            error={input.length > 10000}
            helperText={
              input.length > 9000 
                ? `${input.length}/10,000 characters ${input.length > 10000 ? '(too long!)' : ''}`
                : undefined
            }
          />
          <IconButton
            color="primary"
            onClick={() => handleSendMessage()}
            disabled={(!input.trim() && !selectedFile) || loading || input.length > 10000}
            sx={{ alignSelf: 'flex-end' }}
          >
            <SendIcon />
          </IconButton>
        </Box>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          Press Enter to send, Shift+Enter for new line • 📎 Attach documents for RAG analysis (PDF, DOCX, TXT, CSV, JSON, XML - max 10MB)
        </Typography>
      </Paper>

      {capabilities && capabilities.status === 'unavailable' && (
        <Alert severity="warning" sx={{ mt: 2 }}>
          AI service is not configured. Please set AZURE_OPENAI_ENDPOINT or OPENAI_API_KEY environment variables.
        </Alert>
      )}
    </Container>
  );
};

export default AgenticChatPage;
