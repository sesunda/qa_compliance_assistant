import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Grid,
  Typography,
  Chip,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Stack,
  Paper,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Add as AddIcon,
  Cancel as CancelIcon,
  Delete as DeleteIcon,
  PlayArrow as PlayIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import { agentTasksService, AgentTask, AgentTaskCreate, TaskStats } from '../services/agentTasks';

const AgentTasksPage: React.FC = () => {
  const [tasks, setTasks] = useState<AgentTask[]>([]);
  const [stats, setStats] = useState<TaskStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterType, setFilterType] = useState<string>('');
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Form state for creating tasks
  const [newTask, setNewTask] = useState<AgentTaskCreate>({
    task_type: 'test',
    title: '',
    description: '',
    payload: {},
  });

  // Load tasks and stats
  const loadData = async () => {
    try {
      const [tasksData, statsData] = await Promise.all([
        agentTasksService.getAll({
          status: filterStatus || undefined,
          task_type: filterType || undefined,
        }),
        agentTasksService.getStats(),
      ]);
      setTasks(tasksData.tasks);
      setStats(statsData);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load tasks');
    } finally {
      setLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    loadData();
  }, [filterStatus, filterType]);

  // Auto-refresh every 5 seconds
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      loadData();
    }, 5000);

    return () => clearInterval(interval);
  }, [autoRefresh, filterStatus, filterType]);

  // Create new task
  const handleCreateTask = async () => {
    try {
      await agentTasksService.create(newTask);
      setCreateDialogOpen(false);
      setNewTask({
        task_type: 'test',
        title: '',
        description: '',
        payload: {},
      });
      await loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create task');
    }
  };

  // Cancel task
  const handleCancelTask = async (id: number) => {
    try {
      await agentTasksService.cancel(id);
      await loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to cancel task');
    }
  };

  // Delete task
  const handleDeleteTask = async (id: number) => {
    if (!confirm('Are you sure you want to delete this task?')) return;
    
    try {
      await agentTasksService.delete(id);
      await loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete task');
    }
  };

  // Get status color
  const getStatusColor = (status: string): 'default' | 'primary' | 'secondary' | 'success' | 'error' | 'warning' => {
    switch (status) {
      case 'pending': return 'default';
      case 'running': return 'primary';
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'cancelled': return 'warning';
      default: return 'default';
    }
  };

  // Get status icon
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending': return <ScheduleIcon />;
      case 'running': return <PlayIcon />;
      case 'completed': return <CheckCircleIcon />;
      case 'failed': return <ErrorIcon />;
      case 'cancelled': return <CancelIcon />;
      default: return <ScheduleIcon />;
    }
  };

  // Format timestamp
  const formatTimestamp = (timestamp: string | null): string => {
    if (!timestamp) return 'N/A';
    return new Date(timestamp).toLocaleString();
  };

  // Calculate duration
  const calculateDuration = (task: AgentTask): string => {
    if (!task.started_at) return 'Not started';
    
    const start = new Date(task.started_at);
    const end = task.completed_at ? new Date(task.completed_at) : new Date();
    const durationMs = end.getTime() - start.getTime();
    const seconds = Math.floor(durationMs / 1000);
    
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ${seconds % 60}s`;
    const hours = Math.floor(minutes / 60);
    return `${hours}h ${minutes % 60}m`;
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4">Agent Tasks</Typography>
        <Box>
          <Tooltip title={autoRefresh ? 'Auto-refresh enabled' : 'Auto-refresh disabled'}>
            <Button
              variant={autoRefresh ? 'contained' : 'outlined'}
              onClick={() => setAutoRefresh(!autoRefresh)}
              sx={{ mr: 1 }}
            >
              <RefreshIcon />
            </Button>
          </Tooltip>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadData}
            sx={{ mr: 1 }}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
          >
            Create Task
          </Button>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Stats Cards */}
      {stats && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={2}>
            <Paper 
              sx={{ 
                p: 2, 
                textAlign: 'center',
                cursor: 'pointer',
                transition: 'all 0.2s',
                border: filterStatus === '' ? '2px solid #1976d2' : 'none',
                '&:hover': { transform: 'translateY(-2px)', boxShadow: 3 }
              }}
              onClick={() => setFilterStatus('')}
            >
              <Typography variant="h4">{stats.total}</Typography>
              <Typography color="text.secondary">Total</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Paper 
              sx={{ 
                p: 2, 
                textAlign: 'center', 
                bgcolor: 'grey.100',
                cursor: 'pointer',
                transition: 'all 0.2s',
                border: filterStatus === 'pending' ? '2px solid #1976d2' : 'none',
                '&:hover': { transform: 'translateY(-2px)', boxShadow: 3 }
              }}
              onClick={() => setFilterStatus('pending')}
            >
              <Typography variant="h4">{stats.pending}</Typography>
              <Typography color="text.secondary">Pending</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Paper 
              sx={{ 
                p: 2, 
                textAlign: 'center', 
                bgcolor: 'primary.light', 
                color: 'white',
                cursor: 'pointer',
                transition: 'all 0.2s',
                border: filterStatus === 'running' ? '3px solid #fff' : 'none',
                '&:hover': { transform: 'translateY(-2px)', boxShadow: 3 }
              }}
              onClick={() => setFilterStatus('running')}
            >
              <Typography variant="h4">{stats.running}</Typography>
              <Typography>Running</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Paper 
              sx={{ 
                p: 2, 
                textAlign: 'center', 
                bgcolor: 'success.light', 
                color: 'white',
                cursor: 'pointer',
                transition: 'all 0.2s',
                border: filterStatus === 'completed' ? '3px solid #fff' : 'none',
                '&:hover': { transform: 'translateY(-2px)', boxShadow: 3 }
              }}
              onClick={() => setFilterStatus('completed')}
            >
              <Typography variant="h4">{stats.completed}</Typography>
              <Typography>Completed</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Paper 
              sx={{ 
                p: 2, 
                textAlign: 'center', 
                bgcolor: 'error.light', 
                color: 'white',
                cursor: 'pointer',
                transition: 'all 0.2s',
                border: filterStatus === 'failed' ? '3px solid #fff' : 'none',
                '&:hover': { transform: 'translateY(-2px)', boxShadow: 3 }
              }}
              onClick={() => setFilterStatus('failed')}
            >
              <Typography variant="h4">{stats.failed}</Typography>
              <Typography>Failed</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Paper 
              sx={{ 
                p: 2, 
                textAlign: 'center', 
                bgcolor: 'warning.light',
                cursor: 'pointer',
                transition: 'all 0.2s',
                border: filterStatus === 'cancelled' ? '2px solid #1976d2' : 'none',
                '&:hover': { transform: 'translateY(-2px)', boxShadow: 3 }
              }}
              onClick={() => setFilterStatus('cancelled')}
            >
              <Typography variant="h4">{stats.cancelled}</Typography>
              <Typography color="text.secondary">Cancelled</Typography>
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* Filters */}
      <Box sx={{ mb: 2, display: 'flex', gap: 2 }}>
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Status</InputLabel>
          <Select
            value={filterStatus}
            label="Status"
            onChange={(e) => setFilterStatus(e.target.value)}
          >
            <MenuItem value="">All</MenuItem>
            <MenuItem value="pending">Pending</MenuItem>
            <MenuItem value="running">Running</MenuItem>
            <MenuItem value="completed">Completed</MenuItem>
            <MenuItem value="failed">Failed</MenuItem>
            <MenuItem value="cancelled">Cancelled</MenuItem>
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Task Type</InputLabel>
          <Select
            value={filterType}
            label="Task Type"
            onChange={(e) => setFilterType(e.target.value)}
          >
            <MenuItem value="">All</MenuItem>
            <MenuItem value="test">Test</MenuItem>
            <MenuItem value="fetch_evidence">Fetch Evidence</MenuItem>
            <MenuItem value="generate_report">Generate Report</MenuItem>
            <MenuItem value="analyze_compliance">Analyze Compliance</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Tasks List */}
      {loading ? (
        <LinearProgress />
      ) : tasks.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="text.secondary">No tasks found</Typography>
        </Paper>
      ) : (
        <Grid container spacing={2}>
          {tasks.map((task) => (
            <Grid item xs={12} key={task.id}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="h6" gutterBottom>
                        {task.title}
                      </Typography>
                      <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
                        <Chip
                          icon={getStatusIcon(task.status)}
                          label={task.status.toUpperCase()}
                          color={getStatusColor(task.status)}
                          size="small"
                        />
                        <Chip label={task.task_type} size="small" variant="outlined" />
                        <Chip label={`ID: ${task.id}`} size="small" variant="outlined" />
                      </Stack>
                      {task.description && (
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                          {task.description}
                        </Typography>
                      )}
                    </Box>
                    <Box>
                      {task.status === 'running' && (
                        <Tooltip title="Cancel Task">
                          <IconButton onClick={() => handleCancelTask(task.id)} color="warning" size="small">
                            <CancelIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                      {(task.status === 'completed' || task.status === 'failed' || task.status === 'cancelled') && (
                        <Tooltip title="Delete Task">
                          <IconButton onClick={() => handleDeleteTask(task.id)} color="error" size="small">
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                    </Box>
                  </Box>

                  {/* Progress Bar */}
                  {task.status === 'running' && (
                    <Box sx={{ mb: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                        <Typography variant="body2" color="text.secondary">
                          Progress
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {task.progress}%
                        </Typography>
                      </Box>
                      <LinearProgress variant="determinate" value={task.progress} />
                    </Box>
                  )}

                  {/* Timestamps */}
                  <Grid container spacing={2} sx={{ mb: task.result || task.error_message ? 2 : 0 }}>
                    <Grid item xs={12} sm={6} md={3}>
                      <Typography variant="caption" color="text.secondary">Created</Typography>
                      <Typography variant="body2">{formatTimestamp(task.created_at)}</Typography>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Typography variant="caption" color="text.secondary">Started</Typography>
                      <Typography variant="body2">{formatTimestamp(task.started_at)}</Typography>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Typography variant="caption" color="text.secondary">Completed</Typography>
                      <Typography variant="body2">{formatTimestamp(task.completed_at)}</Typography>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Typography variant="caption" color="text.secondary">Duration</Typography>
                      <Typography variant="body2">{calculateDuration(task)}</Typography>
                    </Grid>
                  </Grid>

                  {/* Result */}
                  {task.result && (
                    <Paper variant="outlined" sx={{ p: 2, bgcolor: 'success.50' }}>
                      <Typography variant="subtitle2" gutterBottom>Result:</Typography>
                      <pre style={{ margin: 0, overflow: 'auto', fontSize: '0.75rem' }}>
                        {JSON.stringify(task.result, null, 2)}
                      </pre>
                    </Paper>
                  )}

                  {/* Error */}
                  {task.error_message && (
                    <Alert severity="error" sx={{ mt: 2 }}>
                      <Typography variant="subtitle2">Error:</Typography>
                      <Typography variant="body2">{task.error_message}</Typography>
                    </Alert>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Create Task Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Agent Task</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <FormControl fullWidth>
              <InputLabel>Task Type</InputLabel>
              <Select
                value={newTask.task_type}
                label="Task Type"
                onChange={(e) => {
                  const taskType = e.target.value;
                  // Initialize payload based on task type
                  let payload = {};
                  if (taskType === 'test') {
                    payload = { steps: 5 };
                  } else if (taskType === 'analyze_compliance') {
                    payload = { project_id: 1, framework: 'IM8' };
                  } else if (taskType === 'fetch_evidence') {
                    payload = {
                      sources: [
                        {
                          type: 'file',
                          location: '/app/storage/test_evidence/test_doc.txt',
                          description: 'Sample evidence document',
                          control_id: 1
                        }
                      ],
                      project_id: 1,
                      created_by: 1
                    };
                  }
                  setNewTask({ ...newTask, task_type: taskType, payload });
                }}
              >
                <MenuItem value="test">Test Task</MenuItem>
                <MenuItem value="fetch_evidence">Fetch Evidence</MenuItem>
                <MenuItem value="generate_report">Generate Report</MenuItem>
                <MenuItem value="analyze_compliance">Analyze Compliance</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Title"
              fullWidth
              required
              value={newTask.title}
              onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
            />
            <TextField
              label="Description"
              fullWidth
              multiline
              rows={2}
              value={newTask.description}
              onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
            />
            {newTask.task_type === 'test' && (
              <TextField
                label="Number of Steps"
                type="number"
                fullWidth
                defaultValue={5}
                onChange={(e) => setNewTask({
                  ...newTask,
                  payload: { steps: parseInt(e.target.value) || 5 }
                })}
              />
            )}
            {newTask.task_type === 'fetch_evidence' && (
              <>
                <Alert severity="info">
                  Evidence will be fetched from test files in /app/storage/test_evidence/
                </Alert>
                <TextField
                  label="Control ID"
                  type="number"
                  fullWidth
                  required
                  defaultValue={1}
                  helperText="Enter the control ID to associate evidence with"
                />
                <TextField
                  label="File Location"
                  fullWidth
                  defaultValue="/app/storage/test_evidence/test_doc.txt"
                  helperText="Path to evidence file in container"
                />
                <FormControl fullWidth>
                  <InputLabel>Evidence Type</InputLabel>
                  <Select
                    defaultValue="file"
                    label="Evidence Type"
                  >
                    <MenuItem value="file">Local File</MenuItem>
                    <MenuItem value="url">URL</MenuItem>
                  </Select>
                </FormControl>
              </>
            )}
            {newTask.task_type === 'analyze_compliance' && (
              <>
                <TextField
                  label="Project ID"
                  type="number"
                  fullWidth
                  required
                  defaultValue={1}
                  onChange={(e) => setNewTask({
                    ...newTask,
                    payload: { 
                      ...newTask.payload,
                      project_id: parseInt(e.target.value) || 1 
                    }
                  })}
                  helperText="Enter the project ID to analyze"
                />
                <FormControl fullWidth>
                  <InputLabel>Framework</InputLabel>
                  <Select
                    defaultValue="IM8"
                    label="Framework"
                    onChange={(e) => setNewTask({
                      ...newTask,
                      payload: { 
                        ...newTask.payload,
                        framework: e.target.value
                      }
                    })}
                  >
                    <MenuItem value="IM8">IM8</MenuItem>
                    <MenuItem value="ISO27001">ISO 27001</MenuItem>
                    <MenuItem value="NIST">NIST</MenuItem>
                  </Select>
                </FormControl>
              </>
            )}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleCreateTask}
            variant="contained"
            disabled={!newTask.title}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AgentTasksPage;
