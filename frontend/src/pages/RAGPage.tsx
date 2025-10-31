import React, { useState, useRef, useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  Chip,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Grid,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material'
import {
  Send,
  ExpandMore,
  AccountTree,
  AutoAwesome,
} from '@mui/icons-material'

interface Message {
  id: string
  text: string
  sender: 'user' | 'assistant'
  timestamp: Date
  metadata?: {
    searchType?: 'vector' | 'graph' | 'hybrid'
    sources?: Array<{
      title: string
      content: string
      score: number
      type: string
    }>
  }
}

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  )
}

const RAGPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: 'Hello! I\'m your AI Compliance Assistant. I can help you with compliance questions using advanced RAG (Retrieval-Augmented Generation) techniques. Ask me about controls, regulations, best practices, or upload documents for analysis.',
      sender: 'assistant',
      timestamp: new Date(),
    },
  ])
  const [inputText, setInputText] = useState('')
  const [loading, setLoading] = useState(false)
  const [selectedTab, setSelectedTab] = useState(0)
  const [searchType, setSearchType] = useState<'vector' | 'graph' | 'hybrid'>('hybrid')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputText.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText,
      sender: 'user',
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInputText('')
    setLoading(true)

    try {
      // Simulate RAG processing
      const response = await simulateRAGResponse(inputText, searchType)
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: response.answer,
        sender: 'assistant',
        timestamp: new Date(),
        metadata: {
          searchType,
          sources: response.sources,
        },
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: 'Sorry, I encountered an error while processing your request. Please try again.',
        sender: 'assistant',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const simulateRAGResponse = async (query: string, type: 'vector' | 'graph' | 'hybrid') => {
    // Simulate API delay
    await new Promise((resolve) => setTimeout(resolve, 2000))

    // Mock response based on search type
    const responses = {
      vector: {
        answer: `Based on vector similarity search, I found relevant compliance information. ${query.toLowerCase().includes('control') ? 'Security controls should be implemented according to ISO 27001 framework, including access controls, encryption, and monitoring.' : 'For compliance requirements, consider implementing regular assessments, documentation, and staff training.'}`,
        sources: [
          {
            title: 'ISO 27001 Security Controls',
            content: 'Access control and information security management...',
            score: 0.95,
            type: 'standard',
          },
          {
            title: 'NIST Cybersecurity Framework',
            content: 'Framework for improving critical infrastructure cybersecurity...',
            score: 0.87,
            type: 'framework',
          },
        ],
      },
      graph: {
        answer: `Using graph-based knowledge retrieval, I can show you the relationships between compliance concepts. ${query.toLowerCase().includes('audit') ? 'Audit processes are connected to risk management, evidence collection, and reporting requirements through regulatory frameworks.' : 'Compliance concepts are interconnected through regulatory frameworks, policies, and implementation procedures.'}`,
        sources: [
          {
            title: 'Compliance Knowledge Graph',
            content: 'Regulatory framework connections and dependencies...',
            score: 0.92,
            type: 'knowledge_graph',
          },
          {
            title: 'Risk Management Relationships',
            content: 'Risk assessment connects to control implementation...',
            score: 0.89,
            type: 'relationship',
          },
        ],
      },
      hybrid: {
        answer: `Using hybrid RAG (combining vector and graph search), I can provide comprehensive insights. ${query.toLowerCase().includes('evidence') ? 'Evidence management requires both semantic understanding of document content and knowledge of regulatory relationships. Documents should be categorized, tagged, and linked to specific control requirements.' : 'Compliance management benefits from both semantic search of documents and understanding regulatory relationships.'}`,
        sources: [
          {
            title: 'Evidence Management Best Practices',
            content: 'Document classification and regulatory mapping...',
            score: 0.94,
            type: 'best_practice',
          },
          {
            title: 'Regulatory Framework Analysis',
            content: 'Cross-reference analysis of compliance requirements...',
            score: 0.91,
            type: 'analysis',
          },
          {
            title: 'Control Implementation Guide',
            content: 'Step-by-step implementation procedures...',
            score: 0.88,
            type: 'guide',
          },
        ],
      },
    }

    return responses[type]
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const renderMessage = (message: Message) => (
    <Box
      key={message.id}
      sx={{
        display: 'flex',
        justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start',
        mb: 2,
      }}
    >
      <Paper
        sx={{
          p: 2,
          maxWidth: '70%',
          bgcolor: message.sender === 'user' ? 'primary.main' : 'grey.100',
          color: message.sender === 'user' ? 'white' : 'text.primary',
        }}
      >
        <Typography variant="body1">{message.text}</Typography>
        <Typography
          variant="caption"
          sx={{
            display: 'block',
            mt: 1,
            opacity: 0.8,
          }}
        >
          {message.timestamp.toLocaleTimeString()}
        </Typography>
        
        {message.metadata?.sources && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
              Sources ({message.metadata.searchType} search):
            </Typography>
            {message.metadata.sources.map((source, index) => (
              <Accordion key={index} sx={{ mt: 1 }}>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="caption">
                      {source.title}
                    </Typography>
                    <Chip
                      label={`${Math.round(source.score * 100)}% match`}
                      size="small"
                      color="primary"
                    />
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography variant="caption">
                    {source.content}
                  </Typography>
                </AccordionDetails>
              </Accordion>
            ))}
          </Box>
        )}
      </Paper>
    </Box>
  )

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        AI Compliance Assistant
      </Typography>
      <Typography variant="body1" color="textSecondary" paragraph>
        Intelligent compliance assistance using RAG (Retrieval-Augmented Generation) with vector search, graph-based knowledge retrieval, and hybrid approaches.
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card sx={{ height: '600px', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
              {/* Chat Messages */}
              <Box
                sx={{
                  flexGrow: 1,
                  overflowY: 'auto',
                  mb: 2,
                  p: 1,
                }}
              >
                {messages.map(renderMessage)}
                {loading && (
                  <Box display="flex" justifyContent="flex-start" mb={2}>
                    <Paper sx={{ p: 2, bgcolor: 'grey.100' }}>
                      <Box display="flex" alignItems="center" gap={1}>
                        <CircularProgress size={16} />
                        <Typography variant="body2">AI is thinking...</Typography>
                      </Box>
                    </Paper>
                  </Box>
                )}
                <div ref={messagesEndRef} />
              </Box>

              {/* Input Area */}
              <Box display="flex" gap={2}>
                <TextField
                  fullWidth
                  multiline
                  maxRows={3}
                  placeholder="Ask about compliance, controls, regulations, or upload documents..."
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyPress={handleKeyPress}
                  disabled={loading}
                />
                <Button
                  variant="contained"
                  onClick={handleSendMessage}
                  disabled={loading || !inputText.trim()}
                  sx={{ minWidth: 'auto', px: 2 }}
                >
                  <Send />
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                RAG Configuration
              </Typography>
              
              <Tabs value={selectedTab} onChange={(_, newValue) => setSelectedTab(newValue)}>
                <Tab label="Search Type" />
                <Tab label="Settings" />
              </Tabs>

              <TabPanel value={selectedTab} index={0}>
                <Box display="flex" flexDirection="column" gap={2}>
                  <Button
                    variant={searchType === 'vector' ? 'contained' : 'outlined'}
                    onClick={() => setSearchType('vector')}
                    startIcon={<AutoAwesome />}
                  >
                    Vector Search
                  </Button>
                  <Button
                    variant={searchType === 'graph' ? 'contained' : 'outlined'}
                    onClick={() => setSearchType('graph')}
                    startIcon={<AccountTree />}
                  >
                    Graph Search
                  </Button>
                  <Button
                    variant={searchType === 'hybrid' ? 'contained' : 'outlined'}
                    onClick={() => setSearchType('hybrid')}
                    startIcon={<AutoAwesome />}
                  >
                    Hybrid RAG
                  </Button>
                </Box>
                
                <Alert severity="info" sx={{ mt: 2 }}>
                  <Typography variant="caption">
                    <strong>Vector:</strong> Semantic similarity search<br />
                    <strong>Graph:</strong> Knowledge relationships<br />
                    <strong>Hybrid:</strong> Combined approach
                  </Typography>
                </Alert>
              </TabPanel>

              <TabPanel value={selectedTab} index={1}>
                <Typography variant="body2" color="textSecondary">
                  Advanced RAG settings and document upload will be available here.
                </Typography>
              </TabPanel>
            </CardContent>
          </Card>

          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Examples
              </Typography>
              <List dense>
                <ListItem button onClick={() => setInputText('What are the key ISO 27001 controls?')}>
                  <ListItemText primary="ISO 27001 controls" />
                </ListItem>
                <ListItem button onClick={() => setInputText('How to implement access controls?')}>
                  <ListItemText primary="Access control implementation" />
                </ListItem>
                <ListItem button onClick={() => setInputText('Evidence management best practices?')}>
                  <ListItemText primary="Evidence management" />
                </ListItem>
                <ListItem button onClick={() => setInputText('Risk assessment procedures?')}>
                  <ListItemText primary="Risk assessment" />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

export default RAGPage