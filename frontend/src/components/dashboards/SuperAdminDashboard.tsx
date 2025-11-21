import React, { useState, useEffect } from 'react';
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
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Security,
  Warning,
  CheckCircle,
  TrendingUp,
  Assignment,
  Shield,
} from '@mui/icons-material';
import { api } from '../../services/api';

interface DashboardMetrics {
  assessments: {
    total: number;
    active: number;
    completed: number;
  };
  findings: {
    total: number;
    open: number;
    resolved: number;
    overdue: number;
    by_severity: {
      critical: number;
      high: number;
      medium: number;
      low: number;
    };
  };
  controls: {
    total: number;
    tested: number;
    passed: number;
    failed: number;
    compliance_score: number;
  };
  evidence: {
    total: number;
  };
  recent_activity: {
    new_assessments: number;
    new_findings: number;
    resolved_findings: number;
  };
  risk_score: number;
}

const SuperAdminDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await api.get('/analytics/dashboard');
        setMetrics(response.data);
      } catch (err: any) {
        console.error('Failed to fetch dashboard data:', err);
        setError(err.response?.data?.detail || 'Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !metrics) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          <Typography variant="h6">Dashboard Load Error</Typography>
          <Typography>{error || 'Internal server error'}</Typography>
          <Typography variant="body2" sx={{ mt: 1 }}>
            This could mean:
          </Typography>
          <ul style={{ margin: '8px 0' }}>
            <li>The database migration hasn't been applied yet</li>
            <li>The API service is not responding</li>
            <li>You don't have permission to access dashboard data</li>
            <li>No data exists yet (first time setup)</li>
          </ul>
        </Alert>
      </Box>
    );
  }

  const systemHealth = metrics.controls.total > 0 
    ? Math.round((metrics.controls.passed / metrics.controls.total) * 100)
    : 0;

  const recentActivities = [
    { 
      action: `${metrics.recent_activity.new_assessments} new assessment${metrics.recent_activity.new_assessments !== 1 ? 's' : ''} created`, 
      time: 'Last 30 days', 
      type: 'info' 
    },
    { 
      action: `${metrics.recent_activity.new_findings} new finding${metrics.recent_activity.new_findings !== 1 ? 's' : ''} identified`, 
      time: 'Last 30 days', 
      type: metrics.findings.by_severity.critical > 0 ? 'error' : 'warning' 
    },
    { 
      action: `${metrics.recent_activity.resolved_findings} finding${metrics.recent_activity.resolved_findings !== 1 ? 's' : ''} resolved`, 
      time: 'Last 30 days', 
      type: 'success' 
    },
    { 
      action: `${metrics.findings.overdue} overdue finding${metrics.findings.overdue !== 1 ? 's' : ''}`, 
      time: 'Current', 
      type: metrics.findings.overdue > 0 ? 'error' : 'success' 
    },
  ];

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Typography variant="h5" gutterBottom>
        System Dashboard
      </Typography>
      
      <Grid container spacing={3}>
        {/* System Metrics */}
        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Assignment color="primary" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Total Assessments
                  </Typography>
                  <Typography variant="h4">
                    {metrics.assessments.total}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    {metrics.assessments.active} active
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
                <Warning color={metrics.findings.by_severity.critical > 0 ? "error" : "secondary"} sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Total Findings
                  </Typography>
                  <Typography variant="h4">
                    {metrics.findings.total}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    {metrics.findings.open} open
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
                <Shield color="info" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Controls
                  </Typography>
                  <Typography variant="h4">
                    {metrics.controls.total}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    {metrics.controls.passed} passed
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
                <Warning color={metrics.findings.by_severity.critical > 0 ? "error" : "warning"} sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Critical Findings
                  </Typography>
                  <Typography variant="h4">
                    {metrics.findings.by_severity.critical}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    {metrics.findings.by_severity.high} high severity
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
                System Health (Controls Passing)
              </Typography>
              <Box display="flex" alignItems="center" mb={2}>
                <Typography variant="h4" color="primary">
                  {systemHealth}%
                </Typography>
                <Shield sx={{ ml: 2, color: systemHealth >= 80 ? 'green' : systemHealth >= 60 ? 'orange' : 'red' }} />
              </Box>
              <LinearProgress
                variant="determinate"
                value={systemHealth}
                sx={{ 
                  height: 8, 
                  borderRadius: 4,
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: systemHealth >= 80 ? 'green' : systemHealth >= 60 ? 'orange' : 'red'
                  }
                }}
              />
              <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                {metrics.controls.passed} of {metrics.controls.total} controls passing
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Overall Compliance Score */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Compliance Score
              </Typography>
              <Box display="flex" alignItems="center" mb={2}>
                <Typography variant="h4" color="primary">
                  {metrics.controls.compliance_score}%
                </Typography>
                <TrendingUp sx={{ ml: 2, color: metrics.controls.compliance_score >= 80 ? 'green' : 'orange' }} />
              </Box>
              <LinearProgress
                variant="determinate"
                value={metrics.controls.compliance_score}
                sx={{ 
                  height: 8, 
                  borderRadius: 4,
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: metrics.controls.compliance_score >= 80 ? 'green' : metrics.controls.compliance_score >= 60 ? 'orange' : 'red'
                  }
                }}
              />
              <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                Risk Score: {metrics.risk_score}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Activities */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent Activity Summary
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