import React from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
} from '@mui/material'
import {
  Assessment,
  Download,
  Visibility,
  Share,
  Add,
  PictureAsPdf,
  TableChart,
} from '@mui/icons-material'

const ReportsPage: React.FC = () => {
  // Mock data for demonstration
  const reports = [
    {
      id: 1,
      name: 'Infrastructure Penetration Test Report',
      type: 'Security Assessment',
      project: 'Infrastructure PT',
      generatedDate: '2024-01-15',
      status: 'Completed',
      format: 'PDF',
    },
    {
      id: 2,
      name: 'Compliance Audit Summary',
      type: 'Compliance Report',
      project: 'Compliance Audit',
      generatedDate: '2024-01-14',
      status: 'In Progress',
      format: 'Excel',
    },
    {
      id: 3,
      name: 'Risk Assessment Matrix',
      type: 'Risk Analysis',
      project: 'Risk Assessment',
      generatedDate: '2024-01-13',
      status: 'Completed',
      format: 'PDF',
    },
  ]

  const reportTemplates = [
    {
      id: 1,
      name: 'Infrastructure Penetration Test',
      description: 'Comprehensive infrastructure security assessment report',
      type: 'Security Assessment',
    },
    {
      id: 2,
      name: 'VAPT Report',
      description: 'Vulnerability assessment and penetration testing report',
      type: 'Security Assessment',
    },
    {
      id: 3,
      name: 'Compliance Audit',
      description: 'Regulatory compliance audit findings and recommendations',
      type: 'Compliance Report',
    },
    {
      id: 4,
      name: 'Risk Assessment',
      description: 'Risk analysis and mitigation strategies',
      type: 'Risk Analysis',
    },
  ]

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'success'
      case 'in progress':
        return 'warning'
      case 'draft':
        return 'info'
      default:
        return 'default'
    }
  }

  const getFormatIcon = (format: string) => {
    switch (format.toLowerCase()) {
      case 'pdf':
        return <PictureAsPdf color="error" />
      case 'excel':
        return <TableChart color="success" />
      default:
        return <Assessment />
    }
  }

  const reportStats = {
    total: reports.length,
    completed: reports.filter(r => r.status === 'Completed').length,
    inProgress: reports.filter(r => r.status === 'In Progress').length,
    draft: reports.filter(r => r.status === 'Draft').length,
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Reports
          </Typography>
          <Typography variant="body1" color="textSecondary">
            Generate, manage, and share compliance and security assessment reports
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<Add />}
        >
          Generate Report
        </Button>
      </Box>

      {/* Report Statistics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Reports
              </Typography>
              <Typography variant="h4">{reportStats.total}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Completed
              </Typography>
              <Typography variant="h4" color="success.main">
                {reportStats.completed}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                In Progress
              </Typography>
              <Typography variant="h4" color="warning.main">
                {reportStats.inProgress}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Draft
              </Typography>
              <Typography variant="h4" color="info.main">
                {reportStats.draft}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Generated Reports */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Generated Reports
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Report Name</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Project</TableCell>
                      <TableCell>Generated</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {reports.map((report) => (
                      <TableRow key={report.id}>
                        <TableCell>
                          <Box display="flex" alignItems="center" gap={1}>
                            {getFormatIcon(report.format)}
                            <Typography variant="body2">
                              {report.name}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>{report.type}</TableCell>
                        <TableCell>{report.project}</TableCell>
                        <TableCell>
                          {new Date(report.generatedDate).toLocaleDateString()}
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={report.status}
                            color={getStatusColor(report.status) as any}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <IconButton size="small" title="View">
                            <Visibility fontSize="small" />
                          </IconButton>
                          <IconButton size="small" title="Download">
                            <Download fontSize="small" />
                          </IconButton>
                          <IconButton size="small" title="Share">
                            <Share fontSize="small" />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Report Templates */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Report Templates
              </Typography>
              <Box display="flex" flexDirection="column" gap={2}>
                {reportTemplates.map((template) => (
                  <Card
                    key={template.id}
                    variant="outlined"
                    sx={{
                      cursor: 'pointer',
                      '&:hover': { bgcolor: 'grey.50' },
                    }}
                  >
                    <CardContent sx={{ py: 2 }}>
                      <Typography variant="body2" fontWeight="bold">
                        {template.name}
                      </Typography>
                      <Typography variant="caption" color="textSecondary" display="block">
                        {template.description}
                      </Typography>
                      <Chip
                        label={template.type}
                        size="small"
                        variant="outlined"
                        sx={{ mt: 1 }}
                      />
                    </CardContent>
                  </Card>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

export default ReportsPage