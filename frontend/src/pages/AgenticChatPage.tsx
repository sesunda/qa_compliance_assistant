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
  IconButton
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PersonIcon from '@mui/icons-material/Person';
import TaskIcon from '@mui/icons-material/Task';
import api from '../services/api';

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
}

const AgenticChatPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '0',
      role: 'assistant',
      content: `👋 Hello! I'm your AI Compliance Assistant. I can help you automate compliance workflows using natural language.

**Here's what I can do:**

🛡️ **Create Controls** - "Upload IM8 controls"
🔍 **Create Findings** - "Generate findings: SQL injection (critical), XSS (high)"
📄 **Analyze Evidence** - "Analyze evidence items for IM8-01 controls"
📊 **Generate Reports** - "Generate executive compliance report"

**Just describe what you need, and I'll guide you through the process!**

💡 **Tip**: I'll ask clarifying questions if I need more information. You can also provide complete details upfront for faster execution.`,
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [capabilities, setCapabilities] = useState<any>(null);
  const [conversationContext, setConversationContext] = useState<any>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Fetch available capabilities
    fetchCapabilities();
  }, []);

  useEffect(() => {
    // Scroll to bottom when messages change
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchCapabilities = async () => {
    try {
      const response = await api.get('/agentic-chat/capabilities');
      setCapabilities(response.data);
    } catch (error) {
      console.error('Error fetching capabilities:', error);
    }
  };

  const handleSendMessage = async (messageText?: string) => {
    const textToSend = messageText || input;
    if (!textToSend.trim() || loading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: textToSend,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    if (!messageText) setInput('');  // Only clear if typing manually
    setLoading(true);

    try {
      const response = await api.post<ChatResponse>('/agentic-chat/', {
        message: textToSend,
        context: conversationContext,
        conversation_id: conversationId
      });

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
        can_edit: response.data.can_edit
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      // Update conversation state
      if (response.data.is_clarifying) {
        setConversationContext(response.data.conversation_context);
        setConversationId(response.data.conversation_id || null);
      } else if (response.data.task_created) {
        // Task created, reset conversation
        setConversationContext(null);
        setConversationId(null);
      }
    } catch (error: any) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `❌ Error: ${error.response?.data?.detail || 'Failed to process your request. Please try again.'}`,
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

  const examplePrompts = [
    "Upload IM8 controls",
    "Create security findings",
    "Generate compliance report",
    "Upload 30 IM8 controls for all domains to project 1"  // Expert mode example
  ];

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
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
                onClick={() => setInput(prompt)}
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
                </Paper>
                <Typography variant="caption" color="text.secondary" sx={{ ml: 1, mt: 0.5, display: 'block' }}>
                  {message.timestamp.toLocaleTimeString()}
                </Typography>
              </Box>
            </Box>
          </Box>
        ))}

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
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Describe what you need... (e.g., 'Upload 30 IM8 controls')"
            disabled={loading}
          />
          <IconButton
            color="primary"
            onClick={handleSendMessage}
            disabled={!input.trim() || loading}
            sx={{ alignSelf: 'flex-end' }}
          >
            <SendIcon />
          </IconButton>
        </Box>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          Press Enter to send, Shift+Enter for new line
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
