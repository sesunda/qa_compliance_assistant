import React, { useState, useEffect } from 'react'
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  LinearProgress,
  Alert,
  CircularProgress,
} from '@mui/material'
import {
  Assignment,
  BugReport,
  TrendingUp,
  Warning,
} from '@mui/icons-material'
import analyticsService, { WorkloadData } from '../../services/analytics'

const WorkloadView: React.FC = () => {
  const [workloadData, setWorkloadData] = useState<WorkloadData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadWorkloadData()
  }, [])

  const loadWorkloadData = async () => {
    try {
      setLoading(true)
      const data = await analyticsService.getMyWorkload()
      setWorkloadData(data)
      setError(null)
    } catch (err: any) {
      console.error('Failed to load workload data:', err)
      setError(err.response?.data?.detail || 'Failed to load workload data')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '40vh' }}>
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>{error}</Alert>
    )
  }

  if (!workloadData) {
    return (
      <Alert severity="info" sx={{ m: 2 }}>
        No workload data available
      </Alert>
    )
  }

  const workloadPercentage = Math.min(
    Math.round(
      ((workloadData.assigned_assessments * 10 + workloadData.assigned_findings * 5) / 100) * 100
    ),
    100
  )

  const getWorkloadColor = () => {
    if (workloadPercentage > 80) return 'error'
    if (workloadPercentage > 60) return 'warning'
    return 'success'
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        My Workload Overview
      </Typography>

      {/* Workload Summary Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Assignment color="primary" sx={{ mr: 2, fontSize: 40 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Active Assessments
                  </Typography>
                  <Typography variant="h4">
                    {workloadData.assigned_assessments}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Assigned to you
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <BugReport color="warning" sx={{ mr: 2, fontSize: 40 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Active Findings
                  </Typography>
                  <Typography variant="h4">
                    {workloadData.assigned_findings}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Awaiting resolution
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ bgcolor: workloadData.overdue_findings > 0 ? 'error.light' : undefined }}>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Warning 
                  color={workloadData.overdue_findings > 0 ? 'error' : 'disabled'} 
                  sx={{ mr: 2, fontSize: 40 }} 
                />
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Overdue Items
                  </Typography>
                  <Typography variant="h4" color={workloadData.overdue_findings > 0 ? 'error.dark' : undefined}>
                    {workloadData.overdue_findings}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Need immediate action
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Workload Capacity */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Capacity Utilization
        </Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Based on assigned assessments and findings
        </Typography>

        <Box sx={{ mt: 2 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="body2">
              Current Workload
            </Typography>
            <Typography variant="h6" color={`${getWorkloadColor()}.main`}>
              {workloadPercentage}%
            </Typography>
          </Box>
          <LinearProgress 
            variant="determinate" 
            value={workloadPercentage} 
            sx={{ height: 12, borderRadius: 6 }}
            color={getWorkloadColor()}
          />
          <Box sx={{ mt: 1, display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="caption" color="text.secondary">
              {workloadPercentage < 50 && 'Light workload - capacity available'}
              {workloadPercentage >= 50 && workloadPercentage < 80 && 'Moderate workload - well balanced'}
              {workloadPercentage >= 80 && 'Heavy workload - consider redistribution'}
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Urgency Breakdown */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Urgency Breakdown
        </Typography>

        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12} sm={4}>
            <Box 
              sx={{ 
                p: 2, 
                bgcolor: 'error.lighter', 
                borderRadius: 1,
                border: '1px solid',
                borderColor: 'error.light'
              }}
            >
              <Typography variant="h3" color="error.main" gutterBottom>
                {workloadData.overdue_findings}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Overdue
              </Typography>
              <Typography variant="caption" color="error.main">
                Past due date
              </Typography>
            </Box>
          </Grid>

          <Grid item xs={12} sm={4}>
            <Box 
              sx={{ 
                p: 2, 
                bgcolor: 'warning.lighter', 
                borderRadius: 1,
                border: '1px solid',
                borderColor: 'warning.light'
              }}
            >
              <Typography variant="h3" color="warning.main" gutterBottom>
                {workloadData.due_soon_findings}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Due Soon
              </Typography>
              <Typography variant="caption" color="warning.main">
                Within 7 days
              </Typography>
            </Box>
          </Grid>

          <Grid item xs={12} sm={4}>
            <Box 
              sx={{ 
                p: 2, 
                bgcolor: 'success.lighter', 
                borderRadius: 1,
                border: '1px solid',
                borderColor: 'success.light'
              }}
            >
              <Typography variant="h3" color="success.main" gutterBottom>
                {workloadData.assigned_findings - workloadData.overdue_findings - workloadData.due_soon_findings}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                On Track
              </Typography>
              <Typography variant="caption" color="success.main">
                Good progress
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Alerts */}
      {workloadData.overdue_findings > 0 && (
        <Alert severity="error" icon={<Warning />} sx={{ mb: 2 }}>
          You have <strong>{workloadData.overdue_findings}</strong> overdue finding(s) that need immediate attention!
        </Alert>
      )}

      {workloadData.due_soon_findings > 0 && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          <strong>{workloadData.due_soon_findings}</strong> finding(s) are due within the next 7 days. Plan your work accordingly.
        </Alert>
      )}

      {workloadPercentage > 80 && (
        <Alert severity="warning" icon={<TrendingUp />}>
          Your current workload is at {workloadPercentage}%. Consider requesting assistance or reprioritizing tasks.
        </Alert>
      )}

      {workloadData.overdue_findings === 0 && workloadData.due_soon_findings === 0 && (
        <Alert severity="success">
          All your assigned work is on track with no overdue items. Keep up the great work!
        </Alert>
      )}
    </Box>
  )
}

export default WorkloadView
