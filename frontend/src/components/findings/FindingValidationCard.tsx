import React, { useState } from 'react'
import {
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Chip,
  Divider,
  Alert,
  TextField,
  FormControl,
  FormControlLabel,
  Radio,
  RadioGroup,
  FormLabel,
  CircularProgress,
  Stack,
  Collapse,
} from '@mui/material'
import {
  CheckCircle,
  Cancel,
  ExpandMore,
  ExpandLess,
  RateReview,
} from '@mui/icons-material'
import { Finding } from '../../services/findings'
import findingsService from '../../services/findings'

interface FindingValidationCardProps {
  finding: Finding
  onValidated?: () => void
}

const FindingValidationCard: React.FC<FindingValidationCardProps> = ({
  finding,
  onValidated,
}) => {
  const [expanded, setExpanded] = useState(false)
  const [validating, setValidating] = useState(false)
  const [validationForm, setValidationForm] = useState({
    approved: true,
    validation_notes: '',
  })
  const [error, setError] = useState<string | null>(null)

  const canValidate = finding.resolution_status === 'resolved'

  const handleValidate = async () => {
    if (!validationForm.validation_notes.trim()) {
      setError('Validation notes are required')
      return
    }

    try {
      setValidating(true)
      setError(null)
      
      await findingsService.validate(
        finding.id,
        validationForm.approved,
        validationForm.validation_notes.trim()
      )

      if (onValidated) {
        onValidated()
      }
      
      // Reset form
      setValidationForm({
        approved: true,
        validation_notes: '',
      })
      setExpanded(false)
    } catch (err: any) {
      console.error('Failed to validate finding:', err)
      setError(err.response?.data?.detail || 'Failed to validate finding')
    } finally {
      setValidating(false)
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

  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        {/* Finding Header */}
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Box flex={1}>
            <Typography variant="h6" gutterBottom>
              {finding.title}
            </Typography>
            <Stack direction="row" spacing={1} mb={1}>
              <Chip
                label={finding.severity.toUpperCase()}
                color={getSeverityColor(finding.severity)}
                size="small"
              />
              <Chip
                label={finding.resolution_status.replace('_', ' ').toUpperCase()}
                size="small"
                variant="outlined"
              />
              <Chip
                label={`Priority: ${finding.priority}`}
                size="small"
                variant="outlined"
              />
            </Stack>
          </Box>
          
          {canValidate && (
            <Button
              variant={expanded ? 'outlined' : 'contained'}
              color="primary"
              size="small"
              startIcon={expanded ? <ExpandLess /> : <RateReview />}
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? 'Cancel' : 'Validate'}
            </Button>
          )}
        </Box>

        {/* Finding Details */}
        <Typography variant="body2" color="text.secondary" paragraph>
          {finding.description}
        </Typography>

        {finding.resolution_notes && (
          <Box sx={{ bgcolor: 'success.lighter', p: 2, borderRadius: 1, mb: 2 }}>
            <Typography variant="subtitle2" color="success.dark" gutterBottom>
              Resolution Notes
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {finding.resolution_notes}
            </Typography>
          </Box>
        )}

        {/* Validation Status */}
        {!canValidate && (
          <Alert 
            severity={
              finding.resolution_status === 'validated' || finding.resolution_status === 'closed'
                ? 'success'
                : 'info'
            }
            icon={
              finding.resolution_status === 'validated' || finding.resolution_status === 'closed'
                ? <CheckCircle />
                : <RateReview />
            }
          >
            {finding.resolution_status === 'open' && 'Finding is open - no validation needed yet'}
            {finding.resolution_status === 'in_progress' && 'Finding is in progress - waiting for resolution'}
            {finding.resolution_status === 'validated' && 'Finding has been validated and approved'}
            {finding.resolution_status === 'closed' && 'Finding is closed'}
          </Alert>
        )}

        {/* Validation Form */}
        <Collapse in={expanded && canValidate}>
          <Divider sx={{ my: 2 }} />
          
          <Box sx={{ mt: 2 }}>
            <Alert severity="info" sx={{ mb: 2 }}>
              Review the resolution and provide your validation decision
            </Alert>

            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            <FormControl component="fieldset" sx={{ mb: 3, width: '100%' }}>
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
                    <Box display="flex" alignItems="center" gap={1}>
                      <CheckCircle color="success" fontSize="small" />
                      <Box>
                        <Typography variant="body2" fontWeight={500}>
                          Approve Resolution
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          The finding has been properly resolved
                        </Typography>
                      </Box>
                    </Box>
                  }
                />
                <FormControlLabel
                  value="false"
                  control={<Radio />}
                  label={
                    <Box display="flex" alignItems="center" gap={1}>
                      <Cancel color="error" fontSize="small" />
                      <Box>
                        <Typography variant="body2" fontWeight={500}>
                          Reject Resolution
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          The resolution is inadequate
                        </Typography>
                      </Box>
                    </Box>
                  }
                />
              </RadioGroup>
            </FormControl>

            <TextField
              label="Validation Notes"
              multiline
              rows={4}
              fullWidth
              required
              value={validationForm.validation_notes}
              onChange={(e) => setValidationForm({
                ...validationForm,
                validation_notes: e.target.value
              })}
              placeholder="Provide detailed feedback on the resolution quality and effectiveness..."
              sx={{ mb: 2 }}
            />

            <Box display="flex" justifyContent="flex-end" gap={2}>
              <Button
                variant="outlined"
                onClick={() => {
                  setExpanded(false)
                  setError(null)
                  setValidationForm({
                    approved: true,
                    validation_notes: '',
                  })
                }}
                disabled={validating}
              >
                Cancel
              </Button>
              <Button
                variant="contained"
                color={validationForm.approved ? 'success' : 'error'}
                onClick={handleValidate}
                disabled={validating || !validationForm.validation_notes.trim()}
                startIcon={validating ? <CircularProgress size={20} /> : <CheckCircle />}
              >
                {validating 
                  ? 'Submitting...' 
                  : validationForm.approved 
                    ? 'Approve & Close' 
                    : 'Reject & Reopen'}
              </Button>
            </Box>
          </Box>
        </Collapse>

        {/* Metadata */}
        <Divider sx={{ my: 2 }} />
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="caption" color="text.secondary">
            Assessment: {finding.assessment_title}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {finding.assigned_to_name || finding.assigned_to_username || 'Unassigned'}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  )
}

export default FindingValidationCard
