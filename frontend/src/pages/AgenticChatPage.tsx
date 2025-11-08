import React, { useState, useRef, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Box,
  Card,
  CardContent,
  Chip,
  Alert,
  CircularProgress,
  IconButton,
  Divider
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PersonIcon from '@mui/icons-material/Person';
import TaskIcon from '@mui/icons-material/Task';
import { apiClient } from '../services/api';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  task_id?: number;
  task_type?: string;
  timestamp: Date;
}

interface ChatResponse {
  response: string;
  task_created: boolean;
  task_id?: number;
  task_type?: string;
  intent?: any;
}

const AgenticChatPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '0',
      role: 'assistant',
      content: `👋 Hello! I'm your AI Compliance Assistant. I can help you automate compliance workflows using natural language.

**Here's what I can do:**

🛡️ **Create Controls** - "Upload 30 IM8 controls covering all 10 domain areas"
🔍 **Create Findings** - "Generate findings: SQL injection (critical), XSS (high)"
📄 **Analyze Evidence** - "Analyze evidence items for IM8-01 controls"
📊 **Generate Reports** - "Generate executive compliance report for assessment 1"

**Just describe what you need, and I'll create the tasks automatically!**`,
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [capabilities, setCapabilities] = useState<any>(null);
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
      const response = await apiClient.get('/agentic-chat/capabilities');
      setCapabilities(response.data);
    } catch (error) {
      console.error('Error fetching capabilities:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await apiClient.post<ChatResponse>('/agentic-chat/', {
        message: input
      });

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.data.response,
        task_id: response.data.task_id,
        task_type: response.data.task_type,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error: any) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `❌ Error: ${error.response?.data?.detail || 'Failed to process your request. Please try again.'}`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const examplePrompts = [
    "Upload 30 IM8 controls covering all 10 domain areas",
    "Create findings: SQL injection (critical), XSS vulnerability (high), weak passwords (medium)",
    "Generate executive compliance report for assessment 1",
    "Analyze evidence for control 5"
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
