import React from 'react'
import { useAuth } from '../contexts/AuthContext'
import SuperAdminDashboard from '../components/dashboards/SuperAdminDashboard'
import AgencyAdminDashboard from '../components/dashboards/AgencyAdminDashboard'
import AgencySeniorManagementDashboard from '../components/dashboards/AgencySeniorManagementDashboard'
import AgencyUserDashboard from '../components/dashboards/AgencyUserDashboard'
import AnalystDashboard from '../components/dashboards/AnalystDashboard'
import {
  Box,
  Typography,
  Alert,
} from '@mui/material'

const DashboardPage: React.FC = () => {
  const { user } = useAuth()

  if (!user) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          User not authenticated. Please log in again.
        </Alert>
      </Box>
    )
  }

  // Role-based dashboard rendering
  const renderDashboard = () => {
    const roleName = user.role?.name?.toLowerCase()
    
    switch (roleName) {
      case 'super_admin':
        return <SuperAdminDashboard />
      case 'admin':
        return <AgencyAdminDashboard />
      case 'agency_admin':
        return <AgencyAdminDashboard />
      case 'agency_senior_management':
        return <AgencySeniorManagementDashboard />
      case 'auditor':
        return <AgencyUserDashboard />
      case 'analyst':
        return <AnalystDashboard />
      case 'agency_user':
        return <AgencyUserDashboard />
      case 'viewer':
        return <AgencyUserDashboard />
      default:
        return (
          <Box sx={{ p: 3 }}>
            <Typography variant="h4" gutterBottom>
              Dashboard
            </Typography>
            <Alert severity="warning">
              Dashboard not configured for role: {user.role?.name || 'Unknown'}
              <br />
              Using default Agency User dashboard.
            </Alert>
            <AgencyUserDashboard />
          </Box>
        )
    }
  }

  return renderDashboard()
}

export default DashboardPage