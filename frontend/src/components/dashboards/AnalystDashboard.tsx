import React, { useState, useEffect } from 'react'
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Paper,
  Chip,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  Alert,
  CircularProgress,
  Divider,
} from '@mui/material'
import {
  Assessment,
  BugReport,
  CheckCircle,
  Warning,
  Assignment,
  TrendingUp,
  Policy,
  Error as ErrorIcon,
  Security,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import analyticsService, { DashboardMetrics, WorkloadData } from '../../services/analytics'
import assessmentsService, { AssessmentListItem } from '../../services/assessments'
import findingsService, { FindingListItem } from '../../services/findings'

const AnalystDashboard: React.FC = () => {
  const navigate = useNavigate()
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null)
  const [workload, setWorkload] = useState<WorkloadData | null>(null)
  const [myAssessments, setMyAssessments] = useState<AssessmentListItem[]>([])
  const [criticalFindings, setCriticalFindings] = useState<FindingListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      
      // Load all data in parallel
      const [metricsData, workloadData, assessmentsData, findingsData] = await Promise.all([
        analyticsService.getDashboard(),
        analyticsService.getMyWorkload(),
        assessmentsService.list({ assigned_to_me: true }),
        findingsService.list({ 
          severity: 'critical',
          resolution_status: 'open'
        })
      ])

      setMetrics(metricsData)
      setWorkload(workloadData)
      setMyAssessments(assessmentsData.filter(a => ['planning', 'in_progress'].includes(a.status)))
      setCriticalFindings(findingsData.slice(0, 5)) // Top 5 critical
      setError(null)
    } catch (err: any) {
      console.error('Failed to load dashboard:', err)
      console.error('Error response:', err.response)
      console.error('Error data:', err.response?.data)
      
      let errorMessage = 'Failed to load dashboard data'
      if (err.response?.status === 404) {
        errorMessage = 'API endpoint not found. The database migration may not have been applied yet.'
      } else if (err.response?.status === 401 || err.response?.status === 403) {
        errorMessage = 'Authentication error. Please log in again.'
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail
      } else if (err.message) {
        errorMessage = err.message
      }
      
      setError(errorMessage)
    } finally {
      setLoading(false)
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

  const calculateDaysOpen = (createdAt: string) => {
    const created = new Date(createdAt)
    const now = new Date()
    const diffTime = Math.abs(now.getTime() - created.getTime())
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          <Typography variant="h6" gutterBottom>Dashboard Load Error</Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>{error}</Typography>
          <Typography variant="caption" color="text.secondary">
            This could mean:
            <br />• The database migration hasn't been applied yet
            <br />• The API service is not responding
            <br />• You don't have permission to access dashboard data
            <br />• No data exists yet (first time setup)
          </Typography>
        </Alert>
        <Button variant="contained" onClick={loadDashboardData}>
          Retry Loading Dashboard
        </Button>
      </Box>
    )
  }

  if (!metrics || !workload) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="info">No data available</Alert>
      </Box>
    )
  }

  const openCriticalHigh = metrics.findings.by_severity.critical + metrics.findings.by_severity.high

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" gutterBottom>
          Security Analyst Dashboard
        </Typography>
        <Box display="flex" gap={2}>
          <Button 
            variant="contained" 
            color="primary" 
            startIcon={<Policy />}
            onClick={() => navigate('/assessments')}
          >
            My Assessments
          </Button>
          <Button 
            variant="outlined" 
            startIcon={<BugReport />}
            onClick={() => navigate('/findings?assigned_to_me=true')}
          >
            My Findings
          </Button>
        </Box>
      </Box>

      {/* Alert for Overdue Items */}
      {workload.overdue_findings > 0 && (
        <Alert severity="error" sx={{ mb: 3 }} icon={<ErrorIcon />}>
          You have <strong>{workload.overdue_findings}</strong> overdue finding(s) that need immediate attention!
        </Alert>
      )}

      {/* Alert for Due Soon */}
      {workload.due_soon_findings > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <strong>{workload.due_soon_findings}</strong> finding(s) are due within the next 7 days
        </Alert>
      )}
      
      <Grid container spacing={3}>
        {/* My Workload Metrics */}
        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Assessment color="primary" sx={{ mr: 2, fontSize: 40 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    My Active Assessments
                  </Typography>
                  <Typography variant="h4">
                    {workload.assigned_assessments}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Assigned to you
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
                <Assignment color="warning" sx={{ mr: 2, fontSize: 40 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    My Assigned Findings
                  </Typography>
                  <Typography variant="h4">
                    {workload.assigned_findings}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Awaiting resolution
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6} lg={3}>
          <Card sx={{ bgcolor: workload.overdue_findings > 0 ? 'error.light' : undefined }}>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Warning 
                  color={workload.overdue_findings > 0 ? 'error' : 'disabled'} 
                  sx={{ mr: 2, fontSize: 40 }} 
                />
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Overdue Findings
                  </Typography>
                  <Typography variant="h4" color={workload.overdue_findings > 0 ? 'error.dark' : undefined}>
                    {workload.overdue_findings}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Need immediate action
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6} lg={3}>
          <Card sx={{ bgcolor: workload.due_soon_findings > 0 ? 'warning.light' : undefined }}>
            <CardContent>
              <Box display="flex" alignItems="center">
                <TrendingUp 
                  color={workload.due_soon_findings > 0 ? 'warning' : 'disabled'} 
                  sx={{ mr: 2, fontSize: 40 }} 
                />
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Due Within 7 Days
                  </Typography>
                  <Typography variant="h4" color={workload.due_soon_findings > 0 ? 'warning.dark' : undefined}>
                    {workload.due_soon_findings}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Plan your work
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Agency-Wide Statistics */}
        <Grid item xs={12}>
          <Paper 
            sx={{ 
              p: 3, 
              background: 'linear-gradient(135deg, #FFFFFF 0%, #F0F9FF 100%)',
              borderLeft: '4px solid #006D77',
              boxShadow: '0 2px 8px rgba(0, 109, 119, 0.1)',
              '&:hover': {
                boxShadow: '0 4px 16px rgba(0, 109, 119, 0.15)',
                transform: 'translateY(-2px)',
                transition: 'all 0.3s ease',
              },
            }}
          >
            <Typography 
              variant="h6" 
              gutterBottom 
              sx={{ 
                color: '#006D77', 
                fontWeight: 600,
                mb: 3,
              }}
            >
              Agency-Wide Compliance Overview
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={6} sm={3}>
                <Box 
                  textAlign="center"
                  sx={{
                    p: 2,
                    borderRadius: 2,
                    background: 'linear-gradient(135deg, rgba(0, 109, 119, 0.05) 0%, rgba(131, 197, 190, 0.05) 100%)',
                  }}
                >
                  <Box
                    sx={{
                      width: 56,
                      height: 56,
                      borderRadius: '50%',
                      background: 'linear-gradient(135deg, #006D77 0%, #83C5BE 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      margin: '0 auto 12px',
                      boxShadow: '0 4px 12px rgba(0, 109, 119, 0.2)',
                    }}
                  >
                    <Assessment sx={{ fontSize: 28, color: '#FFFFFF' }} />
                  </Box>
                  <Typography variant="h3" sx={{ color: '#006D77', fontWeight: 700, mb: 0.5 }}>
                    {metrics.assessments.total}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#1A1A1A', fontWeight: 500 }}>
                    Total Assessments
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#6B7280' }}>
                    {metrics.assessments.active} active
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Box 
                  textAlign="center"
                  sx={{
                    p: 2,
                    borderRadius: 2,
                    background: 'linear-gradient(135deg, rgba(251, 146, 60, 0.05) 0%, rgba(251, 191, 36, 0.05) 100%)',
                  }}
                >
                  <Box
                    sx={{
                      width: 56,
                      height: 56,
                      borderRadius: '50%',
                      background: 'linear-gradient(135deg, #FB923C 0%, #FBBF24 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      margin: '0 auto 12px',
                      boxShadow: '0 4px 12px rgba(251, 146, 60, 0.2)',
                    }}
                  >
                    <BugReport sx={{ fontSize: 28, color: '#FFFFFF' }} />
                  </Box>
                  <Typography variant="h3" sx={{ color: '#F59E0B', fontWeight: 700, mb: 0.5 }}>
                    {metrics.findings.total}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#1A1A1A', fontWeight: 500 }}>
                    Total Findings
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#6B7280' }}>
                    {metrics.findings.open} open
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Box 
                  textAlign="center"
                  sx={{
                    p: 2,
                    borderRadius: 2,
                    background: openCriticalHigh > 0 
                      ? 'linear-gradient(135deg, rgba(255, 107, 107, 0.05) 0%, rgba(239, 68, 68, 0.05) 100%)'
                      : 'linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, rgba(34, 197, 94, 0.05) 100%)',
                  }}
                >
                  <Box
                    sx={{
                      width: 56,
                      height: 56,
                      borderRadius: '50%',
                      background: openCriticalHigh > 0 
                        ? 'linear-gradient(135deg, #FF6B6B 0%, #EF4444 100%)'
                        : 'linear-gradient(135deg, #10B981 0%, #22C55E 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      margin: '0 auto 12px',
                      boxShadow: openCriticalHigh > 0 
                        ? '0 4px 12px rgba(255, 107, 107, 0.2)'
                        : '0 4px 12px rgba(16, 185, 129, 0.2)',
                    }}
                  >
                    {openCriticalHigh > 0 ? (
                      <Warning sx={{ fontSize: 28, color: '#FFFFFF' }} />
                    ) : (
                      <CheckCircle sx={{ fontSize: 28, color: '#FFFFFF' }} />
                    )}
                  </Box>
                  <Typography 
                    variant="h3" 
                    sx={{ 
                      color: openCriticalHigh > 0 ? '#FF6B6B' : '#10B981', 
                      fontWeight: 700, 
                      mb: 0.5 
                    }}
                  >
                    {openCriticalHigh}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#1A1A1A', fontWeight: 500 }}>
                    Critical/High Findings
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#6B7280' }}>
                    Open severity
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Box 
                  textAlign="center"
                  sx={{
                    p: 2,
                    borderRadius: 2,
                    background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, rgba(34, 197, 94, 0.05) 100%)',
                  }}
                >
                  <Box
                    sx={{
                      width: 56,
                      height: 56,
                      borderRadius: '50%',
                      background: 'linear-gradient(135deg, #10B981 0%, #22C55E 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      margin: '0 auto 12px',
                      boxShadow: '0 4px 12px rgba(16, 185, 129, 0.2)',
                    }}
                  >
                    <Security sx={{ fontSize: 28, color: '#FFFFFF' }} />
                  </Box>
                  <Typography variant="h3" sx={{ color: '#10B981', fontWeight: 700, mb: 0.5 }}>
                    {metrics.controls.compliance_score}%
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#1A1A1A', fontWeight: 500 }}>
                    Compliance Score
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#6B7280' }}>
                    {metrics.controls.passed}/{metrics.controls.total} controls
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* My Active Assessments */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                My Active Assessments
              </Typography>
              <Button 
                size="small" 
                onClick={() => navigate('/assessments?assigned_to_me=true')}
              >
                View All
              </Button>
            </Box>
            {myAssessments.length === 0 ? (
              <Alert severity="info">No active assessments assigned to you</Alert>
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Assessment</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Progress</TableCell>
                      <TableCell>Findings</TableCell>
                      <TableCell>Due Date</TableCell>
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {myAssessments.map((assessment) => (
                      <TableRow key={assessment.id} hover>
                        <TableCell>
                          <Typography variant="body2" fontWeight={500}>
                            {assessment.title}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip label={assessment.assessment_type.toUpperCase()} size="small" />
                        </TableCell>
                        <TableCell>
                          <Box display="flex" alignItems="center" gap={1}>
                            <LinearProgress
                              variant="determinate"
                              value={assessment.progress_percentage}
                              sx={{ width: 100, height: 8, borderRadius: 4 }}
                            />
                            <Typography variant="caption">
                              {assessment.progress_percentage}%
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={assessment.findings_count}
                            size="small"
                            color={assessment.findings_count > 0 ? 'warning' : 'default'}
                          />
                        </TableCell>
                        <TableCell>
                          {assessment.target_completion_date
                            ? new Date(assessment.target_completion_date).toLocaleDateString()
                            : '-'}
                        </TableCell>
                        <TableCell align="right">
                          <Button
                            size="small"
                            onClick={() => navigate(`/assessments/${assessment.id}`)}
                          >
                            Continue
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Paper>
        </Grid>

        {/* Critical Findings Requiring Attention */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                Critical Findings Requiring Attention
              </Typography>
              <Button 
                size="small" 
                onClick={() => navigate('/findings?severity=critical&resolution_status=open')}
              >
                View All
              </Button>
            </Box>
            {criticalFindings.length === 0 ? (
              <Alert severity="success" icon={<CheckCircle />}>
                No open critical findings - Great work!
              </Alert>
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Finding</TableCell>
                      <TableCell>Severity</TableCell>
                      <TableCell>Assessment</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Days Open</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {criticalFindings.map((finding) => {
                      const daysOpen = calculateDaysOpen(finding.created_at)
                      return (
                        <TableRow 
                          key={finding.id} 
                          hover
                          sx={{ cursor: 'pointer' }}
                          onClick={() => navigate(`/findings/${finding.id}`)}
                        >
                          <TableCell>
                            <Typography variant="body2" fontWeight={500}>
                              {finding.title}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={finding.severity.toUpperCase()}
                              color={getSeverityColor(finding.severity)}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {finding.assessment_title}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={finding.resolution_status.replace('_', ' ').toUpperCase()}
                              size="small"
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell>
                            <Typography color={daysOpen > 7 ? 'error.main' : 'text.primary'}>
                              {daysOpen} days
                            </Typography>
                          </TableCell>
                        </TableRow>
                      )
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Paper>
        </Grid>

        {/* Quick Stats */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Quick Statistics
            </Typography>
            <Box display="flex" flexDirection="column" gap={2}>
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Finding Resolution Rate
                </Typography>
                <Box display="flex" alignItems="center" gap={1}>
                  <LinearProgress
                    variant="determinate"
                    value={metrics.findings.total > 0 
                      ? (metrics.findings.resolved / metrics.findings.total) * 100 
                      : 0}
                    sx={{ flexGrow: 1, height: 8, borderRadius: 4 }}
                    color="success"
                  />
                  <Typography variant="body2">
                    {metrics.findings.total > 0 
                      ? Math.round((metrics.findings.resolved / metrics.findings.total) * 100)
                      : 0}%
                  </Typography>
                </Box>
                <Typography variant="caption" color="text.secondary">
                  {metrics.findings.resolved} of {metrics.findings.total} resolved
                </Typography>
              </Box>

              <Box>
                <Typography variant="body2" color="text.secondary">
                  Control Testing Coverage
                </Typography>
                <Box display="flex" alignItems="center" gap={1}>
                  <LinearProgress
                    variant="determinate"
                    value={metrics.controls.total > 0 
                      ? (metrics.controls.tested / metrics.controls.total) * 100 
                      : 0}
                    sx={{ flexGrow: 1, height: 8, borderRadius: 4 }}
                    color="info"
                  />
                  <Typography variant="body2">
                    {metrics.controls.total > 0 
                      ? Math.round((metrics.controls.tested / metrics.controls.total) * 100)
                      : 0}%
                  </Typography>
                </Box>
                <Typography variant="caption" color="text.secondary">
                  {metrics.controls.tested} of {metrics.controls.total} tested
                </Typography>
              </Box>

              <Divider />

              <Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Recent Activity (30 days)
                </Typography>
                <Grid container spacing={1}>
                  <Grid item xs={6}>
                    <Typography variant="h5" color="primary">
                      {metrics.recent_activity.new_assessments}
                    </Typography>
                    <Typography variant="caption">New Assessments</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="h5" color="warning.main">
                      {metrics.recent_activity.new_findings}
                    </Typography>
                    <Typography variant="caption">New Findings</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="h5" color="success.main">
                      {metrics.recent_activity.resolved_findings}
                    </Typography>
                    <Typography variant="caption">Resolved</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="h5" color="error.main">
                      {metrics.risk_score}
                    </Typography>
                    <Typography variant="caption">Risk Score</Typography>
                  </Grid>
                </Grid>
              </Box>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}

export default AnalystDashboard