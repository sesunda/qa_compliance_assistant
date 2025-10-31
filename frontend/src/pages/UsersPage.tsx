import React from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Grid,
} from '@mui/material'
import {
  People,
  Edit,
  Delete,
  PersonAdd,
  Block,
  CheckCircle,
} from '@mui/icons-material'
import { useAuth } from '../contexts/AuthContext'

const UsersPage: React.FC = () => {
  const { user } = useAuth()

  // Mock data for demonstration
  const users = [
    {
      id: 1,
      username: 'admin',
      email: 'admin@qca.com',
      full_name: 'System Administrator',
      role: 'super_admin',
      agency: 'QCA Administration',
      is_active: true,
      is_verified: true,
      last_login: '2024-01-15T10:30:00Z',
      created_at: '2024-01-01T00:00:00Z',
    },
    {
      id: 2,
      username: 'auditor1',
      email: 'auditor@agency.gov',
      full_name: 'John Auditor',
      role: 'auditor',
      agency: 'Government Agency',
      is_active: true,
      is_verified: true,
      last_login: '2024-01-14T15:45:00Z',
      created_at: '2024-01-02T00:00:00Z',
    },
    {
      id: 3,
      username: 'analyst1',
      email: 'analyst@company.com',
      full_name: 'Jane Analyst',
      role: 'analyst',
      agency: 'Tech Company',
      is_active: false,
      is_verified: true,
      last_login: '2024-01-10T09:15:00Z',
      created_at: '2024-01-03T00:00:00Z',
    },
  ]

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'super_admin':
        return 'error'
      case 'admin':
        return 'warning'
      case 'auditor':
        return 'info'
      case 'analyst':
        return 'success'
      case 'viewer':
        return 'default'
      default:
        return 'default'
    }
  }

  const getRoleLabel = (role: string) => {
    switch (role) {
      case 'super_admin':
        return 'Super Admin'
      case 'admin':
        return 'Admin'
      case 'auditor':
        return 'Auditor'
      case 'analyst':
        return 'Analyst'
      case 'viewer':
        return 'Viewer'
      default:
        return role
    }
  }

  const userStats = {
    total: users.length,
    active: users.filter(u => u.is_active).length,
    inactive: users.filter(u => !u.is_active).length,
    verified: users.filter(u => u.is_verified).length,
  }

  // Check if current user has permission to manage users
  const canManageUsers = user?.role?.permissions?.users?.includes('create') || false

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            User Management
          </Typography>
          <Typography variant="body1" color="textSecondary">
            Manage user accounts, roles, and permissions
          </Typography>
        </Box>
        {canManageUsers && (
          <Button
            variant="contained"
            startIcon={<PersonAdd />}
          >
            Add User
          </Button>
        )}
      </Box>

      {/* User Statistics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Users
              </Typography>
              <Typography variant="h4">{userStats.total}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Active Users
              </Typography>
              <Typography variant="h4" color="success.main">
                {userStats.active}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Inactive Users
              </Typography>
              <Typography variant="h4" color="error.main">
                {userStats.inactive}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Verified Users
              </Typography>
              <Typography variant="h4" color="info.main">
                {userStats.verified}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Users Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            System Users
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>User</TableCell>
                  <TableCell>Role</TableCell>
                  <TableCell>Agency</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Last Login</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {users.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell>
                      <Box>
                        <Typography variant="body2" fontWeight="bold">
                          {user.full_name}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          {user.username} • {user.email}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={getRoleLabel(user.role)}
                        color={getRoleColor(user.role) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{user.agency}</TableCell>
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={1}>
                        {user.is_active ? (
                          <CheckCircle color="success" fontSize="small" />
                        ) : (
                          <Block color="error" fontSize="small" />
                        )}
                        <Typography
                          variant="body2"
                          color={user.is_active ? 'success.main' : 'error.main'}
                        >
                          {user.is_active ? 'Active' : 'Inactive'}
                        </Typography>
                        {user.is_verified && (
                          <Chip
                            label="Verified"
                            size="small"
                            color="info"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    </TableCell>
                    <TableCell>
                      {user.last_login
                        ? new Date(user.last_login).toLocaleDateString()
                        : 'Never'
                      }
                    </TableCell>
                    <TableCell>
                      {canManageUsers && (
                        <>
                          <IconButton size="small" title="Edit">
                            <Edit fontSize="small" />
                          </IconButton>
                          <IconButton size="small" title="Delete">
                            <Delete fontSize="small" />
                          </IconButton>
                        </>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
                {users.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      <Box py={4}>
                        <People sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
                        <Typography variant="h6" color="textSecondary">
                          No users found
                        </Typography>
                      </Box>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  )
}

export default UsersPage