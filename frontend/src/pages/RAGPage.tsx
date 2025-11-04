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
  AttachFile,
  Mic,
  Stop,
} from '@mui/icons-material'
import { api } from '../services/api'

interface Message {
  id: string
  text: string
  sender: 'user' | 'assistant'
  timestamp: Date
  metadata?: {
    searchType?: string
    sources?: any[]
    taskCreated?: boolean
    taskId?: number
    taskType?: string
  }
  attachedFile?: {
    name: string
    size: number
    type: string
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
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [selectedModel, setSelectedModel] = useState<string>('groq')
  const [isRecording, setIsRecording] = useState(false)
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    // Only require document for first message (when no session exists)
    if (!sessionId && !selectedFile) {
      alert('⚠️ Please upload a document to start the conversation. Click 📎 to attach a file.')
      return
    }
    
    if (!inputText.trim() && !selectedFile) return

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText || (selectedFile ? `📎 Uploaded: ${selectedFile.name}` : ''),
      sender: 'user',
      timestamp: new Date(),
      attachedFile: selectedFile ? {
        name: selectedFile.name,
        size: selectedFile.size,
        type: selectedFile.type
      } : undefined
    }

    setMessages((prev) => [...prev, userMessage])
    const currentInput = inputText
    const currentFile = selectedFile
    setInputText('')
    setSelectedFile(null)
    setLoading(true)

    try {
      if (currentFile) {
        const formData = new FormData()
        formData.append('file', currentFile)
        formData.append('query', currentInput || `Uploading evidence document: ${currentFile.name}`)
        formData.append('search_type', searchType)
        formData.append('enable_task_execution', 'true')
        formData.append('model_provider', selectedModel)
        
        if (sessionId) {
          formData.append('session_id', sessionId)
        }
        
        const response = await api.post('/rag/ask-with-file', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        
        const ragData = response.data
        
        if (ragData.session_id) {
          setSessionId(ragData.session_id)
          console.log('📝 Session ID stored:', ragData.session_id)
        }
        
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: ragData.answer,
          sender: 'assistant',
          timestamp: new Date(),
          metadata: {
            searchType: ragData.search_type,
            sources: ragData.sources,
            taskCreated: ragData.task_created,
            taskId: ragData.task_id,
            taskType: ragData.task_type,
          },
        }

        setMessages((prev) => [...prev, assistantMessage])
      } else {
        const response = await api.post('/rag/ask', {
          query: currentInput,
          search_type: searchType,
          max_results: 5,
          enable_task_execution: true,
          model_provider: selectedModel,
          session_id: sessionId
        })
        
        const ragData = response.data
        
        if (ragData.session_id) {
          setSessionId(ragData.session_id)
          console.log('📝 Session ID stored:', ragData.session_id)
        }
        
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: ragData.answer,
          sender: 'assistant',
          timestamp: new Date(),
          metadata: {
            searchType: ragData.search_type,
            sources: ragData.sources,
            taskCreated: ragData.task_created,
            taskId: ragData.task_id,
            taskType: ragData.task_type,
          },
        }

        setMessages((prev) => [...prev, assistantMessage])
      }
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

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      console.log('📎 File selected:', file.name)
    }
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        setAudioBlob(audioBlob)
        await transcribeAudio(audioBlob)
        stream.getTracks().forEach(track => track.stop())
      }

      mediaRecorder.start()
      setIsRecording(true)
    } catch (error: any) {
      console.error('❌ Error accessing microphone:', error)
      alert(`Could not access microphone: ${error.message}`)
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }

  const transcribeAudio = async (audioBlob: Blob) => {
    try {
      setLoading(true)
      const formData = new FormData()
      formData.append('audio', audioBlob, 'recording.webm')
      
      const response = await api.post('/rag/transcribe', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      
      const transcribedText = response.data.text || ''
      setInputText(prev => {
        console.log('✅ Transcription:', transcribedText)
        return transcribedText
      })
    } catch (error: any) {
      console.error('❌ Transcription error:', error)
      setInputText('⚠️ Transcription failed - please type your message')
    } finally {
      setLoading(false)
      setAudioBlob(null)
    }
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
              <Box display="flex" gap={1} alignItems="flex-end">
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileSelect}
                  style={{ display: 'none' }}
                  accept=".txt,.pdf,.doc,.docx,.json"
                />
                <Button
                  variant="outlined"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={loading}
                  sx={{ minWidth: 'auto', px: 2 }}
                  title="Attach file"
                >
                  <AttachFile />
                </Button>
                <Button
                  variant={isRecording ? 'contained' : 'outlined'}
                  color={isRecording ? 'error' : 'primary'}
                  onClick={isRecording ? stopRecording : startRecording}
                  disabled={loading}
                  sx={{ minWidth: 'auto', px: 2 }}
                  title={isRecording ? 'Stop recording' : 'Voice input'}
                >
                  {isRecording ? <Stop /> : <Mic />}
                </Button>
                <TextField
                  fullWidth
                  multiline
                  maxRows={3}
                  placeholder={
                    isRecording 
                      ? "🎤 Recording... Click stop when done" 
                      : sessionId
                        ? "Continue the conversation..." 
                        : selectedFile 
                          ? "Describe your document or ask questions..." 
                          : "First, click 📎 to upload a document to start"
                  }
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyPress={handleKeyPress}
                  disabled={loading || isRecording}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      bgcolor: isRecording ? 'error.50' : selectedFile ? 'success.50' : 'background.paper'
                    }
                  }}
                />
                <Button
                  variant="contained"
                  onClick={handleSendMessage}
                  disabled={loading || (!sessionId && !selectedFile) || !inputText.trim()}
                  sx={{ minWidth: 'auto', px: 2 }}
                  title={
                    !sessionId && !selectedFile 
                      ? "Please attach a document to start" 
                      : !inputText.trim()
                        ? "Please type a message"
                        : "Send message"
                  }
                >
                  <Send />
                </Button>
              </Box>
              
              {selectedFile && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  📎 File attached: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(2)} KB)
                  <Button size="small" onClick={() => setSelectedFile(null)} sx={{ ml: 2 }}>
                    Remove
                  </Button>
                </Alert>
              )}
              
              {sessionId && (
                <Alert severity="success" sx={{ mt: 1 }}>
                  💬 Conversation active (Session: {sessionId.substring(0, 8)}...)
                </Alert>
              )}
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