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
import assessmentsService, { CreateAssessmentData } from '../../services/assessments'
import { api } from '../../services/api'

interface CreateAssessmentDialogProps {
  open: boolean
  onClose: () => void
  onSuccess: () => void
}

interface User {
  id: number
  username: string
  role: { name: string }
}

const CreateAssessmentDialog: React.FC<CreateAssessmentDialogProps> = ({
  open,
  onClose,
  onSuccess
}) => {
  const [formData, setFormData] = useState<CreateAssessmentData>({
    title: '',
    assessment_type: 'vapt',
    framework: '',
    scope: '',
    target_completion_date: '',
    period_start: '',
    period_end: '',
    assigned_to: undefined
  })
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      // Load analysts for assignment
      loadUsers()
      // Reset form
      setFormData({
        title: '',
        assessment_type: 'vapt',
        framework: '',
        scope: '',
        target_completion_date: '',
        period_start: '',
        period_end: '',
        assigned_to: undefined
      })
      setError(null)
    }
  }, [open])

  const loadUsers = async () => {
    try {
      const response = await api.get('/users')
      setUsers(response.data.filter((u: User) => 
        ['analyst', 'auditor'].includes(u.role.name.toLowerCase())
      ))
    } catch (err) {
      console.error('Failed to load users:', err)
    }
  }

  const handleChange = (field: keyof CreateAssessmentData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleSubmit = async () => {
    // Validation
    if (!formData.title.trim()) {
      setError('Title is required')
      return
    }

    setLoading(true)
    setError(null)

    try {
      await assessmentsService.create(formData)
      onSuccess()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create assessment')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Create New Assessment</DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12}>
            <TextField
              label="Assessment Title"
              fullWidth
              required
              value={formData.title}
              onChange={(e) => handleChange('title', e.target.value)}
              placeholder="Q4 2025 Security Assessment"
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              select
              label="Assessment Type"
              fullWidth
              required
              value={formData.assessment_type}
              onChange={(e) => handleChange('assessment_type', e.target.value)}
            >
              <MenuItem value="vapt">VAPT (Vulnerability Assessment & Penetration Testing)</MenuItem>
              <MenuItem value="infra_pt">Infrastructure Penetration Testing</MenuItem>
              <MenuItem value="compliance_audit">Compliance Audit</MenuItem>
            </TextField>
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              label="Framework"
              fullWidth
              value={formData.framework}
              onChange={(e) => handleChange('framework', e.target.value)}
              placeholder="ISO27001, NIST, PCI-DSS, etc."
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              label="Scope"
              fullWidth
              multiline
              rows={3}
              value={formData.scope}
              onChange={(e) => handleChange('scope', e.target.value)}
              placeholder="Describe the assessment scope..."
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              label="Assessment Period Start"
              type="date"
              fullWidth
              InputLabelProps={{ shrink: true }}
              value={formData.period_start}
              onChange={(e) => handleChange('period_start', e.target.value)}
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              label="Assessment Period End"
              type="date"
              fullWidth
              InputLabelProps={{ shrink: true }}
              value={formData.period_end}
              onChange={(e) => handleChange('period_end', e.target.value)}
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              label="Target Completion Date"
              type="date"
              fullWidth
              InputLabelProps={{ shrink: true }}
              value={formData.target_completion_date}
              onChange={(e) => handleChange('target_completion_date', e.target.value)}
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
          Create Assessment
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default CreateAssessmentDialog
