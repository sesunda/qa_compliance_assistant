import React, { useState, useMemo } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
} from '@mui/material'
import {
  Security,
  CheckCircle,
  Warning,
  Error,
  Add,
  FilterList,
} from '@mui/icons-material'
import { useQuery } from 'react-query'
import { api } from '../services/api'
import { useAuth } from '../contexts/AuthContext'

const ControlsPage: React.FC = () => {
  const { user } = useAuth()
  const [selectedProject, setSelectedProject] = useState<string>('all')
  const [selectedDomain, setSelectedDomain] = useState<string>('all')

  // Fetch projects for filter dropdown
  const { data: projects } = useQuery(
    'projects',
    () => api.get('/projects/').then((res) => res.data),
    { refetchOnWindowFocus: false }
  )

  // Fetch controls with project filter
  const { data: controls, isLoading } = useQuery(
    ['controls', selectedProject],
    () => {
      const params = selectedProject !== 'all' ? { project_id: selectedProject } : {}
      return api.get('/controls/', { params }).then((res) => res.data)
    },
    { refetchOnWindowFocus: false }
  )

  // Ensure controls is an array
  const allControls = Array.isArray(controls) ? controls : []
  
  // Get available domains from current controls (project-specific)
  const availableDomains = useMemo(() => {
    const domains = new Set<string>()
    allControls.forEach((control: any) => {
      if (control.control_type) {
        // Extract domain prefix (e.g., "IM8-01" from "IM8-01-1")
        const match = control.control_type.match(/^(IM8-\d{2})/)
        if (match) {
          domains.add(match[1])
        }
      }
    })
    return Array.from(domains).sort()
  }, [allControls])

  // Filter by domain on frontend
  const controlsList = useMemo(() => {
    if (selectedDomain === 'all') return allControls
    return allControls.filter((c: any) => 
      c.control_type?.startsWith(selectedDomain)
    )
  }, [allControls, selectedDomain])

  // All IM8 Domains with labels
  const allIm8Domains = [
    { value: 'IM8-01', label: 'IM8-01: Information Security Governance' },
    { value: 'IM8-02', label: 'IM8-02: Network Security' },
    { value: 'IM8-03', label: 'IM8-03: Data Protection' },
    { value: 'IM8-04', label: 'IM8-04: Vulnerability & Patch Management' },
    { value: 'IM8-05', label: 'IM8-05: Secure Software Development' },
    { value: 'IM8-06', label: 'IM8-06: Identity & Access Management' },
    { value: 'IM8-07', label: 'IM8-07: Incident Response' },
    { value: 'IM8-08', label: 'IM8-08: Change & Configuration Management' },
    { value: 'IM8-09', label: 'IM8-09: Risk Assessment & Compliance' },
    { value: 'IM8-10', label: 'IM8-10: Digital Service Standards' },
  ]

  // Filter domains based on what's available in selected project
  const im8Domains = useMemo(() => {
    if (selectedProject === 'all') {
      // Show all domains when no project is selected
      return allIm8Domains
    }
    // Show only domains that exist in the current controls
    return allIm8Domains.filter(domain => availableDomains.includes(domain.value))
  }, [selectedProject, availableDomains])

  const handleProjectChange = (event: SelectChangeEvent<string>) => {
    setSelectedProject(event.target.value)
    // Reset domain filter when project changes
    setSelectedDomain('all')
  }

  const handleDomainChange = (event: SelectChangeEvent<string>) => {
    setSelectedDomain(event.target.value)
  }
  
  // Check if user can create/edit/delete controls (auditors and super_admin only)
  const canManageControls = user?.role?.name === 'auditor' || user?.role?.name === 'super_admin'

  const getImplementationStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'implemented':
        return 'success'
      case 'partially implemented':
        return 'warning'
      case 'not implemented':
        return 'error'
      default:
        return 'default'
    }
  }

  const getImplementationIcon = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'implemented':
        return <CheckCircle color="success" />
      case 'partially implemented':
        return <Warning color="warning" />
      case 'not implemented':
        return <Error color="error" />
      default:
        return <Security />
    }
  }

  const getImplementationProgress = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'implemented':
        return 100
      case 'partially implemented':
        return 50
      case 'not implemented':
        return 0
      default:
        return 0
    }
  }

  if (isLoading) {
    return <Typography>Loading controls...</Typography>
  }

  // Map status to implementation status for display
  const getImplementationStatusFromControl = (control: any) => {
    // For now, all active controls are considered "Implemented"
    // TODO: Add implementation_status field to controls table
    if (control.status === 'active') return 'Implemented'
    if (control.status === 'partial') return 'Partially Implemented'
    return 'Not Implemented'
  }

  const controlStats = {
    total: controlsList.length || 0,
    implemented: controlsList.filter((c: any) => c.status === 'active').length || 0,
    partial: controlsList.filter((c: any) => c.status === 'partial').length || 0,
    notImplemented: controlsList.filter((c: any) => c.status === 'inactive' || c.status === 'not_implemented').length || 0,
  }

  const overallProgress = controlStats.total > 0 
    ? ((controlStats.implemented * 100 + controlStats.partial * 50) / (controlStats.total * 100)) * 100
    : 0

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h5" gutterBottom>
            Security Controls
          </Typography>
          <Typography variant="body1" color="textSecondary">
            Manage and monitor your security control implementations
          </Typography>
        </Box>
        {canManageControls && (
          <Button variant="contained" startIcon={<Add />}>
            Map New Control
          </Button>
        )}
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" alignItems="center" gap={2} flexWrap="wrap">
            <FilterList color="action" />
            <FormControl size="small" sx={{ minWidth: 250 }}>
              <InputLabel>Filter by Project</InputLabel>
              <Select
                value={selectedProject}
                label="Filter by Project"
                onChange={handleProjectChange}
              >
                <MenuItem value="all">All Projects</MenuItem>
                {projects && Array.isArray(projects) && projects.map((project: any) => (
                  <MenuItem key={project.id} value={project.id.toString()}>
                    {project.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            
            <FormControl size="small" sx={{ minWidth: 300 }}>
              <InputLabel>Filter by IM8 Domain</InputLabel>
              <Select
                value={selectedDomain}
                label="Filter by IM8 Domain"
                onChange={handleDomainChange}
                disabled={im8Domains.length === 0}
              >
                <MenuItem value="all">
                  All Domains {selectedProject !== 'all' && `(${availableDomains.length})`}
                </MenuItem>
                {im8Domains.map((domain) => {
                  // Count controls in this domain
                  const controlCount = allControls.filter((c: any) => 
                    c.control_type?.startsWith(domain.value)
                  ).length
                  
                  return (
                    <MenuItem key={domain.value} value={domain.value}>
                      {domain.label} ({controlCount})
                    </MenuItem>
                  )
                })}
              </Select>
            </FormControl>

            {(selectedProject !== 'all' || selectedDomain !== 'all') && (
              <Button 
                size="small" 
                onClick={() => {
                  setSelectedProject('all')
                  setSelectedDomain('all')
                }}
              >
                Clear Filters
              </Button>
            )}
          </Box>
        </CardContent>
      </Card>

      {/* Control Statistics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Controls
              </Typography>
              <Typography variant="h4">{controlStats.total}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Implemented
              </Typography>
              <Typography variant="h4" color="success.main">
                {controlStats.implemented}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Partial
              </Typography>
              <Typography variant="h4" color="warning.main">
                {controlStats.partial}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Not Implemented
              </Typography>
              <Typography variant="h4" color="error.main">
                {controlStats.notImplemented}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Overall Progress */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">Implementation Progress</Typography>
            <Typography variant="h6" color="primary">
              {Math.round(overallProgress)}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={overallProgress}
            sx={{ height: 10, borderRadius: 1 }}
          />
        </CardContent>
      </Card>

      {/* Controls Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Control Details
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Control ID</TableCell>
                  <TableCell>Name</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Project</TableCell>
                  <TableCell>Implementation Status</TableCell>
                  <TableCell>Progress</TableCell>
                  <TableCell>Last Updated</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {controlsList.map((control: any) => {
                  const implementationStatus = getImplementationStatusFromControl(control)
                  const project = projects && Array.isArray(projects) 
                    ? projects.find((p: any) => p.id === control.project_id)
                    : null
                  
                  return (
                    <TableRow key={control.id}>
                      <TableCell>
                        <Typography variant="body2" fontWeight="bold">
                          {control.id}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box>
                          <Typography variant="body2">
                            {control.name}
                          </Typography>
                          <Typography variant="caption" color="textSecondary">
                            {control.description?.substring(0, 100)}{control.description?.length > 100 ? '...' : ''}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        {control.control_type && (
                          <Chip
                            label={control.control_type}
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </TableCell>
                      <TableCell>
                        {project ? (
                          <Typography variant="body2">
                            {project.name}
                          </Typography>
                        ) : (
                          <Typography variant="caption" color="textSecondary">
                            N/A
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={1}>
                          {getImplementationIcon(implementationStatus)}
                          <Chip
                            label={implementationStatus}
                            color={getImplementationStatusColor(implementationStatus) as any}
                            size="small"
                          />
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box width={80}>
                          <LinearProgress
                            variant="determinate"
                            value={getImplementationProgress(implementationStatus)}
                            color={getImplementationStatusColor(implementationStatus) as any}
                          />
                        </Box>
                      </TableCell>
                      <TableCell>
                        {control.updated_at 
                          ? new Date(control.updated_at).toLocaleDateString()
                          : 'N/A'
                        }
                      </TableCell>
                    </TableRow>
                  )
                })}
                {(!controls || controls.length === 0) && (
                  <TableRow>
                    <TableCell colSpan={7} align="center">
                      <Box py={4}>
                        <Security sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
                        <Typography variant="h6" color="textSecondary">
                          No controls found
                        </Typography>
                        <Typography variant="body2" color="textSecondary" paragraph>
                          Start by mapping controls to your projects
                        </Typography>
                      </Box>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  )
}

export default ControlsPage