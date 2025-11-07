import api from './api'

export interface DashboardMetrics {
  assessments: {
    total: number
    active: number
    completed: number
  }
  findings: {
    total: number
    open: number
    resolved: number
    overdue: number
    by_severity: {
      critical: number
      high: number
      medium: number
      low: number
    }
  }
  controls: {
    total: number
    tested: number
    passed: number
    failed: number
    compliance_score: number
  }
  evidence: {
    total: number
  }
  recent_activity: {
    new_assessments: number
    new_findings: number
    resolved_findings: number
  }
  risk_score: number
  agency_id: number
}

export interface TrendData {
  created: { date: string; count: number }[]
  completed: { date: string; count: number }[]
}

export interface FindingTrendData {
  created: { date: string; count: number }[]
  resolved: { date: string; count: number }[]
}

export interface SeverityBreakdown {
  [severity: string]: {
    open: number
    in_progress: number
    resolved: number
    validated: number
    closed: number
  }
}

export interface ControlTestingStats {
  total_controls: number
  never_tested: number
  recently_tested: number
  tested_90_days: number
  by_status: {
    passed: number
    failed: number
    needs_improvement: number
    pending: number
  }
  testing_coverage: number
}

export interface WorkloadData {
  user_id: number
  username: string
  assigned_assessments: number
  assigned_findings: number
  overdue_findings: number
  due_soon_findings: number
}

export const analyticsService = {
  // Get dashboard metrics
  getDashboard: async () => {
    const response = await api.get<DashboardMetrics>('/analytics/dashboard')
    return response.data
  },

  // Get assessment trends
  getAssessmentTrends: async (days: number = 30) => {
    const response = await api.get<TrendData>('/analytics/assessments/trends', {
      params: { days }
    })
    return response.data
  },

  // Get finding trends
  getFindingTrends: async (days: number = 30) => {
    const response = await api.get<FindingTrendData>('/analytics/findings/trends', {
      params: { days }
    })
    return response.data
  },

  // Get findings severity breakdown
  getSeverityBreakdown: async (assessment_id?: number) => {
    const response = await api.get<SeverityBreakdown>('/analytics/findings/severity-breakdown', {
      params: assessment_id ? { assessment_id } : {}
    })
    return response.data
  },

  // Get control testing stats
  getControlTestingStats: async () => {
    const response = await api.get<ControlTestingStats>('/analytics/controls/testing-stats')
    return response.data
  },

  // Get my workload
  getMyWorkload: async () => {
    const response = await api.get<WorkloadData>('/analytics/my-workload')
    return response.data
  }
}

export default analyticsService
