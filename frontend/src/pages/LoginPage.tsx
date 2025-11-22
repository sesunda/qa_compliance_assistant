import React, { useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Container,
  Alert,
  InputAdornment,
  IconButton,
} from '@mui/material'
import { Visibility, VisibilityOff } from '@mui/icons-material'
import { useAuth } from '../contexts/AuthContext'
import { useNavigate } from 'react-router-dom'

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [coldStartMessage, setColdStartMessage] = useState('')
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setColdStartMessage('')

    if (!username || !password) {
      setError('Please enter both username and password')
      setLoading(false)
      return
    }

    // Show cold start message after 3 seconds if still loading
    const coldStartTimer = setTimeout(() => {
      if (loading) {
        setColdStartMessage('🔄 System is waking up from sleep mode... Please wait (10-15 seconds)')
      }
    }, 3000)

    try {
      const success = await login(username, password)
      clearTimeout(coldStartTimer)
      if (success) {
        navigate('/agentic-chat')
      } else {
        setError('Invalid username or password')
        setColdStartMessage('')
      }
    } catch (err: any) {
      clearTimeout(coldStartTimer)
      
      // Check if it's a cold start/timeout error
      if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        setError('System is taking longer than expected to wake up. Please try again in a moment.')
      } else if (err.response?.status === 502 || err.response?.status === 503) {
        setError('System is waking up. Please wait a moment and try again.')
      } else {
        setError('An unexpected error occurred')
      }
      setColdStartMessage('')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #006D77 0%, #83C5BE 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        overflow: 'hidden',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: '-50%',
          right: '-50%',
          width: '100%',
          height: '100%',
          background: 'radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%)',
          animation: 'float 20s ease-in-out infinite',
        },
        '@keyframes float': {
          '0%, 100%': { transform: 'translate(0, 0) rotate(0deg)' },
          '33%': { transform: 'translate(30px, -30px) rotate(120deg)' },
          '66%': { transform: 'translate(-20px, 20px) rotate(240deg)' },
        },
      }}
    >
      <Container component="main" maxWidth="xs" sx={{ position: 'relative', zIndex: 1 }}>
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              mb: 3,
            }}
          >
            {/* Company Logo */}
            <Box 
              component="img" 
              src="/assets/logo.png" 
              alt="Quantique Analytica"
              sx={{ 
                width: '280px', 
                height: 'auto',
                mb: 2,
                display: 'block',
                opacity: 1,
              }}
            />
            <Typography 
              component="h1" 
              variant="h4" 
              sx={{ 
                fontWeight: 700, 
                color: '#FFFFFF', 
                mt: 1,
                textAlign: 'center',
                letterSpacing: '-0.02em',
              }}
            >
              AI Compliance Assistant
            </Typography>
            <Typography 
              variant="h6" 
              sx={{ 
                mt: 1, 
                color: 'rgba(255, 255, 255, 0.9)',
                textAlign: 'center',
                fontWeight: 400,
              }}
            >
              Smarter Compliance through Context-Aware AI
            </Typography>
          </Box>
          
          <Card 
            sx={{ 
              width: '100%',
              backdropFilter: 'blur(20px)',
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.18)',
              border: '1px solid rgba(255, 255, 255, 0.3)',
              borderRadius: 3,
            }}
          >
            <CardContent sx={{ p: 4 }}>
            <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
              {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {error}
                </Alert>
              )}
              
              {coldStartMessage && (
                <Alert severity="info" sx={{ mb: 2 }}>
                  {coldStartMessage}
                </Alert>
              )}
              
              <TextField
                margin="normal"
                required
                fullWidth
                id="username"
                label="Username"
                name="username"
                autoComplete="username"
                autoFocus
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={loading}
              />
              
              <TextField
                margin="normal"
                required
                fullWidth
                name="password"
                label="Password"
                type={showPassword ? 'text' : 'password'}
                id="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        aria-label="toggle password visibility"
                        onClick={() => setShowPassword(!showPassword)}
                        edge="end"
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
              
              <Button
                type="submit"
                fullWidth
                variant="contained"
                sx={{ mt: 3, mb: 2 }}
                disabled={loading}
                size="large"
              >
                {loading ? 'Signing In...' : 'Sign In'}
              </Button>
            </Box>
          </CardContent>
        </Card>
        </Box>
      </Container>
    </Box>
  )
}

export default LoginPage