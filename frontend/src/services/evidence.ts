import { api } from './api'

export interface EvidenceItem {
  id: number
  control_id: number
  agency_id: number
  title: string
  description?: string | null
  evidence_type?: string | null
  verified: boolean
  file_path?: string | null
  original_filename?: string | null
  mime_type?: string | null
  file_size?: number | null
  checksum?: string | null
  storage_backend?: string | null
  uploaded_by?: number | null
  uploaded_at?: string | null
  verification_status: string  // 'pending', 'under_review', 'approved', 'rejected'
  submitted_by?: number | null
  reviewed_by?: number | null
  reviewed_at?: string | null
  review_comments?: string | null
  created_at: string
  updated_at: string
}

export interface EvidenceFilters {
  control_id?: number
  skip?: number
  limit?: number
}

export interface UploadEvidencePayload {
  control_id: number
  file: File
  title?: string
  description?: string
  evidence_type?: string
}

export interface UpdateEvidencePayload {
  title?: string | null
  description?: string | null
  evidence_type?: string | null
  verified?: boolean
}

export const fetchEvidence = async (filters: EvidenceFilters = {}): Promise<EvidenceItem[]> => {
  const response = await api.get<EvidenceItem[]>('/evidence/', { params: filters })
  return response.data
}

export const uploadEvidence = async (payload: UploadEvidencePayload): Promise<EvidenceItem> => {
  const formData = new FormData()
  formData.append('control_id', String(payload.control_id))
  if (payload.title) {
    formData.append('title', payload.title)
  }
  if (payload.description) {
    formData.append('description', payload.description)
  }
  if (payload.evidence_type) {
    formData.append('evidence_type', payload.evidence_type)
  }
  formData.append('file', payload.file)

  const response = await api.post<EvidenceItem>('/evidence/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

  return response.data
}

export const deleteEvidence = async (evidenceId: number): Promise<void> => {
  await api.delete(`/evidence/${evidenceId}`)
}

export const updateEvidence = async (
  evidenceId: number,
  payload: UpdateEvidencePayload
): Promise<EvidenceItem> => {
  const response = await api.put<EvidenceItem>(`/evidence/${evidenceId}`, payload)
  return response.data
}

export const downloadEvidence = async (
  evidenceId: number
): Promise<{ blob: Blob; filename: string }> => {
  const response = await api.get<Blob>(`/evidence/${evidenceId}/download`, {
    responseType: 'blob',
  })

  const disposition = response.headers['content-disposition']
  let filename = `evidence-${evidenceId}`
  if (disposition) {
    const match = disposition.match(/filename="?([^";]+)"?/)
    if (match?.[1]) {
      filename = decodeURIComponent(match[1])
    }
  }

  return { blob: response.data, filename }
}

// Maker-Checker workflow functions
export const submitEvidenceForReview = async (
  evidenceId: number,
  comments?: string
): Promise<EvidenceItem> => {
  const response = await api.post<EvidenceItem>(
    `/evidence/${evidenceId}/submit-for-review`,
    { comments }
  )
  return response.data
}

export const approveEvidence = async (
  evidenceId: number,
  comments?: string
): Promise<EvidenceItem> => {
  const response = await api.post<EvidenceItem>(
    `/evidence/${evidenceId}/approve`,
    { comments }
  )
  return response.data
}

export const rejectEvidence = async (
  evidenceId: number,
  comments: string
): Promise<EvidenceItem> => {
  const response = await api.post<EvidenceItem>(
    `/evidence/${evidenceId}/reject`,
    { comments }
  )
  return response.data
}
