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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  Security,
  Assignment,
  Assessment,
  CheckCircle,
  Warning,
  Timeline,
  Visibility,
} from '@mui/icons-material';

const AgencyUserDashboard: React.FC = () => {
  const userMetrics = {
    assignedProjects: 3,
    completedTasks: 12,
    pendingTasks: 5,
    overdueTasks: 1,
    complianceScore: 85,
  };

  const myProjects = [
    { 
      id: 1, 
      name: 'FISMA Assessment Q4', 
      role: 'Lead Assessor', 
      status: 'In Progress', 
      progress: 68,
      dueDate: '2025-11-30'
    },
    { 
      id: 2, 
      name: 'SOC 2 Evidence Collection', 
      role: 'Evidence Collector', 
      status: 'Active', 
      progress: 45,
      dueDate: '2025-12-15'
    },
    { 
      id: 3, 
      name: 'Vulnerability Assessment', 
      role: 'Technical Reviewer', 
      status: 'Review', 
      progress: 90,
      dueDate: '2025-11-10'
    },
  ];

  const myTasks = [
    { task: 'Review AC-2 Control Implementation', project: 'FISMA Assessment Q4', priority: 'High', dueDate: '2025-11-05' },
    { task: 'Collect Network Diagrams', project: 'SOC 2 Evidence Collection', priority: 'Medium', dueDate: '2025-11-08' },
    { task: 'Validate Encryption Controls', project: 'FISMA Assessment Q4', priority: 'High', dueDate: '2025-11-12' },
    { task: 'Update Risk Register', project: 'Vulnerability Assessment', priority: 'Low', dueDate: '2025-11-15' },
  ];

  const recentActivities = [
    { action: 'Completed control assessment for AC-3', time: '2 hours ago', type: 'success' },
    { action: 'Uploaded evidence for IA-5', time: '4 hours ago', type: 'info' },
    { action: 'Task overdue: Review security logs', time: '1 day ago', type: 'warning' },
  ];

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" gutterBottom>
          My Dashboard
        </Typography>
        <Button variant="contained" color="primary" startIcon={<Timeline />}>
          View My Performance
        </Button>
      </Box>
      
      <Grid container spacing={3}>
        {/* Personal Metrics */}
        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Assignment color="primary" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Assigned Projects
                  </Typography>
                  <Typography variant="h4">
                    {userMetrics.assignedProjects}
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
                <CheckCircle color="success" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Completed Tasks
                  </Typography>
                  <Typography variant="h4">
                    {userMetrics.completedTasks}
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
                <Assessment color="info" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Pending Tasks
                  </Typography>
                  <Typography variant="h4">
                    {userMetrics.pendingTasks}
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
                    Overdue Tasks
                  </Typography>
                  <Typography variant="h4">
                    {userMetrics.overdueTasks}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Performance Score */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                My Performance Score
              </Typography>
              <Box display="flex" alignItems="center" mb={2}>
                <Typography variant="h4" color="primary">
                  {userMetrics.complianceScore}%
                </Typography>
                <Security sx={{ ml: 2, color: 'green' }} />
              </Box>
              <LinearProgress
                variant="determinate"
                value={userMetrics.complianceScore}
                sx={{ height: 8, borderRadius: 4 }}
              />
              <Typography variant="body2" color="textSecondary" mt={1}>
                Based on task completion and quality metrics
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Box display="flex" flexDirection="column" gap={2}>
                <Button variant="outlined" fullWidth startIcon={<Assignment />}>
                  View My Tasks
                </Button>
                <Button variant="outlined" fullWidth startIcon={<Assessment />}>
                  Submit Evidence
                </Button>
                <Button variant="outlined" fullWidth startIcon={<Visibility />}>
                  View Projects
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* My Projects */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              My Projects
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Project Name</TableCell>
                    <TableCell>My Role</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Progress</TableCell>
                    <TableCell>Due Date</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {myProjects.map((project) => (
                    <TableRow key={project.id}>
                      <TableCell>{project.name}</TableCell>
                      <TableCell>{project.role}</TableCell>
                      <TableCell>
                        <Chip
                          label={project.status}
                          color={project.status === 'In Progress' ? 'primary' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Box display="flex" alignItems="center">
                          <LinearProgress
                            variant="determinate"
                            value={project.progress}
                            sx={{ width: 100, mr: 1 }}
                          />
                          <Typography variant="body2">
                            {project.progress}%
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>{project.dueDate}</TableCell>
                      <TableCell>
                        <Button size="small" startIcon={<Visibility />}>
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>

        {/* My Tasks */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              My Pending Tasks
            </Typography>
            <List>
              {myTasks.map((task, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    <Assignment color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary={task.task}
                    secondary={`Project: ${task.project} | Due: ${task.dueDate}`}
                  />
                  <Chip
                    label={task.priority}
                    color={task.priority === 'High' ? 'error' : task.priority === 'Medium' ? 'warning' : 'default'}
                    size="small"
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>

        {/* Recent Activities */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent Activities
            </Typography>
            <List dense>
              {recentActivities.map((activity, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    {activity.type === 'success' && <CheckCircle color="success" />}
                    {activity.type === 'info' && <Security color="info" />}
                    {activity.type === 'warning' && <Warning color="warning" />}
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

export default AgencyUserDashboard;