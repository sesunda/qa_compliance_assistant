import React, { useState, useEffect } from 'react'
import {
  Box,
  Paper,
  Typography,
  LinearProgress,
  Grid,
  Card,
  CardContent,
  Chip,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Button,
  Stack,
} from '@mui/material'
import {
  CheckCircle,
  RadioButtonUnchecked,
  Schedule,
  Warning,
  TrendingUp,
  Assignment,
  BugReport,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import findingsService, { FindingListItem } from '../../services/findings'

interface RemediationTrackerProps {
  assessmentId?: number
  showHeader?: boolean
}

const RemediationTracker: React.FC<RemediationTrackerProps> = ({ 
  assessmentId,
  showHeader = true 
}) => {
  const navigate = useNavigate()
  const [findings, setFindings] = useState<FindingListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadFindings()
  }, [assessmentId])

  const loadFindings = async () => {
    try {
      setLoading(true)
      const params: any = {}
      if (assessmentId) {
        params.assessment_id = assessmentId
      }
      const data = await findingsService.list(params)
      setFindings(data)
      setError(null)
    } catch (err: any) {
      console.error('Failed to load findings:', err)
      setError(err.response?.data?.detail || 'Failed to load findings')
    } finally {
      setLoading(false)
    }
  }

  const stats = {
    total: findings.length,
    open: findings.filter(f => f.resolution_status === 'open').length,
    inProgress: findings.filter(f => f.resolution_status === 'in_progress').length,
    resolved: findings.filter(f => ['resolved', 'validated', 'closed'].includes(f.resolution_status)).length,
    critical: findings.filter(f => f.severity === 'critical' && !['closed'].includes(f.resolution_status)).length,
    overdue: findings.filter(f => f.due_date && new Date(f.due_date) < new Date() && f.resolution_status !== 'closed').length,
  }

  const progress = stats.total > 0 
    ? Math.round((stats.resolved / stats.total) * 100)
    : 0

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'open': return <RadioButtonUnchecked color="error" />
      case 'in_progress': return <Schedule color="warning" />
      case 'resolved':
      case 'validated':
      case 'closed':
        return <CheckCircle color="success" />
      default: return <RadioButtonUnchecked />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open': return 'error'
      case 'in_progress': return 'warning'
      case 'resolved': return 'info'
      case 'validated': return 'success'
      case 'closed': return 'default'
      default: return 'default'
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'error'
      case 'high': return 'warning'
      case 'medium': return 'info'
      default: return 'default'
    }
  }

  if (loading) {
    return (
      <Box sx={{ p: 2 }}>
        <LinearProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>{error}</Alert>
    )
  }

  return (
    <Box>
      {showHeader && (
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h6">
            Remediation Tracker
          </Typography>
          <Button
            size="small"
            startIcon={<BugReport />}
            onClick={() => navigate('/findings')}
          >
            View All Findings
          </Button>
        </Box>
      )}

      {/* Progress Overview */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Overall Remediation Progress
          </Typography>
          
          <Box sx={{ mb: 2 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
              <Typography variant="body2" color="text.secondary">
                {stats.resolved} of {stats.total} findings resolved
              </Typography>
              <Typography variant="h6" color="primary">
                {progress}%
              </Typography>
            </Box>
            <LinearProgress 
              variant="determinate" 
              value={progress} 
              sx={{ height: 12, borderRadius: 6 }}
              color={progress === 100 ? 'success' : 'primary'}
            />
          </Box>

          <Divider sx={{ my: 2 }} />

          <Grid container spacing={2}>
            <Grid item xs={6} sm={3}>
              <Box textAlign="center">
                <Typography variant="h4" color="error.main">
                  {stats.open}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Open
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Box textAlign="center">
                <Typography variant="h4" color="warning.main">
                  {stats.inProgress}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  In Progress
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Box textAlign="center">
                <Typography variant="h4" color="success.main">
                  {stats.resolved}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Resolved
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Box textAlign="center">
                <Typography variant="h4" color={stats.overdue > 0 ? 'error.main' : 'text.primary'}>
                  {stats.overdue}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Overdue
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Critical Alerts */}
      {stats.critical > 0 && (
        <Alert severity="error" icon={<Warning />} sx={{ mb: 3 }}>
          <strong>{stats.critical}</strong> critical finding(s) require immediate attention!
        </Alert>
      )}

      {stats.overdue > 0 && (
        <Alert severity="warning" icon={<Schedule />} sx={{ mb: 3 }}>
          <strong>{stats.overdue}</strong> finding(s) are past their due date
        </Alert>
      )}

      {/* Findings by Status */}
      <Grid container spacing={3}>
        {/* Open Findings */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle1" fontWeight={600} gutterBottom color="error.main">
              Open Findings ({stats.open})
            </Typography>
            {findings.filter(f => f.resolution_status === 'open').length === 0 ? (
              <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                No open findings
              </Typography>
            ) : (
              <List dense>
                {findings
                  .filter(f => f.resolution_status === 'open')
                  .slice(0, 5)
                  .map((finding) => (
                    <ListItem 
                      key={finding.id}
                      button
                      onClick={() => navigate(`/findings/${finding.id}`)}
                    >
                      <ListItemIcon>
                        {getStatusIcon(finding.resolution_status)}
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Stack direction="row" spacing={1} alignItems="center">
                            <Typography variant="body2" noWrap sx={{ maxWidth: '60%' }}>
                              {finding.title}
                            </Typography>
                            <Chip
                              label={finding.severity}
                              size="small"
                              color={getSeverityColor(finding.severity)}
                            />
                          </Stack>
                        }
                        secondary={finding.assessment_title}
                      />
                    </ListItem>
                  ))}
              </List>
            )}
          </Paper>
        </Grid>

        {/* In Progress Findings */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle1" fontWeight={600} gutterBottom color="warning.main">
              In Progress ({stats.inProgress})
            </Typography>
            {findings.filter(f => f.resolution_status === 'in_progress').length === 0 ? (
              <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                No findings in progress
              </Typography>
            ) : (
              <List dense>
                {findings
                  .filter(f => f.resolution_status === 'in_progress')
                  .slice(0, 5)
                  .map((finding) => (
                    <ListItem 
                      key={finding.id}
                      button
                      onClick={() => navigate(`/findings/${finding.id}`)}
                    >
                      <ListItemIcon>
                        {getStatusIcon(finding.resolution_status)}
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Stack direction="row" spacing={1} alignItems="center">
                            <Typography variant="body2" noWrap sx={{ maxWidth: '60%' }}>
                              {finding.title}
                            </Typography>
                            <Chip
                              label={finding.severity}
                              size="small"
                              color={getSeverityColor(finding.severity)}
                            />
                          </Stack>
                        }
                        secondary={finding.assigned_to || 'Unassigned'}
                      />
                    </ListItem>
                  ))}
              </List>
            )}
          </Paper>
        </Grid>

        {/* Resolved Findings */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle1" fontWeight={600} gutterBottom color="success.main">
              Resolved Findings ({stats.resolved})
            </Typography>
            {findings.filter(f => ['resolved', 'validated', 'closed'].includes(f.resolution_status)).length === 0 ? (
              <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                No resolved findings yet
              </Typography>
            ) : (
              <List dense>
                {findings
                  .filter(f => ['resolved', 'validated', 'closed'].includes(f.resolution_status))
                  .slice(0, 5)
                  .map((finding) => (
                    <ListItem 
                      key={finding.id}
                      button
                      onClick={() => navigate(`/findings/${finding.id}`)}
                    >
                      <ListItemIcon>
                        {getStatusIcon(finding.resolution_status)}
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Stack direction="row" spacing={1} alignItems="center">
                            <Typography variant="body2" noWrap sx={{ maxWidth: '70%' }}>
                              {finding.title}
                            </Typography>
                            <Chip
                              label={finding.resolution_status.replace('_', ' ')}
                              size="small"
                              color={getStatusColor(finding.resolution_status)}
                            />
                          </Stack>
                        }
                        secondary={finding.assessment_title}
                      />
                    </ListItem>
                  ))}
              </List>
            )}
            {stats.resolved > 5 && (
              <Button
                fullWidth
                size="small"
                onClick={() => navigate('/findings?resolution_status=resolved,validated,closed')}
                sx={{ mt: 1 }}
              >
                View All Resolved ({stats.resolved})
              </Button>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Summary */}
      {stats.total === 0 && (
        <Alert severity="info" icon={<Assignment />} sx={{ mt: 3 }}>
          No findings to track yet. Findings will appear here as they are created during assessments.
        </Alert>
      )}

      {stats.total > 0 && stats.resolved === stats.total && (
        <Alert severity="success" icon={<CheckCircle />} sx={{ mt: 3 }}>
          All findings have been resolved! Excellent work on achieving 100% remediation.
        </Alert>
      )}
    </Box>
  )
}

export default RemediationTracker
