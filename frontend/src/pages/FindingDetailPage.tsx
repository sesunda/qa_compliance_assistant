import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  Button,
  Divider,
  Alert,
  CircularProgress,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  IconButton,
} from '@mui/material'
import {
  ArrowBack,
  Edit,
  Assignment,
  CheckCircle,
  Block,
  Comment,
  Send,
  Timeline,
  Info,
  Person,
  CalendarToday,
  Error as ErrorIcon,
} from '@mui/icons-material'
import findingsService, { Finding, FindingComment } from '../services/findings'

const FindingDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [finding, setFinding] = useState<Finding | null>(null)
  const [comments, setComments] = useState<FindingComment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Dialog states
  const [assignDialogOpen, setAssignDialogOpen] = useState(false)
  const [resolveDialogOpen, setResolveDialogOpen] = useState(false)
  const [commentDialogOpen, setCommentDialogOpen] = useState(false)

  // Form states
  const [assigneeId, setAssigneeId] = useState('')
  const [resolutionNotes, setResolutionNotes] = useState('')
  const [newComment, setNewComment] = useState('')
  const [actionLoading, setActionLoading] = useState(false)

  useEffect(() => {
    if (id) {
      loadFindingData()
    }
  }, [id])

  const loadFindingData = async () => {
    try {
      setLoading(true)
      const [findingData, commentsData] = await Promise.all([
        findingsService.get(parseInt(id!)),
        findingsService.getComments(parseInt(id!)),
      ])
      setFinding(findingData)
      setComments(commentsData)
      setError(null)
    } catch (err: any) {
      console.error('Failed to load finding:', err)
      setError(err.response?.data?.detail || 'Failed to load finding')
    } finally {
      setLoading(false)
    }
  }

  const handleAssign = async () => {
    if (!assigneeId) return
    
    try {
      setActionLoading(true)
      await findingsService.assign(parseInt(id!), parseInt(assigneeId))
      setAssignDialogOpen(false)
      setAssigneeId('')
      await loadFindingData()
    } catch (err: any) {
      console.error('Failed to assign finding:', err)
      alert(err.response?.data?.detail || 'Failed to assign finding')
    } finally {
      setActionLoading(false)
    }
  }

  const handleResolve = async () => {
    if (!resolutionNotes.trim()) {
      alert('Please provide resolution notes')
      return
    }

    try {
      setActionLoading(true)
      await findingsService.resolve(parseInt(id!), resolutionNotes.trim())
      setResolveDialogOpen(false)
      setResolutionNotes('')
      await loadFindingData()
    } catch (err: any) {
      console.error('Failed to resolve finding:', err)
      alert(err.response?.data?.detail || 'Failed to resolve finding')
    } finally {
      setActionLoading(false)
    }
  }

  const handleValidate = async () => {
    if (!window.confirm('Validate this finding resolution?')) return

    try {
      setActionLoading(true)
      await findingsService.validate(parseInt(id!), true, 'Validation approved')
      await loadFindingData()
    } catch (err: any) {
      console.error('Failed to validate finding:', err)
      alert(err.response?.data?.detail || 'Failed to validate finding')
    } finally {
      setActionLoading(false)
    }
  }

  const handleMarkFalsePositive = async () => {
    if (!window.confirm('Mark this finding as a false positive?')) return

    try {
      setActionLoading(true)
      await findingsService.markFalsePositive(parseInt(id!), 'Marked as false positive')
      await loadFindingData()
    } catch (err: any) {
      console.error('Failed to mark as false positive:', err)
      alert(err.response?.data?.detail || 'Failed to mark as false positive')
    } finally {
      setActionLoading(false)
    }
  }

  const handleAddComment = async () => {
    if (!newComment.trim()) return

    try {
      setActionLoading(true)
      await findingsService.addComment(parseInt(id!), 'general', newComment.trim())
      setCommentDialogOpen(false)
      setNewComment('')
      await loadFindingData()
    } catch (err: any) {
      console.error('Failed to add comment:', err)
      alert(err.response?.data?.detail || 'Failed to add comment')
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open': return 'error'
      case 'in_progress': return 'info'
      case 'resolved': return 'warning'
      case 'validated': return 'success'
      case 'closed': return 'default'
      default: return 'default'
    }
  }

  const isOverdue = finding?.due_date 
    ? new Date(finding.due_date) < new Date() && finding.resolution_status !== 'closed'
    : false

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress />
      </Box>
    )
  }

  if (error || !finding) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error || 'Finding not found'}</Alert>
        <Button onClick={() => navigate('/findings')} sx={{ mt: 2 }}>
          Back to Findings
        </Button>
      </Box>
    )
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <IconButton onClick={() => navigate('/findings')}>
            <ArrowBack />
          </IconButton>
          <Typography variant="h5">Finding Details</Typography>
        </Box>
        <Box display="flex" gap={1}>
          <Button
            startIcon={<Edit />}
            variant="outlined"
            onClick={() => {/* TODO: Edit dialog */}}
          >
            Edit
          </Button>
        </Box>
      </Box>

      {/* Overdue Alert */}
      {isOverdue && (
        <Alert severity="error" sx={{ mb: 3 }} icon={<ErrorIcon />}>
          This finding is overdue! Due date: {new Date(finding.due_date!).toLocaleDateString()}
        </Alert>
      )}

      {/* False Positive Alert */}
      {finding.is_false_positive && (
        <Alert severity="info" sx={{ mb: 3 }} icon={<Info />}>
          This finding has been marked as a <strong>false positive</strong>
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Main Information */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              {finding.title}
            </Typography>
            
            <Box display="flex" gap={1} mb={2}>
              <Chip
                label={finding.severity.toUpperCase()}
                color={getSeverityColor(finding.severity)}
                size="small"
              />
              <Chip
                label={finding.resolution_status.replace('_', ' ').toUpperCase()}
                color={getStatusColor(finding.resolution_status)}
                size="small"
              />
              <Chip
                label={`Priority: ${finding.priority}`}
                size="small"
                variant="outlined"
              />
            </Box>

            <Divider sx={{ my: 2 }} />

            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Description
            </Typography>
            <Typography variant="body1" paragraph>
              {finding.description}
            </Typography>

            {finding.remediation_plan && (
              <>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Remediation Plan
                </Typography>
                <Typography variant="body2" paragraph>
                  {finding.remediation_plan}
                </Typography>
              </>
            )}

            {finding.resolution_notes && (
              <>
                <Divider sx={{ my: 2 }} />
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Resolution Notes
                </Typography>
                <Alert severity="success" icon={<CheckCircle />}>
                  {finding.resolution_notes}
                </Alert>
              </>
            )}
          </Paper>

          {/* Comments Section */}
          <Paper sx={{ p: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                Comments ({comments.length})
              </Typography>
              <Button
                startIcon={<Comment />}
                variant="outlined"
                size="small"
                onClick={() => setCommentDialogOpen(true)}
              >
                Add Comment
              </Button>
            </Box>

            {comments.length === 0 ? (
              <Alert severity="info">No comments yet</Alert>
            ) : (
              <List>
                {comments.map((comment) => (
                  <ListItem key={comment.id} alignItems="flex-start">
                    <ListItemAvatar>
                      <Avatar>
                        {comment.user_name.charAt(0).toUpperCase()}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={
                        <Box display="flex" justifyContent="space-between" alignItems="center">
                          <Typography variant="subtitle2">{comment.user_name}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {new Date(comment.created_at).toLocaleString()}
                          </Typography>
                        </Box>
                      }
                      secondary={
                        <Typography variant="body2" sx={{ mt: 1 }}>
                          {comment.comment}
                        </Typography>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            )}
          </Paper>
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} md={4}>
          {/* Actions Card */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Actions
              </Typography>
              <Box display="flex" flexDirection="column" gap={1}>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<Assignment />}
                  onClick={() => setAssignDialogOpen(true)}
                  disabled={finding.resolution_status === 'closed'}
                >
                  Assign
                </Button>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<CheckCircle />}
                  onClick={() => setResolveDialogOpen(true)}
                  disabled={finding.resolution_status !== 'in_progress'}
                  color="success"
                >
                  Resolve
                </Button>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<CheckCircle />}
                  onClick={handleValidate}
                  disabled={finding.resolution_status !== 'resolved'}
                  color="info"
                >
                  Validate
                </Button>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<Block />}
                  onClick={handleMarkFalsePositive}
                  disabled={finding.is_false_positive || finding.resolution_status === 'closed'}
                  color="warning"
                >
                  Mark False Positive
                </Button>
              </Box>
            </CardContent>
          </Card>

          {/* Details Card */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Details
              </Typography>
              
              <Box display="flex" flexDirection="column" gap={2}>
                <Box>
                  <Typography variant="caption" color="text.secondary" display="flex" alignItems="center" gap={0.5}>
                    <Person fontSize="small" /> Assigned To
                  </Typography>
                  <Typography variant="body2">
                    {finding.assigned_to_name || 'Unassigned'}
                  </Typography>
                </Box>

                <Box>
                  <Typography variant="caption" color="text.secondary" display="flex" alignItems="center" gap={0.5}>
                    <Timeline fontSize="small" /> Assessment
                  </Typography>
                  <Typography variant="body2">
                    {finding.assessment_title}
                  </Typography>
                </Box>

                <Box>
                  <Typography variant="caption" color="text.secondary" display="flex" alignItems="center" gap={0.5}>
                    <CalendarToday fontSize="small" /> Due Date
                  </Typography>
                  <Typography 
                    variant="body2"
                    color={isOverdue ? 'error.main' : 'text.primary'}
                  >
                    {finding.due_date 
                      ? new Date(finding.due_date).toLocaleDateString()
                      : 'Not set'}
                  </Typography>
                </Box>

                <Divider />

                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Created
                  </Typography>
                  <Typography variant="body2">
                    {new Date(finding.created_at).toLocaleString()}
                  </Typography>
                </Box>

                {finding.updated_at && (
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Last Updated
                    </Typography>
                    <Typography variant="body2">
                      {new Date(finding.updated_at).toLocaleString()}
                    </Typography>
                  </Box>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Assign Dialog */}
      <Dialog open={assignDialogOpen} onClose={() => setAssignDialogOpen(false)}>
        <DialogTitle>Assign Finding</DialogTitle>
        <DialogContent>
          <TextField
            label="Assignee User ID"
            type="number"
            fullWidth
            value={assigneeId}
            onChange={(e) => setAssigneeId(e.target.value)}
            sx={{ mt: 2 }}
            helperText="Enter the user ID to assign this finding to"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAssignDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleAssign} variant="contained" disabled={actionLoading}>
            {actionLoading ? <CircularProgress size={20} /> : 'Assign'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Resolve Dialog */}
      <Dialog open={resolveDialogOpen} onClose={() => setResolveDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Resolve Finding</DialogTitle>
        <DialogContent>
          <TextField
            label="Resolution Notes"
            multiline
            rows={4}
            fullWidth
            required
            value={resolutionNotes}
            onChange={(e) => setResolutionNotes(e.target.value)}
            sx={{ mt: 2 }}
            placeholder="Describe how this finding was resolved..."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResolveDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleResolve} variant="contained" color="success" disabled={actionLoading}>
            {actionLoading ? <CircularProgress size={20} /> : 'Resolve'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Comment Dialog */}
      <Dialog open={commentDialogOpen} onClose={() => setCommentDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Comment</DialogTitle>
        <DialogContent>
          <TextField
            label="Comment"
            multiline
            rows={4}
            fullWidth
            required
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            sx={{ mt: 2 }}
            placeholder="Enter your comment..."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCommentDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleAddComment} variant="contained" startIcon={<Send />} disabled={actionLoading}>
            {actionLoading ? <CircularProgress size={20} /> : 'Add Comment'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default FindingDetailPage
