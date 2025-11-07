import React, { useState, useEffect } from 'react'
import {
  Box,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Tooltip,
  TextField,
  MenuItem,
  Stack,
  LinearProgress,
  Alert
} from '@mui/material'
import {
  Add as AddIcon,
  Visibility as ViewIcon,
  Warning as WarningIcon,
  CheckCircle as ResolvedIcon,
  Block as FalsePositiveIcon
} from '@mui/icons-material'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import findingsService, { FindingListItem } from '../services/findings'
import CreateFindingDialog from '../components/findings/CreateFindingDialog'

const FindingsPage: React.FC = () => {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [searchParams] = useSearchParams()
  const assessmentIdParam = searchParams.get('assessment_id')
  
  const [findings, setFindings] = useState<FindingListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  
  // Filters
  const [assessmentFilter, setAssessmentFilter] = useState(assessmentIdParam || '')
  const [severityFilter, setSeverityFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [assignedToMe, setAssignedToMe] = useState(false)

  const loadFindings = async () => {
    try {
      setLoading(true)
      const data = await findingsService.list({
        assessment_id: assessmentFilter ? parseInt(assessmentFilter) : undefined,
        severity: severityFilter || undefined,
        resolution_status: statusFilter || undefined,
        assigned_to_me: assignedToMe
      })
      setFindings(data)
      setError(null)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load findings')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadFindings()
  }, [assessmentFilter, severityFilter, statusFilter, assignedToMe])

  const handleCreateSuccess = () => {
    setCreateDialogOpen(false)
    loadFindings()
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'error'
      case 'high': return 'warning'
      case 'medium': return 'info'
      case 'low': return 'default'
      case 'info': return 'default'
      default: return 'default'
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

  const getPriorityIcon = (priority: string) => {
    if (priority === 'critical' || priority === 'high') {
      return <WarningIcon fontSize="small" color="error" />
    }
    return null
  }

  const isOverdue = (due_date?: string) => {
    if (!due_date) return false
    return new Date(due_date) < new Date()
  }

  const canCreateFinding = () => {
    const role = user?.role?.name?.toLowerCase()
    return ['analyst', 'auditor', 'admin', 'super_admin'].includes(role || '')
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Security Findings</Typography>
        {canCreateFinding() && (
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
          >
            New Finding
          </Button>
        )}
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap">
          <TextField
            select
            label="Severity"
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            size="small"
            sx={{ minWidth: 150 }}
          >
            <MenuItem value="">All Severities</MenuItem>
            <MenuItem value="critical">Critical</MenuItem>
            <MenuItem value="high">High</MenuItem>
            <MenuItem value="medium">Medium</MenuItem>
            <MenuItem value="low">Low</MenuItem>
            <MenuItem value="info">Info</MenuItem>
          </TextField>

          <TextField
            select
            label="Status"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            size="small"
            sx={{ minWidth: 150 }}
          >
            <MenuItem value="">All Statuses</MenuItem>
            <MenuItem value="open">Open</MenuItem>
            <MenuItem value="in_progress">In Progress</MenuItem>
            <MenuItem value="resolved">Resolved</MenuItem>
            <MenuItem value="validated">Validated</MenuItem>
            <MenuItem value="closed">Closed</MenuItem>
          </TextField>

          <Button
            variant={assignedToMe ? 'contained' : 'outlined'}
            onClick={() => setAssignedToMe(!assignedToMe)}
            size="small"
          >
            Assigned to Me
          </Button>

          {(severityFilter || statusFilter || assignedToMe || assessmentFilter) && (
            <Button
              onClick={() => {
                setSeverityFilter('')
                setStatusFilter('')
                setAssignedToMe(false)
                setAssessmentFilter('')
              }}
              size="small"
            >
              Clear Filters
            </Button>
          )}
        </Stack>
      </Paper>

      {/* Error */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Loading */}
      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {/* Findings Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Title</TableCell>
              <TableCell>Severity</TableCell>
              <TableCell>Priority</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Assessment</TableCell>
              <TableCell>Assigned To</TableCell>
              <TableCell>Due Date</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {findings.length === 0 && !loading ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  <Typography variant="body2" color="text.secondary" sx={{ py: 4 }}>
                    No findings found. {canCreateFinding() && 'Click "New Finding" to create one.'}
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              findings.map((finding) => (
                <TableRow
                  key={finding.id}
                  hover
                  sx={{
                    bgcolor: finding.false_positive ? 'action.hover' : undefined,
                    opacity: finding.false_positive ? 0.6 : 1
                  }}
                >
                  <TableCell>
                    <Stack direction="row" alignItems="center" spacing={1}>
                      {getPriorityIcon(finding.priority)}
                      <Typography variant="body2" fontWeight={500}>
                        {finding.title}
                      </Typography>
                      {finding.false_positive && (
                        <Chip
                          icon={<FalsePositiveIcon />}
                          label="False Positive"
                          size="small"
                          color="default"
                        />
                      )}
                    </Stack>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={finding.severity.toUpperCase()}
                      color={getSeverityColor(finding.severity)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={finding.priority.toUpperCase()}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={finding.resolution_status.replace('_', ' ').toUpperCase()}
                      color={getStatusColor(finding.resolution_status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {finding.assessment_title}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {finding.assigned_to || '-'}
                  </TableCell>
                  <TableCell>
                    {finding.due_date ? (
                      <Chip
                        label={new Date(finding.due_date).toLocaleDateString()}
                        size="small"
                        color={isOverdue(finding.due_date) ? 'error' : 'default'}
                        variant={isOverdue(finding.due_date) ? 'filled' : 'outlined'}
                      />
                    ) : (
                      '-'
                    )}
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="View Details">
                      <IconButton
                        size="small"
                        onClick={() => navigate(`/findings/${finding.id}`)}
                      >
                        <ViewIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Summary Stats */}
      {findings.length > 0 && (
        <Paper sx={{ p: 2, mt: 2 }}>
          <Stack direction="row" spacing={4}>
            <Box>
              <Typography variant="caption" color="text.secondary">Total Findings</Typography>
              <Typography variant="h6">{findings.length}</Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">Critical/High</Typography>
              <Typography variant="h6" color="error">
                {findings.filter(f => ['critical', 'high'].includes(f.severity)).length}
              </Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">Open/In Progress</Typography>
              <Typography variant="h6" color="warning.main">
                {findings.filter(f => ['open', 'in_progress'].includes(f.resolution_status)).length}
              </Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">Resolved/Validated</Typography>
              <Typography variant="h6" color="success.main">
                {findings.filter(f => ['resolved', 'validated', 'closed'].includes(f.resolution_status)).length}
              </Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">Overdue</Typography>
              <Typography variant="h6" color="error">
                {findings.filter(f => isOverdue(f.due_date) && !['resolved', 'validated', 'closed'].includes(f.resolution_status)).length}
              </Typography>
            </Box>
          </Stack>
        </Paper>
      )}

      {/* Create Dialog */}
      <CreateFindingDialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        onSuccess={handleCreateSuccess}
        defaultAssessmentId={assessmentFilter ? parseInt(assessmentFilter) : undefined}
      />
    </Box>
  )
}

export default FindingsPage
