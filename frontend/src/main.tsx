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

// Create theme with refreshing teal/green color palette
const theme = createTheme({
  palette: {
    primary: {
      main: '#14b8a6', // Teal-500 - modern, professional, calming
      light: '#5eead4', // Teal-300
      dark: '#0f766e', // Teal-700
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#10b981', // Emerald-500 - complementary green
      light: '#6ee7b7', // Emerald-300
      dark: '#047857', // Emerald-700
      contrastText: '#ffffff',
    },
    background: {
      default: '#f0fdf4', // Green-50 - very light green tint
      paper: '#ffffff',
    },
    text: {
      primary: '#0f172a', // Slate-900 - darker for better readability
      secondary: '#475569', // Slate-600 - softer secondary text
    },
  },
  typography: {
    fontFamily: '"Montserrat", "Inter", "Arial", "Helvetica", sans-serif',
    h1: {
      fontFamily: '"Montserrat", sans-serif',
      fontWeight: 700,
      color: '#0f172a', // Slate-900
    },
    h2: {
      fontFamily: '"Montserrat", sans-serif',
      fontWeight: 700,
      color: '#0f172a',
    },
    h3: {
      fontFamily: '"Montserrat", sans-serif',
      fontWeight: 700,
      color: '#0f172a',
    },
    h4: {
      fontFamily: '"Montserrat", sans-serif',
      fontWeight: 700,
      color: '#0f172a',
    },
    h5: {
      fontFamily: '"Montserrat", sans-serif',
      fontWeight: 600,
      color: '#0f172a',
    },
    h6: {
      fontFamily: '"Montserrat", sans-serif',
      fontWeight: 600,
      color: '#0f172a',
    },
    subtitle1: {
      fontFamily: '"Montserrat", sans-serif',
      fontWeight: 400,
    },
    subtitle2: {
      fontFamily: '"Montserrat", sans-serif',
      fontWeight: 400,
    },
    body1: {
      fontFamily: '"Montserrat", sans-serif',
      fontWeight: 400,
    },
    body2: {
      fontFamily: '"Montserrat", sans-serif',
      fontWeight: 400,
    },
    button: {
      fontFamily: '"Montserrat", sans-serif',
      fontWeight: 500,
    },
  },
  components: {
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#14b8a6', // Teal-500
          boxShadow: '0 2px 4px 0 rgba(20, 184, 166, 0.2)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          fontFamily: '"Montserrat", sans-serif',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
          borderRadius: '8px',
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          '&.Mui-selected': {
            backgroundColor: 'rgba(20, 184, 166, 0.08)', // Teal with transparency
            '&:hover': {
              backgroundColor: 'rgba(20, 184, 166, 0.12)',
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