import React from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Grid,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
} from '@mui/material'
import {
  CloudUpload,
  Description,
  Download,
  Visibility,
  Delete,
  Add,
} from '@mui/icons-material'

const EvidencePage: React.FC = () => {
  // Mock data for demonstration
  const evidenceItems = [
    {
      id: 1,
      filename: 'vulnerability_scan_report.pdf',
      type: 'Vulnerability Assessment',
      project: 'Infrastructure PT',
      uploadDate: '2024-01-15',
      size: '2.3 MB',
      status: 'Approved',
    },
    {
      id: 2,
      filename: 'access_control_policy.docx',
      type: 'Policy Document',
      project: 'Compliance Audit',
      uploadDate: '2024-01-14',
      size: '1.1 MB',
      status: 'Under Review',
    },
    {
      id: 3,
      filename: 'security_controls_implementation.xlsx',
      type: 'Implementation Guide',
      project: 'Risk Assessment',
      uploadDate: '2024-01-13',
      size: '856 KB',
      status: 'Approved',
    },
  ]

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'approved':
        return 'success'
      case 'under review':
        return 'warning'
      case 'rejected':
        return 'error'
      default:
        return 'default'
    }
  }

  const evidenceStats = {
    total: evidenceItems.length,
    approved: evidenceItems.filter(item => item.status === 'Approved').length,
    pending: evidenceItems.filter(item => item.status === 'Under Review').length,
    rejected: evidenceItems.filter(item => item.status === 'Rejected').length,
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Evidence Management
          </Typography>
          <Typography variant="body1" color="textSecondary">
            Upload, manage, and track compliance evidence and documentation
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<CloudUpload />}
        >
          Upload Evidence
        </Button>
      </Box>

      {/* Evidence Statistics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Evidence
              </Typography>
              <Typography variant="h4">{evidenceStats.total}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Approved
              </Typography>
              <Typography variant="h4" color="success.main">
                {evidenceStats.approved}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Under Review
              </Typography>
              <Typography variant="h4" color="warning.main">
                {evidenceStats.pending}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Rejected
              </Typography>
              <Typography variant="h4" color="error.main">
                {evidenceStats.rejected}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Upload Area */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box
            sx={{
              border: '2px dashed',
              borderColor: 'grey.300',
              borderRadius: 2,
              p: 4,
              textAlign: 'center',
              cursor: 'pointer',
              '&:hover': {
                borderColor: 'primary.main',
                bgcolor: 'grey.50',
              },
            }}
          >
            <CloudUpload sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              Drag and drop files here
            </Typography>
            <Typography variant="body2" color="textSecondary" paragraph>
              or click to browse files
            </Typography>
            <Button variant="outlined" startIcon={<Add />}>
              Select Files
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Evidence Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Evidence Repository
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Filename</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Project</TableCell>
                  <TableCell>Upload Date</TableCell>
                  <TableCell>Size</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {evidenceItems.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={1}>
                        <Description color="primary" />
                        <Typography variant="body2">
                          {item.filename}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>{item.type}</TableCell>
                    <TableCell>{item.project}</TableCell>
                    <TableCell>
                      {new Date(item.uploadDate).toLocaleDateString()}
                    </TableCell>
                    <TableCell>{item.size}</TableCell>
                    <TableCell>
                      <Chip
                        label={item.status}
                        color={getStatusColor(item.status) as any}
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
                      <IconButton size="small" title="Delete">
                        <Delete fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  )
}

export default EvidencePage