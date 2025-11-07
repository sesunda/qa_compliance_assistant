import React, { useState, useEffect } from 'react'
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControlLabel,
  Radio,
  RadioGroup,
  FormControl,
  FormLabel,
  Divider,
  Stack,
} from '@mui/material'
import {
  RateReview,
  CheckCircle,
  Cancel,
  Warning,
  TrendingUp,
  Assignment,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import findingsService, { FindingListItem } from '../services/findings'

const QAReviewPage: React.FC = () => {
  const navigate = useNavigate()
  const [pendingFindings, setPendingFindings] = useState<FindingListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [validationDialogOpen, setValidationDialogOpen] = useState(false)
  const [selectedFinding, setSelectedFinding] = useState<FindingListItem | null>(null)
  const [validationForm, setValidationForm] = useState({
    approved: true,
    validation_notes: '',
  })
  const [actionLoading, setActionLoading] = useState(false)

  useEffect(() => {
    loadPendingFindings()
  }, [])

  const loadPendingFindings = async () => {
    try {
      setLoading(true)
      // Load findings that are resolved but not yet validated
      const findings = await findingsService.list({
        resolution_status: 'resolved',
      })
      setPendingFindings(findings)
      setError(null)
    } catch (err: any) {
      console.error('Failed to load pending findings:', err)
      setError(err.response?.data?.detail || 'Failed to load findings')
    } finally {
      setLoading(false)
    }
  }

  const handleOpenValidation = (finding: FindingListItem) => {
    setSelectedFinding(finding)
    setValidationForm({
      approved: true,
      validation_notes: '',
    })
    setValidationDialogOpen(true)
  }

  const handleValidate = async () => {
    if (!selectedFinding) return

    if (!validationForm.validation_notes.trim()) {
      alert('Please provide validation notes')
      return
    }

    try {
      setActionLoading(true)
      await findingsService.validate(
        selectedFinding.id,
        validationForm.approved,
        validationForm.validation_notes.trim()
      )
      setValidationDialogOpen(false)
      await loadPendingFindings()
    } catch (err: any) {
      console.error('Failed to validate finding:', err)
      alert(err.response?.data?.detail || 'Failed to validate finding')
    } finally {
      setActionLoading(false)
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

  const calculateDaysInReview = (createdAt: string) => {
    const created = new Date(createdAt)
    const now = new Date()
    const diffTime = Math.abs(now.getTime() - created.getTime())
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  }

  const stats = {
    total: pendingFindings.length,
    critical: pendingFindings.filter(f => f.severity === 'critical').length,
    high: pendingFindings.filter(f => f.severity === 'high').length,
    overdue: pendingFindings.filter(f => f.due_date && new Date(f.due_date) < new Date()).length,
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">
          QA Review Dashboard
        </Typography>
        <Button
          variant="outlined"
          startIcon={<Assignment />}
          onClick={() => navigate('/findings')}
        >
          All Findings
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      {/* Statistics Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <RateReview color="primary" sx={{ mr: 2, fontSize: 40 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Pending Review
                  </Typography>
                  <Typography variant="h4">
                    {stats.total}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ bgcolor: stats.critical > 0 ? 'error.light' : undefined }}>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Warning 
                  color={stats.critical > 0 ? 'error' : 'disabled'} 
                  sx={{ mr: 2, fontSize: 40 }} 
                />
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Critical
                  </Typography>
                  <Typography variant="h4" color={stats.critical > 0 ? 'error.dark' : undefined}>
                    {stats.critical}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ bgcolor: stats.high > 0 ? 'warning.light' : undefined }}>
            <CardContent>
              <Box display="flex" alignItems="center">
                <TrendingUp 
                  color={stats.high > 0 ? 'warning' : 'disabled'} 
                  sx={{ mr: 2, fontSize: 40 }} 
                />
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    High Severity
                  </Typography>
                  <Typography variant="h4" color={stats.high > 0 ? 'warning.dark' : undefined}>
                    {stats.high}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ bgcolor: stats.overdue > 0 ? 'error.light' : undefined }}>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Cancel 
                  color={stats.overdue > 0 ? 'error' : 'disabled'} 
                  sx={{ mr: 2, fontSize: 40 }} 
                />
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Overdue
                  </Typography>
                  <Typography variant="h4" color={stats.overdue > 0 ? 'error.dark' : undefined}>
                    {stats.overdue}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Pending Findings Table */}
      <Paper>
        <Box sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Findings Pending Validation
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Review and validate resolved findings to complete the QA process
          </Typography>
        </Box>
        
        {pendingFindings.length === 0 ? (
          <Alert severity="success" icon={<CheckCircle />} sx={{ m: 2 }}>
            No findings pending validation - Great work!
          </Alert>
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Finding</TableCell>
                  <TableCell>Assessment</TableCell>
                  <TableCell>Severity</TableCell>
                  <TableCell>Priority</TableCell>
                  <TableCell>Assigned To</TableCell>
                  <TableCell>Days in Review</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {pendingFindings.map((finding) => {
                  const daysInReview = calculateDaysInReview(finding.created_at)
                  const isOverdue = finding.due_date && new Date(finding.due_date) < new Date()
                  
                  return (
                    <TableRow 
                      key={finding.id}
                      hover
                      sx={{ 
                        cursor: 'pointer',
                        bgcolor: isOverdue ? 'error.lighter' : undefined
                      }}
                      onClick={() => navigate(`/findings/${finding.id}`)}
                    >
                      <TableCell>
                        <Typography variant="body2" fontWeight={500}>
                          {finding.title}
                        </Typography>
                        {isOverdue && (
                          <Chip 
                            label="OVERDUE" 
                            color="error" 
                            size="small" 
                            sx={{ mt: 0.5 }}
                          />
                        )}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {finding.assessment_title}
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
                        <Chip
                          label={finding.priority}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {finding.assigned_to || 'Unassigned'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography 
                          variant="body2"
                          color={daysInReview > 7 ? 'error.main' : 'text.primary'}
                        >
                          {daysInReview} days
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Stack direction="row" spacing={1} justifyContent="flex-end">
                          <Button
                            size="small"
                            variant="outlined"
                            startIcon={<RateReview />}
                            onClick={(e) => {
                              e.stopPropagation()
                              handleOpenValidation(finding)
                            }}
                          >
                            Review
                          </Button>
                        </Stack>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      {/* Validation Dialog */}
      <Dialog 
        open={validationDialogOpen} 
        onClose={() => setValidationDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <RateReview color="primary" />
            <Typography variant="h6">Validate Finding Resolution</Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedFinding && (
            <Box sx={{ pt: 2 }}>
              <Alert severity="info" sx={{ mb: 2 }}>
                Reviewing: <strong>{selectedFinding.title}</strong>
              </Alert>

              <FormControl component="fieldset" sx={{ mb: 3 }}>
                <FormLabel component="legend">Validation Decision</FormLabel>
                <RadioGroup
                  value={validationForm.approved.toString()}
                  onChange={(e) => setValidationForm({
                    ...validationForm,
                    approved: e.target.value === 'true'
                  })}
                >
                  <FormControlLabel
                    value="true"
                    control={<Radio />}
                    label={
                      <Box>
                        <Typography variant="body1" fontWeight={500} color="success.main">
                          Approve Resolution
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          The finding has been properly resolved and can be closed
                        </Typography>
                      </Box>
                    }
                  />
                  <FormControlLabel
                    value="false"
                    control={<Radio />}
                    label={
                      <Box>
                        <Typography variant="body1" fontWeight={500} color="error.main">
                          Reject Resolution
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          The resolution is inadequate and requires additional work
                        </Typography>
                      </Box>
                    }
                  />
                </RadioGroup>
              </FormControl>

              <Divider sx={{ mb: 2 }} />

              <TextField
                label="Validation Notes"
                multiline
                rows={6}
                fullWidth
                required
                value={validationForm.validation_notes}
                onChange={(e) => setValidationForm({
                  ...validationForm,
                  validation_notes: e.target.value
                })}
                placeholder="Provide detailed feedback on the resolution quality, completeness, and effectiveness..."
                helperText="Required: Explain your validation decision"
              />

              <Box sx={{ bgcolor: 'background.default', p: 2, borderRadius: 1, mt: 2 }}>
                <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                  <strong>QA Review Guidelines:</strong>
                </Typography>
                <Typography variant="caption" color="text.secondary" display="block">
                  • Verify the root cause was properly identified
                </Typography>
                <Typography variant="caption" color="text.secondary" display="block">
                  • Confirm the remediation is complete and effective
                </Typography>
                <Typography variant="caption" color="text.secondary" display="block">
                  • Check that evidence supports the resolution
                </Typography>
                <Typography variant="caption" color="text.secondary" display="block">
                  • Assess if similar issues exist elsewhere
                </Typography>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setValidationDialogOpen(false)} disabled={actionLoading}>
            Cancel
          </Button>
          <Button
            onClick={handleValidate}
            variant="contained"
            color={validationForm.approved ? 'success' : 'error'}
            startIcon={actionLoading ? <CircularProgress size={20} /> : <CheckCircle />}
            disabled={actionLoading}
          >
            {actionLoading 
              ? 'Submitting...' 
              : validationForm.approved 
                ? 'Approve & Close' 
                : 'Reject & Reopen'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default QAReviewPage
