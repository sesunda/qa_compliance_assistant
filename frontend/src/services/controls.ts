import { api } from './api'

export interface ControlSummary {
  id: number
  project_id: number
  agency_id: number
  name: string
  description?: string | null
  control_type?: string | null
  status: string
  created_at: string
  updated_at: string
}

export interface RecordTestResultData {
  test_result: string
  assessment_score: number
  test_notes?: string
}

export interface SubmitReviewData {
  review_status: string
  review_notes: string
}

export const fetchControls = async (): Promise<ControlSummary[]> => {
  const response = await api.get<ControlSummary[]>('/controls/')
  return response.data
}

export const recordTestResult = async (
  controlId: number,
  data: RecordTestResultData
): Promise<void> => {
  await api.post(`/controls/${controlId}/test`, data)
}

export const submitReview = async (
  controlId: number,
  data: SubmitReviewData
): Promise<void> => {
  await api.post(`/controls/${controlId}/review`, data)
}

const controlsService = {
  fetchControls,
  recordTestResult,
  submitReview,
}

export default controlsService
