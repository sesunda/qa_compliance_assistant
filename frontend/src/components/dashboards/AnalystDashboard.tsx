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
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
} from '@mui/material';
import {
  Security,
  Assessment,
  BugReport,
  Speed,
  CheckCircle,
  Warning,
  Assignment,
  SearchOff,
  Analytics,
  Science,
} from '@mui/icons-material';

const AnalystDashboard: React.FC = () => {
  const analystMetrics = {
    activeAssessments: 4,
    vulnerabilitiesFound: 23,
    controlsReviewed: 67,
    findingsResolved: 18,
    assessmentAccuracy: 94,
  };

  const currentAssessments = [
    { 
      id: 1, 
      name: 'Network Security Assessment', 
      framework: 'NIST CSF', 
      progress: 78,
      priority: 'High',
      dueDate: '2025-11-15'
    },
    { 
      id: 2, 
      name: 'Access Control Review', 
      framework: 'FISMA', 
      progress: 45,
      priority: 'Medium',
      dueDate: '2025-11-25'
    },
    { 
      id: 3, 
      name: 'Data Protection Audit', 
      framework: 'SOC 2', 
      progress: 92,
      priority: 'High',
      dueDate: '2025-11-08'
    },
    { 
      id: 4, 
      name: 'Incident Response Testing', 
      framework: 'ISO 27001', 
      progress: 23,
      priority: 'Low',
      dueDate: '2025-12-01'
    },
  ];

  const criticalFindings = [
    { 
      control: 'AC-2 (Account Management)', 
      severity: 'High', 
      status: 'Open',
      description: 'Privileged accounts not properly reviewed',
      daysOpen: 5
    },
    { 
      control: 'SC-8 (Transmission Confidentiality)', 
      severity: 'Medium', 
      status: 'In Progress',
      description: 'Unencrypted data transmission detected',
      daysOpen: 12
    },
    { 
      control: 'IR-4 (Incident Handling)', 
      severity: 'High', 
      status: 'Open',
      description: 'Incident response plan outdated',
      daysOpen: 8
    },
  ];

  const recentActivities = [
    { action: 'Completed vulnerability scan for Web Applications', time: '1 hour ago', type: 'success' },
    { action: 'Found critical finding in AC-6 control', time: '3 hours ago', type: 'warning' },
    { action: 'Updated risk assessment for Cloud Infrastructure', time: '5 hours ago', type: 'info' },
    { action: 'Submitted evidence package for SOC 2', time: '1 day ago', type: 'success' },
  ];

  const technicalStats = {
    scanAccuracy: 96,
    falsePositives: 3,
    avgResolutionTime: '4.2 days',
    toolsUsed: 12,
  };

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" gutterBottom>
          Security Analyst Dashboard
        </Typography>
        <Box display="flex" gap={2}>
          <Button variant="contained" color="primary" startIcon={<Science />}>
            Run Analysis
          </Button>
          <Button variant="outlined" startIcon={<Analytics />}>
            Generate Report
          </Button>
        </Box>
      </Box>
      
      <Grid container spacing={3}>
        {/* Analyst Metrics */}
        <Grid item xs={12} md={6} lg={2.4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Assessment color="primary" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Active Assessments
                  </Typography>
                  <Typography variant="h4">
                    {analystMetrics.activeAssessments}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6} lg={2.4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <BugReport color="error" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Vulnerabilities
                  </Typography>
                  <Typography variant="h4">
                    {analystMetrics.vulnerabilitiesFound}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6} lg={2.4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Security color="info" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Controls Reviewed
                  </Typography>
                  <Typography variant="h4">
                    {analystMetrics.controlsReviewed}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6} lg={2.4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <CheckCircle color="success" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Findings Resolved
                  </Typography>
                  <Typography variant="h4">
                    {analystMetrics.findingsResolved}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6} lg={2.4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Speed color="secondary" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Accuracy Rate
                  </Typography>
                  <Typography variant="h4">
                    {analystMetrics.assessmentAccuracy}%
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Technical Performance */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Technical Performance Metrics
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Box>
                    <Typography color="textSecondary" variant="body2">
                      Scan Accuracy
                    </Typography>
                    <Typography variant="h5" color="primary">
                      {technicalStats.scanAccuracy}%
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box>
                    <Typography color="textSecondary" variant="body2">
                      False Positives
                    </Typography>
                    <Typography variant="h5" color="secondary">
                      {technicalStats.falsePositives}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box>
                    <Typography color="textSecondary" variant="body2">
                      Avg Resolution Time
                    </Typography>
                    <Typography variant="h5" color="info.main">
                      {technicalStats.avgResolutionTime}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box>
                    <Typography color="textSecondary" variant="body2">
                      Tools Utilized
                    </Typography>
                    <Typography variant="h5" color="warning.main">
                      {technicalStats.toolsUsed}
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Analyst Tools
              </Typography>
              <Box display="flex" flexDirection="column" gap={2}>
                <Button variant="outlined" fullWidth startIcon={<BugReport />}>
                  Vulnerability Scanner
                </Button>
                <Button variant="outlined" fullWidth startIcon={<Security />}>
                  Control Assessment
                </Button>
                <Button variant="outlined" fullWidth startIcon={<SearchOff />}>
                  Penetration Testing
                </Button>
                <Button variant="outlined" fullWidth startIcon={<Analytics />}>
                  Risk Analysis
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Current Assessments */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Current Security Assessments
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Assessment Name</TableCell>
                    <TableCell>Framework</TableCell>
                    <TableCell>Progress</TableCell>
                    <TableCell>Priority</TableCell>
                    <TableCell>Due Date</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {currentAssessments.map((assessment) => (
                    <TableRow key={assessment.id}>
                      <TableCell>{assessment.name}</TableCell>
                      <TableCell>
                        <Chip label={assessment.framework} size="small" />
                      </TableCell>
                      <TableCell>
                        <Box display="flex" alignItems="center">
                          <LinearProgress
                            variant="determinate"
                            value={assessment.progress}
                            sx={{ width: 100, mr: 2 }}
                          />
                          <Typography variant="body2">
                            {assessment.progress}%
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={assessment.priority}
                          color={
                            assessment.priority === 'High' ? 'error' :
                            assessment.priority === 'Medium' ? 'warning' : 'default'
                          }
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{assessment.dueDate}</TableCell>
                      <TableCell>
                        <Button size="small" startIcon={<Assignment />}>
                          Continue
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>

        {/* Critical Findings */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Critical Security Findings
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Control</TableCell>
                    <TableCell>Severity</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Description</TableCell>
                    <TableCell>Days Open</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {criticalFindings.map((finding, index) => (
                    <TableRow key={index}>
                      <TableCell>{finding.control}</TableCell>
                      <TableCell>
                        <Chip
                          label={finding.severity}
                          color={finding.severity === 'High' ? 'error' : 'warning'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={finding.status}
                          color={finding.status === 'Open' ? 'error' : 'warning'}
                          variant="outlined"
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{finding.description}</TableCell>
                      <TableCell>
                        <Typography 
                          color={finding.daysOpen > 10 ? 'error.main' : 'text.primary'}
                        >
                          {finding.daysOpen}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>

        {/* Recent Activities */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent Analysis Activities
            </Typography>
            <List dense>
              {recentActivities.map((activity, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    {activity.type === 'success' && <CheckCircle color="success" />}
                    {activity.type === 'warning' && <Warning color="warning" />}
                    {activity.type === 'info' && <Security color="info" />}
                  </ListItemIcon>
                  <ListItemText
                    primary={activity.action}
                    secondary={activity.time}
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

export default AnalystDashboard;