import React, { useState, useEffect } from 'react'
import {
  Box,
  Paper,
  Typography,
  Grid,
  Chip,
  Button,
  LinearProgress,
  Divider,
  Card,
  CardContent,
  Stack,
  Alert,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Slider
} from '@mui/material'
import {
  ArrowBack,
  Edit,
  CheckCircle,
  Add,
} from '@mui/icons-material'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import assessmentsService, { Assessment } from '../services/assessments'

const AssessmentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [assessment, setAssessment] = useState<Assessment | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [progressDialogOpen, setProgressDialogOpen] = useState(false)
  const [newProgress, setNewProgress] = useState(0)

  useEffect(() => {
    if (id) {
      loadAssessment()
    }
  }, [id])

  const loadAssessment = async () => {
    if (!id) return
    
    try {
      setLoading(true)
      const data = await assessmentsService.get(parseInt(id))
      setAssessment(data)
      setNewProgress(data.progress_percentage)
      setError(null)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load assessment')
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateProgress = async () => {
    if (!assessment) return

    try {
      await assessmentsService.updateProgress(assessment.id, newProgress)
      setProgressDialogOpen(false)
      loadAssessment()
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update progress')
    }
  }

  const handleComplete = async () => {
    if (!assessment) return
    if (!window.confirm('Mark this assessment as complete? This will set progress to 100% and change status to Completed.')) {
      return
    }

    try {
      await assessmentsService.complete(assessment.id)
      loadAssessment()
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to complete assessment')
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'planning': return 'default'
      case 'in_progress': return 'primary'
      case 'completed': return 'success'
      case 'closed': return 'default'
      default: return 'default'
    }
  }

  const canUpdateProgress = () => {
    const role = user?.role?.name?.toLowerCase()
    return assessment?.assigned_to === user?.id || ['admin', 'super_admin'].includes(role || '')
  }

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
      </Box>
    )
  }

  if (error || !assessment) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error || 'Assessment not found'}</Alert>
        <Button startIcon={<ArrowBack />} onClick={() => navigate('/assessments')} sx={{ mt: 2 }}>
          Back to Assessments
        </Button>
      </Box>
    )
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <IconButton onClick={() => navigate('/assessments')}>
          <ArrowBack />
        </IconButton>
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="h4">{assessment.title}</Typography>
          <Typography variant="body2" color="text.secondary">
            Assessment ID: {assessment.id}
          </Typography>
        </Box>
        <Chip
          label={assessment.status.replace('_', ' ').toUpperCase()}
          color={getStatusColor(assessment.status)}
        />
      </Box>

      <Grid container spacing={3}>
        {/* Left Column - Main Info */}
        <Grid item xs={12} md={8}>
          {/* Overview Card */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Overview</Typography>
              <Divider sx={{ mb: 2 }} />
              
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">Type</Typography>
                  <Typography variant="body1">{assessment.assessment_type.toUpperCase()}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">Framework</Typography>
                  <Typography variant="body1">{assessment.framework || 'N/A'}</Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="caption" color="text.secondary">Scope</Typography>
                  <Typography variant="body1">{assessment.scope || 'N/A'}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">Assessment Period</Typography>
                  <Typography variant="body1">
                    {assessment.assessment_period_start && assessment.assessment_period_end
                      ? `${new Date(assessment.assessment_period_start).toLocaleDateString()} - ${new Date(assessment.assessment_period_end).toLocaleDateString()}`
                      : 'Not set'}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">Target Completion</Typography>
                  <Typography variant="body1">
                    {assessment.target_completion_date
                      ? new Date(assessment.target_completion_date).toLocaleDateString()
                      : 'Not set'}
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* Progress Card */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">Progress</Typography>
                {canUpdateProgress() && assessment.status !== 'completed' && (
                  <Button
                    size="small"
                    startIcon={<Edit />}
                    onClick={() => setProgressDialogOpen(true)}
                  >
                    Update Progress
                  </Button>
                )}
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <LinearProgress
                  variant="determinate"
                  value={assessment.progress_percentage}
                  sx={{ flexGrow: 1, height: 12, borderRadius: 6 }}
                />
                <Typography variant="h6" color="primary">
                  {assessment.progress_percentage}%
                </Typography>
              </Box>
              {assessment.completed_at && (
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  Completed on {new Date(assessment.completed_at).toLocaleString()}
                </Typography>
              )}
            </CardContent>
          </Card>

          {/* Findings Summary */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Findings Summary</Typography>
              <Divider sx={{ mb: 2 }} />
              
              <Grid container spacing={2}>
                <Grid item xs={6} sm={3}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'background.default' }}>
                    <Typography variant="h4">{assessment.findings_count}</Typography>
                    <Typography variant="caption">Total</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'success.light' }}>
                    <Typography variant="h4">{assessment.findings_resolved || 0}</Typography>
                    <Typography variant="caption">Resolved</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="caption" color="text.secondary" gutterBottom display="block">
                    By Severity
                  </Typography>
                  <Stack direction="row" spacing={1} flexWrap="wrap">
                    {assessment.findings_by_severity && (
                      <>
                        {assessment.findings_by_severity.critical > 0 && (
                          <Chip
                            label={`Critical: ${assessment.findings_by_severity.critical}`}
                            color="error"
                            size="small"
                          />
                        )}
                        {assessment.findings_by_severity.high > 0 && (
                          <Chip
                            label={`High: ${assessment.findings_by_severity.high}`}
                            color="warning"
                            size="small"
                          />
                        )}
                        {assessment.findings_by_severity.medium > 0 && (
                          <Chip
                            label={`Medium: ${assessment.findings_by_severity.medium}`}
                            color="info"
                            size="small"
                          />
                        )}
                        {assessment.findings_by_severity.low > 0 && (
                          <Chip
                            label={`Low: ${assessment.findings_by_severity.low}`}
                            size="small"
                          />
                        )}
                      </>
                    )}
                  </Stack>
                </Grid>
              </Grid>

              <Button
                fullWidth
                variant="outlined"
                sx={{ mt: 2 }}
                onClick={() => navigate(`/findings?assessment_id=${assessment.id}`)}
              >
                View All Findings
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Right Column - Actions & Stats */}
        <Grid item xs={12} md={4}>
          {/* Actions Card */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Actions</Typography>
              <Divider sx={{ mb: 2 }} />
              
              <Stack spacing={2}>
                <Button
                  variant="outlined"
                  fullWidth
                  startIcon={<Add />}
                  onClick={() => navigate(`/findings/new?assessment_id=${assessment.id}`)}
                >
                  Add Finding
                </Button>

                {canUpdateProgress() && assessment.status !== 'completed' && (
                  <Button
                    variant="contained"
                    fullWidth
                    color="success"
                    startIcon={<CheckCircle />}
                    onClick={handleComplete}
                  >
                    Mark as Complete
                  </Button>
                )}
              </Stack>
            </CardContent>
          </Card>

          {/* Assignment Card */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Assignment</Typography>
              <Divider sx={{ mb: 2 }} />
              
              <Typography variant="caption" color="text.secondary">Assigned To</Typography>
              <Typography variant="body1" gutterBottom>
                {assessment.assigned_to_username || 'Unassigned'}
              </Typography>

              <Typography variant="caption" color="text.secondary">Created</Typography>
              <Typography variant="body1">
                {new Date(assessment.created_at).toLocaleDateString()}
              </Typography>
            </CardContent>
          </Card>

          {/* Controls Tested */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Controls</Typography>
              <Divider sx={{ mb: 2 }} />
              
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h3" color="primary">
                  {assessment.controls_tested_count}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Controls Tested
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Progress Update Dialog */}
      <Dialog open={progressDialogOpen} onClose={() => setProgressDialogOpen(false)}>
        <DialogTitle>Update Assessment Progress</DialogTitle>
        <DialogContent>
          <Box sx={{ px: 2, py: 3 }}>
            <Typography gutterBottom>Progress: {newProgress}%</Typography>
            <Slider
              value={newProgress}
              onChange={(_, value) => setNewProgress(value as number)}
              min={0}
              max={100}
              step={5}
              marks
              valueLabelDisplay="auto"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setProgressDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleUpdateProgress} variant="contained">
            Update
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default AssessmentDetailPage
