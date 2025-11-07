import React, { useState, useEffect } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  MenuItem,
  Grid,
  Alert,
  CircularProgress
} from '@mui/material'
import findingsService, { CreateFindingData } from '../../services/findings'
import assessmentsService, { AssessmentListItem } from '../../services/assessments'
import { api } from '../../services/api'

interface CreateFindingDialogProps {
  open: boolean
  onClose: () => void
  onSuccess: () => void
  defaultAssessmentId?: number
}

interface User {
  id: number
  username: string
  role: { name: string }
}

const CreateFindingDialog: React.FC<CreateFindingDialogProps> = ({
  open,
  onClose,
  onSuccess,
  defaultAssessmentId
}) => {
  const [formData, setFormData] = useState<CreateFindingData>({
    assessment_id: defaultAssessmentId || 0,
    title: '',
    description: '',
    severity: 'medium',
    priority: 'medium',
    risk_rating: '',
    affected_systems: '',
    remediation_recommendation: '',
    assigned_to: undefined,
    due_date: ''
  })
  const [assessments, setAssessments] = useState<AssessmentListItem[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      loadData()
      // Reset form
      setFormData({
        assessment_id: defaultAssessmentId || 0,
        title: '',
        description: '',
        severity: 'medium',
        priority: 'medium',
        risk_rating: '',
        affected_systems: '',
        remediation_recommendation: '',
        assigned_to: undefined,
        due_date: ''
      })
      setError(null)
    }
  }, [open, defaultAssessmentId])

  const loadData = async () => {
    try {
      const [assessmentData, userData] = await Promise.all([
        assessmentsService.list({ status_filter: 'in_progress' }),
        api.get('/users')
      ])
      setAssessments(assessmentData)
      setUsers(userData.data.filter((u: User) => 
        ['analyst', 'auditor'].includes(u.role.name.toLowerCase())
      ))
    } catch (err) {
      console.error('Failed to load data:', err)
    }
  }

  const handleChange = (field: keyof CreateFindingData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleSubmit = async () => {
    // Validation
    if (!formData.title.trim()) {
      setError('Title is required')
      return
    }
    if (!formData.description.trim()) {
      setError('Description is required')
      return
    }
    if (!formData.assessment_id) {
      setError('Please select an assessment')
      return
    }

    setLoading(true)
    setError(null)

    try {
      await findingsService.create(formData)
      onSuccess()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create finding')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Create New Finding</DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12}>
            <TextField
              select
              label="Assessment"
              fullWidth
              required
              value={formData.assessment_id}
              onChange={(e) => handleChange('assessment_id', parseInt(e.target.value))}
              disabled={!!defaultAssessmentId}
            >
              <MenuItem value={0}>Select Assessment</MenuItem>
              {assessments.map(assessment => (
                <MenuItem key={assessment.id} value={assessment.id}>
                  {assessment.title}
                </MenuItem>
              ))}
            </TextField>
          </Grid>

          <Grid item xs={12}>
            <TextField
              label="Finding Title"
              fullWidth
              required
              value={formData.title}
              onChange={(e) => handleChange('title', e.target.value)}
              placeholder="SQL Injection vulnerability in login form"
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              label="Description"
              fullWidth
              required
              multiline
              rows={4}
              value={formData.description}
              onChange={(e) => handleChange('description', e.target.value)}
              placeholder="Detailed description of the finding..."
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              select
              label="Severity"
              fullWidth
              required
              value={formData.severity}
              onChange={(e) => handleChange('severity', e.target.value)}
            >
              <MenuItem value="critical">Critical</MenuItem>
              <MenuItem value="high">High</MenuItem>
              <MenuItem value="medium">Medium</MenuItem>
              <MenuItem value="low">Low</MenuItem>
              <MenuItem value="info">Info</MenuItem>
            </TextField>
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              select
              label="Priority"
              fullWidth
              value={formData.priority}
              onChange={(e) => handleChange('priority', e.target.value)}
            >
              <MenuItem value="critical">Critical</MenuItem>
              <MenuItem value="high">High</MenuItem>
              <MenuItem value="medium">Medium</MenuItem>
              <MenuItem value="low">Low</MenuItem>
            </TextField>
          </Grid>

          <Grid item xs={12}>
            <TextField
              label="Affected Systems"
              fullWidth
              value={formData.affected_systems}
              onChange={(e) => handleChange('affected_systems', e.target.value)}
              placeholder="Production web server, database cluster..."
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              label="Remediation Recommendation"
              fullWidth
              multiline
              rows={3}
              value={formData.remediation_recommendation}
              onChange={(e) => handleChange('remediation_recommendation', e.target.value)}
              placeholder="Recommended steps to remediate this finding..."
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              label="Due Date"
              type="date"
              fullWidth
              InputLabelProps={{ shrink: true }}
              value={formData.due_date}
              onChange={(e) => handleChange('due_date', e.target.value)}
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              select
              label="Assign To"
              fullWidth
              value={formData.assigned_to || ''}
              onChange={(e) => handleChange('assigned_to', e.target.value ? parseInt(e.target.value) : undefined)}
            >
              <MenuItem value="">Unassigned</MenuItem>
              {users.map(user => (
                <MenuItem key={user.id} value={user.id}>
                  {user.username} ({user.role.name})
                </MenuItem>
              ))}
            </TextField>
          </Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={loading}
          startIcon={loading && <CircularProgress size={16} />}
        >
          Create Finding
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default CreateFindingDialog
