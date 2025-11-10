import React, { useState } from 'react'
import {
  Box,
  Typography,
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
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Grid,
  Alert,
  Snackbar,
} from '@mui/material'
import {
  Add,
  Edit,
  Delete,
  Visibility,
  Assignment,
} from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { api } from '../services/api'
import { useAuth } from '../contexts/AuthContext'

const ProjectsPage: React.FC = () => {
  const { user } = useAuth()
  const [open, setOpen] = useState(false)
  const [selectedProject, setSelectedProject] = useState<any>(null)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    project_type: '',
    status: 'Pending',
    start_date: '',
    agency_id: 1, // Default to first agency
  })
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' })

  const queryClient = useQueryClient()
  
  // Check if user can create/edit/delete projects (auditors and super_admin only)
  const canManageProjects = user?.role === 'auditor' || user?.role === 'super_admin'

  const { data: projects, isLoading } = useQuery('projects', () =>
    api.get('/projects').then((res) => res.data)
  )

  const { data: agencies } = useQuery('agencies', () =>
    api.get('/agencies').then((res) => res.data)
  )

  // Ensure projects and agencies are arrays
  const projectsList = Array.isArray(projects) ? projects : []
  const agenciesList = Array.isArray(agencies) ? agencies : []

  const createProjectMutation = useMutation(
    (projectData: any) => api.post('/projects', projectData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('projects')
        setSnackbar({ open: true, message: 'Project created successfully!', severity: 'success' })
        handleClose()
      },
      onError: () => {
        setSnackbar({ open: true, message: 'Failed to create project', severity: 'error' })
      },
    }
  )

  const updateProjectMutation = useMutation(
    ({ id, data }: { id: number; data: any }) => api.put(`/projects/${id}`, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('projects')
        setSnackbar({ open: true, message: 'Project updated successfully!', severity: 'success' })
        handleClose()
      },
      onError: () => {
        setSnackbar({ open: true, message: 'Failed to update project', severity: 'error' })
      },
    }
  )

  const deleteProjectMutation = useMutation(
    (id: number) => api.delete(`/projects/${id}`),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('projects')
        setSnackbar({ open: true, message: 'Project deleted successfully!', severity: 'success' })
      },
      onError: () => {
        setSnackbar({ open: true, message: 'Failed to delete project', severity: 'error' })
      },
    }
  )

  const projectTypes = [
    'Infrastructure Penetration Test',
    'Web Application Security Test',
    'Vulnerability Assessment',
    'Compliance Audit',
    'Risk Assessment',
  ]

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
        return 'success'
      case 'pending':
        return 'warning'
      case 'completed':
        return 'primary'
      case 'on hold':
        return 'default'
      default:
        return 'default'
    }
  }

  const handleCreateProject = () => {
    setSelectedProject(null)
    setFormData({
      name: '',
      description: '',
      project_type: '',
      status: 'Pending',
      start_date: '',
      agency_id: 1,
    })
    setOpen(true)
  }

  const handleEditProject = (project: any) => {
    setSelectedProject(project)
    setFormData({
      name: project.name || '',
      description: project.description || '',
      project_type: project.project_type || '',
      status: project.status || 'Pending',
      start_date: project.start_date ? project.start_date.split('T')[0] : '',
      agency_id: project.agency_id || 1,
    })
    setOpen(true)
  }

  const handleClose = () => {
    setOpen(false)
    setSelectedProject(null)
    setFormData({
      name: '',
      description: '',
      project_type: '',
      status: 'Pending',
      start_date: '',
      agency_id: 1,
    })
  }

  const handleSubmit = () => {
    if (selectedProject) {
      updateProjectMutation.mutate({ id: selectedProject.id, data: formData })
    } else {
      createProjectMutation.mutate(formData)
    }
  }

  const handleDelete = (projectId: number) => {
    if (window.confirm('Are you sure you want to delete this project?')) {
      deleteProjectMutation.mutate(projectId)
    }
  }

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  if (isLoading) {
    return <Typography>Loading projects...</Typography>
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h5" gutterBottom>
            Projects
          </Typography>
          <Typography variant="body1" color="textSecondary">
            Manage your compliance and security assessment projects
          </Typography>
        </Box>
        {canManageProjects && (
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={handleCreateProject}
          >
            New Project
          </Button>
        )}
      </Box>

      <Card>
        <CardContent>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Project Name</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Agency</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {projectsList.map((project: any) => (
                  <TableRow key={project.id}>
                    <TableCell>
                      <Box>
                        <Typography variant="body2" fontWeight="bold">
                          {project.name}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          {project.description}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>{project.project_type}</TableCell>
                    <TableCell>{project.agency?.name || 'N/A'}</TableCell>
                    <TableCell>
                      <Chip
                        label={project.status}
                        color={getStatusColor(project.status) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {new Date(project.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      <IconButton size="small" title="View">
                        <Visibility fontSize="small" />
                      </IconButton>
                      {canManageProjects && (
                        <>
                          <IconButton
                            size="small"
                            title="Edit"
                            onClick={() => handleEditProject(project)}
                          >
                            <Edit fontSize="small" />
                          </IconButton>
                          <IconButton size="small" title="Delete" onClick={() => handleDelete(project.id)}>
                            <Delete fontSize="small" />
                          </IconButton>
                        </>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
                {(!projects || projects.length === 0) && (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      <Box py={4}>
                        <Assignment sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
                        <Typography variant="h6" color="textSecondary">
                          No projects found
                        </Typography>
                        <Typography variant="body2" color="textSecondary" paragraph>
                          Create your first project to get started with compliance management
                        </Typography>
                        {canManageProjects && (
                          <Button
                            variant="contained"
                            startIcon={<Add />}
                            onClick={handleCreateProject}
                          >
                            Create Project
                          </Button>
                        )}
                      </Box>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Create/Edit Project Dialog */}
      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>
          {selectedProject ? 'Edit Project' : 'Create New Project'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Project Name"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                multiline
                rows={3}
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                select
                label="Project Type"
                value={formData.project_type}
                onChange={(e) => handleInputChange('project_type', e.target.value)}
              >
                {projectTypes.map((type) => (
                  <MenuItem key={type} value={type}>
                    {type}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                select
                label="Status"
                value={formData.status}
                onChange={(e) => handleInputChange('status', e.target.value)}
              >
                <MenuItem value="Pending">Pending</MenuItem>
                <MenuItem value="Active">Active</MenuItem>
                <MenuItem value="On Hold">On Hold</MenuItem>
                <MenuItem value="Completed">Completed</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                select
                label="Agency"
                value={formData.agency_id}
                onChange={(e) => handleInputChange('agency_id', parseInt(e.target.value))}
              >
                {agenciesList.map((agency: any) => (
                  <MenuItem key={agency.id} value={agency.id}>
                    {agency.name}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Start Date"
                type="date"
                InputLabelProps={{ shrink: true }}
                value={formData.start_date}
                onChange={(e) => handleInputChange('start_date', e.target.value)}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={handleSubmit}
            disabled={createProjectMutation.isLoading || updateProjectMutation.isLoading}
          >
            {selectedProject ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
      >
        <Alert
          onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  )
}

export default ProjectsPage