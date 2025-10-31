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
  Button,
} from '@mui/material';
import {
  Security,
  Assignment,
  Groups,
  TrendingUp,
  Warning,
  Assessment,
  AccountBalance,
} from '@mui/icons-material';

const AgencyAdminDashboard: React.FC = () => {
  const agencyMetrics = {
    agencyName: 'Department of Homeland Security',
    totalProjects: 15,
    activeProjects: 8,
    completedProjects: 7,
    totalUsers: 45,
    complianceScore: 89,
    criticalFindings: 2,
    pendingReviews: 5,
  };

  const projectStatus = [
    { name: 'FISMA Assessment 2025', status: 'In Progress', progress: 75, priority: 'High' },
    { name: 'SOC 2 Type II', status: 'Planning', progress: 25, priority: 'Medium' },
    { name: 'NIST Cybersecurity Framework', status: 'Review', progress: 90, priority: 'High' },
    { name: 'ISO 27001 Certification', status: 'On Hold', progress: 60, priority: 'Low' },
  ];

  const upcomingDeadlines = [
    { task: 'FISMA Annual Assessment', deadline: '2025-11-15', daysLeft: 15 },
    { task: 'Vulnerability Scan Report', deadline: '2025-11-08', daysLeft: 8 },
    { task: 'Security Training Completion', deadline: '2025-12-01', daysLeft: 31 },
  ];

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" gutterBottom>
          {agencyMetrics.agencyName} Dashboard
        </Typography>
        <Button variant="contained" color="primary" startIcon={<Assessment />}>
          Generate Agency Report
        </Button>
      </Box>
      
      <Grid container spacing={3}>
        {/* Agency Overview Metrics */}
        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Assignment color="primary" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Total Projects
                  </Typography>
                  <Typography variant="h4">
                    {agencyMetrics.totalProjects}
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
                    Agency Users
                  </Typography>
                  <Typography variant="h4">
                    {agencyMetrics.totalUsers}
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
                <Security color="success" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Compliance Score
                  </Typography>
                  <Typography variant="h4">
                    {agencyMetrics.complianceScore}%
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
                    Critical Findings
                  </Typography>
                  <Typography variant="h4">
                    {agencyMetrics.criticalFindings}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Agency Compliance Score */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Agency Compliance Status
              </Typography>
              <Box display="flex" alignItems="center" mb={2}>
                <Typography variant="h4" color="primary">
                  {agencyMetrics.complianceScore}%
                </Typography>
                <TrendingUp sx={{ ml: 2, color: 'green' }} />
              </Box>
              <LinearProgress
                variant="determinate"
                value={agencyMetrics.complianceScore}
                sx={{ height: 10, borderRadius: 5 }}
              />
              <Typography variant="body2" color="textSecondary" mt={1}>
                Meeting federal compliance requirements
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Box display="flex" flexDirection="column" gap={2}>
                <Button variant="outlined" fullWidth startIcon={<Assignment />}>
                  Create New Project
                </Button>
                <Button variant="outlined" fullWidth startIcon={<Groups />}>
                  Manage Users
                </Button>
                <Button variant="outlined" fullWidth startIcon={<Assessment />}>
                  View Reports
                </Button>
                <Button variant="outlined" fullWidth startIcon={<AccountBalance />}>
                  Agency Settings
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Project Status Overview */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Project Status Overview
            </Typography>
            <List>
              {projectStatus.map((project, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    <Assignment color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary={project.name}
                    secondary={
                      <Box>
                        <Box display="flex" alignItems="center" mt={1}>
                          <LinearProgress
                            variant="determinate"
                            value={project.progress}
                            sx={{ flexGrow: 1, mr: 2, height: 6, borderRadius: 3 }}
                          />
                          <Typography variant="body2" color="textSecondary">
                            {project.progress}%
                          </Typography>
                        </Box>
                      </Box>
                    }
                  />
                  <Box display="flex" gap={1}>
                    <Chip
                      label={project.status}
                      color={project.status === 'In Progress' ? 'primary' : 'default'}
                      size="small"
                    />
                    <Chip
                      label={project.priority}
                      color={project.priority === 'High' ? 'error' : project.priority === 'Medium' ? 'warning' : 'default'}
                      size="small"
                    />
                  </Box>
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>

        {/* Upcoming Deadlines */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Upcoming Deadlines
            </Typography>
            <List dense>
              {upcomingDeadlines.map((item, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    <Warning color={item.daysLeft <= 10 ? 'error' : 'warning'} />
                  </ListItemIcon>
                  <ListItemText
                    primary={item.task}
                    secondary={`${item.daysLeft} days left`}
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

export default AgencyAdminDashboard;