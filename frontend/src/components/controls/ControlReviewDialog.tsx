import React, { useState } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Typography,
  Alert,
  CircularProgress,
  Chip,
} from '@mui/material'
import { RateReview } from '@mui/icons-material'
import controlsService from '../../services/controls'

interface ControlReviewDialogProps {
  open: boolean
  onClose: () => void
  controlId: number
  controlTitle: string
  onSuccess?: () => void
}

const ControlReviewDialog: React.FC<ControlReviewDialogProps> = ({
  open,
  onClose,
  controlId,
  controlTitle,
  onSuccess,
}) => {
  const [formData, setFormData] = useState({
    review_status: 'approved',
    review_notes: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }))
  }

  const handleSubmit = async () => {
    // Validation
    if (!formData.review_notes.trim()) {
      setError('Please provide review notes')
      return
    }

    try {
      setLoading(true)
      setError(null)

      await controlsService.submitReview(controlId, {
        review_status: formData.review_status,
        review_notes: formData.review_notes.trim(),
      })

      if (onSuccess) {
        onSuccess()
      }

      handleClose()
    } catch (err: any) {
      console.error('Failed to submit review:', err)
      setError(err.response?.data?.detail || 'Failed to submit review')
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    setFormData({
      review_status: 'approved',
      review_notes: '',
    })
    setError(null)
    onClose()
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved': return 'success'
      case 'needs_improvement': return 'warning'
      case 'rejected': return 'error'
      default: return 'default'
    }
  }

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          <RateReview color="primary" />
          <Typography variant="h6">Submit Control Review</Typography>
        </Box>
      </DialogTitle>
      <DialogContent>
        <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Alert severity="info">
            Reviewing control: <strong>{controlTitle}</strong>
          </Alert>

          {error && <Alert severity="error">{error}</Alert>}

          <FormControl fullWidth required>
            <InputLabel>Review Status</InputLabel>
            <Select
              value={formData.review_status}
              label="Review Status"
              onChange={(e) => handleChange('review_status', e.target.value)}
            >
              <MenuItem value="approved">
                <Box display="flex" alignItems="center" gap={1}>
                  <Chip 
                    label="Approved" 
                    color="success" 
                    size="small" 
                  />
                  <Typography variant="body2">Control design is acceptable</Typography>
                </Box>
              </MenuItem>
              <MenuItem value="needs_improvement">
                <Box display="flex" alignItems="center" gap={1}>
                  <Chip 
                    label="Needs Improvement" 
                    color="warning" 
                    size="small" 
                  />
                  <Typography variant="body2">Minor changes required</Typography>
                </Box>
              </MenuItem>
              <MenuItem value="rejected">
                <Box display="flex" alignItems="center" gap={1}>
                  <Chip 
                    label="Rejected" 
                    color="error" 
                    size="small" 
                  />
                  <Typography variant="body2">Significant redesign needed</Typography>
                </Box>
              </MenuItem>
            </Select>
          </FormControl>

          <TextField
            label="Review Notes"
            multiline
            rows={6}
            required
            fullWidth
            value={formData.review_notes}
            onChange={(e) => handleChange('review_notes', e.target.value)}
            placeholder="Provide detailed feedback on the control design, implementation, and effectiveness..."
            helperText="Required: Explain the rationale for your review decision"
          />

          <Box sx={{ bgcolor: 'background.default', p: 2, borderRadius: 1 }}>
            <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
              <strong>Review Guidelines:</strong>
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block">
              • Evaluate control design against security requirements
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block">
              • Assess implementation feasibility and completeness
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block">
              • Verify alignment with compliance framework standards
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block">
              • Provide constructive feedback for improvements
            </Typography>
          </Box>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          color={getStatusColor(formData.review_status) as any}
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} /> : <RateReview />}
        >
          {loading ? 'Submitting...' : 'Submit Review'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default ControlReviewDialog
