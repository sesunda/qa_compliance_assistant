import React, { useMemo, useRef, useState } from 'react'
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
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  TextField,
  MenuItem,
  Stack,
  LinearProgress,
} from '@mui/material'
import {
  CloudUpload,
  Description,
  Download,
  Delete,
  Add,
  CheckCircle,
  HourglassEmpty,
} from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { useForm, Controller, Resolver } from 'react-hook-form'
import { yupResolver } from '@hookform/resolvers/yup'
import * as yup from 'yup'
import toast from 'react-hot-toast'
import { useAuth } from '../contexts/AuthContext'
import {
  fetchEvidence,
  uploadEvidence,
  deleteEvidence,
  downloadEvidence,
  EvidenceItem,
} from '../services/evidence'
import { fetchControls, ControlSummary } from '../services/controls'

type UploadFormValues = {
  control_id: number
  title: string
  description?: string | null
  evidence_type?: string | null
  file: File | null
}

const uploadSchema = yup.object({
  control_id: yup
    .number()
    .typeError('Select a control')
    .required('Control is required'),
  title: yup.string().trim().required('Title is required'),
  description: yup.string().nullable(),
  evidence_type: yup.string().nullable(),
  file: yup
    .mixed<File>()
    .nullable()
    .required('Please select a file')
    .test('file-exists', 'Please select a file', value => value instanceof File),
})

const formatFileSize = (bytes?: number | null) => {
  if (!bytes || bytes <= 0) {
    return '—'
  }

  const units = ['B', 'KB', 'MB', 'GB']
  const exponent = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
  const size = bytes / Math.pow(1024, exponent)
  return `${size.toFixed(size >= 10 || exponent === 0 ? 0 : 1)} ${units[exponent]}`
}

const formatDateTime = (value?: string | null) => {
  if (!value) {
    return '—'
  }
  return new Date(value).toLocaleString()
}

