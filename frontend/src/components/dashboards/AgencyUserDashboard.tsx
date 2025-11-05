import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from 'react-query';
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
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Security,
  Assignment,
  Assessment,
  CheckCircle,
  Warning,
  Timeline,
  Visibility,
  Description,
  RateReview,
  ThumbUp,
} from '@mui/icons-material';
import { fetchEvidence, EvidenceItem } from '../../services/evidence';
import { formatSingaporeDateTime } from '../../utils/datetime';

const AgencyUserDashboard: React.FC = () => {
  const navigate = useNavigate();
  
  // Fetch real evidence data
  const { data: evidenceItems, isLoading: isLoadingEvidence } = useQuery<EvidenceItem[]>(
    ['evidence'],
    fetchEvidence
  );
  
  // Calculate metrics from real data
  const pendingEvidence = evidenceItems?.filter(e => e.verification_status === 'pending') || [];
  const underReviewEvidence = evidenceItems?.filter(e => e.verification_status === 'under_review') || [];
  const approvedEvidence = evidenceItems?.filter(e => e.verification_status === 'approved') || [];
  const rejectedEvidence = evidenceItems?.filter(e => e.verification_status === 'rejected') || [];
  
  const userMetrics = {
    assignedProjects: 3,
    completedTasks: approvedEvidence.length,
    pendingTasks: pendingEvidence.length + underReviewEvidence.length,
    overdueTasks: rejectedEvidence.length, // Rejected evidence as "overdue" items needing rework
    complianceScore: evidenceItems && evidenceItems.length > 0 
      ? Math.round((approvedEvidence.length / evidenceItems.length) * 100)
      : 0,
  };

  // Sample projects data (can be replaced with real API data later)
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

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" gutterBottom>
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
                <Button 
                  variant="outlined" 
                  fullWidth 
                  startIcon={<Assignment />}
                  onClick={() => navigate('/evidence')}
                >
                  View My Evidence
                </Button>
                <Button 
                  variant="outlined" 
                  fullWidth 
                  startIcon={<Assessment />}
                  onClick={() => navigate('/evidence')}
                >
                  Submit Evidence
                </Button>
                <Button 
                  variant="outlined" 
                  fullWidth 
                  startIcon={<Visibility />}
                  onClick={() => navigate('/projects')}
                >
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
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                My Pending Tasks
              </Typography>
              <Button 
                size="small" 
                onClick={() => navigate('/evidence')}
                endIcon={<Description />}
              >
                View All Evidence
              </Button>
            </Box>
            
            {isLoadingEvidence ? (
              <Box display="flex" justifyContent="center" p={3}>
                <CircularProgress />
              </Box>
            ) : (
              <>
                {userMetrics.pendingTasks === 0 ? (
                  <Alert severity="info">No pending tasks at the moment</Alert>
                ) : (
                  <List>
                    {/* Evidence pending submission */}
                    {pendingEvidence.slice(0, 3).map((item) => (
                      <ListItem 
                        key={`pending-${item.id}`}
                        button
                        onClick={() => navigate('/evidence')}
                      >
                        <ListItemIcon>
                          <RateReview color="primary" />
                        </ListItemIcon>
                        <ListItemText
                          primary={item.title}
                          secondary={`Uploaded: ${formatSingaporeDateTime(item.uploaded_at)} | Needs submission for review`}
                        />
                        <Chip
                          label="Pending"
                          color="warning"
                          size="small"
                        />
                      </ListItem>
                    ))}
                    
                    {/* Evidence awaiting review */}
                    {underReviewEvidence.slice(0, 3).map((item) => (
                      <ListItem 
                        key={`review-${item.id}`}
                        button
                        onClick={() => navigate('/evidence')}
                      >
                        <ListItemIcon>
                          <ThumbUp color="info" />
                        </ListItemIcon>
                        <ListItemText
                          primary={item.title}
                          secondary={`Submitted: ${formatSingaporeDateTime(item.uploaded_at)} | Awaiting approval`}
                        />
                        <Chip
                          label="Under Review"
                          color="info"
                          size="small"
                        />
                      </ListItem>
                    ))}
                    
                    {(pendingEvidence.length + underReviewEvidence.length) > 6 && (
                      <ListItem>
                        <ListItemText 
                          primary={
                            <Typography variant="body2" color="textSecondary" align="center">
                              + {(pendingEvidence.length + underReviewEvidence.length) - 6} more tasks
                            </Typography>
                          }
                        />
                      </ListItem>
                    )}
                  </List>
                )}
              </>
            )}
          </Paper>
        </Grid>

        {/* Recent Activities */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent Evidence Activity
            </Typography>
            {isLoadingEvidence ? (
              <Box display="flex" justifyContent="center" p={2}>
                <CircularProgress size={24} />
              </Box>
            ) : (
              <List dense>
                {/* Show most recent evidence items */}
                {evidenceItems && evidenceItems.slice(0, 5).map((item) => {
                  let icon = <Description color="info" />;
                  let statusText = '';
                  
                  if (item.verification_status === 'approved') {
                    icon = <CheckCircle color="success" />;
                    statusText = 'Approved';
                  } else if (item.verification_status === 'rejected') {
                    icon = <Warning color="error" />;
                    statusText = 'Rejected';
                  } else if (item.verification_status === 'under_review') {
                    icon = <Assessment color="info" />;
                    statusText = 'Under Review';
                  } else {
                    icon = <Description color="action" />;
                    statusText = 'Uploaded';
                  }
                  
                  return (
                    <ListItem key={item.id}>
                      <ListItemIcon>
                        {icon}
                      </ListItemIcon>
                      <ListItemText
                        primary={`${statusText}: ${item.title.substring(0, 30)}${item.title.length > 30 ? '...' : ''}`}
                        secondary={formatSingaporeDateTime(item.created_at)}
                      />
                    </ListItem>
                  );
                })}
                
                {(!evidenceItems || evidenceItems.length === 0) && (
                  <ListItem>
                    <ListItemText 
                      primary="No recent activity"
                      secondary="Upload evidence to get started"
                    />
                  </ListItem>
                )}
              </List>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default AgencyUserDashboard;