import React, { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  IconButton,
  TextField,
  Typography,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tooltip
} from '@mui/material'
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Business as BusinessIcon,
  People as PeopleIcon,
  FolderOpen as ProjectIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material'
import toast from 'react-hot-toast'
import { agenciesService, Agency, AgencyCreate, AgencyStats } from '../services/agencies'

const AgenciesPage: React.FC = () => {
  const [agencies, setAgencies] = useState<Agency[]>([])
  const [selectedAgency, setSelectedAgency] = useState<Agency | null>(null)
  const [agencyStats, setAgencyStats] = useState<Record<number, AgencyStats>>({})
  const [loading, setLoading] = useState(true)
  const [statsLoading, setStatsLoading] = useState<Record<number, boolean>>({})
  const [openDialog, setOpenDialog] = useState(false)
  const [openDeleteDialog, setOpenDeleteDialog] = useState(false)
  const [formData, setFormData] = useState<AgencyCreate>({
    name: '',
    code: '',
    description: '',
    contact_email: '',
    active: true
  })
  const [searchTerm, setSearchTerm] = useState('')
  const [showInactive, setShowInactive] = useState(false)

  useEffect(() => {
    loadAgencies()
  }, [showInactive, searchTerm])

  const loadAgencies = async () => {
    try {
      setLoading(true)
      const data = await agenciesService.getAll({
        active_only: !showInactive,
        search: searchTerm || undefined
      })
      setAgencies(data)
    } catch (error) {
      console.error('Failed to load agencies:', error)
      toast.error('Failed to load agencies')
    } finally {
      setLoading(false)
    }
  }

  const loadAgencyStats = async (agencyId: number) => {
    try {
      setStatsLoading(prev => ({ ...prev, [agencyId]: true }))
      const stats = await agenciesService.getStats(agencyId)
      setAgencyStats(prev => ({ ...prev, [agencyId]: stats }))
    } catch (error) {
      console.error(`Failed to load stats for agency ${agencyId}:`, error)
    } finally {
      setStatsLoading(prev => ({ ...prev, [agencyId]: false }))
    }
  }

  const handleOpenDialog = (agency?: Agency) => {
    if (agency) {
      setSelectedAgency(agency)
      setFormData({
        name: agency.name,
        code: agency.code || '',
        description: agency.description || '',
        contact_email: agency.contact_email || '',
        active: agency.active
      })
    } else {
      setSelectedAgency(null)
      setFormData({
        name: '',
        code: '',
        description: '',
        contact_email: '',
        active: true
      })
    }
    setOpenDialog(true)
  }

  const handleCloseDialog = () => {
    setOpenDialog(false)
    setSelectedAgency(null)
  }

  const handleSubmit = async () => {
    try {
      if (selectedAgency) {
        await agenciesService.update(selectedAgency.id, formData)
        toast.success('Agency updated successfully')
      } else {
        await agenciesService.create(formData)
        toast.success('Agency created successfully')
      }
      handleCloseDialog()
      loadAgencies()
    } catch (error: any) {
      console.error('Failed to save agency:', error)
      toast.error(error.response?.data?.detail || 'Failed to save agency')
    }
  }

  const handleDelete = async () => {
    if (!selectedAgency) return

    try {
      await agenciesService.delete(selectedAgency.id)
      toast.success('Agency deleted successfully')
      setOpenDeleteDialog(false)
      setSelectedAgency(null)
      loadAgencies()
    } catch (error: any) {
      console.error('Failed to delete agency:', error)
      toast.error(error.response?.data?.detail || 'Failed to delete agency')
    }
  }

  const handleOpenDeleteDialog = (agency: Agency) => {
    setSelectedAgency(agency)
    setOpenDeleteDialog(true)
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <BusinessIcon fontSize="large" />
            Agency Management
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Manage government agencies and organizations
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadAgencies}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
          >
            Add Agency
          </Button>
        </Box>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                size="small"
                label="Search agencies"
                placeholder="Search by name, code, or description"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Button
                variant={showInactive ? 'contained' : 'outlined'}
                onClick={() => setShowInactive(!showInactive)}
              >
                {showInactive ? 'Show Active Only' : 'Show All'}
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Agencies Table */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 5 }}>
          <CircularProgress />
        </Box>
      ) : agencies.length === 0 ? (
        <Alert severity="info">No agencies found. Create one to get started!</Alert>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell><strong>Name</strong></TableCell>
                <TableCell><strong>Code</strong></TableCell>
                <TableCell><strong>Contact Email</strong></TableCell>
                <TableCell align="center"><strong>Status</strong></TableCell>
                <TableCell align="center"><strong>Statistics</strong></TableCell>
                <TableCell align="right"><strong>Actions</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {agencies.map((agency) => {
                const stats = agencyStats[agency.id]
                const statsLoaded = stats !== undefined

                return (
                  <TableRow key={agency.id} hover>
                    <TableCell>
                      <Typography variant="subtitle2">{agency.name}</Typography>
                      {agency.description && (
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                          {agency.description}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      {agency.code && (
                        <Chip label={agency.code} size="small" color="primary" variant="outlined" />
                      )}
                    </TableCell>
                    <TableCell>{agency.contact_email || '-'}</TableCell>
                    <TableCell align="center">
                      <Chip
                        label={agency.active ? 'Active' : 'Inactive'}
                        color={agency.active ? 'success' : 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="center">
                      {statsLoaded ? (
                        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
                          <Tooltip title="Total Users">
                            <Chip
                              icon={<PeopleIcon />}
                              label={stats.total_users}
                              size="small"
                              variant="outlined"
                            />
                          </Tooltip>
                          <Tooltip title="Total Projects">
                            <Chip
                              icon={<ProjectIcon />}
                              label={stats.total_projects}
                              size="small"
                              variant="outlined"
                            />
                          </Tooltip>
                        </Box>
                      ) : (
                        <Button
                          size="small"
                          onClick={() => loadAgencyStats(agency.id)}
                          disabled={statsLoading[agency.id]}
                        >
                          {statsLoading[agency.id] ? <CircularProgress size={16} /> : 'Load Stats'}
                        </Button>
                      )}
                    </TableCell>
                    <TableCell align="right">
                      <IconButton
                        size="small"
                        color="primary"
                        onClick={() => handleOpenDialog(agency)}
                        title="Edit"
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleOpenDeleteDialog(agency)}
                        title="Delete"
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {selectedAgency ? 'Edit Agency' : 'Create New Agency'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              fullWidth
              required
              label="Agency Name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
            <TextField
              fullWidth
              label="Agency Code"
              placeholder="e.g., IMDA, GovTech"
              value={formData.code}
              onChange={(e) => setFormData({ ...formData, code: e.target.value })}
            />
            <TextField
              fullWidth
              multiline
              rows={3}
              label="Description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            />
            <TextField
              fullWidth
              type="email"
              label="Contact Email"
              value={formData.contact_email}
              onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
            />
            <Box>
              <Button
                variant={formData.active ? 'contained' : 'outlined'}
                color={formData.active ? 'success' : 'inherit'}
                onClick={() => setFormData({ ...formData, active: !formData.active })}
              >
                {formData.active ? 'Active' : 'Inactive'}
              </Button>
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={!formData.name.trim()}
          >
            {selectedAgency ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={openDeleteDialog} onClose={() => setOpenDeleteDialog(false)}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete <strong>{selectedAgency?.name}</strong>?
          </Typography>
          <Alert severity="warning" sx={{ mt: 2 }}>
            This action cannot be undone. The agency can only be deleted if it has no users or projects.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDeleteDialog(false)}>Cancel</Button>
          <Button variant="contained" color="error" onClick={handleDelete}>
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default AgenciesPage