const EvidencePage: React.FC = () => {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const dropzoneInputRef = useRef<HTMLInputElement | null>(null)
  const dialogFileInputRef = useRef<HTMLInputElement | null>(null)
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false)
  const [downloadingId, setDownloadingId] = useState<number | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)

  // Simple permission checks
  const canManageEvidence = user?.permissions?.evidence?.includes('delete') || false
  const canUploadEvidence = user?.permissions?.evidence?.includes('create') || false

  const evidenceQuery = useQuery<EvidenceItem[]>(['evidence'], () => fetchEvidence())
  const controlsQuery = useQuery<ControlSummary[]>(['controls'], fetchControls)

  const controls = controlsQuery.data ?? []
  const controlMap = useMemo(() => {
    return new Map(controls.map(control => [control.id, control]))
  }, [controls])

  const resolver = useMemo(() => yupResolver(uploadSchema) as Resolver<UploadFormValues>, [])

  const {
    control,
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<UploadFormValues>({
    defaultValues: {
      control_id: 0,
      title: '',
      description: '',
      evidence_type: '',
      file: null,
    },
    resolver,
  })

  const selectedFile = watch('file')

  const uploadMutation = useMutation(uploadEvidence, {
    onSuccess: () => {
      toast.success('Evidence uploaded successfully')
      queryClient.invalidateQueries(['evidence'])
      setUploadDialogOpen(false)
      reset({
        control_id: controls[0]?.id ?? 0,
        title: '',
        description: '',
        evidence_type: '',
        file: null,
      })
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail ?? 'Failed to upload evidence'
      toast.error(message)
    },
  })

  const deleteMutation = useMutation(deleteEvidence, {
    onMutate: (id: number) => {
      setDeletingId(id)
    },
    onSuccess: () => {
      toast.success('Evidence deleted successfully')
      queryClient.invalidateQueries(['evidence'])
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail ?? 'Failed to delete evidence'
      toast.error(message)
    },
    onSettled: () => {
      setDeletingId(null)
    },
  })

  const downloadMutation = useMutation(downloadEvidence, {
    onMutate: (id: number) => {
      setDownloadingId(id)
    },
    onSuccess: ({ blob, filename }) => {
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    },
    onError: () => {
      toast.error('Failed to download evidence')
    },
    onSettled: () => {
      setDownloadingId(null)
    },
  })

  const evidenceItems = evidenceQuery.data ?? []

  const evidenceStats = useMemo(() => ({
    total: evidenceItems.length,
    withFiles: evidenceItems.filter(item => Boolean(item.file_path)).length,
    verified: evidenceItems.filter(item => item.verified).length,
    pending: evidenceItems.filter(item => !item.verified).length,
  }), [evidenceItems])

  const handleOpenUpload = (prefilledFile?: File) => {
    if (!canUploadEvidence) {
      toast.error('You do not have permission to upload evidence')
      return
    }

    if (controlsQuery.isLoading) {
      toast.error('Controls are still loading. Please wait a moment...')
      return
    }

    if (controlsQuery.isError || !controls.length) {
      toast.error('No controls available. Please create a control first.')
      return
    }

    reset({
      control_id: controls[0].id,
      title: prefilledFile?.name ?? '',
      description: '',
      evidence_type: '',
      file: prefilledFile ?? null,
    })
    setUploadDialogOpen(true)
  }

  const handleFileInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      handleOpenUpload(file)
    }
    // Reset the input so the same file can be re-selected
    event.target.value = ''
  }

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
  }

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    const file = event.dataTransfer.files?.[0]
    if (file) {
      handleOpenUpload(file)
    }
  }

  const onSubmit = async (values: UploadFormValues) => {
    if (!values.file) {
      toast.error('Please select a file to upload')
      return
    }

    try {
      await uploadMutation.mutateAsync({
        control_id: values.control_id,
        title: values.title.trim(),
        description: values.description?.trim() || undefined,
        evidence_type: values.evidence_type?.trim() || undefined,
        file: values.file,
      })
    } catch (error) {
      // handled by mutation onError
    }
  }

  const handleDeleteEvidence = (id: number, title: string) => {
    if (!canManageEvidence) {
      toast.error('You do not have permission to delete evidence')
      return
    }

    const confirmed = window.confirm(`Delete evidence "${title}"? This action cannot be undone.`)
    if (!confirmed) {
      return
    }

    deleteMutation.mutate(id)
  }

  const handleDownloadEvidence = (id: number) => {
    downloadMutation.mutate(id)
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Evidence Management
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Upload, manage, and track compliance evidence and documentation
          </Typography>
        </Box>
        {canUploadEvidence && (
          <Button
            variant="contained"
            startIcon={<CloudUpload />}
            onClick={() => handleOpenUpload()}
            disabled={controlsQuery.isLoading}
          >
            Upload Evidence
          </Button>
        )}
      </Box>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Evidence
              </Typography>
              <Typography variant="h4">
                {evidenceQuery.isLoading ? <CircularProgress size={24} /> : evidenceStats.total}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                With Files
              </Typography>
              <Typography variant="h4" color="primary.main">
                {evidenceQuery.isLoading ? <CircularProgress size={24} /> : evidenceStats.withFiles}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Verified
              </Typography>
              <Typography variant="h4" color="success.main">
                {evidenceQuery.isLoading ? <CircularProgress size={24} /> : evidenceStats.verified}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Pending Review
              </Typography>
              <Typography variant="h4" color="warning.main">
                {evidenceQuery.isLoading ? <CircularProgress size={24} /> : evidenceStats.pending}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {canUploadEvidence && (
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
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              onClick={() => dropzoneInputRef.current?.click()}
            >
              <CloudUpload sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Drag and drop files here
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                or click to browse files to upload as evidence
              </Typography>
              <Button variant="outlined" startIcon={<Add />}>Select File</Button>
              <input
                ref={dropzoneInputRef}
                type="file"
                hidden
                onChange={handleFileInputChange}
              />
            </Box>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent>
          <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">Evidence Repository</Typography>
            {evidenceQuery.isFetching && <CircularProgress size={20} />}
          </Stack>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Title</TableCell>
                  <TableCell>Control</TableCell>
                  <TableCell>Evidence Type</TableCell>
                  <TableCell>Uploaded</TableCell>
                  <TableCell>Size</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {evidenceQuery.isLoading && (
                  <TableRow>
                    <TableCell colSpan={7} align="center">
                      <Box py={4} display="flex" justifyContent="center">
                        <CircularProgress size={32} />
                      </Box>
                    </TableCell>
                  </TableRow>
                )}

                {evidenceQuery.isError && !evidenceQuery.isLoading && (
                  <TableRow>
                    <TableCell colSpan={7} align="center">
                      <Box py={4}>
                        <Typography color="error">Unable to load evidence records</Typography>
                      </Box>
                    </TableCell>
                  </TableRow>
                )}

                {!evidenceQuery.isLoading && evidenceItems.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} align="center">
                      <Box py={4}>
                        <CloudUpload sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
                        <Typography variant="h6" color="text.secondary">
                          No evidence uploaded yet
                        </Typography>
                      </Box>
                    </TableCell>
                  </TableRow>
                )}

                {evidenceItems.map(item => {
                  const control = controlMap.get(item.control_id)
                  const controlLabel = control ? `${control.name}` : `Control #${item.control_id}`
                  const uploadedAt = item.uploaded_at || item.created_at
                  const hasFile = Boolean(item.file_path)

                  return (
                    <TableRow key={item.id} hover>
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={1}>
                          <Description color={hasFile ? 'primary' : 'disabled'} />
                          <Box>
                            <Typography variant="body2" fontWeight="bold">
                              {item.title || item.original_filename || 'Untitled Evidence'}
                            </Typography>
                            {item.original_filename && (
                              <Typography variant="caption" color="text.secondary">
                                {item.original_filename}
                              </Typography>
                            )}
                          </Box>
                        </Box>
                      </TableCell>
                      <TableCell>{controlLabel}</TableCell>
                      <TableCell>{item.evidence_type || '—'}</TableCell>
                      <TableCell>{formatDateTime(uploadedAt)}</TableCell>
                      <TableCell>{formatFileSize(item.file_size)}</TableCell>
                      <TableCell>
                        <Chip
                          label={item.verified ? 'Verified' : 'Pending Review'}
                          color={item.verified ? 'success' : 'warning'}
                          size="small"
                          icon={item.verified ? <CheckCircle /> : <HourglassEmpty />}
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Stack direction="row" spacing={1} justifyContent="flex-end">
                          <IconButton
                            size="small"
                            title={hasFile ? 'Download evidence' : 'No file attached'}
                            onClick={() => hasFile && handleDownloadEvidence(item.id)}
                            disabled={!hasFile || downloadingId === item.id}
                          >
                            {downloadingId === item.id ? (
                              <CircularProgress size={18} />
                            ) : (
                              <Download fontSize="small" />
                            )}
                          </IconButton>
                          {canManageEvidence && (
                            <IconButton
                              size="small"
                              title="Delete evidence"
                              onClick={() => handleDeleteEvidence(item.id, item.title)}
                              disabled={deletingId === item.id}
                            >
                              {deletingId === item.id ? (
                                <CircularProgress size={18} />
                              ) : (
                                <Delete fontSize="small" />
                              )}
                            </IconButton>
                          )}
                        </Stack>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      <Dialog open={uploadDialogOpen} onClose={() => setUploadDialogOpen(false)} maxWidth="sm" fullWidth>
        <form onSubmit={handleSubmit(onSubmit as any)} noValidate>
          <DialogTitle>Upload Evidence</DialogTitle>
          <DialogContent dividers>
            <Stack spacing={2} sx={{ mt: 1 }}>
              <Controller
                name="control_id"
                control={control}
                render={({ field }) => (
                  <TextField
                    select
                    label="Control"
                    fullWidth
                    value={field.value || ''}
                    onChange={event => field.onChange(Number(event.target.value))}
                    error={Boolean(errors.control_id)}
                    helperText={errors.control_id?.message}
                  >
                    {controls.map(ctrl => (
                      <MenuItem key={ctrl.id} value={ctrl.id}>
                        {ctrl.name}
                      </MenuItem>
                    ))}
                  </TextField>
                )}
              />

              <TextField
                label="Title"
                fullWidth
                {...register('title')}
                error={Boolean(errors.title)}
                helperText={errors.title?.message}
              />

              <TextField
                label="Evidence Type"
                fullWidth
                {...register('evidence_type')}
                error={Boolean(errors.evidence_type)}
                helperText={errors.evidence_type?.message}
              />

              <TextField
                label="Description"
                fullWidth
                multiline
                minRows={3}
                {...register('description')}
                error={Boolean(errors.description)}
                helperText={errors.description?.message}
              />

              <Controller
                name="file"
                control={control}
                render={({ field }) => (
                  <Box>
                    <Button
                      variant="outlined"
                      startIcon={<CloudUpload />}
                      onClick={() => dialogFileInputRef.current?.click()}
                    >
                      {field.value ? 'Change File' : 'Select File'}
                    </Button>
                    <input
                      ref={dialogFileInputRef}
                      type="file"
                      hidden
                      onChange={(event) => {
                        const file = event.target.files?.[0] ?? null
                        field.onChange(file)
                        if (file) {
                          // Pre-fill the title if it is empty
                          const currentTitle = watch('title')
                          if (!currentTitle) {
                            setValue('title', file.name, { shouldValidate: true })
                          }
                        }
                        event.target.value = ''
                      }}
                    />
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                      {selectedFile ? selectedFile.name : 'No file selected yet'}
                    </Typography>
                    {errors.file && (
                      <Typography variant="caption" color="error">
                        {errors.file.message}
                      </Typography>
                    )}
                  </Box>
                )}
              />
            </Stack>
          </DialogContent>
          {(isSubmitting || uploadMutation.isLoading) && <LinearProgress />}
          <DialogActions>
            <Button onClick={() => setUploadDialogOpen(false)} color="secondary" disabled={isSubmitting || uploadMutation.isLoading}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="contained"
              disabled={isSubmitting || uploadMutation.isLoading}
            >
              {(isSubmitting || uploadMutation.isLoading) && (
                <CircularProgress size={20} sx={{ mr: 1, color: 'inherit' }} />
              )}
              Upload
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Box>
  )
}

export default EvidencePage