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
  Delete as DeleteIcon,
  FilterList as FilterIcon
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import assessmentsService, { AssessmentListItem } from '../services/assessments'
import CreateAssessmentDialog from '../components/assessments/CreateAssessmentDialog'

const AssessmentsPage: React.FC = () => {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [assessments, setAssessments] = useState<AssessmentListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  
  // Filters
  const [statusFilter, setStatusFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [assignedToMe, setAssignedToMe] = useState(false)

  const loadAssessments = async () => {
    try {
      setLoading(true)
      const data = await assessmentsService.list({
        status_filter: statusFilter || undefined,
        assessment_type: typeFilter || undefined,
        assigned_to_me: assignedToMe
      })
      setAssessments(data)
      setError(null)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load assessments')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAssessments()
  }, [statusFilter, typeFilter, assignedToMe])

  const handleCreateSuccess = () => {
    setCreateDialogOpen(false)
    loadAssessments()
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this assessment?')) {
      return
    }
    
    try {
      await assessmentsService.delete(id)
      loadAssessments()
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete assessment')
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

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'vapt': return 'VAPT'
      case 'infra_pt': return 'Infrastructure PT'
      case 'compliance_audit': return 'Compliance Audit'
      default: return type
    }
  }

  const canCreateAssessment = () => {
    const role = user?.role?.name?.toLowerCase()
    return ['analyst', 'auditor', 'admin', 'super_admin'].includes(role || '')
  }

  const canDeleteAssessment = () => {
    const role = user?.role?.name?.toLowerCase()
    return ['admin', 'super_admin'].includes(role || '')
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Security Assessments</Typography>
        {canCreateAssessment() && (
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
          >
            New Assessment
          </Button>
        )}
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Stack direction="row" spacing={2} alignItems="center">
          <FilterIcon color="action" />
          <TextField
            select
            label="Status"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            size="small"
            sx={{ minWidth: 150 }}
          >
            <MenuItem value="">All Statuses</MenuItem>
            <MenuItem value="planning">Planning</MenuItem>
            <MenuItem value="in_progress">In Progress</MenuItem>
            <MenuItem value="completed">Completed</MenuItem>
            <MenuItem value="closed">Closed</MenuItem>
          </TextField>

          <TextField
            select
            label="Type"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            size="small"
            sx={{ minWidth: 180 }}
          >
            <MenuItem value="">All Types</MenuItem>
            <MenuItem value="vapt">VAPT</MenuItem>
            <MenuItem value="infra_pt">Infrastructure PT</MenuItem>
            <MenuItem value="compliance_audit">Compliance Audit</MenuItem>
          </TextField>

          <Button
            variant={assignedToMe ? 'contained' : 'outlined'}
            onClick={() => setAssignedToMe(!assignedToMe)}
            size="small"
          >
            Assigned to Me
          </Button>

          {(statusFilter || typeFilter || assignedToMe) && (
            <Button
              onClick={() => {
                setStatusFilter('')
                setTypeFilter('')
                setAssignedToMe(false)
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

      {/* Assessments Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Title</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Framework</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Progress</TableCell>
              <TableCell>Assigned To</TableCell>
              <TableCell align="center">Findings</TableCell>
              <TableCell align="center">Controls</TableCell>
              <TableCell>Target Date</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {assessments.length === 0 && !loading ? (
              <TableRow>
                <TableCell colSpan={10} align="center">
                  <Typography variant="body2" color="text.secondary" sx={{ py: 4 }}>
                    No assessments found. {canCreateAssessment() && 'Click "New Assessment" to create one.'}
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              assessments.map((assessment) => (
                <TableRow key={assessment.id} hover>
                  <TableCell>
                    <Typography variant="body2" fontWeight={500}>
                      {assessment.title}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip label={getTypeLabel(assessment.assessment_type)} size="small" />
                  </TableCell>
                  <TableCell>
                    {assessment.framework || '-'}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={assessment.status.replace('_', ' ').toUpperCase()}
                      color={getStatusColor(assessment.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <LinearProgress
                        variant="determinate"
                        value={assessment.progress_percentage}
                        sx={{ flexGrow: 1, height: 8, borderRadius: 4 }}
                      />
                      <Typography variant="caption">
                        {assessment.progress_percentage}%
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    {assessment.assigned_to || '-'}
                  </TableCell>
                  <TableCell align="center">
                    <Chip
                      label={assessment.findings_count}
                      size="small"
                      color={assessment.findings_count > 0 ? 'warning' : 'default'}
                    />
                  </TableCell>
                  <TableCell align="center">
                    {assessment.controls_tested_count}
                  </TableCell>
                  <TableCell>
                    {assessment.target_completion_date
                      ? new Date(assessment.target_completion_date).toLocaleDateString()
                      : '-'}
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="View Details">
                      <IconButton
                        size="small"
                        onClick={() => navigate(`/assessments/${assessment.id}`)}
                      >
                        <ViewIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    {canDeleteAssessment() && (
                      <Tooltip title="Delete">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDelete(assessment.id)}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create Dialog */}
      <CreateAssessmentDialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        onSuccess={handleCreateSuccess}
      />
    </Box>
  )
}

export default AssessmentsPage
