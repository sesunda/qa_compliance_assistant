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
} from '@mui/material'
import { Science } from '@mui/icons-material'
import controlsService from '../../services/controls'

interface ControlTestingDialogProps {
  open: boolean
  onClose: () => void
  controlId: number
  controlTitle: string
  onSuccess?: () => void
}

const ControlTestingDialog: React.FC<ControlTestingDialogProps> = ({
  open,
  onClose,
  controlId,
  controlTitle,
  onSuccess,
}) => {
  const [formData, setFormData] = useState({
    test_result: 'passed',
    assessment_score: '',
    test_notes: '',
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
    if (!formData.assessment_score || isNaN(parseFloat(formData.assessment_score))) {
      setError('Please enter a valid assessment score')
      return
    }

    const score = parseFloat(formData.assessment_score)
    if (score < 0 || score > 100) {
      setError('Assessment score must be between 0 and 100')
      return
    }

    try {
      setLoading(true)
      setError(null)

      await controlsService.recordTestResult(controlId, {
        test_result: formData.test_result,
        assessment_score: score,
        test_notes: formData.test_notes || undefined,
      })

      if (onSuccess) {
        onSuccess()
      }

      handleClose()
    } catch (err: any) {
      console.error('Failed to record test result:', err)
      setError(err.response?.data?.detail || 'Failed to record test result')
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    setFormData({
      test_result: 'passed',
      assessment_score: '',
      test_notes: '',
    })
    setError(null)
    onClose()
  }

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          <Science color="primary" />
          <Typography variant="h6">Record Test Result</Typography>
        </Box>
      </DialogTitle>
      <DialogContent>
        <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Alert severity="info">
            Recording test result for: <strong>{controlTitle}</strong>
          </Alert>

          {error && <Alert severity="error">{error}</Alert>}

          <FormControl fullWidth required>
            <InputLabel>Test Result</InputLabel>
            <Select
              value={formData.test_result}
              label="Test Result"
              onChange={(e) => handleChange('test_result', e.target.value)}
            >
              <MenuItem value="passed">Passed</MenuItem>
              <MenuItem value="failed">Failed</MenuItem>
              <MenuItem value="not_applicable">Not Applicable</MenuItem>
            </Select>
          </FormControl>

          <TextField
            label="Assessment Score"
            type="number"
            required
            fullWidth
            value={formData.assessment_score}
            onChange={(e) => handleChange('assessment_score', e.target.value)}
            inputProps={{ min: 0, max: 100, step: 1 }}
            helperText="Enter a score between 0 and 100"
          />

          <TextField
            label="Test Notes"
            multiline
            rows={4}
            fullWidth
            value={formData.test_notes}
            onChange={(e) => handleChange('test_notes', e.target.value)}
            placeholder="Enter detailed notes about the testing procedure, findings, and any observations..."
            helperText="Optional: Add notes about the test execution"
          />

          <Box sx={{ bgcolor: 'background.default', p: 2, borderRadius: 1 }}>
            <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
              <strong>Test Result Guidelines:</strong>
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block">
              • <strong>Passed:</strong> Control is implemented and functioning as intended
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block">
              • <strong>Failed:</strong> Control has deficiencies or is not functioning properly
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block">
              • <strong>Not Applicable:</strong> Control does not apply to the current environment
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
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} /> : <Science />}
        >
          {loading ? 'Recording...' : 'Record Test Result'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default ControlTestingDialog
