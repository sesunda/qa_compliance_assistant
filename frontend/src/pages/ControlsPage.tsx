import React from 'react'
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
} from '@mui/material'
import {
  Security,
  CheckCircle,
  Warning,
  Error,
  Add,
} from '@mui/icons-material'
import { useQuery } from 'react-query'
import { api } from '../services/api'

const ControlsPage: React.FC = () => {
  const { data: controls, isLoading } = useQuery(
    'controls',
    () => api.get('/controls/').then((res) => res.data),
    {
      refetchOnMount: true,
      refetchOnWindowFocus: false,
      staleTime: 30000, // 30 seconds
    }
  )

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
    total: controls?.length || 0,
    implemented: controls?.filter((c: any) => c.status === 'active').length || 0,
    partial: controls?.filter((c: any) => c.status === 'partial').length || 0,
    notImplemented: controls?.filter((c: any) => c.status === 'inactive' || c.status === 'not_implemented').length || 0,
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
        <Button variant="contained" startIcon={<Add />}>
          Map New Control
        </Button>
      </Box>

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
                  <TableCell>Implementation Status</TableCell>
                  <TableCell>Progress</TableCell>
                  <TableCell>Last Updated</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {controls?.map((control: any) => {
                  const implementationStatus = getImplementationStatusFromControl(control)
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
                    <TableCell colSpan={6} align="center">
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