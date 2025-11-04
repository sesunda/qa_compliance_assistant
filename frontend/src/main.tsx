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
      main: '#C93E3E', // Quantique Analytica red from logo
      light: '#E57373',
      dark: '#B71C1C',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#2C2C2C', // Dark gray for secondary elements (matching logo text)
      light: '#616161',
      dark: '#000000',
      contrastText: '#ffffff',
    },
    background: {
      default: '#fafafa',
      paper: '#ffffff',
    },
    text: {
      primary: '#000000', // Pure black matching logo
      secondary: '#666666',
    },
  },
  typography: {
    fontFamily: '"Montserrat", "Inter", "Arial", "Helvetica", sans-serif',
    h1: {
      fontFamily: '"Montserrat", sans-serif',
      fontWeight: 700,
      color: '#000000',
    },
    h2: {
      fontFamily: '"Montserrat", sans-serif',
      fontWeight: 700,
      color: '#000000',
    },
    h3: {
      fontFamily: '"Montserrat", sans-serif',
      fontWeight: 700,
      color: '#000000',
    },
    h4: {
      fontFamily: '"Montserrat", sans-serif',
      fontWeight: 700,
      color: '#000000',
    },
    h5: {
      fontFamily: '"Montserrat", sans-serif',
      fontWeight: 600,
      color: '#000000',
    },
    h6: {
      fontFamily: '"Montserrat", sans-serif',
      fontWeight: 600,
      color: '#000000',
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
          backgroundColor: '#C93E3E', // Match logo red
          boxShadow: '0 2px 4px 0 rgba(201, 62, 62, 0.2)',
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
            backgroundColor: 'rgba(201, 62, 62, 0.08)',
            '&:hover': {
              backgroundColor: 'rgba(201, 62, 62, 0.12)',
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