import React, { useState, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  LinearProgress,
  Alert,
  Chip,
  Stack,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemIcon
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  CheckCircle as CheckIcon,
  Cancel as CancelIcon,
  Description as FileIcon,
  Close as CloseIcon
} from '@mui/icons-material';

interface EvidenceUploadWidgetProps {
  evidenceId: number;
  uploadId: string;
  controlId: number;
  controlTitle: string;
  title: string;
  acceptedTypes?: string[];
  onUploadComplete: (evidence: any) => void;
  onCancel: () => void;
}

const EvidenceUploadWidget: React.FC<EvidenceUploadWidgetProps> = ({
  evidenceId,
  uploadId,
  controlId,
  controlTitle,
  title,
  acceptedTypes = ['document', 'screenshot'],
  onUploadComplete,
  onCancel
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const [success, setSuccess] = useState(false);

  // File type validation
  const acceptedFileTypes = {
    'application/pdf': ['.pdf'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    'image/png': ['.png'],
    'image/jpeg': ['.jpg', '.jpeg']
  };

  const maxFileSize = 10 * 1024 * 1024; // 10MB

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    setError(null);

    if (rejectedFiles.length > 0) {
      const rejection = rejectedFiles[0];
      if (rejection.errors.some((e: any) => e.code === 'file-too-large')) {
        setError('File is too large. Maximum size is 10MB.');
      } else {
        setError('Invalid file type. Accepted: PDF, DOCX, XLSX, PNG, JPG');
      }
      return;
    }

    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      setError(null);
    }
  }, []);

  const handleFileChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      onDrop([selectedFile]);
    }
  }, [onDrop]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(true);
  };

  const handleDragLeave = () => {
    setIsDragActive(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(false);
    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile) {
      onDrop([droppedFile]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('control_id', controlId.toString());
      formData.append('title', title);
      formData.append('evidence_id', evidenceId.toString());

      const token = localStorage.getItem('token');
      
      // Simulate progress for better UX
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      const response = await fetch('/api/evidence/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const evidence = await response.json();
      setSuccess(true);
      
      // Wait a moment to show success state
      setTimeout(() => {
        onUploadComplete(evidence);
      }, 1000);

    } catch (err: any) {
      setError(err.message || 'Failed to upload evidence');
      setUploadProgress(0);
    } finally {
      setUploading(false);
    }
  };

  const handleRemoveFile = () => {
    setFile(null);
    setError(null);
    setUploadProgress(0);
  };

  return (
    <Card sx={{ mb: 2, border: '2px solid', borderColor: success ? 'success.main' : 'primary.main' }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" gutterBottom>
              Upload Evidence
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {title}
            </Typography>
            <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
              <Chip
                label={`Control ${controlId}`}
                size="small"
                color="primary"
                variant="outlined"
              />
              <Chip
                label={controlTitle}
                size="small"
                color="default"
                variant="outlined"
              />
            </Stack>
          </Box>
          {!success && (
            <IconButton size="small" onClick={onCancel} disabled={uploading}>
              <CloseIcon />
            </IconButton>
          )}
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {success ? (
          <Alert severity="success" icon={<CheckIcon />}>
            Evidence uploaded successfully!
          </Alert>
        ) : file ? (
          <Box>
            <List dense>
              <ListItem
                secondaryAction={
                  !uploading && (
                    <IconButton edge="end" onClick={handleRemoveFile} size="small">
                      <CancelIcon />
                    </IconButton>
                  )
                }
              >
                <ListItemIcon>
                  <FileIcon color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary={file.name}
                  secondary={`${(file.size / 1024 / 1024).toFixed(2)} MB`}
                />
              </ListItem>
            </List>

            {uploading && (
              <Box sx={{ mt: 2 }}>
                <LinearProgress variant="determinate" value={uploadProgress} />
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block', textAlign: 'center' }}>
                  Uploading... {uploadProgress}%
                </Typography>
              </Box>
            )}

            {!uploading && (
              <Button
                variant="contained"
                color="primary"
                fullWidth
                onClick={handleUpload}
                sx={{ mt: 2 }}
                startIcon={<UploadIcon />}
              >
                Upload Evidence
              </Button>
            )}
          </Box>
        ) : (
          <Box
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => document.getElementById('evidence-file-input')?.click()}
            sx={{
              border: '2px dashed',
              borderColor: isDragActive ? 'primary.main' : 'grey.400',
              borderRadius: 2,
              p: 4,
              textAlign: 'center',
              cursor: 'pointer',
              bgcolor: isDragActive ? 'action.hover' : 'background.paper',
              transition: 'all 0.2s',
              '&:hover': {
                bgcolor: 'action.hover',
                borderColor: 'primary.main'
              }
            }}
          >
            <input
              id="evidence-file-input"
              type="file"
              hidden
              accept=".pdf,.docx,.xlsx,.png,.jpg,.jpeg"
              onChange={handleFileChange}
            />
            <UploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="body1" gutterBottom>
              {isDragActive ? 'Drop the file here' : 'Drag & drop file here, or click to select'}
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block">
              Accepted: PDF, DOCX, XLSX, PNG, JPG (max 10MB)
            </Typography>
          </Box>
        )}

        {acceptedTypes.length > 0 && !file && !success && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
              Recommended evidence types for this control:
            </Typography>
            <Stack direction="row" spacing={0.5} flexWrap="wrap">
              {acceptedTypes.map(type => (
                <Chip
                  key={type}
                  label={type}
                  size="small"
                  variant="outlined"
                  sx={{ mb: 0.5 }}
                />
              ))}
            </Stack>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default EvidenceUploadWidget;
