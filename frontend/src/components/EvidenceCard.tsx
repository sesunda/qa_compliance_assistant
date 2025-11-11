import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Chip,
  Stack,
  Box,
  Divider,
  LinearProgress
} from '@mui/material';
import {
  CheckCircle as ApprovedIcon,
  Cancel as RejectedIcon,
  HourglassEmpty as PendingIcon,
  RateReview as ReviewIcon,
  Description as DocumentIcon,
  Image as ImageIcon,
  Settings as ConfigIcon,
  ListAlt as LogIcon,
  Assessment as ReportIcon,
  FolderOpen as OtherIcon
} from '@mui/icons-material';

interface EvidenceCardProps {
  evidence: {
    id: number;
    title: string;
    description?: string;
    evidence_type: string;
    verification_status: string;
    control_id: number;
    original_filename?: string;
    uploaded_at?: string;
    analysis?: {
      overall_score: number;
      passed: boolean;
      validation_results: any[];
      recommendations: string[];
    };
    suggestions?: {
      control_id: number;
      control_title: string;
      relevance_score: number;
      reason: string;
    }[];
  };
  showAnalysis?: boolean;
}

const EvidenceCard: React.FC<EvidenceCardProps> = ({ evidence, showAnalysis = true }) => {
  // Status configuration
  const statusConfig = {
    pending: { label: 'Pending', icon: <PendingIcon />, color: 'default' as const },
    under_review: { label: 'Under Review', icon: <ReviewIcon />, color: 'warning' as const },
    approved: { label: 'Approved', icon: <ApprovedIcon />, color: 'success' as const },
    rejected: { label: 'Rejected', icon: <RejectedIcon />, color: 'error' as const }
  };

  // Evidence type icons
  const typeIcons: Record<string, JSX.Element> = {
    document: <DocumentIcon />,
    screenshot: <ImageIcon />,
    configuration: <ConfigIcon />,
    log: <LogIcon />,
    report: <ReportIcon />,
    other: <OtherIcon />
  };

  const status = statusConfig[evidence.verification_status as keyof typeof statusConfig] || statusConfig.pending;

  return (
    <Card sx={{ mb: 2, border: '1px solid', borderColor: 'divider' }}>
      <CardContent>
        {/* Header */}
        <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 2 }}>
          <Box sx={{ color: 'text.secondary' }}>
            {typeIcons[evidence.evidence_type] || typeIcons.other}
          </Box>
          <Typography variant="h6" sx={{ flex: 1 }}>
            {evidence.title}
          </Typography>
          <Chip
            icon={status.icon}
            label={status.label}
            color={status.color}
            size="small"
          />
        </Stack>

        {/* Description */}
        {evidence.description && (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {evidence.description}
          </Typography>
        )}

        {/* Metadata */}
        <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mb: showAnalysis && evidence.analysis ? 2 : 0 }}>
          <Chip
            label={`Control ${evidence.control_id}`}
            size="small"
            variant="outlined"
            color="primary"
          />
          <Chip
            label={evidence.evidence_type}
            size="small"
            variant="outlined"
          />
          {evidence.original_filename && (
            <Chip
              label={evidence.original_filename}
              size="small"
              variant="outlined"
            />
          )}
        </Stack>

        {/* Analysis Results */}
        {showAnalysis && evidence.analysis && (
          <>
            <Divider sx={{ my: 2 }} />
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                AI Analysis
              </Typography>
              
              {/* Score Bar */}
              <Box sx={{ mb: 2 }}>
                <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    Compliance Score
                  </Typography>
                  <Typography
                    variant="body2"
                    fontWeight="bold"
                    color={evidence.analysis.passed ? 'success.main' : 'warning.main'}
                  >
                    {evidence.analysis.overall_score}%
                  </Typography>
                </Stack>
                <LinearProgress
                  variant="determinate"
                  value={evidence.analysis.overall_score}
                  color={evidence.analysis.passed ? 'success' : 'warning'}
                  sx={{ height: 8, borderRadius: 1 }}
                />
              </Box>

              {/* Validation Results */}
              {evidence.analysis.validation_results && evidence.analysis.validation_results.length > 0 && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                    Validation Checks:
                  </Typography>
                  <Stack spacing={0.5}>
                    {evidence.analysis.validation_results.map((result: any, idx: number) => (
                      <Stack key={idx} direction="row" spacing={1} alignItems="center">
                        {result.passed ? (
                          <CheckCircle sx={{ fontSize: 16, color: 'success.main' }} />
                        ) : (
                          <Cancel sx={{ fontSize: 16, color: 'error.main' }} />
                        )}
                        <Typography variant="caption">
                          {result.criterion}
                          {result.coverage_percent && ` (${result.coverage_percent}%)`}
                        </Typography>
                      </Stack>
                    ))}
                  </Stack>
                </Box>
              )}

              {/* Recommendations */}
              {evidence.analysis.recommendations && evidence.analysis.recommendations.length > 0 && (
                <Box>
                  <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                    Recommendations:
                  </Typography>
                  <Stack spacing={0.5}>
                    {evidence.analysis.recommendations.map((rec: string, idx: number) => (
                      <Typography key={idx} variant="caption" sx={{ pl: 2 }}>
                        • {rec}
                      </Typography>
                    ))}
                  </Stack>
                </Box>
              )}
            </Box>
          </>
        )}

        {/* Related Controls Suggestions */}
        {showAnalysis && evidence.suggestions && evidence.suggestions.length > 0 && (
          <>
            <Divider sx={{ my: 2 }} />
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Related Controls (Graph RAG)
              </Typography>
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                This evidence may also apply to:
              </Typography>
              <Stack spacing={1}>
                {evidence.suggestions.slice(0, 3).map((suggestion) => (
                  <Box
                    key={suggestion.control_id}
                    sx={{
                      p: 1,
                      bgcolor: 'action.hover',
                      borderRadius: 1,
                      border: '1px solid',
                      borderColor: 'divider'
                    }}
                  >
                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                      <Box>
                        <Typography variant="caption" fontWeight="bold">
                          Control {suggestion.control_id}: {suggestion.control_title}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" display="block">
                          {suggestion.reason}
                        </Typography>
                      </Box>
                      <Chip
                        label={`${suggestion.relevance_score}%`}
                        size="small"
                        color={suggestion.relevance_score >= 70 ? 'success' : 'default'}
                      />
                    </Stack>
                  </Box>
                ))}
              </Stack>
            </Box>
          </>
        )}
      </CardContent>
    </Card>
  );
};

// Helper component imports
import { CheckCircle, Cancel } from '@mui/icons-material';

export default EvidenceCard;
