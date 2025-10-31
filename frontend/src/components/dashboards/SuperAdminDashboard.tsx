import React from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  Security,
  Warning,
  CheckCircle,
  TrendingUp,
  Groups,
  Assignment,
  Shield,
} from '@mui/icons-material';

const SuperAdminDashboard: React.FC = () => {
  const systemMetrics = {
    totalAgencies: 12,
    totalUsers: 156,
    activeProjects: 45,
    criticalAlerts: 3,
    systemHealth: 98,
    complianceScore: 92,
  };

  const recentActivities = [
    { action: 'New agency onboarded', time: '2 hours ago', type: 'success' },
    { action: 'Critical control failed', time: '4 hours ago', type: 'error' },
    { action: 'System backup completed', time: '6 hours ago', type: 'info' },
    { action: 'User permissions updated', time: '8 hours ago', type: 'warning' },
  ];

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Typography variant="h4" gutterBottom>
        System Administration Dashboard
      </Typography>
      
      <Grid container spacing={3}>
        {/* System Metrics */}
        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Groups color="primary" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Total Agencies
                  </Typography>
                  <Typography variant="h4">
                    {systemMetrics.totalAgencies}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Groups color="secondary" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Total Users
                  </Typography>
                  <Typography variant="h4">
                    {systemMetrics.totalUsers}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Assignment color="info" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Active Projects
                  </Typography>
                  <Typography variant="h4">
                    {systemMetrics.activeProjects}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Warning color="error" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Critical Alerts
                  </Typography>
                  <Typography variant="h4">
                    {systemMetrics.criticalAlerts}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* System Health */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Health
              </Typography>
              <Box display="flex" alignItems="center" mb={2}>
                <Typography variant="h4" color="primary">
                  {systemMetrics.systemHealth}%
                </Typography>
                <Shield sx={{ ml: 2, color: 'green' }} />
              </Box>
              <LinearProgress
                variant="determinate"
                value={systemMetrics.systemHealth}
                sx={{ height: 8, borderRadius: 4 }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Overall Compliance Score */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Overall Compliance Score
              </Typography>
              <Box display="flex" alignItems="center" mb={2}>
                <Typography variant="h4" color="primary">
                  {systemMetrics.complianceScore}%
                </Typography>
                <TrendingUp sx={{ ml: 2, color: 'green' }} />
              </Box>
              <LinearProgress
                variant="determinate"
                value={systemMetrics.complianceScore}
                sx={{ height: 8, borderRadius: 4 }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Activities */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              System-wide Recent Activities
            </Typography>
            <List>
              {recentActivities.map((activity, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    {activity.type === 'success' && <CheckCircle color="success" />}
                    {activity.type === 'error' && <Warning color="error" />}
                    {activity.type === 'info' && <Security color="info" />}
                    {activity.type === 'warning' && <Warning color="warning" />}
                  </ListItemIcon>
                  <ListItemText
                    primary={activity.action}
                    secondary={activity.time}
                  />
                  <Chip
                    label={activity.type}
                    color={activity.type as any}
                    size="small"
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default SuperAdminDashboard;