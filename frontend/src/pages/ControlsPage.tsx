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
  const { data: controls, isLoading } = useQuery('controls', () =>
    api.get('/controls').then((res) => res.data)
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

  const controlStats = {
    total: controls?.length || 0,
    implemented: controls?.filter((c: any) => c.implementation_status === 'Implemented').length || 0,
    partial: controls?.filter((c: any) => c.implementation_status === 'Partially Implemented').length || 0,
    notImplemented: controls?.filter((c: any) => c.implementation_status === 'Not Implemented').length || 0,
  }

  const overallProgress = controlStats.total > 0 
    ? ((controlStats.implemented * 100 + controlStats.partial * 50) / (controlStats.total * 100)) * 100
    : 0

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
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
                  <TableCell>Title</TableCell>
                  <TableCell>Domain</TableCell>
                  <TableCell>Implementation Status</TableCell>
                  <TableCell>Progress</TableCell>
                  <TableCell>Last Updated</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {controls?.map((control: any) => (
                  <TableRow key={control.id}>
                    <TableCell>
                      <Typography variant="body2" fontWeight="bold">
                        {control.control_id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Box>
                        <Typography variant="body2">
                          {control.title}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          {control.description?.substring(0, 100)}...
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      {control.im8_domain && (
                        <Chip
                          label={control.im8_domain}
                          size="small"
                          variant="outlined"
                        />
                      )}
                    </TableCell>
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={1}>
                        {getImplementationIcon(control.implementation_status)}
                        <Chip
                          label={control.implementation_status || 'Not Set'}
                          color={getImplementationStatusColor(control.implementation_status) as any}
                          size="small"
                        />
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Box width={80}>
                        <LinearProgress
                          variant="determinate"
                          value={getImplementationProgress(control.implementation_status)}
                          color={getImplementationStatusColor(control.implementation_status) as any}
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
                ))}
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