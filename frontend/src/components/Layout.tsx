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
  Psychology,
  People,
  AccountCircle,
  Logout,
  SmartToy,
  Business,
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
    { text: 'Dashboard', icon: Dashboard, path: '/dashboard' },
    { text: 'Projects', icon: Assignment, path: '/projects' },
    { text: 'Controls', icon: Security, path: '/controls' },
    { text: 'Evidence', icon: Description, path: '/evidence' },
    { text: 'Reports', icon: Assessment, path: '/reports' },
    { text: 'AI Assistant', icon: Psychology, path: '/rag' },
    { text: 'Agent Tasks', icon: SmartToy, path: '/agent-tasks' },
    { text: 'Agencies', icon: Business, path: '/agencies' },
    { text: 'Users', icon: People, path: '/users' },
  ]

  const drawer = (
    <div>
      <Box sx={{ p: 3, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <QuantiqueAnalyticaLogo size="xlarge" />
      </Box>
      <Divider />
      <List>
                  {menuItems.map((item) => {
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
            >
              <MenuItem onClick={handleClose}>
                <ListItemIcon>
                  <AccountCircle fontSize="small" />
                </ListItemIcon>
                <ListItemText>Profile</ListItemText>
              </MenuItem>
              <MenuItem onClick={handleLogout}>
                <ListItemIcon>
                  <Logout fontSize="small" />
                </ListItemIcon>
                <ListItemText>Logout</ListItemText>
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