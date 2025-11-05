import React from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Paper,
  LinearProgress,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
} from '@mui/material';
import {
  Security,
  Assessment,
  TrendingUp,
  TrendingDown,
  AccountBalance,
  Groups,
  Warning,
  PictureAsPdf,
  Insights,
} from '@mui/icons-material';

const AgencySeniorManagementDashboard: React.FC = () => {
  const executiveMetrics = {
    overallRiskScore: 7.2, // Out of 10 (lower is better)
    compliancePosture: 91,
    budgetUtilization: 78,
    incidentCount: 3,
    auditReadiness: 95,
    teamProductivity: 88,
  };

  const complianceFrameworks = [
    { framework: 'FISMA', score: 92, status: 'Compliant', lastAssessment: '2025-09-15' },
    { framework: 'NIST CSF', score: 89, status: 'Mostly Compliant', lastAssessment: '2025-08-20' },
    { framework: 'SOC 2', score: 94, status: 'Compliant', lastAssessment: '2025-10-10' },
    { framework: 'ISO 27001', score: 87, status: 'In Progress', lastAssessment: '2025-07-30' },
  ];

  const riskAreas = [
    { area: 'Access Management', risk: 'Medium', trend: 'improving', impact: 'Medium' },
    { area: 'Data Encryption', risk: 'Low', trend: 'stable', impact: 'High' },
    { area: 'Incident Response', risk: 'High', trend: 'worsening', impact: 'High' },
    { area: 'Vendor Management', risk: 'Medium', trend: 'improving', impact: 'Medium' },
  ];

  const businessImpact = {
    potentialCostAvoidance: '$2.4M',
    productivityGains: '15%',
    riskReduction: '23%',
    auditSavings: '$180K',
  };

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" gutterBottom>
          Executive Security Dashboard
        </Typography>
        <Box display="flex" gap={2}>
          <Button variant="contained" color="primary" startIcon={<PictureAsPdf />}>
            Executive Report
          </Button>
          <Button variant="outlined" startIcon={<Insights />}>
            Risk Analysis
          </Button>
        </Box>
      </Box>
      
      <Grid container spacing={3}>
        {/* Executive KPIs */}
        <Grid item xs={12} md={6} lg={2}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Warning color="warning" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Risk Score
                  </Typography>
                  <Typography variant="h4">
                    {executiveMetrics.overallRiskScore}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    / 10
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6} lg={2}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Security color="success" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Compliance
                  </Typography>
                  <Typography variant="h4">
                    {executiveMetrics.compliancePosture}%
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6} lg={2}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <AccountBalance color="info" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Budget Used
                  </Typography>
                  <Typography variant="h4">
                    {executiveMetrics.budgetUtilization}%
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6} lg={2}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Warning color="error" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Incidents
                  </Typography>
                  <Typography variant="h4">
                    {executiveMetrics.incidentCount}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    This Month
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6} lg={2}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Assessment color="primary" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Audit Ready
                  </Typography>
                  <Typography variant="h4">
                    {executiveMetrics.auditReadiness}%
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6} lg={2}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Groups color="secondary" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Team Efficiency
                  </Typography>
                  <Typography variant="h4">
                    {executiveMetrics.teamProductivity}%
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Business Impact Metrics */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Business Impact & ROI
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} md={3}>
                <Box textAlign="center">
                  <Typography variant="h4" color="success.main">
                    {businessImpact.potentialCostAvoidance}
                  </Typography>
                  <Typography color="textSecondary">
                    Potential Cost Avoidance
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={3}>
                <Box textAlign="center">
                  <Typography variant="h4" color="primary.main">
                    {businessImpact.productivityGains}
                  </Typography>
                  <Typography color="textSecondary">
                    Productivity Improvement
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={3}>
                <Box textAlign="center">
                  <Typography variant="h4" color="warning.main">
                    {businessImpact.riskReduction}
                  </Typography>
                  <Typography color="textSecondary">
                    Risk Reduction
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={3}>
                <Box textAlign="center">
                  <Typography variant="h4" color="info.main">
                    {businessImpact.auditSavings}
                  </Typography>
                  <Typography color="textSecondary">
                    Audit Cost Savings
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* Compliance Framework Status */}
        <Grid item xs={12} md={7}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Compliance Framework Status
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Framework</TableCell>
                    <TableCell>Score</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Last Assessment</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {complianceFrameworks.map((framework, index) => (
                    <TableRow key={index}>
                      <TableCell>{framework.framework}</TableCell>
                      <TableCell>
                        <Box display="flex" alignItems="center">
                          <LinearProgress
                            variant="determinate"
                            value={framework.score}
                            sx={{ width: 100, mr: 2 }}
                          />
                          <Typography variant="body2">
                            {framework.score}%
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={framework.status}
                          color={
                            framework.status === 'Compliant' ? 'success' :
                            framework.status === 'Mostly Compliant' ? 'warning' : 'default'
                          }
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{framework.lastAssessment}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>

        {/* Risk Areas */}
        <Grid item xs={12} md={5}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Key Risk Areas
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Risk Area</TableCell>
                    <TableCell>Level</TableCell>
                    <TableCell>Trend</TableCell>
                    <TableCell>Impact</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {riskAreas.map((risk, index) => (
                    <TableRow key={index}>
                      <TableCell>{risk.area}</TableCell>
                      <TableCell>
                        <Chip
                          label={risk.risk}
                          color={
                            risk.risk === 'High' ? 'error' :
                            risk.risk === 'Medium' ? 'warning' : 'success'
                          }
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Box display="flex" alignItems="center">
                          {risk.trend === 'improving' && <TrendingUp color="success" />}
                          {risk.trend === 'worsening' && <TrendingDown color="error" />}
                          {risk.trend === 'stable' && <Typography>→</Typography>}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={risk.impact}
                          variant="outlined"
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>

        {/* Security Posture */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Overall Security Posture
              </Typography>
              <Box display="flex" alignItems="center" mb={2}>
                <Typography variant="h3" color="primary">
                  {executiveMetrics.compliancePosture}%
                </Typography>
                <Box ml={3}>
                  <Typography variant="h6" color="success.main">
                    ↑ 3.2% from last quarter
                  </Typography>
                  <Typography color="textSecondary">
                    Exceeding industry benchmarks by 12%
                  </Typography>
                </Box>
              </Box>
              <LinearProgress
                variant="determinate"
                value={executiveMetrics.compliancePosture}
                sx={{ height: 12, borderRadius: 6 }}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default AgencySeniorManagementDashboard;