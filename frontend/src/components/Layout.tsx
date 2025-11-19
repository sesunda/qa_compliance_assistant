import React, { useState } from 'react'
import {
  AppBar,
  Box,
  CssBaseline,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  Button,
  Menu,
  MenuItem,
  Avatar,
  Divider,
} from '@mui/material'
import {
  Menu as MenuIcon,
  Dashboard,
  Assignment,
  Security,
  Description,
  Assessment,
  People,
  AccountCircle,
  Logout,
  SmartToy,
  Business,
  BugReport,
  Policy,
  RateReview,
} from '@mui/icons-material'
import { useLocation, Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import QuantiqueAnalyticaLogo from './QuantiqueAnalyticaLogo'

const drawerWidth = 240

interface LayoutProps {
  children: React.ReactNode
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen)
  }

  const handleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleClose = () => {
    setAnchorEl(null)
  }

  const handleLogout = () => {
    logout()
    handleClose()
    navigate('/login')
  }

  const menuItems = [
    { text: 'Dashboard', icon: Dashboard, path: '/dashboard', roles: ['auditor', 'analyst', 'viewer', 'super_admin', 'agency_admin', 'senior_management'] },
    { text: 'Assessments', icon: Policy, path: '/assessments', roles: ['auditor', 'analyst', 'super_admin', 'agency_admin'] },
    { text: 'Findings', icon: BugReport, path: '/findings', roles: ['auditor', 'analyst', 'super_admin', 'agency_admin'] },
    { text: 'QA Review', icon: RateReview, path: '/qa-review', roles: ['auditor', 'super_admin', 'agency_admin'] },
    { text: 'Controls', icon: Security, path: '/controls', roles: ['auditor', 'viewer', 'super_admin', 'agency_admin', 'senior_management'] },
    { text: 'Evidence', icon: Description, path: '/evidence', roles: ['auditor', 'analyst', 'viewer', 'super_admin', 'agency_admin'] },
    { text: 'Projects', icon: Assignment, path: '/projects', roles: ['auditor', 'viewer', 'super_admin', 'agency_admin', 'senior_management'] },
    { text: 'Reports', icon: Assessment, path: '/reports', roles: ['auditor', 'analyst', 'viewer', 'super_admin', 'agency_admin', 'senior_management'] },
    { text: 'Agentic Chat', icon: SmartToy, path: '/agentic-chat', roles: ['auditor', 'analyst', 'super_admin', 'agency_admin'] },
    { text: 'Agent Tasks', icon: SmartToy, path: '/agent-tasks', roles: ['auditor', 'analyst', 'super_admin', 'agency_admin'] },
    { text: 'Agencies', icon: Business, path: '/agencies', roles: ['super_admin'] },
    { text: 'Users', icon: People, path: '/users', roles: ['super_admin', 'agency_admin'] },
  ]

  // Filter menu items based on user role
  const filteredMenuItems = menuItems.filter(item => {
    const userRole = (user?.role?.name || '').toLowerCase()
    return !item.roles || item.roles.includes(userRole)
  })

  const drawer = (
    <div>
      <Box sx={{ 
        p: 3, 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        backgroundColor: '#003B3F'
      }}>
        <QuantiqueAnalyticaLogo size="xlarge" />
      </Box>
      <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.12)' }} />
      <List sx={{ px: 1 }}>
                  {filteredMenuItems.map((item) => {
            const IconComponent = item.icon;
            return (
              <ListItem key={item.text} disablePadding>
                <ListItemButton
                  component={Link}
                  to={item.path}
                  selected={location.pathname === item.path}
                >
                  <ListItemIcon>
                    <IconComponent />
                  </ListItemIcon>
                  <ListItemText primary={item.text} />
                </ListItemButton>
              </ListItem>
            );
          })}
      </List>
    </div>
  )

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          
          {/* Show logo on mobile when drawer is closed */}
          <Box sx={{ display: { xs: 'flex', sm: 'none' }, mr: 2 }}>
            <QuantiqueAnalyticaLogo size="small" />
          </Box>
          
          <Typography variant="h4" noWrap component="div" sx={{ flexGrow: 1, fontWeight: 700, color: '#ffffff' }}>
            Compliance Assistant
          </Typography>
          <div>
            <Button
              size="large"
              aria-label="account of current user"
              aria-controls="menu-appbar"
              aria-haspopup="true"
              onClick={handleMenu}
              color="inherit"
              startIcon={<Avatar sx={{ width: 32, height: 32 }}>{user?.full_name?.charAt(0)}</Avatar>}
            >
              {user?.full_name}
            </Button>
            <Menu
              id="menu-appbar"
              anchorEl={anchorEl}
              anchorOrigin={{
                vertical: 'bottom',
                horizontal: 'right',
              }}
              keepMounted
              transformOrigin={{
                vertical: 'top',
                horizontal: 'right',
              }}
              open={Boolean(anchorEl)}
              onClose={handleClose}
              sx={{
                '& .MuiPaper-root': {
                  minWidth: '180px',
                  mt: 1,
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
                },
              }}
            >
              <MenuItem 
                onClick={handleClose}
                sx={{
                  py: 1.5,
                  px: 2,
                  '&:hover': {
                    backgroundColor: 'rgba(0, 109, 119, 0.08)',
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: 36, color: '#006D77' }}>
                  <AccountCircle fontSize="small" />
                </ListItemIcon>
                <ListItemText sx={{ '& .MuiTypography-root': { color: '#1A1A1A', fontWeight: 500 } }}>Profile</ListItemText>
              </MenuItem>
              <MenuItem 
                onClick={handleLogout}
                sx={{
                  py: 1.5,
                  px: 2,
                  '&:hover': {
                    backgroundColor: 'rgba(0, 109, 119, 0.08)',
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: 36, color: '#FF6B6B' }}>
                  <Logout fontSize="small" />
                </ListItemIcon>
                <ListItemText sx={{ '& .MuiTypography-root': { color: '#1A1A1A', fontWeight: 500 } }}>Logout</ListItemText>
              </MenuItem>
            </Menu>
          </div>
        </Toolbar>
      </AppBar>
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
        aria-label="mailbox folders"
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true,
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
        }}
      >
        <Toolbar />
        {children}
      </Box>
    </Box>
  )
}

export default Layout