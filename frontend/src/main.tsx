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

// Create theme with Quantique Analytica branding colors (red from logo)
const theme = createTheme({
  palette: {
    primary: {
      main: '#D32F2F', // Quantique Analytica red from logo
      light: '#F44336',
      dark: '#B71C1C',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#424242', // Dark gray for secondary elements
      light: '#616161',
      dark: '#212121',
      contrastText: '#ffffff',
    },
    background: {
      default: '#fafafa',
      paper: '#ffffff',
    },
    text: {
      primary: '#333333', // Dark text matching logo
      secondary: '#666666',
    },
  },
  typography: {
    fontFamily: '"Inter", "Arial", "Helvetica", sans-serif',
    h4: {
      fontWeight: 600,
      color: '#333333',
    },
    h5: {
      fontWeight: 600,
      color: '#333333',
    },
    h6: {
      fontWeight: 600,
      color: '#333333',
    },
  },
  components: {
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#D32F2F', // Match logo red
          boxShadow: '0 2px 4px 0 rgba(211, 47, 47, 0.2)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
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
            backgroundColor: 'rgba(211, 47, 47, 0.08)',
            '&:hover': {
              backgroundColor: 'rgba(211, 47, 47, 0.12)',
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