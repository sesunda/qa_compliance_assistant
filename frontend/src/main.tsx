import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from 'react-query'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import { Toaster } from 'react-hot-toast'
import App from './App'
import { AuthProvider } from './contexts/AuthContext'

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

// Create theme with modern enterprise color palette
const theme = createTheme({
  palette: {
    primary: {
      main: '#006D77', // Deep teal - professional, trustworthy
      light: '#83C5BE', // Light teal - softer accent
      dark: '#004B50', // Darker teal - sidebar/emphasis
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#83C5BE', // Soft teal - complementary
      light: '#B8D8D3', // Very light teal
      dark: '#5FA8A0', // Medium teal
      contrastText: '#1A1A1A',
    },
    error: {
      main: '#FF6B6B', // Accent red - warm, attention-grabbing
      light: '#FF9999',
      dark: '#E65555',
      contrastText: '#ffffff',
    },
    background: {
      default: '#EDF6F9', // Light blue-tinted background
      paper: '#FFFFFF', // Pure white for cards
    },
    text: {
      primary: '#1A1A1A', // Near black - excellent readability
      secondary: '#4F4F4F', // Medium gray - subtle text
    },
  },
  typography: {
    fontFamily: '"Montserrat", "Segoe UI", "Roboto", "Helvetica Neue", sans-serif',
    h1: {
      fontFamily: '"Montserrat", sans-serif',
      fontWeight: 700,
      fontSize: '2.5rem',
      lineHeight: 1.2,
      color: '#1A1A1A',
    },
    h2: {
      fontFamily: '"Montserrat", sans-serif',
      fontWeight: 700,
      fontSize: '2rem',
      lineHeight: 1.3,
      color: '#1A1A1A',
    },
    h3: {
      fontFamily: '"Montserrat", sans-serif',
      fontWeight: 600,
      fontSize: '1.75rem',
      lineHeight: 1.4,
      color: '#1A1A1A',
    },
    h4: {
      fontFamily: '"Montserrat", sans-serif',
      fontWeight: 600,
      fontSize: '1.5rem',
      lineHeight: 1.4,
      color: '#1A1A1A',
    },
    h5: {
      fontFamily: '"Montserrat", sans-serif',
      fontWeight: 600,
      fontSize: '1.25rem',
      lineHeight: 1.5,
      color: '#1A1A1A',
    },
    h6: {
      fontFamily: '"Montserrat", sans-serif',
      fontWeight: 600,
      fontSize: '1rem',
      lineHeight: 1.5,
      color: '#1A1A1A',
    },
    subtitle1: {
      fontFamily: '"Montserrat", sans-serif',
      fontWeight: 500,
      fontSize: '1rem',
      lineHeight: 1.75,
    },
    subtitle2: {
      fontFamily: '"Montserrat", sans-serif',
      fontWeight: 500,
      fontSize: '0.875rem',
      lineHeight: 1.57,
    },
    body1: {
      fontFamily: '"Montserrat", sans-serif',
      fontWeight: 400,
      fontSize: '1rem',
      lineHeight: 1.5,
    },
    body2: {
      fontFamily: '"Montserrat", sans-serif',
      fontWeight: 400,
      fontSize: '0.875rem',
      lineHeight: 1.43,
    },
    button: {
      fontFamily: '"Montserrat", sans-serif',
      fontWeight: 600,
      textTransform: 'none',
    },
    caption: {
      fontFamily: '"Montserrat", sans-serif',
      fontWeight: 400,
      fontSize: '0.75rem',
      lineHeight: 1.66,
      color: '#4F4F4F',
    },
  },
  shape: {
    borderRadius: 8,
  },
  shadows: [
    'none',
    '0px 1px 2px rgba(0, 0, 0, 0.05)',
    '0px 1px 3px rgba(0, 0, 0, 0.1), 0px 1px 2px rgba(0, 0, 0, 0.06)',
    '0px 4px 6px -1px rgba(0, 0, 0, 0.1), 0px 2px 4px -1px rgba(0, 0, 0, 0.06)',
    '0px 10px 15px -3px rgba(0, 0, 0, 0.1), 0px 4px 6px -2px rgba(0, 0, 0, 0.05)',
    '0px 20px 25px -5px rgba(0, 0, 0, 0.1), 0px 10px 10px -5px rgba(0, 0, 0, 0.04)',
    '0px 25px 50px -12px rgba(0, 0, 0, 0.25)',
    '0px 2px 4px rgba(0, 109, 119, 0.1)',
    '0px 4px 8px rgba(0, 109, 119, 0.12)',
    '0px 8px 16px rgba(0, 109, 119, 0.15)',
    '0px 12px 24px rgba(0, 109, 119, 0.18)',
    '0px 16px 32px rgba(0, 109, 119, 0.2)',
    '0px 20px 40px rgba(0, 109, 119, 0.22)',
    '0px 24px 48px rgba(0, 109, 119, 0.25)',
    '0px 2px 8px rgba(0, 0, 0, 0.08)',
    '0px 4px 12px rgba(0, 0, 0, 0.1)',
    '0px 8px 20px rgba(0, 0, 0, 0.12)',
    '0px 12px 28px rgba(0, 0, 0, 0.15)',
    '0px 16px 36px rgba(0, 0, 0, 0.18)',
    '0px 20px 44px rgba(0, 0, 0, 0.2)',
    '0px 24px 52px rgba(0, 0, 0, 0.22)',
    '0px 28px 60px rgba(0, 0, 0, 0.25)',
    '0px 32px 68px rgba(0, 0, 0, 0.28)',
    '0px 36px 76px rgba(0, 0, 0, 0.3)',
    '0px 40px 84px rgba(0, 0, 0, 0.32)',
  ],
  components: {
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#006D77',
          borderBottom: '1px solid rgba(0, 0, 0, 0.08)',
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: '#004B50',
          color: '#FFFFFF',
          borderRight: 'none',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          borderRadius: '8px',
          padding: '8px 16px',
          fontSize: '0.875rem',
        },
        contained: {
          boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
          '&:hover': {
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
          },
        },
        containedPrimary: {
          backgroundColor: '#006D77',
          '&:hover': {
            backgroundColor: '#005864',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundColor: '#FFFFFF',
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
          borderRadius: '12px',
          border: '1px solid rgba(0, 0, 0, 0.05)',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
        elevation1: {
          boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        },
        elevation2: {
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
        },
        elevation3: {
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          color: 'rgba(255, 255, 255, 0.85)',
          borderRadius: '6px',
          margin: '4px 8px',
          '&:hover': {
            backgroundColor: 'rgba(255, 255, 255, 0.08)',
          },
          '&.Mui-selected': {
            backgroundColor: 'rgba(131, 197, 190, 0.2)',
            color: '#FFFFFF',
            '&:hover': {
              backgroundColor: 'rgba(131, 197, 190, 0.28)',
            },
            '& .MuiListItemIcon-root': {
              color: '#83C5BE',
            },
          },
        },
      },
    },
    MuiListItemIcon: {
      styleOverrides: {
        root: {
          color: 'rgba(255, 255, 255, 0.7)',
          minWidth: 40,
        },
      },
    },
    MuiListItemText: {
      styleOverrides: {
        primary: {
          fontSize: '0.875rem',
          fontWeight: 500,
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: '6px',
          fontWeight: 500,
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            '&:hover fieldset': {
              borderColor: '#83C5BE',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#006D77',
            },
          },
        },
      },
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <AuthProvider>
            <App />
            <Toaster position="top-right" />
          </AuthProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </BrowserRouter>
  </React.StrictMode>,
)